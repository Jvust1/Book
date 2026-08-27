"""Orchestration tests for the Phase 1F v2 textbook QA runtime."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime import CourseRuntime, QARuntime, QAQuestionError
from runtime.qa_models import ModelResponse, QAHistoryMessage
from runtime.qa_runtime import QASectionError
from tests.runtime_fixture_factory import main_book_entry, make_repo, write_course, write_ready_book


class RecordingModelProvider:
    def __init__(self, *, mode: str = "answer") -> None:
        self.mode = mode
        self.requests = []

    def answer(self, request):
        self.requests.append(request)
        if self.mode == "insufficient":
            return ModelResponse.from_mapping(
                {
                    "answer": None,
                    "evidence_ids": [],
                    "insufficient_evidence": True,
                    "answer_style": "explain",
                }
            )
        first = request.evidence[0]
        return ModelResponse.from_mapping(
            {
                "answer": f"根据教材：{first.content_zh or first.formula or first.title_zh}",
                "evidence_ids": [first.evidence_id],
                "insufficient_evidence": False,
                "answer_style": "brief",
            }
        )


class FailIfCalledProvider:
    def __init__(self) -> None:
        self.called = False

    def answer(self, request):
        self.called = True
        raise AssertionError(f"provider must not be called: {request!r}")


class QARuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        repo = make_repo(Path(self.tempdir.name))
        book_dir = repo / "books" / "fixture-book"
        course_dir = repo / "courses" / "fixture-course"
        write_ready_book(
            book_dir,
            book_id="fixture_book",
            objects=[
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
            ],
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
            search_records=[
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
            ],
        )
        write_course(
            course_dir,
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
        )
        self.course = CourseRuntime.open(course_dir)

    def test_rejects_blank_overlong_malformed_history_and_unknown_section(self) -> None:
        runtime = QARuntime.from_course(self.course, provider=RecordingModelProvider())

        for question in ("", "   "):
            with self.subTest(question=question):
                with self.assertRaises(QAQuestionError):
                    runtime.answer(question)
        with self.assertRaises(QAQuestionError):
            runtime.answer("x" * 1001)

        with self.assertRaises(QAQuestionError):
            runtime.answer(
                "甲概念是什么？",
                history=(QAHistoryMessage(role="system", content="非法"),),  # type: ignore[arg-type]
            )
        with self.assertRaises(QAQuestionError):
            runtime.answer(
                "甲概念是什么？",
                history=(QAHistoryMessage(role="user", content="   "),),
            )
        with self.assertRaises(QASectionError):
            runtime.answer("甲概念是什么？", section_id="missing_section")

    def test_section_evidence_stays_in_section_when_gate_is_sufficient(self) -> None:
        provider = RecordingModelProvider()
        runtime = QARuntime.from_course(self.course, provider=provider)

        result = runtime.answer("甲概念是什么？", section_id="sec_a")

        self.assertEqual(result.scope_requested, "section_then_book")
        self.assertEqual(result.scope_used, "section")
        self.assertFalse(result.insufficient_evidence)
        self.assertEqual(len(provider.requests), 1)
        self.assertTrue(provider.requests[0].evidence)
        self.assertTrue(all(row.section_id == "sec_a" for row in provider.requests[0].evidence))

    def test_section_gate_falls_back_to_whole_book(self) -> None:
        provider = RecordingModelProvider()
        runtime = QARuntime.from_course(self.course, provider=provider)

        result = runtime.answer("乙概念是什么？", section_id="sec_a")

        self.assertEqual(result.scope_requested, "section_then_book")
        self.assertEqual(result.scope_used, "book")
        self.assertEqual(result.citations[0].source_id, "def_b")
        self.assertEqual(len(provider.requests), 1)

    def test_course_mode_uses_book_scope_directly(self) -> None:
        provider = RecordingModelProvider()
        runtime = QARuntime.from_course(self.course, provider=provider)

        result = runtime.answer("乙概念是什么？")

        self.assertEqual(result.scope_requested, "book")
        self.assertEqual(result.scope_used, "book")
        self.assertEqual(result.citations[0].source_id, "def_b")

    def test_insufficient_server_gate_does_not_call_provider(self) -> None:
        provider = FailIfCalledProvider()
        runtime = QARuntime.from_course(self.course, provider=provider)

        result = runtime.answer("definitely-no-such-topic-92831", section_id="sec_a")

        self.assertFalse(provider.called)
        self.assertTrue(result.insufficient_evidence)
        self.assertEqual(result.answer_kind, "system_notice")
        self.assertIsNone(result.answer)
        self.assertEqual(result.scope_requested, "section_then_book")
        self.assertEqual(result.scope_used, "book")
        self.assertEqual(
            result.message,
            "根据当前教材中检索到的内容，暂时无法可靠回答这个问题。",
        )
        self.assertEqual(result.citations, ())

    def test_model_second_gate_can_decline_after_server_gate(self) -> None:
        provider = RecordingModelProvider(mode="insufficient")
        runtime = QARuntime.from_course(self.course, provider=provider)

        result = runtime.answer("甲概念是什么？", section_id="sec_a")

        self.assertEqual(len(provider.requests), 1)
        self.assertTrue(result.insufficient_evidence)
        self.assertIsNone(result.answer)
        self.assertEqual(result.citations, ())
        self.assertEqual(result.scope_used, "section")

    def test_history_is_bounded_and_sent_as_context_not_evidence(self) -> None:
        provider = RecordingModelProvider()
        runtime = QARuntime.from_course(self.course, provider=provider)
        history = tuple(
            QAHistoryMessage(
                role="user" if index % 2 == 0 else "assistant",
                content=f"m{index}:" + ("x" * 1200),
            )
            for index in range(8)
        )

        result = runtime.answer("甲概念是什么？", history=history)

        self.assertFalse(result.insufficient_evidence)
        request = provider.requests[0]
        self.assertLessEqual(len(request.history), 6)
        self.assertLessEqual(sum(len(row.content) for row in request.history), 6000)
        self.assertTrue(request.history[-1].content.startswith("m7:"))
        self.assertFalse(any(row.content.startswith("m0:") for row in request.history))
        self.assertTrue(all(hasattr(row, "source_id") for row in request.evidence))
        self.assertFalse(any(hasattr(row, "source_id") for row in request.history))


if __name__ == "__main__":
    unittest.main()
