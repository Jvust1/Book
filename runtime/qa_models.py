"""Immutable internal contracts for source-backed textbook question answering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AnswerKind = Literal["generated", "system_notice"]
EvidenceStatus = Literal["sufficient", "insufficient_evidence"]


@dataclass(frozen=True)
class EvidenceItem:
    """One server-selected and source-resolved textbook evidence item."""

    evidence_id: str
    source_kind: str
    source_id: str
    object_type: str | None
    title_zh: str | None
    title_en: str | None
    number: str | None
    formula: str | None
    content_zh: str | None
    source_anchor: str | None
    pdf_page: int | None
    printed_page: int | str | None
    search_score: int


@dataclass(frozen=True)
class EvidencePack:
    """Bounded textbook context selected by trusted Runtime code."""

    course_id: str
    book_id: str
    question: str
    evidence: tuple[EvidenceItem, ...]


@dataclass(frozen=True)
class ProviderRequest:
    """The complete context an answer provider is allowed to receive."""

    question: str
    course_id: str
    book_id: str
    evidence: tuple[EvidenceItem, ...]

    @classmethod
    def from_pack(cls, pack: EvidencePack) -> "ProviderRequest":
        return cls(
            question=pack.question,
            course_id=pack.course_id,
            book_id=pack.book_id,
            evidence=pack.evidence,
        )


@dataclass(frozen=True)
class ProviderAnswer:
    """Provider-owned wording plus references to server-issued evidence IDs."""

    answer_text: str
    cited_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class QACitation:
    """Verified citation projected exclusively from server-owned evidence."""

    citation_id: str
    evidence_id: str
    source_kind: str
    source_id: str
    object_type: str | None
    number: str | None
    title_zh: str | None
    title_en: str | None
    source_anchor: str | None
    pdf_page: int | None
    printed_page: int | str | None


@dataclass(frozen=True)
class QAResult:
    """Canonical QA Runtime result before App/API DTO projection."""

    course_id: str
    book_id: str
    question: str
    answer_kind: AnswerKind
    evidence_status: EvidenceStatus
    answer: str
    citations: tuple[QACitation, ...]

    @classmethod
    def generated(
        cls,
        *,
        course_id: str,
        book_id: str,
        question: str,
        answer: str,
        citations: tuple[QACitation, ...],
    ) -> "QAResult":
        return cls(
            course_id=course_id,
            book_id=book_id,
            question=question,
            answer_kind="generated",
            evidence_status="sufficient",
            answer=answer,
            citations=citations,
        )

    @classmethod
    def system_notice(
        cls,
        *,
        course_id: str,
        book_id: str,
        question: str,
        answer: str,
        citations: tuple[QACitation, ...] = (),
    ) -> "QAResult":
        return cls(
            course_id=course_id,
            book_id=book_id,
            question=question,
            answer_kind="system_notice",
            evidence_status="insufficient_evidence",
            answer=answer,
            citations=citations,
        )
