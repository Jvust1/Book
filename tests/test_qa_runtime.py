"""Orchestration tests for the Phase 1F textbook QA runtime."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime import (
    AnswerProviderInvalidResponseError,
    AnswerProviderUnavailableError,
    CourseRuntime,
    DeterministicFakeAnswerProvider,
    ProviderAnswer,
    QARuntime,
    QAQuestionError,
    UnavailableAnswerProvider,
)
from tests.runtime_fixture_factory import main_book_entry, make_repo, write_course, write_ready_book


class FailIfCalledProvider:
    def __init__(self) -> None:
        self.called = False

    def answer(self, request):
        self.called = True
        raise AssertionError("provider must not be called")


class InvalidCitationProvider:
    def answer(self, request):
        del request
        return ProviderAnswer(
            answer_text="这是一个带有非法 citation 的回答",
            cited_evidence_ids=("E99",),
        )


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
                }
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
                }
            ],
        )
        write_course(
            course_dir,
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
        )
        self.course = CourseRuntime.open(course_dir)

    def test_rejects_blank_overlong_and_invalid_evidence_limit(self) -> None:
        runtime = QARuntime.from_course(
            self.course,
            provider=DeterministicFakeAnswerProvider(),
        )

        for question in ("", "   "):
            with self.subTest(question=question):
                with self.assertRaises(QAQuestionError):
                    runtime.answer(question)
        with self.assertRaises(QAQuestionError):
            runtime.answer("x" * 1001)
        for limit in (0, 13, True, 1.5):
            with self.subTest(limit=limit):
                with self.assertRaises(QAQuestionError):
                    runtime.answer("巴拿赫空间是什么？", evidence_limit=limit)  # type: ignore[arg-type]

    def test_insufficient_evidence_does_not_call_provider(self) -> None:
        provider = FailIfCalledProvider()
        runtime = QARuntime.from_course(self.course, provider=provider)

        result = runtime.answer("definitely-no-such-topic-92831")

        self.assertFalse(provider.called)
        self.assertEqual(result.answer_kind, "system_notice")
        self.assertEqual(result.evidence_status, "insufficient_evidence")
        self.assertEqual(result.answer, "现有教材证据不足，暂不能给出可靠回答。")
        self.assertEqual(result.citations, ())

    def test_sufficient_fake_provider_answer_has_verified_citation(self) -> None:
        runtime = QARuntime.from_course(
            self.course,
            provider=DeterministicFakeAnswerProvider(),
        )

        result = runtime.answer("什么是巴拿赫空间？")

        self.assertEqual(result.course_id, "fixture_course")
        self.assertEqual(result.book_id, "fixture_book")
        self.assertEqual(result.question, "什么是巴拿赫空间？")
        self.assertEqual(result.answer_kind, "generated")
        self.assertEqual(result.evidence_status, "sufficient")
        self.assertTrue(result.citations)
        self.assertEqual(result.citations[0].evidence_id, "E1")
        self.assertEqual(result.citations[0].source_id, "def_banach")
        self.assertIn("巴拿赫空间", result.answer)

    def test_provider_unavailable_remains_distinct(self) -> None:
        runtime = QARuntime.from_course(
            self.course,
            provider=UnavailableAnswerProvider(),
        )

        with self.assertRaises(AnswerProviderUnavailableError):
            runtime.answer("什么是巴拿赫空间？")

    def test_invalid_provider_citation_remains_distinct(self) -> None:
        runtime = QARuntime.from_course(
            self.course,
            provider=InvalidCitationProvider(),
        )

        with self.assertRaises(AnswerProviderInvalidResponseError):
            runtime.answer("什么是巴拿赫空间？")


if __name__ == "__main__":
    unittest.main()
