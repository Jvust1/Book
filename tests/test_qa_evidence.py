"""Evidence retrieval and citation-integrity tests for Phase 1F textbook QA."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

from runtime import CourseRuntime, SourceResolver
from runtime.qa_evidence import (
    CitationVerifier,
    EvidenceBuilder,
    EvidenceGate,
    QAEvidenceUnavailableError,
    QuestionProbeBuilder,
    normalize_history,
)
from runtime.qa_models import EvidenceItem, EvidencePack, ModelResponse, QAHistoryMessage
from tests.runtime_fixture_factory import main_book_entry, make_repo, write_course, write_ready_book


REPO_ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = "functional_analysis_course"
BOOK_ID = "stein_shakarchi_functional_analysis_2011"
FORBIDDEN_INTERNAL_KEYS = {
    "book_version_id",
    "logical_book_id",
    "provenance",
    "identity",
    "retriever_id",
}


class QuestionProbeBuilderTests(unittest.TestCase):
    def test_builds_bounded_deterministic_chinese_and_latin_probes(self) -> None:
        holder = QuestionProbeBuilder.build("  Hölder 不等式的作用是什么？  ")
        banach = QuestionProbeBuilder.build("什么是巴拿赫空间？")

        self.assertEqual(holder[0], "Hölder 不等式的作用是什么？")
        self.assertIn("Hölder", holder)
        self.assertIn("巴拿赫空间", banach)
        self.assertLessEqual(len(holder), 24)
        self.assertLessEqual(len(banach), 24)
        self.assertEqual(holder, QuestionProbeBuilder.build("Hölder 不等式的作用是什么？"))
        self.assertEqual(len(holder), len(set(holder)))


class HistoryBoundingTests(unittest.TestCase):
    def test_keeps_only_recent_six_messages_with_total_text_at_most_6000(self) -> None:
        history = tuple(
            QAHistoryMessage(
                role="user" if index % 2 == 0 else "assistant",
                content=f"m{index}:" + ("x" * 1200),
            )
            for index in range(8)
        )

        normalized = normalize_history(history)

        self.assertLessEqual(len(normalized), 6)
        self.assertLessEqual(sum(len(row.content) for row in normalized), 6000)
        self.assertTrue(normalized[-1].content.startswith("m7:"))
        self.assertFalse(any(row.content.startswith("m0:") for row in normalized))


class EvidenceFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.repo = make_repo(Path(self.tempdir.name))
        self.book_dir = self.repo / "books" / "fixture-book"
        self.course_dir = self.repo / "courses" / "fixture-course"

    def _open_course(self, *, long_evidence: bool = False) -> CourseRuntime:
        if long_evidence:
            objects = [
                {
                    "type": "definition",
                    "id": f"def_common_{index}",
                    "name_zh": f"共同概念 {index}",
                    "content_zh": (f"证据{index}-" + ("甲" * 1990)),
                    "anchor": {
                        "pdf_page": 1,
                        "printed_page": 1,
                        "source_anchor": None,
                    },
                }
                for index in range(10)
            ]
            search_records = [
                {
                    "id": f"def_common_{index}",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "name_zh": f"共同概念 {index}",
                    "pdf_page": 1,
                    "printed_page": 1,
                }
                for index in range(10)
            ]
        else:
            objects = [
                {
                    "type": "definition",
                    "id": "def_a",
                    "name_zh": "甲概念",
                    "content_zh": "甲概念只在 A 节定义。",
                    "anchor": {"pdf_page": 1, "printed_page": 1},
                },
                {
                    "type": "definition",
                    "id": "def_b",
                    "name_zh": "乙概念",
                    "content_zh": "乙概念只在 B 节定义。",
                    "anchor": {"pdf_page": 2, "printed_page": 2},
                },
            ]
            search_records = [
                {
                    "id": "def_a",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "name_zh": "甲概念",
                    "pdf_page": 1,
                    "printed_page": 1,
                },
                {
                    "id": "def_b",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "name_zh": "乙概念",
                    "pdf_page": 2,
                    "printed_page": 2,
                },
            ]

        write_ready_book(
            self.book_dir,
            book_id="fixture_book",
            objects=objects,
            sections=[
                {
                    "id": "sec_a",
                    "number": "1",
                    "title_en": "Section A",
                    "title_zh": "A 节",
                    "pdf_pages": [1, 1],
                    "printed_pages": [1, 1],
                },
                {
                    "id": "sec_b",
                    "number": "2",
                    "title_en": "Section B",
                    "title_zh": "B 节",
                    "pdf_pages": [2, 2],
                    "printed_pages": [2, 2],
                },
            ],
            search_records=search_records,
        )
        write_course(
            self.course_dir,
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
        )
        return CourseRuntime.open(self.course_dir)

    def test_builder_re_resolves_canonical_metadata_and_respects_budgets(self) -> None:
        course = self._open_course(long_evidence=True)
        pack = EvidenceBuilder.from_course(course).build(
            "共同概念",
            section_id="sec_a",
            limit=8,
        )

        self.assertLessEqual(len(pack.evidence), 8)
        self.assertLessEqual(
            sum(len(row.content_zh or "") + len(row.formula or "") for row in pack.evidence),
            12000,
        )
        self.assertTrue(pack.evidence)
        for row in pack.evidence:
            self.assertEqual(row.course_id, "fixture_course")
            self.assertEqual(row.book_id, "fixture_book")
            self.assertEqual(row.chapter_id, "chapter_01")
            self.assertEqual(row.section_id, "sec_a")
            self.assertEqual(row.type_zh, "定义")
            self.assertTrue(
                FORBIDDEN_INTERNAL_KEYS.isdisjoint(field.name for field in fields(row))
            )
        self.assertIsNone(pack.evidence[0].source_anchor)

    def test_builder_scope_filter_uses_real_section_identity(self) -> None:
        course = self._open_course()
        section_pack = EvidenceBuilder.from_course(course).build(
            "乙概念",
            section_id="sec_a",
            limit=8,
        )
        book_pack = EvidenceBuilder.from_course(course).build(
            "乙概念",
            section_id=None,
            limit=8,
        )

        self.assertEqual(section_pack.evidence, ())
        self.assertEqual([row.source_id for row in book_pack.evidence], ["def_b"])

    def test_missing_search_index_is_infrastructure_unavailable(self) -> None:
        course = self._open_course()
        path = course.main_book().search_index_path
        self.assertIsNotNone(path)
        Path(path).unlink()

        with self.assertRaises(QAEvidenceUnavailableError):
            EvidenceBuilder.from_course(course).build("甲概念", section_id=None, limit=8)

    def test_gate_requires_real_content_and_more_than_type_only_score(self) -> None:
        base = dict(
            evidence_id="E1",
            source_kind="object",
            source_id="def_a",
            object_type="definition",
            title_zh="甲概念",
            title_en=None,
            number=None,
            formula=None,
            source_anchor=None,
            pdf_page=1,
            printed_page=1,
            course_id="fixture_course",
            book_id="fixture_book",
            chapter_id="chapter_01",
            section_id="sec_a",
            type_zh="定义",
        )
        pure_title = EvidencePack(
            course_id="fixture_course",
            book_id="fixture_book",
            question="甲概念",
            evidence=(EvidenceItem(**base, content_zh=None, search_score=1000),),
        )
        type_only = EvidencePack(
            course_id="fixture_course",
            book_id="fixture_book",
            question="definition",
            evidence=(EvidenceItem(**base, content_zh="真实教材内容", search_score=300),),
        )
        strong = EvidencePack(
            course_id="fixture_course",
            book_id="fixture_book",
            question="甲概念",
            evidence=(EvidenceItem(**base, content_zh="真实教材内容", search_score=1000),),
        )

        self.assertEqual(EvidenceGate.status(pure_title), "insufficient_evidence")
        self.assertEqual(EvidenceGate.status(type_only), "insufficient_evidence")
        self.assertEqual(EvidenceGate.status(strong), "sufficient")

    def test_citation_verifier_projects_server_owned_v2_metadata(self) -> None:
        course = self._open_course()
        pack = EvidenceBuilder.from_course(course).build("甲概念", section_id=None, limit=8)
        response = ModelResponse.from_mapping(
            {
                "answer": "基于教材证据的回答",
                "evidence_ids": ["E1", "E1"],
                "insufficient_evidence": False,
                "answer_style": "brief",
            }
        )

        citations = CitationVerifier.from_course(course).verify(pack, response)

        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].evidence_id, "E1")
        self.assertEqual(citations[0].source_id, "def_a")
        self.assertEqual(citations[0].chapter_id, "chapter_01")
        self.assertEqual(citations[0].section_id, "sec_a")
        self.assertEqual(citations[0].type_zh, "定义")
        self.assertTrue(
            FORBIDDEN_INTERNAL_KEYS.isdisjoint(
                field.name for field in fields(citations[0])
            )
        )


class RealFunctionalAnalysisEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.course = CourseRuntime.open(REPO_ROOT / "courses" / "functional-analysis")

    def test_real_natural_language_chinese_question_finds_evidence(self) -> None:
        pack = EvidenceBuilder.from_course(self.course).build(
            "什么是巴拿赫空间？",
            section_id=None,
            limit=8,
        )

        self.assertEqual(pack.course_id, COURSE_ID)
        self.assertEqual(pack.book_id, BOOK_ID)
        self.assertTrue(pack.evidence)
        self.assertEqual(pack.evidence[0].evidence_id, "E1")
        self.assertGreater(pack.evidence[0].search_score, 300)
        for row in pack.evidence:
            resolved = SourceResolver(self.course).resolve(row.source_kind, row.source_id)
            self.assertEqual(resolved.book_id, BOOK_ID)


if __name__ == "__main__":
    unittest.main()