"""Evidence retrieval and citation-integrity tests for Phase 1F textbook QA."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime import (
    AnswerProviderInvalidResponseError,
    CourseRuntime,
    EvidenceItem,
    EvidencePack,
    ProviderAnswer,
    SourceResolver,
)
from runtime.qa_evidence import (
    CitationVerifier,
    EvidencePolicy,
    EvidenceRetriever,
    QAEvidenceUnavailableError,
    QuestionProbeBuilder,
)
from tests.runtime_fixture_factory import main_book_entry, make_repo, write_course, write_ready_book


REPO_ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = "functional_analysis_course"
BOOK_ID = "stein_shakarchi_functional_analysis_2011"


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


class EvidenceFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.repo = make_repo(Path(self.tempdir.name))
        self.book_dir = self.repo / "books" / "fixture-book"
        self.course_dir = self.repo / "courses" / "fixture-course"

    def _open_course(self) -> CourseRuntime:
        write_ready_book(
            self.book_dir,
            book_id="fixture_book",
            objects=[
                {
                    "type": "definition",
                    "id": "def_banach",
                    "name_zh": "巴拿赫空间",
                    "name_en": "Banach space",
                    "number": "1.1",
                    "content_zh": "完备赋范线性空间称为巴拿赫空间。",
                    "anchor": {
                        "pdf_page": 1,
                        "printed_page": 1,
                        "source_anchor": "fixture_book:pdf:1:def_banach",
                    },
                },
                {
                    "type": "definition",
                    "id": "def_banach_duplicate_title",
                    "name_zh": "巴拿赫空间补充说明",
                    "name_en": "Banach space note",
                    "number": "1.2",
                    "anchor": {
                        "pdf_page": 2,
                        "printed_page": 2,
                        "source_anchor": "fixture_book:pdf:2:def_banach_note",
                    },
                },
            ],
            search_records=[
                {
                    "id": "def_banach",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "name_zh": "巴拿赫空间",
                    "name_en": "Banach space",
                    "number": "1.1",
                    "pdf_page": 1,
                    "printed_page": 1,
                    "source_anchor": "fixture_book:pdf:1:def_banach",
                },
                {
                    "id": "def_banach_duplicate_title",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "name_zh": "巴拿赫空间补充说明",
                    "name_en": "Banach space note",
                    "number": "1.2",
                    "pdf_page": 2,
                    "printed_page": 2,
                    "source_anchor": "fixture_book:pdf:2:def_banach_note",
                },
            ],
        )
        write_course(
            self.course_dir,
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
        )
        return CourseRuntime.open(self.course_dir)

    def test_retriever_deduplicates_probes_and_re_resolves_canonical_source(self) -> None:
        course = self._open_course()
        pack = EvidenceRetriever.from_course(course).retrieve("什么是巴拿赫空间？", limit=8)

        self.assertEqual(pack.course_id, "fixture_course")
        self.assertEqual(pack.book_id, "fixture_book")
        self.assertTrue(pack.evidence)
        self.assertEqual(pack.evidence[0].evidence_id, "E1")
        self.assertEqual(pack.evidence[0].source_id, "def_banach")
        self.assertEqual(
            len({(row.source_kind, row.source_id) for row in pack.evidence}),
            len(pack.evidence),
        )

        resolved = SourceResolver(course).resolve(
            pack.evidence[0].source_kind,
            pack.evidence[0].source_id,
        )
        self.assertEqual(pack.evidence[0].title_zh, resolved.title_zh)
        self.assertEqual(pack.evidence[0].content_zh, resolved.content_zh)
        self.assertEqual(pack.evidence[0].source_anchor, resolved.source_anchor)
        self.assertEqual(pack.evidence[0].pdf_page, resolved.pdf_page)

    def test_missing_search_index_is_infrastructure_unavailable(self) -> None:
        course = self._open_course()
        path = course.main_book().search_index_path
        self.assertIsNotNone(path)
        Path(path).unlink()

        with self.assertRaises(QAEvidenceUnavailableError):
            EvidenceRetriever.from_course(course).retrieve("巴拿赫空间", limit=8)

    def test_policy_is_conservative_at_type_only_threshold(self) -> None:
        weak = EvidencePack(
            course_id="fixture_course",
            book_id="fixture_book",
            question="definition",
            evidence=(
                EvidenceItem(
                    evidence_id="E1",
                    source_kind="object",
                    source_id="def_banach",
                    object_type="definition",
                    title_zh="巴拿赫空间",
                    title_en="Banach space",
                    number="1.1",
                    formula=None,
                    content_zh=None,
                    source_anchor="fixture_book:pdf:1:def_banach",
                    pdf_page=1,
                    printed_page=1,
                    search_score=300,
                ),
            ),
        )
        strong = EvidencePack(
            course_id=weak.course_id,
            book_id=weak.book_id,
            question="巴拿赫空间",
            evidence=(
                EvidenceItem(**{**weak.evidence[0].__dict__, "search_score": 1000}),
            ),
        )
        empty = EvidencePack(
            course_id=weak.course_id,
            book_id=weak.book_id,
            question="none",
            evidence=(),
        )

        self.assertEqual(EvidencePolicy.status(empty), "insufficient_evidence")
        self.assertEqual(EvidencePolicy.status(weak), "insufficient_evidence")
        self.assertEqual(EvidencePolicy.status(strong), "sufficient")

    def test_citation_verifier_deduplicates_and_projects_server_owned_metadata(self) -> None:
        course = self._open_course()
        pack = EvidenceRetriever.from_course(course).retrieve("巴拿赫空间", limit=8)
        answer = ProviderAnswer(
            answer_text="基于教材证据的回答",
            cited_evidence_ids=("E1", "E1"),
        )

        citations = CitationVerifier.from_course(course).verify(pack, answer)

        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].citation_id, "C1")
        self.assertEqual(citations[0].evidence_id, "E1")
        self.assertEqual(citations[0].source_id, pack.evidence[0].source_id)
        self.assertEqual(citations[0].source_anchor, pack.evidence[0].source_anchor)
        self.assertEqual(citations[0].pdf_page, pack.evidence[0].pdf_page)

    def test_citation_verifier_rejects_unknown_or_missing_citations(self) -> None:
        course = self._open_course()
        pack = EvidenceRetriever.from_course(course).retrieve("巴拿赫空间", limit=8)
        verifier = CitationVerifier.from_course(course)

        with self.assertRaises(AnswerProviderInvalidResponseError):
            verifier.verify(
                pack,
                ProviderAnswer(answer_text="unsupported", cited_evidence_ids=("E99",)),
            )
        with self.assertRaises(AnswerProviderInvalidResponseError):
            verifier.verify(
                pack,
                ProviderAnswer(answer_text="unsupported", cited_evidence_ids=()),
            )


class RealFunctionalAnalysisEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.course = CourseRuntime.open(REPO_ROOT / "courses" / "functional-analysis")

    def test_real_natural_language_chinese_question_finds_evidence(self) -> None:
        pack = EvidenceRetriever.from_course(self.course).retrieve("什么是巴拿赫空间？", limit=8)

        self.assertEqual(pack.course_id, COURSE_ID)
        self.assertEqual(pack.book_id, BOOK_ID)
        self.assertTrue(pack.evidence)
        self.assertEqual(pack.evidence[0].evidence_id, "E1")
        self.assertGreater(pack.evidence[0].search_score, 300)

    def test_real_mixed_language_question_finds_holder_evidence(self) -> None:
        pack = EvidenceRetriever.from_course(self.course).retrieve(
            "Hölder 不等式的作用是什么？",
            limit=8,
        )

        self.assertTrue(pack.evidence)
        self.assertTrue(any("Hölder" in (row.title_zh or row.title_en or "") for row in pack.evidence))
        for row in pack.evidence:
            resolved = SourceResolver(self.course).resolve(row.source_kind, row.source_id)
            self.assertEqual(resolved.book_id, BOOK_ID)


if __name__ == "__main__":
    unittest.main()
