"""Contract tests for the Phase 1F textbook QA provider boundary."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
import unittest

from runtime import (
    AnswerProviderUnavailableError,
    DeterministicFakeAnswerProvider,
    EvidenceItem,
    EvidencePack,
    ProviderRequest,
    QAResult,
    UnavailableAnswerProvider,
)
from runtime.qa_models import (
    ModelResponse,
    ModelResponseValidationError,
    QAHistoryMessage,
)


COURSE_ID = "functional_analysis_course"
BOOK_ID = "stein_shakarchi_functional_analysis_2011"


def evidence(evidence_id: str = "E1") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_kind="object",
        source_id="obj_holder",
        object_type="theorem",
        title_zh="Hölder 不等式",
        title_en="Holder inequality",
        number="1.4",
        formula="|∫fg| ≤ ||f||p ||g||q",
        content_zh="教材中的确定性内容",
        source_anchor="anchor_holder",
        pdf_page=42,
        printed_page=23,
        search_score=1000,
        course_id=COURSE_ID,
        book_id=BOOK_ID,
        chapter_id="ch01",
        section_id="ch01_s01",
        type_zh="定理",
    )


def pack() -> EvidencePack:
    return EvidencePack(
        course_id=COURSE_ID,
        book_id=BOOK_ID,
        question="Hölder 不等式是什么？",
        evidence=(evidence(),),
        scope_requested="book",
        scope_used="book",
    )


class QAProviderContractTests(unittest.TestCase):
    def test_v2_history_and_evidence_keep_canonical_scope_metadata(self) -> None:
        history = QAHistoryMessage(role="user", content="前一个问题")
        item = evidence()

        self.assertEqual(history.role, "user")
        self.assertEqual(history.content, "前一个问题")
        self.assertEqual(item.course_id, COURSE_ID)
        self.assertEqual(item.book_id, BOOK_ID)
        self.assertEqual(item.chapter_id, "ch01")
        self.assertEqual(item.section_id, "ch01_s01")
        self.assertEqual(item.type_zh, "定理")

    def test_model_response_strictly_validates_success_shape(self) -> None:
        valid = ModelResponse.from_mapping(
            {
                "answer": "巴拿赫空间是完备赋范线性空间。",
                "evidence_ids": ["E1"],
                "insufficient_evidence": False,
                "answer_style": "brief",
            }
        )
        self.assertEqual(valid.answer, "巴拿赫空间是完备赋范线性空间。")
        self.assertEqual(valid.evidence_ids, ("E1",))
        self.assertFalse(valid.insufficient_evidence)
        self.assertEqual(valid.answer_style, "brief")

        with self.assertRaises(ModelResponseValidationError):
            ModelResponse.from_mapping(
                {
                    "answer": "回答",
                    "evidence_ids": [],
                    "insufficient_evidence": False,
                    "answer_style": "brief",
                }
            )

        with self.assertRaises(ModelResponseValidationError):
            ModelResponse.from_mapping(
                {
                    "answer": "回答",
                    "evidence_ids": ["E1"],
                    "insufficient_evidence": False,
                    "answer_style": "essay",
                }
            )

    def test_model_response_accepts_explicit_insufficient_shape(self) -> None:
        result = ModelResponse.from_mapping(
            {
                "answer": None,
                "evidence_ids": [],
                "insufficient_evidence": True,
                "answer_style": "explain",
            }
        )

        self.assertIsNone(result.answer)
        self.assertEqual(result.evidence_ids, ())
        self.assertTrue(result.insufficient_evidence)
        self.assertEqual(result.answer_style, "explain")

    def test_model_response_rejects_unknown_or_wrong_typed_fields(self) -> None:
        invalid_rows = [
            {
                "answer": "回答",
                "evidence_ids": ["E1"],
                "insufficient_evidence": False,
                "answer_style": "brief",
                "source_id": "fabricated",
            },
            {
                "answer": "回答",
                "evidence_ids": "E1",
                "insufficient_evidence": False,
                "answer_style": "brief",
            },
            {
                "answer": "回答",
                "evidence_ids": ["E1"],
                "insufficient_evidence": "false",
                "answer_style": "brief",
            },
            {
                "answer": "   ",
                "evidence_ids": ["E1"],
                "insufficient_evidence": False,
                "answer_style": "brief",
            },
        ]
        for row in invalid_rows:
            with self.subTest(row=row):
                with self.assertRaises(ModelResponseValidationError):
                    ModelResponse.from_mapping(row)

    def test_provider_request_is_built_only_from_evidence_pack(self) -> None:
        request = ProviderRequest.from_pack(pack())

        self.assertEqual(request.question, "Hölder 不等式是什么？")
        self.assertEqual(request.course_id, COURSE_ID)
        self.assertEqual(request.book_id, BOOK_ID)
        self.assertEqual(request.evidence, (evidence(),))
        self.assertEqual(
            {field.name for field in fields(request)},
            {"question", "course_id", "book_id", "evidence"},
        )
        self.assertFalse(hasattr(request, "repository_root"))
        self.assertFalse(hasattr(request, "browser_state"))
        self.assertFalse(hasattr(request, "api_key"))

    def test_contract_dataclasses_are_frozen(self) -> None:
        item = evidence()
        request = ProviderRequest.from_pack(pack())
        history = QAHistoryMessage(role="assistant", content="历史回答")

        with self.assertRaises(FrozenInstanceError):
            item.source_id = "mutated"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            request.question = "mutated"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            history.content = "mutated"  # type: ignore[misc]

    def test_fake_provider_cites_only_supplied_ids(self) -> None:
        result = DeterministicFakeAnswerProvider().answer(ProviderRequest.from_pack(pack()))

        self.assertEqual(result.cited_evidence_ids, ("E1",))
        self.assertIn("Hölder", result.answer_text)
        self.assertNotIn("obj_holder", result.answer_text)

    def test_fake_provider_is_deterministic(self) -> None:
        request = ProviderRequest.from_pack(pack())
        provider = DeterministicFakeAnswerProvider()

        self.assertEqual(provider.answer(request), provider.answer(request))

    def test_unavailable_provider_fails_explicitly(self) -> None:
        with self.assertRaises(AnswerProviderUnavailableError):
            UnavailableAnswerProvider().answer(ProviderRequest.from_pack(pack()))

    def test_qa_result_constructors_expose_v2_scope_and_insufficiency(self) -> None:
        generated = QAResult.generated(
            course_id=COURSE_ID,
            book_id=BOOK_ID,
            question="Hölder 不等式是什么？",
            answer="基于教材证据的生成回答",
            citations=(),
            answer_style="brief",
            scope_requested="book",
            scope_used="book",
        )
        notice = QAResult.system_notice(
            course_id=COURSE_ID,
            book_id=BOOK_ID,
            question="不存在的主题是什么？",
            scope_requested="section_then_book",
            scope_used="book",
        )

        self.assertEqual(generated.answer_kind, "generated")
        self.assertEqual(generated.evidence_status, "sufficient")
        self.assertEqual(generated.answer_style, "brief")
        self.assertEqual(generated.scope_requested, "book")
        self.assertEqual(generated.scope_used, "book")
        self.assertFalse(generated.insufficient_evidence)
        self.assertIsNone(generated.message)

        self.assertEqual(notice.answer_kind, "system_notice")
        self.assertEqual(notice.evidence_status, "insufficient_evidence")
        self.assertIsNone(notice.answer)
        self.assertIsNone(notice.answer_style)
        self.assertEqual(notice.scope_requested, "section_then_book")
        self.assertEqual(notice.scope_used, "book")
        self.assertTrue(notice.insufficient_evidence)
        self.assertEqual(
            notice.message,
            "根据当前教材中检索到的内容，暂时无法可靠回答这个问题。",
        )
        self.assertEqual(notice.citations, ())


if __name__ == "__main__":
    unittest.main()
