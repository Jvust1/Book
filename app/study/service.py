from __future__ import annotations

from app.api.errors import AppUnavailableError, InvalidModeError
from app.api.service import BookAppService

from .repository import StudyRecord, StudyRecordRepository, StudyRecordRepositoryError


VALID_STUDY_MODES = frozenset({"preview", "learn", "review", "practice"})


class StudyRecordService:
    """Canonical runtime validation boundary for local StudyRecord persistence."""

    def __init__(
        self,
        book_app_service: BookAppService,
        repository: StudyRecordRepository,
    ) -> None:
        self._book_app_service = book_app_service
        self._repository = repository

    def touch(
        self,
        course_id: str,
        section_id: str,
        mode: str,
    ) -> StudyRecord:
        normalized_mode = self._normalize_mode(mode)
        section = self._book_app_service.section(course_id, section_id)
        try:
            return self._repository.touch_record(
                section.course_id,
                section.book_id,
                section.section.id,
                normalized_mode,
            )
        except StudyRecordRepositoryError as exc:
            raise self._store_unavailable(exc) from exc

    def complete(
        self,
        course_id: str,
        section_id: str,
        mode: str,
    ) -> StudyRecord:
        normalized_mode = self._normalize_mode(mode)
        section = self._book_app_service.section(course_id, section_id)
        try:
            return self._repository.complete_record(
                section.course_id,
                section.book_id,
                section.section.id,
                normalized_mode,
            )
        except StudyRecordRepositoryError as exc:
            raise self._store_unavailable(exc) from exc

    def list_course(self, course_id: str) -> tuple[StudyRecord, ...]:
        course = self._book_app_service.course(course_id)
        try:
            return self._repository.list_course_records(course.course.course_id)
        except StudyRecordRepositoryError as exc:
            raise self._store_unavailable(exc) from exc

    def recent(self) -> StudyRecord | None:
        try:
            return self._repository.get_recent_record()
        except StudyRecordRepositoryError as exc:
            raise self._store_unavailable(exc) from exc

    @staticmethod
    def _normalize_mode(mode: str) -> str:
        normalized = str(mode).strip().casefold()
        if normalized not in VALID_STUDY_MODES:
            raise InvalidModeError(
                code="invalid_mode",
                user_message="学习模式无效",
                detail=f"Unsupported learning mode: {mode!r}",
            )
        return normalized

    @staticmethod
    def _store_unavailable(exc: StudyRecordRepositoryError) -> AppUnavailableError:
        return AppUnavailableError(
            code="study_store_unavailable",
            user_message="学习进度暂无法保存",
            detail=str(exc),
        )
