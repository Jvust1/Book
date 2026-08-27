"""Source-backed Section learning projections for the Book App."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .book_runtime import BookRuntimeError
from .course_runtime import CourseRuntime


REVIEW_TYPES = frozenset(
    {"definition", "theorem", "proposition", "lemma", "corollary", "formula"}
)
PRACTICE_TYPES = frozenset({"exercise", "problem"})


class SectionLearningRuntimeError(RuntimeError):
    """Base error for Section learning runtime operations."""


class SectionLearningSourceError(SectionLearningRuntimeError):
    """Raised when a Section cannot be projected from runtime evidence."""


class SectionLearningModeError(SectionLearningRuntimeError):
    """Raised when a learning-mode payload cannot be produced."""


@dataclass
class SectionLearningSource:
    course_id: str
    book_id: str
    chapter_id: str | None
    section_id: str
    number: str | None
    title_en: str | None
    title_zh: str | None
    pdf_page_start: int | None
    pdf_page_end: int | None
    printed_page_start: int | str | None
    printed_page_end: int | str | None
    source_batches: list[str]
    page_map_start: dict[str, str] | None
    page_map_end: dict[str, str] | None
    objects: list[dict[str, Any]]
    figures: list[dict[str, Any]]
    translation_sources: list[dict[str, Any]]


class SectionLearningRuntime:
    """Deterministic learning view over one CourseRuntime Section."""

    def __init__(self, source: SectionLearningSource):
        self._source = source

    @classmethod
    def from_course(
        cls,
        course: CourseRuntime,
        section_id: str,
    ) -> "SectionLearningRuntime":
        try:
            section = course.section(section_id)
        except BookRuntimeError as exc:
            raise SectionLearningSourceError(
                f"Unknown Section {section_id!r} in course {course.course_id!r}"
            ) from exc

        book = course.main_book()
        objects = [
            {
                "kind": "object",
                "id": obj.id,
                "type": obj.type,
                "number": obj.number,
                "name_en": obj.name_en,
                "name_zh": obj.name_zh,
                "formula": obj.formula,
                "pdf_page": obj.anchor.pdf_page,
                "printed_page": obj.anchor.printed_page,
                "source_anchor": obj.anchor.source_anchor,
                "source_batch": obj.source_batch,
            }
            for obj in book.objects_for_section(section.id)
        ]

        figures: list[dict[str, Any]] = []
        if section.pdf_page_start is not None and section.pdf_page_end is not None:
            for figure in book.figures.values():
                page = figure.anchor.pdf_page
                if page is None:
                    continue
                if not section.pdf_page_start <= page <= section.pdf_page_end:
                    continue
                figures.append(
                    {
                        "kind": "figure",
                        "id": figure.id,
                        "title_en": figure.title_en,
                        "title_zh": figure.title_zh,
                        "pdf_page": page,
                        "printed_page": figure.anchor.printed_page,
                        "source_anchor": figure.anchor.source_anchor,
                        "source_batch": figure.source_batch,
                    }
                )
            figures.sort(key=lambda row: (int(row["pdf_page"]), str(row["id"])))

        source_batches: list[str] = []
        seen_batches: set[str] = set()
        for batch_id in section.source_batches:
            if batch_id in seen_batches:
                continue
            seen_batches.add(batch_id)
            source_batches.append(batch_id)

        translation_sources = [
            {
                "batch_id": batch_id,
                "available": book.translation_text(batch_id) is not None,
            }
            for batch_id in source_batches
        ]

        page_map_start = (
            book.page_map_row(section.pdf_page_start)
            if section.pdf_page_start is not None
            else None
        )
        page_map_end = (
            book.page_map_row(section.pdf_page_end)
            if section.pdf_page_end is not None
            else None
        )

        return cls(
            SectionLearningSource(
                course_id=course.course_id,
                book_id=book.book_id,
                chapter_id=section.chapter_id,
                section_id=section.id,
                number=section.number,
                title_en=section.title_en,
                title_zh=section.title_zh,
                pdf_page_start=section.pdf_page_start,
                pdf_page_end=section.pdf_page_end,
                printed_page_start=section.printed_page_start,
                printed_page_end=section.printed_page_end,
                source_batches=source_batches,
                page_map_start=page_map_start,
                page_map_end=page_map_end,
                objects=objects,
                figures=figures,
                translation_sources=translation_sources,
            )
        )

    def source(self) -> SectionLearningSource:
        return self._source

    def _envelope(self, mode: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "mode": mode,
            "course_id": self._source.course_id,
            "book_id": self._source.book_id,
            "chapter_id": self._source.chapter_id,
            "section_id": self._source.section_id,
            "source_status": "available",
            "items": items,
            "source_refs": [
                {"kind": str(item["kind"]), "source_id": str(item["source_id"])}
                for item in items
            ],
        }

    def preview(self) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        items.extend(
            {
                "kind": "object",
                "source_id": row["id"],
                "object_type": row["type"],
            }
            for row in self._source.objects
        )
        items.extend(
            {"kind": "figure", "source_id": row["id"]}
            for row in self._source.figures
        )
        items.extend(
            {
                "kind": "translation",
                "source_id": row["batch_id"],
                "available": row["available"],
            }
            for row in self._source.translation_sources
        )
        return self._envelope("preview", items)

    def learn(self) -> dict[str, Any]:
        items = (
            [
                {"kind": "object", "source_id": row["id"]}
                for row in self._source.objects
            ]
            + [
                {"kind": "figure", "source_id": row["id"]}
                for row in self._source.figures
            ]
            + [
                {"kind": "translation", "source_id": row["batch_id"]}
                for row in self._source.translation_sources
            ]
        )
        return self._envelope("learn", items)

    def review(self) -> dict[str, Any]:
        items = [
            {"kind": "object", "source_id": row["id"]}
            for row in self._source.objects
            if str(row.get("type") or "").strip().casefold() in REVIEW_TYPES
        ]
        return self._envelope("review", items)

    def practice(self) -> dict[str, Any]:
        items = [
            {"kind": "object", "source_id": row["id"]}
            for row in self._source.objects
            if str(row.get("type") or "").strip().casefold() in PRACTICE_TYPES
        ]
        return self._envelope("practice", items)
