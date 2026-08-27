"""Server-side provider selection tests for Phase 1F textbook QA."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from runtime import DeterministicFakeModelProvider, UnavailableModelProvider

from app.api.openai_compatible_provider import OpenAICompatibleModelProvider
from app.api.qa_provider_factory import QAProviderConfigurationError, provider_from_environment


REAL_ENV = {
    "BOOK_QA_BASE_URL": "https://model.example.test/v1",
    "BOOK_QA_API_KEY": "server-side-test-key",
    "BOOK_QA_MODEL": "example-model",
}


class QAProviderFactoryTests(unittest.TestCase):
    def test_default_provider_is_explicitly_unavailable(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            provider = provider_from_environment()

        self.assertIsInstance(provider, UnavailableModelProvider)

    def test_fake_provider_requires_explicit_test_configuration(self) -> None:
        with patch.dict(os.environ, {"BOOK_QA_PROVIDER": "fake"}, clear=True):
            provider = provider_from_environment()

        self.assertIsInstance(provider, DeterministicFakeModelProvider)

    def test_provider_name_is_trimmed_and_casefolded(self) -> None:
        with patch.dict(os.environ, {"BOOK_QA_PROVIDER": "  FaKe  "}, clear=True):
            provider = provider_from_environment()

        self.assertIsInstance(provider, DeterministicFakeModelProvider)

    def test_complete_real_configuration_selects_openai_compatible_provider(self) -> None:
        with patch.dict(
            os.environ,
            {**REAL_ENV, "BOOK_QA_TIMEOUT_SECONDS": "17.5"},
            clear=True,
        ):
            provider = provider_from_environment()

        self.assertIsInstance(provider, OpenAICompatibleModelProvider)
        self.assertEqual(provider.base_url, REAL_ENV["BOOK_QA_BASE_URL"])
        self.assertEqual(provider.model, REAL_ENV["BOOK_QA_MODEL"])
        self.assertEqual(provider.timeout_seconds, 17.5)
        self.assertFalse(hasattr(provider, "public_api_key"))

    def test_partial_real_configuration_is_rejected_not_silently_unavailable(self) -> None:
        partial_rows = [
            {"BOOK_QA_BASE_URL": REAL_ENV["BOOK_QA_BASE_URL"]},
            {"BOOK_QA_API_KEY": REAL_ENV["BOOK_QA_API_KEY"]},
            {"BOOK_QA_MODEL": REAL_ENV["BOOK_QA_MODEL"]},
            {
                "BOOK_QA_BASE_URL": REAL_ENV["BOOK_QA_BASE_URL"],
                "BOOK_QA_MODEL": REAL_ENV["BOOK_QA_MODEL"],
            },
        ]
        for env in partial_rows:
            with self.subTest(env=env):
                with patch.dict(os.environ, env, clear=True):
                    with self.assertRaises(QAProviderConfigurationError):
                        provider_from_environment()

    def test_unknown_provider_never_falls_back_to_fake_or_real(self) -> None:
        with patch.dict(
            os.environ,
            {**REAL_ENV, "BOOK_QA_PROVIDER": "mystery"},
            clear=True,
        ):
            with self.assertRaises(QAProviderConfigurationError):
                provider_from_environment()

    def test_invalid_timeout_is_configuration_error(self) -> None:
        for value in ("zero", "0", "-1"):
            with self.subTest(value=value):
                with patch.dict(
                    os.environ,
                    {**REAL_ENV, "BOOK_QA_TIMEOUT_SECONDS": value},
                    clear=True,
                ):
                    with self.assertRaises(QAProviderConfigurationError):
                        provider_from_environment()


if __name__ == "__main__":
    unittest.main()
