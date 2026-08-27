"""Contract tests for the Phase 1F v2 textbook QA provider boundary."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
import unittest

import runtime.qa_provider as qa_provider
from runtime import EvidenceItem, EvidencePack, QAResult
from runtime.qa_models import (
    ModelRequest,
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


def request() -> ModelRequest:
    return ModelRequest.from_pack(
        pack(),
        history=(QAHistoryMessage(role="user", content="前一个问题"),),
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

    def test_model_request_is_built_only_from_bounded_runtime_context(self) -> None:
        model_request = request()

        self.assertEqual(model_request.question, "Hölder 不等式是什么？")
        self.assertEqual(model_request.course_id, COURSE_ID)
        self.assertEqual(model_request.book_id, BOOK_ID)
        self.assertEqual(model_request.evidence, (evidence(),))
        self.assertEqual(model_request.history[0].content, "前一个问题")
        self.assertEqual(
            {field.name for field in fields(model_request)},
            {
                "question",
                "course_id",
                "book_id",
                "section_id",
                "history",
                "evidence",
                "allowed_answer_styles",
            },
        )
        self.assertFalse(hasattr(model_request, "repository_root"))
        self.assertFalse(hasattr(model_request, "browser_state"))
        self.assertFalse(hasattr(model_request, "api_key"))

    def test_contract_dataclasses_are_frozen(self) -> None:
        item = evidence()
        model_request = request()
        history = QAHistoryMessage(role="assistant", content="历史回答")

        with self.assertRaises(FrozenInstanceError):
            item.source_id = "mutated"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            model_request.question = "mutated"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            history.content = "mutated"  # type: ignore[misc]

    def test_model_provider_protocol_and_fake_modes_exist(self) -> None:
        self.assertTrue(hasattr(qa_provider, "ModelProvider"))
        self.assertTrue(hasattr(qa_provider, "ModelProviderError"))
        self.assertTrue(hasattr(qa_provider, "ModelProviderUnavailableError"))
        self.assertTrue(hasattr(qa_provider, "ModelProviderInvalidResponseError"))
        self.assertTrue(hasattr(qa_provider, "DeterministicFakeModelProvider"))
        self.assertTrue(hasattr(qa_provider, "UnavailableModelProvider"))

    def test_fake_answer_mode_uses_only_first_supplied_evidence(self) -> None:
        provider_cls = getattr(qa_provider, "DeterministicFakeModelProvider", None)
        self.assertIsNotNone(provider_cls)
        provider = provider_cls(mode="answer")

        result = provider.answer(request())

        self.assertIsInstance(result, ModelResponse)
        self.assertEqual(result.evidence_ids, ("E1",))
        self.assertFalse(result.insufficient_evidence)
        self.assertEqual(result.answer_style, "brief")
        self.assertIn("Hölder", result.answer or "")
        self.assertNotIn("obj_holder", result.answer or "")
        self.assertEqual(result, provider.answer(request()))

    def test_fake_insufficient_mode_returns_second_gate_decline(self) -> None:
        provider_cls = getattr(qa_provider, "DeterministicFakeModelProvider", None)
        self.assertIsNotNone(provider_cls)

        result = provider_cls(mode="insufficient").answer(request())

        self.assertIsNone(result.answer)
        self.assertEqual(result.evidence_ids, ())
        self.assertTrue(result.insufficient_evidence)
        self.assertEqual(result.answer_style, "explain")

    def test_fake_invalid_citation_mode_returns_unknown_evidence_id(self) -> None:
        provider_cls = getattr(qa_provider, "DeterministicFakeModelProvider", None)
        self.assertIsNotNone(provider_cls)

        result = provider_cls(mode="invalid_citation").answer(request())

        self.assertFalse(result.insufficient_evidence)
        self.assertEqual(result.evidence_ids, ("E999",))

    def test_fake_empty_answer_mode_fails_closed(self) -> None:
        provider_cls = getattr(qa_provider, "DeterministicFakeModelProvider", None)
        error_cls = getattr(qa_provider, "ModelProviderInvalidResponseError", None)
        self.assertIsNotNone(provider_cls)
        self.assertIsNotNone(error_cls)

        with self.assertRaises(error_cls):
            provider_cls(mode="empty_answer").answer(request())

    def test_fake_unavailable_mode_raises_stable_unavailable_error(self) -> None:
        provider_cls = getattr(qa_provider, "DeterministicFakeModelProvider", None)
        error_cls = getattr(qa_provider, "ModelProviderUnavailableError", None)
        self.assertIsNotNone(provider_cls)
        self.assertIsNotNone(error_cls)

        with self.assertRaises(error_cls):
            provider_cls(mode="unavailable").answer(request())

    def test_unavailable_provider_fails_explicitly(self) -> None:
        provider_cls = getattr(qa_provider, "UnavailableModelProvider", None)
        error_cls = getattr(qa_provider, "ModelProviderUnavailableError", None)
        self.assertIsNotNone(provider_cls)
        self.assertIsNotNone(error_cls)

        with self.assertRaises(error_cls):
            provider_cls().answer(request())

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
