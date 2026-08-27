"""Trusted orchestration for course-scoped textbook question answering."""

from __future__ import annotations

from .course_runtime import CourseRuntime
from .qa_evidence import CitationVerifier, EvidencePolicy, EvidenceRetriever
from .qa_models import ProviderRequest, QAResult
from .qa_provider import AnswerProvider, AnswerProviderInvalidResponseError


class QARuntimeError(RuntimeError):
    """Base error for textbook QA runtime contract failures."""


class QAQuestionError(QARuntimeError):
    """Raised when a QA question or evidence limit violates the public contract."""


class QARuntime:
    """Coordinate trusted retrieval, provider generation and citation verification."""

    def __init__(self, course: CourseRuntime, *, provider: AnswerProvider):
        self.course = course
        self._provider = provider
        self._retriever = EvidenceRetriever.from_course(course)
        self._verifier = CitationVerifier.from_course(course)

    @classmethod
    def from_course(cls, course: CourseRuntime, *, provider: AnswerProvider) -> "QARuntime":
        return cls(course, provider=provider)

    def answer(self, question: str, *, evidence_limit: int = 8) -> QAResult:
        normalized_question = self._validate_question(question)
        normalized_limit = self._validate_evidence_limit(evidence_limit)

        pack = self._retriever.retrieve(normalized_question, limit=normalized_limit)
        if EvidencePolicy.status(pack) == "insufficient_evidence":
            return QAResult.system_notice(
                course_id=pack.course_id,
                book_id=pack.book_id,
                question=pack.question,
                answer="现有教材证据不足，暂不能给出可靠回答。",
                citations=(),
            )

        provider_answer = self._provider.answer(ProviderRequest.from_pack(pack))
        answer_text = str(provider_answer.answer_text).strip()
        if not answer_text:
            raise AnswerProviderInvalidResponseError("Provider answer text must not be blank")
        citations = self._verifier.verify(pack, provider_answer)
        return QAResult.generated(
            course_id=pack.course_id,
            book_id=pack.book_id,
            question=pack.question,
            answer=answer_text,
            citations=citations,
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

    @staticmethod
    def _validate_evidence_limit(evidence_limit: int) -> int:
        if (
            isinstance(evidence_limit, bool)
            or not isinstance(evidence_limit, int)
            or not 1 <= evidence_limit <= 12
        ):
            raise QAQuestionError("QA evidence limit must be an integer from 1 through 12")
        return evidence_limit
