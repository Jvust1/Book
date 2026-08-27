"""Server-side provider selection tests for Phase 1F textbook QA."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from runtime import DeterministicFakeAnswerProvider, UnavailableAnswerProvider

from app.api.qa_provider_factory import QAProviderConfigurationError, provider_from_environment


class QAProviderFactoryTests(unittest.TestCase):
    def test_default_provider_is_explicitly_unavailable(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            provider = provider_from_environment()

        self.assertIsInstance(provider, UnavailableAnswerProvider)

    def test_fake_provider_requires_explicit_test_configuration(self) -> None:
        with patch.dict(os.environ, {"BOOK_QA_PROVIDER": "fake"}, clear=True):
            provider = provider_from_environment()

        self.assertIsInstance(provider, DeterministicFakeAnswerProvider)

    def test_provider_name_is_trimmed_and_casefolded(self) -> None:
        with patch.dict(os.environ, {"BOOK_QA_PROVIDER": "  FaKe  "}, clear=True):
            provider = provider_from_environment()

        self.assertIsInstance(provider, DeterministicFakeAnswerProvider)

    def test_unknown_provider_never_falls_back_to_fake(self) -> None:
        with patch.dict(os.environ, {"BOOK_QA_PROVIDER": "mystery"}, clear=True):
            with self.assertRaises(QAProviderConfigurationError):
                provider_from_environment()


if __name__ == "__main__":
    unittest.main()
