"""Server-side answer-provider selection for textbook QA."""

from __future__ import annotations

import os

from runtime import (
    AnswerProvider,
    DeterministicFakeAnswerProvider,
    UnavailableAnswerProvider,
)


class QAProviderConfigurationError(RuntimeError):
    """Configured QA provider name is unsupported or unsafe."""


def provider_from_environment() -> AnswerProvider:
    """Select a provider without ever silently treating the fake provider as production AI."""

    provider_name = os.environ.get("BOOK_QA_PROVIDER", "").strip().casefold()
    if not provider_name:
        return UnavailableAnswerProvider()
    if provider_name == "fake":
        return DeterministicFakeAnswerProvider()
    raise QAProviderConfigurationError(f"Unsupported BOOK_QA_PROVIDER: {provider_name!r}")
