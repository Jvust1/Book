from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from book_core.identity import (
    CANONICAL_BOOK_ROLES,
    LEGACY_BOOK_ROLE_ALIASES,
    build_book_identity,
    canonical_role_from_legacy,
)


class ManifestNormalizationError(RuntimeError):
    """Raised when a legacy course manifest cannot be normalized safely."""


@dataclass(frozen=True)
class NormalizedBookEntry:
    book_id: str
    logical_book_id: str
    book_version_id: str
    role: str
    canonical_path: str
    required: bool
    enabled: bool
    structured_version: str


@dataclass(frozen=True)
class NormalizedCourseManifest:
    course_id: str
    course_name: str
    language: str
    primary_book_id: str
    books: tuple[NormalizedBookEntry, ...]


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestNormalizationError(f"{label} missing: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestNormalizationError(f"cannot read {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestNormalizationError(f"{label} must be a JSON object: {path}")
    return value


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestNormalizationError(f"{field} must be a non-empty string")
    return value.strip()


def normalize_course_manifest(course_dir: Path, repository_root: Path) -> NormalizedCourseManifest:
    course_root = Path(course_dir).resolve()
    repo_root = Path(repository_root).resolve()
    try:
        course_root.relative_to(repo_root)
    except ValueError as exc:
        raise ManifestNormalizationError(
            f"course directory escapes repository root: {course_root}"
        ) from exc

    manifest = _load_json_object(course_root / "course.json", "course manifest")
    if manifest.get("schema_version") != "course_manifest_v1":
        raise ManifestNormalizationError("schema_version must be course_manifest_v1")

    course_id = _require_text(manifest.get("course_id"), "course_id")
    course_name = _require_text(manifest.get("name"), "name")
    language = _require_text(manifest.get("language"), "language")
    main_book_id = _require_text(manifest.get("main_book_id"), "main_book_id")

    raw_books = manifest.get("books")
    if not isinstance(raw_books, list) or not raw_books:
        raise ManifestNormalizationError("books must be a non-empty list")

    normalized_books: list[NormalizedBookEntry] = []
    enabled_ids: set[str] = set()
    enabled_primary: list[NormalizedBookEntry] = []

    for index, raw in enumerate(raw_books):
        if not isinstance(raw, dict):
            raise ManifestNormalizationError(f"books[{index}] must be a JSON object")
        book_id = _require_text(raw.get("book_id"), f"books[{index}].book_id")
        role_value = raw.get("role")
        if not isinstance(role_value, str) or role_value not in LEGACY_BOOK_ROLE_ALIASES:
            raise ManifestNormalizationError(
                f"books[{index}] unsupported legacy role: {role_value!r}"
            )
        try:
            role = canonical_role_from_legacy(role_value)
        except ValueError as exc:
            raise ManifestNormalizationError(
                f"books[{index}] unsupported legacy role: {role_value!r}"
            ) from exc
        if role not in CANONICAL_BOOK_ROLES:
            raise ManifestNormalizationError(f"normalized role is not canonical: {role!r}")

        raw_path = _require_text(raw.get("path"), f"books[{index}].path")
        required = raw.get("required")
        enabled = raw.get("enabled")
        if not isinstance(required, bool):
            raise ManifestNormalizationError(f"books[{index}].required must be boolean")
        if not isinstance(enabled, bool):
            raise ManifestNormalizationError(f"books[{index}].enabled must be boolean")

        if enabled:
            if book_id in enabled_ids:
                raise ManifestNormalizationError(f"duplicate enabled book_id: {book_id!r}")
            enabled_ids.add(book_id)

        path_value = Path(raw_path)
        if path_value.is_absolute():
            raise ManifestNormalizationError(
                f"books[{index}] absolute book paths are not allowed: {raw_path!r}"
            )
        book_root = (course_root / path_value).resolve()
        try:
            canonical_relative = book_root.relative_to(repo_root)
        except ValueError as exc:
            raise ManifestNormalizationError(
                f"book path escapes repository root: {raw_path!r} -> {book_root}"
            ) from exc
        if not book_root.is_dir():
            raise ManifestNormalizationError(f"book directory does not exist: {book_root}")

        completion = _load_json_object(book_root / "STRUCTURED_COMPLETE.json", "STRUCTURED_COMPLETE")
        canonical_book_id = _require_text(completion.get("book_id"), "STRUCTURED_COMPLETE.book_id")
        if canonical_book_id != book_id:
            raise ManifestNormalizationError(
                f"manifest book_id {book_id!r} does not match canonical book_id {canonical_book_id!r}"
            )
        version_value = completion.get("version")
        if not isinstance(version_value, str) or not version_value.strip():
            raise ManifestNormalizationError(
                f"book {book_id!r} structured version must be a non-empty string"
            )
        structured_version = version_value.strip()

        try:
            identity = build_book_identity(book_id, structured_version, role_value)
        except ValueError as exc:
            raise ManifestNormalizationError(
                f"books[{index}] cannot build canonical identity: {exc}"
            ) from exc

        entry = NormalizedBookEntry(
            book_id=identity.book_id,
            logical_book_id=identity.logical_book_id,
            book_version_id=identity.book_version_id,
            role=identity.role,
            canonical_path=canonical_relative.as_posix(),
            required=required,
            enabled=enabled,
            structured_version=structured_version,
        )
        normalized_books.append(entry)
        if enabled and role == "primary":
            enabled_primary.append(entry)

    if len(enabled_primary) != 1:
        raise ManifestNormalizationError(
            f"exactly one enabled primary book is required; found {len(enabled_primary)}"
        )
    if enabled_primary[0].book_id != main_book_id:
        raise ManifestNormalizationError(
            f"main_book_id {main_book_id!r} does not match enabled primary {enabled_primary[0].book_id!r}"
        )

    return NormalizedCourseManifest(
        course_id=course_id,
        course_name=course_name,
        language=language,
        primary_book_id=main_book_id,
        books=tuple(normalized_books),
    )