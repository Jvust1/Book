"""Trusted orchestration for course-scoped textbook question answering."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Mapping

from .book_runtime import BookRuntimeError
from .course_runtime import CourseRuntime, CourseRuntimeError
from .qa_evidence import (
    CitationVerifier,
    EvidenceBuilder,
    EvidenceGate,
    QAHistoryValidationError,
    normalize_history,
)
from .qa_models import (
    ModelRequest,
    ModelResponse,
    ModelResponseValidationError,
    ProviderAnswer,
    QAHistoryMessage,
    QAResult,
)
from .qa_provider import AnswerProvider, AnswerProviderInvalidResponseError


class QARuntimeError(RuntimeError):
    """Base error for textbook QA runtime contract failures."""


class QAQuestionError(QARuntimeError):
    """Raised when a QA question or dialogue history violates the public contract."""


class QASectionError(QARuntimeError):
    """Raised when an optional Section scope is invalid for the selected course."""


class QARuntime:
    """Coordinate trusted retrieval, model generation and citation verification."""

    def __init__(self, course: CourseRuntime, *, provider: AnswerProvider):
        self.course = course
        self._provider = provider
        self._builder = EvidenceBuilder.from_course(course)
        self._verifier = CitationVerifier.from_course(course)

    @classmethod
    def from_course(cls, course: CourseRuntime, *, provider: AnswerProvider) -> "QARuntime":
        return cls(course, provider=provider)

    def answer(
        self,
        question: str,
        *,
        section_id: str | None = None,
        history: Iterable[QAHistoryMessage | Mapping[str, object]] = (),
    ) -> QAResult:
        normalized_question = self._validate_question(question)
        normalized_section_id = self._validate_section_id(section_id)
        try:
            normalized_history = normalize_history(history)
        except QAHistoryValidationError as exc:
            raise QAQuestionError(str(exc)) from exc

        scope_requested = "section_then_book" if normalized_section_id is not None else "book"

        pack = None
        if normalized_section_id is not None:
            section_pack = self._builder.build(
                normalized_question,
                section_id=normalized_section_id,
            )
            if EvidenceGate.status(section_pack) == "sufficient":
                pack = replace(
                    section_pack,
                    scope_requested="section_then_book",
                    scope_used="section",
                )

        if pack is None:
            book_pack = self._builder.build(
                normalized_question,
                section_id=None,
            )
            pack = replace(
                book_pack,
                scope_requested=scope_requested,
                scope_used="book",
            )

        if EvidenceGate.status(pack) == "insufficient_evidence":
            return QAResult.system_notice(
                course_id=pack.course_id,
                book_id=pack.book_id,
                question=pack.question,
                scope_requested=pack.scope_requested,
                scope_used=pack.scope_used,
            )

        raw_response = self._provider.answer(
            ModelRequest.from_pack(
                pack,
                section_id=normalized_section_id,
                history=normalized_history,
            )
        )
        model_response = self._normalize_provider_response(raw_response)

        if model_response.insufficient_evidence:
            return QAResult.system_notice(
                course_id=pack.course_id,
                book_id=pack.book_id,
                question=pack.question,
                scope_requested=pack.scope_requested,
                scope_used=pack.scope_used,
            )

        citations = self._verifier.verify(pack, model_response)
        if model_response.answer is None:
            raise AnswerProviderInvalidResponseError("Model answer must not be null when sufficient")
        return QAResult.generated(
            course_id=pack.course_id,
            book_id=pack.book_id,
            question=pack.question,
            answer=model_response.answer,
            citations=citations,
            answer_style=model_response.answer_style,
            scope_requested=pack.scope_requested,
            scope_used=pack.scope_used,
        )

    @staticmethod
    def _normalize_provider_response(value: object) -> ModelResponse:
        if isinstance(value, ModelResponse):
            return value
        if isinstance(value, ProviderAnswer):
            try:
                return ModelResponse.from_mapping(
                    {
                        "answer": value.answer_text,
                        "evidence_ids": list(value.cited_evidence_ids),
                        "insufficient_evidence": False,
                        "answer_style": "brief",
                    }
                )
            except ModelResponseValidationError as exc:
                raise AnswerProviderInvalidResponseError(str(exc)) from exc
        raise AnswerProviderInvalidResponseError(
            f"Unsupported model-provider response type: {type(value).__name__}"
        )

    @staticmethod
    def _validate_question(question: str) -> str:
        if not isinstance(question, str):
            raise QAQuestionError("QA question must be a string")
        normalized = question.strip()
        if not normalized:
            raise QAQuestionError("QA question must not be blank")
        if len(normalized) > 1000:
            raise QAQuestionError("QA question must contain at most 1000 Unicode code points")
        return normalized

    def _validate_section_id(self, section_id: str | None) -> str | None:
        if section_id is None:
            return None
        if not isinstance(section_id, str):
            raise QASectionError("QA section ID must be a string")
        normalized = section_id.strip()
        if not normalized:
            raise QASectionError("QA section ID must not be blank")
        try:
            self.course.section(normalized)
        except (BookRuntimeError, CourseRuntimeError) as exc:
            raise QASectionError(f"Unknown QA section: {normalized}") from exc
        return normalized
