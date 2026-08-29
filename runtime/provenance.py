"""Internal adapter from resolved Runtime sources to neutral provenance identity."""

from __future__ import annotations

from book_core.provenance import SourceIdentity

from .course_runtime import CourseRuntime
from .source_resolver import SourceResolutionError, SourceResolver


class RuntimeProvenanceError(RuntimeError):
    """Raised when Runtime cannot prove a canonical source identity."""


def source_identity_for(
    course: CourseRuntime,
    source_kind: str,
    source_id: str,
) -> SourceIdentity:
    try:
        resolved = SourceResolver(course).resolve(source_kind, source_id)
    except SourceResolutionError as exc:
        raise RuntimeProvenanceError(str(exc)) from exc

    if resolved.course_id != course.course_id:
        raise RuntimeProvenanceError("Resolved source course identity mismatch")

    main_book = course.main_book()
    if resolved.book_id != main_book.book_id:
        raise RuntimeProvenanceError("Resolved source book identity mismatch")

    return SourceIdentity(
        course_id=course.course_id,
        book=course.main_book_identity(),
        source_kind=resolved.kind,
        source_id=resolved.source_id,
    )
