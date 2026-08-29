from __future__ import annotations

from dataclasses import dataclass

from .identity import BookIdentity


@dataclass(frozen=True)
class SourceIdentity:
    course_id: str
    book: BookIdentity
    source_kind: str
    source_id: str

    def __post_init__(self) -> None:
        if not str(self.course_id).strip():
            raise ValueError("course_id must be non-blank")
        if not str(self.source_kind).strip():
            raise ValueError("source_kind must be non-blank")
        if not str(self.source_id).strip():
            raise ValueError("source_id must be non-blank")

    @property
    def collision_key(self) -> tuple[str, str, str]:
        return (
            self.book.book_version_id,
            self.source_kind,
            self.source_id,
        )
