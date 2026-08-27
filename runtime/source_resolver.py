"""Resolve stable Section learning source refs back to textbook evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .book_runtime import BookRuntimeError, RuntimeObject
from .course_runtime import CourseRuntime


TYPE_LABELS_ZH: dict[str, str] = {
    "definition": "定义",
    "theorem": "定理",
    "proposition": "命题",
    "lemma": "引理",
    "corollary": "推论",
    "formula": "公式",
    "example": "例题",
    "exercise": "练习",
    "problem": "习题",
    "figure": "图",
    "concept": "概念",
}

CONTENT_ZH_KEYS = (
    "content_zh",
    "statement_zh",
    "description_zh",
    "summary_zh",
    "text_zh",
)


class SourceResolutionError(RuntimeError):
    """Raised when a stable source ref cannot be resolved from runtime evidence."""


@dataclass(frozen=True)
class ResolvedSource:
    course_id: str
    book_id: str
    section_id: str | None
    kind: str
    source_id: str
    type: str | None
    type_zh: str
    number: str | None
    title_zh: str | None
    title_en: str | None
    content_zh: str | None
    formula: str | None
    printed_page: int | str | None
    pdf_page: int | None
    source_anchor: str | None
    source_batch: str | None
    translation_available: bool
    context_before: tuple[dict[str, Any], ...]
    context_after: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceResolver:
    """Resolve source refs without reading textbook files outside BookRuntime."""

    def __init__(self, course: CourseRuntime):
        self.course = course
        self.book = course.main_book()

    def resolve(self, kind: str, source_id: str) -> ResolvedSource:
        normalized_kind = str(kind).strip().casefold()
        if normalized_kind != "object":
            raise SourceResolutionError(f"Unsupported source kind: {kind!r}")
        return self._resolve_object(source_id)

    def _resolve_object(self, source_id: str) -> ResolvedSource:
        try:
            obj = self.book.object(source_id)
        except BookRuntimeError as exc:
            raise SourceResolutionError(f"Unknown object source: {source_id!r}") from exc

        context_before, context_after = self._object_context(obj)
        obj_type = str(obj.type or "object").strip().casefold()
        return ResolvedSource(
            course_id=self.course.course_id,
            book_id=self.book.book_id,
            section_id=obj.section_id,
            kind="object",
            source_id=obj.id,
            type=obj.type,
            type_zh=TYPE_LABELS_ZH.get(obj_type, "教材对象"),
            number=obj.number,
            title_zh=obj.name_zh,
            title_en=obj.name_en,
            content_zh=self._content_zh(obj.raw),
            formula=obj.formula,
            printed_page=obj.anchor.printed_page,
            pdf_page=obj.anchor.pdf_page,
            source_anchor=obj.anchor.source_anchor,
            source_batch=obj.source_batch,
            translation_available=self._translation_available(obj.source_batch),
            context_before=context_before,
            context_after=context_after,
        )

    @staticmethod
    def _content_zh(raw: dict[str, Any]) -> str | None:
        for key in CONTENT_ZH_KEYS:
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _translation_available(self, batch_id: str | None) -> bool:
        if not batch_id:
            return False
        try:
            return self.book.translation_text(batch_id) is not None
        except BookRuntimeError:
            return False

    def _object_context(
        self, obj: RuntimeObject
    ) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
        if not obj.section_id:
            return (), ()
        try:
            rows = self.book.objects_for_section(obj.section_id)
        except BookRuntimeError:
            return (), ()

        index = next((i for i, row in enumerate(rows) if row.id == obj.id), None)
        if index is None:
            return (), ()

        def compact(row: RuntimeObject) -> dict[str, Any]:
            return {
                "kind": "object",
                "source_id": row.id,
                "type": row.type,
                "number": row.number,
                "title_zh": row.name_zh,
            }

        before = tuple(compact(row) for row in rows[max(0, index - 2) : index])
        after = tuple(compact(row) for row in rows[index + 1 : index + 3])
        return before, after
