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
    )


def pack() -> EvidencePack:
    return EvidencePack(
        course_id=COURSE_ID,
        book_id=BOOK_ID,
        question="Hölder 不等式是什么？",
        evidence=(evidence(),),
    )


class QAProviderContractTests(unittest.TestCase):
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

        with self.assertRaises(FrozenInstanceError):
            item.source_id = "mutated"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            request.question = "mutated"  # type: ignore[misc]

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

    def test_qa_result_constructors_keep_generated_and_system_notice_distinct(self) -> None:
        generated = QAResult.generated(
            course_id=COURSE_ID,
            book_id=BOOK_ID,
            question="Hölder 不等式是什么？",
            answer="基于教材证据的生成回答",
            citations=(),
        )
        notice = QAResult.system_notice(
            course_id=COURSE_ID,
            book_id=BOOK_ID,
            question="不存在的主题是什么？",
            answer="当前教材证据不足，暂不能可靠回答。",
            citations=(),
        )

        self.assertEqual(generated.answer_kind, "generated")
        self.assertEqual(generated.evidence_status, "sufficient")
        self.assertEqual(notice.answer_kind, "system_notice")
        self.assertEqual(notice.evidence_status, "insufficient_evidence")


if __name__ == "__main__":
    unittest.main()
