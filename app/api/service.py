"""Read-only Book App projection over the existing source-backed runtimes."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from runtime import (
    AnswerProvider,
    AnswerProviderInvalidResponseError,
    AnswerProviderUnavailableError,
    LibraryRuntime,
    LibraryRuntimeError,
    QAEvidenceUnavailableError,
    QARuntime,
    QAQuestionError,
    SearchQueryError,
    SearchRuntime,
    SearchRuntimeError,
    SectionLearningRuntime,
    SectionLearningRuntimeError,
    SourceResolutionError,
    SourceResolver,
    UnavailableAnswerProvider,
)
from runtime.book_runtime import RuntimeSection
from runtime.course_runtime import CourseRuntime

from .errors import (
    AppNotFoundError,
    AppUnavailableError,
    InvalidModeError,
    InvalidQAQuestionError,
    InvalidSearchQueryError,
    QAProviderInvalidResponseError,
)
from .models import (
    ChapterCard,
    ChapterResponse,
    CourseCard,
    CourseResponse,
    LearningMode,
    LibraryResponse,
    ModeItem,
    ModeResponse,
    QACitationItem,
    QAResponse,
    SearchResponse,
    SearchResultItem,
    SectionCard,
    SectionResponse,
    SourceContextItem,
    SourceRef,
    SourceResponse,
)


VALID_MODES = frozenset({"preview", "learn", "review", "practice"})


class BookAppService:
    """Stable App-facing DTO boundary around Library/Course/Book runtimes."""

    def __init__(
        self,
        repository_root: Path,
        *,
        qa_provider: AnswerProvider | None = None,
    ):
        self.repository_root = Path(repository_root).resolve()
        self._qa_provider: AnswerProvider = qa_provider or UnavailableAnswerProvider()
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
            section_count=self._navigation_section_count(course),
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

    def search(self, course_id: str, query: str, *, limit: int = 30) -> SearchResponse:
        course = self._course(course_id)
        try:
            runtime = SearchRuntime.from_course(course)
            hits = runtime.search(query, limit=limit)
        except SearchQueryError as exc:
            raise InvalidSearchQueryError(
                code="invalid_search_query",
                user_message="搜索条件无效",
                detail=str(exc),
            ) from exc
        except SearchRuntimeError as exc:
            raise AppUnavailableError(
                code="search_unavailable",
                user_message="教材搜索暂不可用",
                detail=str(exc),
            ) from exc

        results = [
            SearchResultItem(
                rank=hit.rank,
                score=hit.score,
                source_kind=hit.source_kind,
                source_id=hit.source_id,
                object_type=hit.object_type,
                number=hit.number,
                title_zh=hit.title_zh,
                title_en=hit.title_en,
                formula=hit.formula,
                pdf_page=hit.pdf_page,
                printed_page=hit.printed_page,
                source_anchor=hit.source_anchor,
                snippet=hit.snippet,
            )
            for hit in hits
        ]
        return SearchResponse(
            course_id=course.course_id,
            book_id=course.main_book().book_id,
            query=str(query).strip(),
            result_count=len(results),
            results=results,
        )

    def ask(self, course_id: str, question: str) -> QAResponse:
        course = self._course(course_id)
        try:
            result = QARuntime.from_course(course, provider=self._qa_provider).answer(question)
        except QAQuestionError as exc:
            raise InvalidQAQuestionError(
                code="invalid_qa_question",
                user_message="提问内容无效",
                detail=str(exc),
            ) from exc
        except QAEvidenceUnavailableError as exc:
            raise AppUnavailableError(
                code="qa_unavailable",
                user_message="教材问答暂不可用",
                detail=str(exc),
            ) from exc
        except AnswerProviderUnavailableError as exc:
            raise AppUnavailableError(
                code="qa_provider_unavailable",
                user_message="教材问答模型暂不可用",
                detail=str(exc),
            ) from exc
        except AnswerProviderInvalidResponseError as exc:
            raise QAProviderInvalidResponseError(
                code="qa_provider_invalid_response",
                user_message="教材问答结果校验失败",
                detail=str(exc),
            ) from exc

        return QAResponse(
            course_id=result.course_id,
            book_id=result.book_id,
            question=result.question,
            answer_kind=result.answer_kind,
            evidence_status=result.evidence_status,
            answer=result.answer,
            citations=[
                QACitationItem(
                    citation_id=row.citation_id,
                    evidence_id=row.evidence_id,
                    source_kind=row.source_kind,
                    source_id=row.source_id,
                    object_type=row.object_type,
                    number=row.number,
                    title_zh=row.title_zh,
                    title_en=row.title_en,
                    source_anchor=row.source_anchor,
                    pdf_page=row.pdf_page,
                    printed_page=row.printed_page,
                )
                for row in result.citations
            ],
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

    @classmethod
    def _course_card(cls, course: CourseRuntime) -> CourseCard:
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
            section_count=cls._navigation_section_count(course),
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
    def _navigation_section_count(course: CourseRuntime) -> int:
        return sum(
            len(course.sections_for_chapter(chapter_id))
            for chapter_id in course.chapter_ids()
        )

    @staticmethod
    def _optional_str(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
