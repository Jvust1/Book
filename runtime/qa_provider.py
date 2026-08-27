"""Provider boundary for Phase 1F textbook question answering."""

from __future__ import annotations

from typing import Protocol

from .qa_models import ProviderAnswer, ProviderRequest


class AnswerProviderError(RuntimeError):
    """Base error for answer-provider failures."""


class AnswerProviderUnavailableError(AnswerProviderError):
    """No usable answer provider is configured or reachable."""


class AnswerProviderInvalidResponseError(AnswerProviderError):
    """Provider output violates the trusted QA response contract."""


class AnswerProvider(Protocol):
    """Minimal provider interface; retrieval and source resolution stay outside."""

    def answer(self, request: ProviderRequest) -> ProviderAnswer:
        ...


class DeterministicFakeAnswerProvider:
    """Stable test/CI provider that uses only supplied evidence."""

    def answer(self, request: ProviderRequest) -> ProviderAnswer:
        if not request.evidence:
            raise AnswerProviderInvalidResponseError(
                "Deterministic fake provider requires at least one evidence item"
            )

        first = request.evidence[0]
        label = first.title_zh or first.title_en or first.number or first.object_type or "教材证据"
        details = first.content_zh or first.formula
        answer_text = f"根据提供的教材证据，{label}。"
        if details:
            answer_text = f"{answer_text} {details}"

        return ProviderAnswer(
            answer_text=answer_text,
            cited_evidence_ids=(first.evidence_id,),
        )


class UnavailableAnswerProvider:
    """Safe default used when no real model provider is explicitly configured."""

    def answer(self, request: ProviderRequest) -> ProviderAnswer:
        del request
        raise AnswerProviderUnavailableError("No answer provider is configured")
