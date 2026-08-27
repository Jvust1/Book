"""Strict model-provider boundary for Phase 1F v2 textbook question answering."""

from __future__ import annotations

from typing import Literal, Protocol

from .qa_models import ModelRequest, ModelResponse, ModelResponseValidationError


class ModelProviderError(RuntimeError):
    """Base error for model-provider failures."""


class ModelProviderUnavailableError(ModelProviderError):
    """No usable model provider is configured or reachable."""


class ModelProviderInvalidResponseError(ModelProviderError):
    """Provider output violates the trusted QA response contract."""


class ModelProvider(Protocol):
    """Generation-only provider interface; retrieval and source identity stay outside."""

    def answer(self, request: ModelRequest) -> ModelResponse:
        ...


FakeMode = Literal[
    "answer",
    "insufficient",
    "invalid_citation",
    "empty_answer",
    "unavailable",
]


class DeterministicFakeModelProvider:
    """Stable test/CI provider that uses only the bounded request supplied by Runtime."""

    _MODES = {
        "answer",
        "insufficient",
        "invalid_citation",
        "empty_answer",
        "unavailable",
    }

    def __init__(self, *, mode: FakeMode = "answer") -> None:
        if mode not in self._MODES:
            raise ValueError(f"Unsupported deterministic fake provider mode: {mode!r}")
        self.mode = mode

    def answer(self, request: ModelRequest) -> ModelResponse:
        if self.mode == "unavailable":
            raise ModelProviderUnavailableError("Model provider is unavailable")

        if self.mode == "insufficient":
            return ModelResponse.from_mapping(
                {
                    "answer": None,
                    "evidence_ids": [],
                    "insufficient_evidence": True,
                    "answer_style": "explain",
                }
            )

        if not request.evidence:
            raise ModelProviderInvalidResponseError(
                "Deterministic fake provider requires at least one evidence item"
            )

        first = request.evidence[0]
        label = first.title_zh or first.title_en or first.number or first.object_type or "教材证据"
        details = first.content_zh or first.formula
        answer = f"根据提供的教材证据，{label}。"
        if details:
            answer = f"{answer} {details}"

        if self.mode == "empty_answer":
            try:
                return ModelResponse.from_mapping(
                    {
                        "answer": "",
                        "evidence_ids": [first.evidence_id],
                        "insufficient_evidence": False,
                        "answer_style": "brief",
                    }
                )
            except ModelResponseValidationError as exc:
                raise ModelProviderInvalidResponseError(
                    "Model provider returned an invalid structured response"
                ) from exc

        evidence_id = "E999" if self.mode == "invalid_citation" else first.evidence_id
        return ModelResponse.from_mapping(
            {
                "answer": answer,
                "evidence_ids": [evidence_id],
                "insufficient_evidence": False,
                "answer_style": "brief",
            }
        )


class UnavailableModelProvider:
    """Safe default used when no real model provider is configured."""

    def answer(self, request: ModelRequest) -> ModelResponse:
        del request
        raise ModelProviderUnavailableError("No model provider is configured")


# Temporary aliases are required until Task 6 migrates the existing App provider
# factory, which still imports the pre-v2 public names. They point to the strict
# v2 implementations and do not preserve the old ProviderRequest/ProviderAnswer
# behavior.
AnswerProvider = ModelProvider
AnswerProviderError = ModelProviderError
AnswerProviderUnavailableError = ModelProviderUnavailableError
AnswerProviderInvalidResponseError = ModelProviderInvalidResponseError
DeterministicFakeAnswerProvider = DeterministicFakeModelProvider
UnavailableAnswerProvider = UnavailableModelProvider
