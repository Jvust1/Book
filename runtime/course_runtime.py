"""Course-level aggregation over one or more ready BookRuntime instances."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .book_runtime import BookRuntime, BookRuntimeBlockedError, BookRuntimeError


ALLOWED_BOOK_ROLES = frozenset({"main", "supplementary", "english", "reference"})


class CourseRuntimeError(RuntimeError):
    """Base error for course runtime loading."""


class CourseManifestError(CourseRuntimeError):
    """Raised when course.json violates the CourseRuntime contract."""


class CourseBookResolutionError(CourseRuntimeError):
    """Raised when a configured book path is invalid or outside the repository."""


class CourseRuntimeBlockedError(CourseRuntimeError):
    """Raised when an enabled book cannot be opened as a production BookRuntime."""

    def __init__(self, book_id: str, path: Path, cause: Exception):
        self.book_id = book_id
        self.path = path
        self.cause = cause
        super().__init__(f"Course runtime blocked by book {book_id!r} at {path}: {cause}")


@dataclass(frozen=True)
class CourseBookEntry:
    book_id: str
    role: str
    path: Path
    required: bool
    enabled: bool


class CourseRuntime:
    """Fail-closed course runtime that delegates book internals to BookRuntime."""

    def __init__(self, course_dir: Path, manifest: dict[str, Any]):
        self.course_dir = course_dir
        self.manifest = dict(manifest)
        self.course_id = str(manifest.get("course_id") or "")
        self.name = str(manifest.get("name") or self.course_id)
        self.main_book_id = str(manifest.get("main_book_id") or "")
        self.entries: tuple[CourseBookEntry, ...] = ()
        self.books: dict[str, BookRuntime] = {}

    @classmethod
    def open(cls, course_dir: str | Path) -> "CourseRuntime":
        root = Path(course_dir).resolve()
        manifest_path = root / "course.json"
        if not root.is_dir():
            raise CourseManifestError(f"Course directory does not exist: {root}")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CourseManifestError(f"Course manifest missing: {manifest_path}") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise CourseManifestError(f"Cannot parse course manifest {manifest_path}: {exc}") from exc
        if not isinstance(manifest, dict):
            raise CourseManifestError(f"Expected JSON object in {manifest_path}")

        runtime = cls(root, manifest)
        runtime._load()
        return runtime

    def _load(self) -> None:
        self._validate_manifest()
        self._open_books()

    def _validate_manifest(self) -> None:
        course_id = self.manifest.get("course_id")
        if not isinstance(course_id, str) or not course_id.strip():
            raise CourseManifestError("course_id must be a non-empty string")

        main_book_id = self.manifest.get("main_book_id")
        if not isinstance(main_book_id, str) or not main_book_id.strip():
            raise CourseManifestError("main_book_id must be a non-empty string")

        raw_books = self.manifest.get("books")
        if not isinstance(raw_books, list) or not raw_books:
            raise CourseManifestError("books must be a non-empty list")

        entries: list[CourseBookEntry] = []
        enabled_ids: set[str] = set()
        enabled_main: list[CourseBookEntry] = []

        for index, raw in enumerate(raw_books):
            if not isinstance(raw, dict):
                raise CourseManifestError(f"books[{index}] must be a JSON object")

            book_id = raw.get("book_id")
            if not isinstance(book_id, str) or not book_id.strip():
                raise CourseManifestError(f"books[{index}].book_id must be a non-empty string")

            role = raw.get("role")
            if not isinstance(role, str) or role not in ALLOWED_BOOK_ROLES:
                raise CourseManifestError(
                    f"books[{index}].role must be one of {sorted(ALLOWED_BOOK_ROLES)}"
                )

            raw_path = raw.get("path")
            if not isinstance(raw_path, str) or not raw_path.strip():
                raise CourseManifestError(f"books[{index}].path must be a non-empty string")

            required = raw.get("required")
            if not isinstance(required, bool):
                raise CourseManifestError(f"books[{index}].required must be boolean")

            enabled = raw.get("enabled")
            if not isinstance(enabled, bool):
                raise CourseManifestError(f"books[{index}].enabled must be boolean")

            entry = CourseBookEntry(
                book_id=book_id,
                role=role,
                path=Path(raw_path),
                required=required,
                enabled=enabled,
            )
            entries.append(entry)

            if enabled:
                if book_id in enabled_ids:
                    raise CourseManifestError(f"Duplicate enabled book_id: {book_id!r}")
                enabled_ids.add(book_id)
                if role == "main":
                    enabled_main.append(entry)

        if len(enabled_main) != 1:
            raise CourseManifestError(
                f"Exactly one enabled main book is required; found {len(enabled_main)}"
            )
        if enabled_main[0].book_id != main_book_id:
            raise CourseManifestError(
                f"main_book_id {main_book_id!r} does not match enabled main entry "
                f"{enabled_main[0].book_id!r}"
            )

        self.course_id = course_id
        self.main_book_id = main_book_id
        self.entries = tuple(entries)

    def _find_repository_root(self) -> Path:
        for candidate in (self.course_dir, *self.course_dir.parents):
            if (candidate / "runtime").is_dir() and (candidate / "books").is_dir():
                return candidate.resolve()
        raise CourseBookResolutionError(
            f"Cannot locate repository root above course directory: {self.course_dir}"
        )

    def _resolve_book_path(self, raw_path: str, repository_root: Path) -> Path:
        path = Path(raw_path)
        candidate = path.resolve() if path.is_absolute() else (self.course_dir / path).resolve()
        try:
            candidate.relative_to(repository_root)
        except ValueError as exc:
            raise CourseBookResolutionError(
                f"Configured book path escapes repository root: {raw_path!r} -> {candidate}"
            ) from exc
        if not candidate.is_dir():
            raise CourseBookResolutionError(f"Configured book directory does not exist: {candidate}")
        return candidate

    def _open_books(self) -> None:
        repository_root = self._find_repository_root()
        for entry in self.entries:
            if not entry.enabled:
                continue
            resolved_path = self._resolve_book_path(str(entry.path), repository_root)
            try:
                book = BookRuntime.open(resolved_path)
            except (BookRuntimeBlockedError, BookRuntimeError) as exc:
                raise CourseRuntimeBlockedError(entry.book_id, resolved_path, exc) from exc
            if book.book_id != entry.book_id:
                raise CourseManifestError(
                    f"Manifest book_id {entry.book_id!r} does not match canonical "
                    f"BookRuntime ID {book.book_id!r}"
                )
            self.books[entry.book_id] = book

    def book_ids(self) -> list[str]:
        """Return enabled mounted book IDs in manifest order."""

        return list(self.books)
