"""Repository-bound validation for inert H3a Concept graph references."""

from __future__ import annotations

from book_core.concepts import ConceptGraph

from .book_runtime import BookRuntimeError
from .course_runtime import CourseRuntime, CourseRuntimeError
from .source_resolver import SourceResolutionError, SourceResolver


class ConceptReferenceValidationError(RuntimeError):
    """Raised when a ConceptAlignment cannot prove a canonical runtime reference."""


class ConceptReferenceValidator:
    """Validate ConceptAlignment references without activating Concept in product flows."""

    def __init__(self, course: CourseRuntime):
        self.course = course

    def validate(self, graph: ConceptGraph) -> None:
        identities = {
            self.course.book_identity(book_id).book_version_id: self.course.book_identity(
                book_id
            )
            for book_id in self.course.book_ids()
        }
        main_book_version_id = self.course.main_book_identity().book_version_id
        resolver = SourceResolver(self.course)

        for alignment in graph.alignments:
            identity = identities.get(alignment.book_version_id)
            if identity is None:
                raise ConceptReferenceValidationError(
                    f"Unknown mounted book_version_id: {alignment.book_version_id!r}"
                )

            if alignment.section_id is not None:
                try:
                    self.course.book(identity.book_id).section(alignment.section_id)
                except (BookRuntimeError, CourseRuntimeError) as exc:
                    raise ConceptReferenceValidationError(
                        "Unknown section_id for book_version_id "
                        f"{alignment.book_version_id!r}: {alignment.section_id!r}"
                    ) from exc

            has_source_kind = alignment.source_kind is not None
            has_source_id = alignment.source_id is not None
            if has_source_kind != has_source_id:
                raise ConceptReferenceValidationError(
                    "source_kind and source_id must be supplied together"
                )

            if not has_source_kind:
                continue

            if alignment.book_version_id != main_book_version_id:
                raise ConceptReferenceValidationError(
                    "Source-bearing alignments for non-main books are unsupported in H3a"
                )

            assert alignment.source_kind is not None
            assert alignment.source_id is not None
            try:
                resolved = resolver.resolve(
                    alignment.source_kind,
                    alignment.source_id,
                )
            except SourceResolutionError as exc:
                raise ConceptReferenceValidationError(str(exc)) from exc

            if (
                alignment.section_id is not None
                and resolved.section_id is not None
                and alignment.section_id != resolved.section_id
            ):
                raise ConceptReferenceValidationError(
                    "Alignment section_id does not match the resolved canonical source"
                )
