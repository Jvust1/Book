"""Read-only Book App projection over the existing source-backed runtimes."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from runtime import (
    LibraryRuntime,
    LibraryRuntimeError,
    SectionLearningRuntime,
    SectionLearningRuntimeError,
    SourceResolutionError,
    SourceResolver,
)
from runtime.book_runtime import BookRuntimeError, RuntimeSection
from runtime.course_runtime import CourseRuntime

from .errors import AppNotFoundError, AppUnavailableError, InvalidModeError
from .models import (
    ChapterCard,
    ChapterResponse,
    CourseCard,
    CourseResponse,
    LearningMode,
    LibraryResponse,
    ModeItem,
    ModeResponse,
    SectionCard,
    SectionResponse,
    SourceContextItem,
    SourceRef,
    SourceResponse,
)


VALID_MODES = frozenset({"preview", "learn", "review", "practice"})


class BookAppService:
    """Stable App-facing DTO boundary around Library/Course/Book runtimes."""

    def __init__(self, repository_root: Path):
        self.repository_root = Path(repository_root).resolve()
        try:
            self._library = LibraryRuntime.open(
                self.repository_root / "library",
                repository_root=self.repository_root,
            )
        except LibraryRuntimeError as exc:
            raise AppUnavailableError(
                code="library_unavailable",
                user_message="教材库暂不可用",
                detail=str(exc),
            ) from exc

    def library(self) -> LibraryResponse:
        return LibraryResponse(
            library_id=self._library.library_id,
            name=self._library.name,
            courses=[self._course_card(course) for course in self._library.courses()],
        )

    def course(self, course_id: str) -> CourseResponse:
        course = self._course(course_id)
        chapters = [self._chapter_card(course, row) for row in course.chapters()]
        return CourseResponse(
            course=self._course_card(course),
            chapters=chapters,
            section_count=len(course.main_book().sections),
        )

    def chapter(self, course_id: str, chapter_id: str) -> ChapterResponse:
        course = self._course(course_id)
        chapter_row = self._chapter_row(course, chapter_id)
        sections = course.sections_for_chapter(chapter_id)
        return ChapterResponse(
            course_id=course.course_id,
            book_id=course.main_book().book_id,
            chapter=self._chapter_card(course, chapter_row),
            sections=[self._section_card(section) for section in sections],
        )

    def section(self, course_id: str, section_id: str) -> SectionResponse:
        course = self._course(course_id)
        try:
            learning = SectionLearningRuntime.from_course(course, section_id)
        except SectionLearningRuntimeError as exc:
            raise AppNotFoundError(
                code="section_not_found",
                user_message="小节不存在",
                detail=str(exc),
            ) from exc
        source = learning.source()
        return SectionResponse(
            course_id=source.course_id,
            book_id=source.book_id,
            chapter_id=source.chapter_id,
            section=self._section_card(course.section(section_id)),
            object_count=len(source.objects),
            figure_count=len(source.figures),
            translation_available=any(
                bool(row.get("available")) for row in source.translation_sources
            ),
        )

    def mode(self, course_id: str, section_id: str, mode: LearningMode | str) -> ModeResponse:
        normalized_mode = str(mode).strip().casefold()
        if normalized_mode not in VALID_MODES:
            raise InvalidModeError(
                code="invalid_mode",
                user_message="学习模式无效",
                detail=f"Unsupported learning mode: {mode!r}",
            )

        course = self._course(course_id)
        try:
            learning = SectionLearningRuntime.from_course(course, section_id)
        except SectionLearningRuntimeError as exc:
            raise AppNotFoundError(
                code="section_not_found",
                user_message="小节不存在",
                detail=str(exc),
            ) from exc

        mode_fn = {
            "preview": learning.preview,
            "learn": learning.learn,
            "review": learning.review,
            "practice": learning.practice,
        }[normalized_mode]
        payload = mode_fn()
        resolver = SourceResolver(course)
        items: list[ModeItem] = []
        for row in payload["items"]:
            kind = str(row["kind"])
            source_id = str(row["source_id"])
            try:
                resolved = resolver.resolve(kind, source_id)
            except SourceResolutionError as exc:
                raise AppUnavailableError(
                    code="source_integrity_error",
                    user_message="教材来源暂不可用",
                    detail=str(exc),
                ) from exc
            items.append(
                ModeItem(
                    kind=kind,
                    source_id=source_id,
                    object_type=resolved.type,
                    type_zh=resolved.type_zh,
                    number=resolved.number,
                    title_zh=resolved.title_zh,
                    title_en=resolved.title_en,
                    formula=resolved.formula,
                    printed_page=resolved.printed_page,
                    pdf_page=resolved.pdf_page,
                    content_zh=resolved.content_zh,
                    translation_available=resolved.translation_available,
                )
            )

        return ModeResponse(
            mode=cast(LearningMode, normalized_mode),
            course_id=str(payload["course_id"]),
            book_id=str(payload["book_id"]),
            chapter_id=(
                str(payload["chapter_id"]) if payload.get("chapter_id") is not None else None
            ),
            section_id=str(payload["section_id"]),
            source_status=str(payload["source_status"]),
            items=items,
            source_refs=[SourceRef(**row) for row in payload["source_refs"]],
        )

    def source(self, course_id: str, kind: str, source_id: str) -> SourceResponse:
        course = self._course(course_id)
        try:
            source = SourceResolver(course).resolve(kind, source_id)
        except SourceResolutionError as exc:
            raise AppNotFoundError(
                code="source_not_found",
                user_message="教材来源不存在",
                detail=str(exc),
            ) from exc
        data = source.to_dict()
        data["context_before"] = [SourceContextItem(**row) for row in source.context_before]
        data["context_after"] = [SourceContextItem(**row) for row in source.context_after]
        return SourceResponse(**data)

    def _course(self, course_id: str) -> CourseRuntime:
        try:
            return self._library.course(course_id)
        except LibraryRuntimeError as exc:
            raise AppNotFoundError(
                code="course_not_found",
                user_message="课程不存在",
                detail=str(exc),
            ) from exc

    @staticmethod
    def _course_card(course: CourseRuntime) -> CourseCard:
        book = course.main_book()
        metadata = book.metadata
        authors_raw = metadata.get("authors")
        authors = [str(value) for value in authors_raw] if isinstance(authors_raw, list) else []
        name_zh = str(metadata.get("title_zh") or "").strip()
        if not name_zh:
            name_zh = "中文课程名暂未提供"
        name_en_raw = metadata.get("title_en") or course.name
        return CourseCard(
            course_id=course.course_id,
            name_zh=name_zh,
            name_en=str(name_en_raw) if name_en_raw else None,
            authors=authors,
            book_id=book.book_id,
            chapter_count=len(course.chapter_ids()),
            section_count=len(book.sections),
            runtime_status=str(book.readiness.get("status") or "UNKNOWN"),
        )

    def _chapter_card(self, course: CourseRuntime, row: dict[str, object]) -> ChapterCard:
        chapter_id = self._chapter_id(row)
        sections = course.sections_for_chapter(chapter_id)
        return ChapterCard(
            chapter_id=chapter_id,
            number=self._optional_str(row.get("number")),
            title_zh=self._optional_str(row.get("title_zh")),
            title_en=self._optional_str(row.get("title_en")),
            section_count=len(sections),
        )

    def _chapter_row(self, course: CourseRuntime, chapter_id: str) -> dict[str, object]:
        for row in course.chapters():
            if self._chapter_id(row) == chapter_id:
                return row
        raise AppNotFoundError(
            code="chapter_not_found",
            user_message="章节不存在",
            detail=f"Unknown chapter: {chapter_id}",
        )

    @staticmethod
    def _chapter_id(row: dict[str, object]) -> str:
        value = row.get("id") or row.get("chapter_id")
        return str(value or "")

    @staticmethod
    def _section_card(section: RuntimeSection) -> SectionCard:
        return SectionCard(
            section_id=section.id,
            number=section.number,
            title_zh=section.title_zh,
            title_en=section.title_en,
            printed_page_start=section.printed_page_start,
            printed_page_end=section.printed_page_end,
            pdf_page_start=section.pdf_page_start,
            pdf_page_end=section.pdf_page_end,
        )

    @staticmethod
    def _optional_str(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
