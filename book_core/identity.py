from __future__ import annotations

from dataclasses import dataclass


CANONICAL_BOOK_ROLES = frozenset(
    {"primary", "supplementary", "reference", "translation"}
)

LEGACY_BOOK_ROLE_ALIASES = {
    "main": "primary",
    "supplementary": "supplementary",
    "reference": "reference",
    "english": "translation",
}


@dataclass(frozen=True)
class BookIdentity:
    book_id: str
    logical_book_id: str
    book_version_id: str
    role: str


def canonical_role_from_legacy(role: str) -> str:
    normalized = str(role).strip()
    if normalized not in LEGACY_BOOK_ROLE_ALIASES:
        raise ValueError(f"Unsupported legacy book role: {role!r}")
    return LEGACY_BOOK_ROLE_ALIASES[normalized]


def build_book_identity(
    book_id: str,
    structured_version: str,
    legacy_role: str,
) -> BookIdentity:
    normalized_book_id = str(book_id).strip()
    normalized_version = str(structured_version).strip()
    if not normalized_book_id:
        raise ValueError("book_id must be non-blank")
    if not normalized_version:
        raise ValueError("structured_version must be non-blank")

    role = canonical_role_from_legacy(legacy_role)
    return BookIdentity(
        book_id=normalized_book_id,
        logical_book_id=normalized_book_id,
        book_version_id=f"{normalized_book_id}@{normalized_version}",
        role=role,
    )
