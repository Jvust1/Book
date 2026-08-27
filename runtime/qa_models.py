"""Immutable internal contracts for source-backed textbook question answering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping


AnswerKind = Literal["generated", "system_notice"]
EvidenceStatus = Literal["sufficient", "insufficient_evidence"]
AnswerStyle = Literal["brief", "explain", "compare", "proof"]
ScopeRequested = Literal["book", "section_then_book"]
ScopeUsed = Literal["section", "book"]
HistoryRole = Literal["user", "assistant"]

ANSWER_STYLES: tuple[AnswerStyle, ...] = ("brief", "explain", "compare", "proof")
INSUFFICIENT_EVIDENCE_MESSAGE = "根据当前教材中检索到的内容，暂时无法可靠回答这个问题。"


class ModelResponseValidationError(ValueError):
    """Raised when structured model output violates the trusted JSON contract."""


@dataclass(frozen=True)
class QAHistoryMessage:
    """One short-lived dialogue message; history is context, never textbook evidence."""

    role: HistoryRole
    content: str


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
    course_id: str | None = None
    book_id: str | None = None
    chapter_id: str | None = None
    section_id: str | None = None
    type_zh: str | None = None


@dataclass(frozen=True)
class EvidencePack:
    """Bounded textbook context selected by trusted Runtime code."""

    course_id: str
    book_id: str
    question: str
    evidence: tuple[EvidenceItem, ...]
    scope_requested: ScopeRequested = "book"
    scope_used: ScopeUsed = "book"


@dataclass(frozen=True)
class ModelRequest:
    """The complete bounded context a v2 model provider is allowed to receive."""

    question: str
    course_id: str
    book_id: str
    section_id: str | None
    history: tuple[QAHistoryMessage, ...]
    evidence: tuple[EvidenceItem, ...]
    allowed_answer_styles: tuple[AnswerStyle, ...] = ANSWER_STYLES

    @classmethod
    def from_pack(
        cls,
        pack: EvidencePack,
        *,
        section_id: str | None = None,
        history: tuple[QAHistoryMessage, ...] = (),
    ) -> "ModelRequest":
        return cls(
            question=pack.question,
            course_id=pack.course_id,
            book_id=pack.book_id,
            section_id=section_id,
            history=history,
            evidence=pack.evidence,
        )


@dataclass(frozen=True)
class ModelResponse:
    """Strict structured output accepted from a v2 answer model."""

    answer: str | None
    evidence_ids: tuple[str, ...]
    insufficient_evidence: bool
    answer_style: AnswerStyle

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "ModelResponse":
        if not isinstance(value, Mapping):
            raise ModelResponseValidationError("Model response must be a JSON object")

        expected = {"answer", "evidence_ids", "insufficient_evidence", "answer_style"}
        if set(value.keys()) != expected:
            raise ModelResponseValidationError(
                "Model response fields must be exactly answer, evidence_ids, "
                "insufficient_evidence and answer_style"
            )

        raw_insufficient = value["insufficient_evidence"]
        if not isinstance(raw_insufficient, bool):
            raise ModelResponseValidationError("insufficient_evidence must be a boolean")

        raw_style = value["answer_style"]
        if not isinstance(raw_style, str) or raw_style not in ANSWER_STYLES:
            raise ModelResponseValidationError(
                "answer_style must be one of brief, explain, compare or proof"
            )
        answer_style: AnswerStyle = raw_style  # type: ignore[assignment]

        raw_ids = value["evidence_ids"]
        if not isinstance(raw_ids, list):
            raise ModelResponseValidationError("evidence_ids must be a JSON array")
        ids: list[str] = []
        for raw_id in raw_ids:
            if not isinstance(raw_id, str) or not raw_id.strip():
                raise ModelResponseValidationError(
                    "Every evidence_ids item must be a non-blank string"
                )
            ids.append(raw_id.strip())

        raw_answer = value["answer"]
        if raw_answer is not None and not isinstance(raw_answer, str):
            raise ModelResponseValidationError("answer must be a string or null")
        answer = raw_answer.strip() if isinstance(raw_answer, str) else None

        if raw_insufficient:
            if answer == "":
                raise ModelResponseValidationError(
                    "Insufficient model answer must be null or non-blank when present"
                )
            return cls(
                answer=answer,
                evidence_ids=tuple(ids),
                insufficient_evidence=True,
                answer_style=answer_style,
            )

        if not answer:
            raise ModelResponseValidationError(
                "Sufficient model response must contain a non-blank answer"
            )
        if not ids:
            raise ModelResponseValidationError(
                "Sufficient model response must cite at least one evidence ID"
            )
        return cls(
            answer=answer,
            evidence_ids=tuple(ids),
            insufficient_evidence=False,
            answer_style=answer_style,
        )


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
    chapter_id: str | None = None
    section_id: str | None = None
    type_zh: str | None = None


@dataclass(frozen=True)
class QAResult:
    """Canonical QA Runtime result before App/API DTO projection."""

    course_id: str
    book_id: str
    question: str
    answer_kind: AnswerKind
    evidence_status: EvidenceStatus
    answer: str | None
    citations: tuple[QACitation, ...]
    answer_style: AnswerStyle | None = None
    scope_requested: ScopeRequested = "book"
    scope_used: ScopeUsed = "book"
    insufficient_evidence: bool = False
    message: str | None = None

    @classmethod
    def generated(
        cls,
        *,
        course_id: str,
        book_id: str,
        question: str,
        answer: str,
        citations: tuple[QACitation, ...],
        answer_style: AnswerStyle = "brief",
        scope_requested: ScopeRequested = "book",
        scope_used: ScopeUsed = "book",
    ) -> "QAResult":
        return cls(
            course_id=course_id,
            book_id=book_id,
            question=question,
            answer_kind="generated",
            evidence_status="sufficient",
            answer=answer,
            citations=citations,
            answer_style=answer_style,
            scope_requested=scope_requested,
            scope_used=scope_used,
            insufficient_evidence=False,
            message=None,
        )

    @classmethod
    def system_notice(
        cls,
        *,
        course_id: str,
        book_id: str,
        question: str,
        answer: str | None = None,
        citations: tuple[QACitation, ...] = (),
        scope_requested: ScopeRequested = "book",
        scope_used: ScopeUsed = "book",
        message: str = INSUFFICIENT_EVIDENCE_MESSAGE,
    ) -> "QAResult":
        return cls(
            course_id=course_id,
            book_id=book_id,
            question=question,
            answer_kind="system_notice",
            evidence_status="insufficient_evidence",
            answer=answer,
            citations=citations,
            answer_style=None,
            scope_requested=scope_requested,
            scope_used=scope_used,
            insufficient_evidence=True,
            message=message,
        )
