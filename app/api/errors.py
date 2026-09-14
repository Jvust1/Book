"""Stable application errors for service and HTTP projection."""

from __future__ import annotations


class BookAppError(RuntimeError):
    """Base error carrying a stable machine code and Chinese user message."""

    def __init__(self, *, code: str, user_message: str, detail: str | None = None):
        self.code = code
        self.user_message = user_message
        self.detail = detail
        super().__init__(detail or user_message)


class AppNotFoundError(BookAppError):
    """Requested runtime entity does not exist."""


class AppUnavailableError(BookAppError):
    """Book App runtime cannot be initialized or trusted."""


class QAProviderUnconfiguredError(AppUnavailableError):
    """Server-side QA provider configuration is absent or incomplete."""


class InvalidModeError(BookAppError):
    """Section learning mode is outside the fixed product contract."""


class InvalidSearchQueryError(BookAppError):
    """Course textbook search input is outside the stable query contract."""


class InvalidQAQuestionError(BookAppError):
    """Course textbook QA input is outside the stable question contract."""


class InvalidStudySyncError(BookAppError):
    """Manual study progress package is invalid or incompatible."""


class QAProviderInvalidResponseError(BookAppError):
    """Configured QA provider returned an answer that failed trust validation."""
