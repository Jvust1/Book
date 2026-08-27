"""BookAppService QA projection and stable-error tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from runtime import DeterministicFakeAnswerProvider, ProviderAnswer

from app.api.errors import (
    AppUnavailableError,
    InvalidQAQuestionError,
    QAProviderInvalidResponseError,
)
from app.api.service import BookAppService


REPO_ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = "functional_analysis_course"
BOOK_ID = "stein_shakarchi_functional_analysis_2011"


class InvalidCitationProvider:
    def answer(self, request):
        del request
        return ProviderAnswer(
            answer_text="非法来源回答",
            cited_evidence_ids=("E999",),
        )


class BookAppQAServiceTests(unittest.TestCase):
    def test_fake_provider_projects_generated_answer_and_canonical_citations(self) -> None:
        service = BookAppService(
            REPO_ROOT,
            qa_provider=DeterministicFakeAnswerProvider(),
        )

        payload = service.ask(COURSE_ID, "什么是巴拿赫空间？")

        self.assertEqual(payload.course_id, COURSE_ID)
        self.assertEqual(payload.book_id, BOOK_ID)
        self.assertEqual(payload.question, "什么是巴拿赫空间？")
        self.assertEqual(payload.answer_kind, "generated")
        self.assertEqual(payload.evidence_status, "sufficient")
        self.assertTrue(payload.citations)
        first = payload.citations[0]
        self.assertEqual(first.source_kind, "object")
        self.assertTrue(first.source_id)
        self.assertTrue(first.evidence_id.startswith("E"))
        self.assertTrue(first.citation_id.startswith("C"))

    def test_default_service_provider_is_unavailable_not_fake(self) -> None:
        service = BookAppService(REPO_ROOT)

        with self.assertRaises(AppUnavailableError) as ctx:
            service.ask(COURSE_ID, "什么是巴拿赫空间？")

        self.assertEqual(ctx.exception.code, "qa_provider_unavailable")
        self.assertEqual(ctx.exception.user_message, "教材问答模型暂不可用")

    def test_invalid_question_maps_to_stable_input_error(self) -> None:
        service = BookAppService(
            REPO_ROOT,
            qa_provider=DeterministicFakeAnswerProvider(),
        )

        with self.assertRaises(InvalidQAQuestionError) as ctx:
            service.ask(COURSE_ID, "   ")

        self.assertEqual(ctx.exception.code, "invalid_qa_question")
        self.assertEqual(ctx.exception.user_message, "提问内容无效")

    def test_invalid_provider_citation_maps_to_distinct_gateway_error(self) -> None:
        service = BookAppService(REPO_ROOT, qa_provider=InvalidCitationProvider())

        with self.assertRaises(QAProviderInvalidResponseError) as ctx:
            service.ask(COURSE_ID, "什么是巴拿赫空间？")

        self.assertEqual(ctx.exception.code, "qa_provider_invalid_response")
        self.assertEqual(ctx.exception.user_message, "教材问答结果校验失败")

    def test_insufficient_evidence_is_normal_system_notice(self) -> None:
        service = BookAppService(
            REPO_ROOT,
            qa_provider=DeterministicFakeAnswerProvider(),
        )

        payload = service.ask(COURSE_ID, "definitely-no-such-topic-92831")

        self.assertEqual(payload.answer_kind, "system_notice")
        self.assertEqual(payload.evidence_status, "insufficient_evidence")
        self.assertEqual(payload.citations, [])
        self.assertEqual(payload.answer, "现有教材证据不足，暂不能给出可靠回答。")


if __name__ == "__main__":
    unittest.main()
