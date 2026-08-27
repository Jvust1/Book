"""Server-side model-provider selection for textbook QA."""

from __future__ import annotations

import math
import os

from runtime import (
    DeterministicFakeModelProvider,
    ModelProvider,
    UnavailableModelProvider,
)

from .openai_compatible_provider import OpenAICompatibleModelProvider


class QAProviderConfigurationError(RuntimeError):
    """Server-side QA provider configuration is incomplete or unsupported."""


def provider_from_environment() -> ModelProvider:
    """Select fake, real or unavailable provider without exposing server secrets."""

    provider_name = os.environ.get("BOOK_QA_PROVIDER", "").strip().casefold()
    if provider_name == "fake":
        return DeterministicFakeModelProvider()
    if provider_name:
        raise QAProviderConfigurationError(
            f"Unsupported BOOK_QA_PROVIDER: {provider_name!r}"
        )

    base_url = os.environ.get("BOOK_QA_BASE_URL", "").strip()
    api_key = os.environ.get("BOOK_QA_API_KEY", "").strip()
    model = os.environ.get("BOOK_QA_MODEL", "").strip()
    configured = (bool(base_url), bool(api_key), bool(model))

    if not any(configured):
        return UnavailableModelProvider()
    if not all(configured):
        raise QAProviderConfigurationError(
            "BOOK_QA_BASE_URL, BOOK_QA_API_KEY and BOOK_QA_MODEL must be configured together"
        )

    timeout_raw = os.environ.get("BOOK_QA_TIMEOUT_SECONDS", "60").strip() or "60"
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        raise QAProviderConfigurationError(
            "BOOK_QA_TIMEOUT_SECONDS must be a positive number"
        ) from None
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise QAProviderConfigurationError(
            "BOOK_QA_TIMEOUT_SECONDS must be a positive number"
        )

    try:
        return OpenAICompatibleModelProvider(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
        )
    except ValueError:
        raise QAProviderConfigurationError(
            "OpenAI-compatible QA provider configuration is invalid"
        ) from None
