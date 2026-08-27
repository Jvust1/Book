"""App-level catalog runtime for independent textbook courses."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .course_runtime import CourseRuntime, CourseRuntimeError


class LibraryRuntimeError(RuntimeError):
    """Base error for App-level course catalog loading."""


class LibraryManifestError(LibraryRuntimeError):
    """Raised when library.json violates the Phase 1C contract."""


class LibraryCourseResolutionError(LibraryRuntimeError):
    """Raised when configured library/course paths are missing or untrusted."""


class LibraryRuntimeBlockedError(LibraryRuntimeError):
    """Raised when an enabled course cannot pass its normal runtime gates."""

    def __init__(self, course_id: str, path: Path, cause: Exception):
        self.course_id = course_id
        self.path = path
        self.cause = cause
        super().__init__(f"Library blocked by course {course_id!r} at {path}: {cause}")


@dataclass(frozen=True)
class LibraryCourseEntry:
    course_id: str
    name: str
    path: Path
    enabled: bool
    order: int
    position: int


class LibraryRuntime:
    """Fail-closed App-level catalog of independent CourseRuntime instances."""

    def __init__(self, library_dir: Path, manifest: dict[str, Any], repository_root: Path):
        self.library_dir = library_dir
        self.repository_root = repository_root
        self.manifest = dict(manifest)
        self.library_id = str(manifest.get("library_id") or "")
        self.name = str(manifest.get("name") or "")
        self.entries: tuple[LibraryCourseEntry, ...] = ()
        self._courses: dict[str, CourseRuntime] = {}

    @classmethod
    def open(
        cls,
        library_dir: str | Path,
        *,
        repository_root: str | Path | None = None,
    ) -> "LibraryRuntime":
        root = Path(library_dir).resolve()
        if not root.is_dir():
            raise LibraryManifestError(f"Library directory does not exist: {root}")

        repo = cls._repository_root(root, repository_root)
        manifest_path = root / "library.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise LibraryManifestError(f"Library manifest missing: {manifest_path}") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise LibraryManifestError(f"Cannot parse library manifest {manifest_path}: {exc}") from exc

        if not isinstance(manifest, dict):
            raise LibraryManifestError(f"Expected JSON object in {manifest_path}")

        runtime = cls(root, manifest, repo)
        runtime._load()
        return runtime

    @staticmethod
    def _repository_root(library_dir: Path, explicit: str | Path | None) -> Path:
        if explicit is not None:
            repo = Path(explicit).resolve()
        else:
            if library_dir.name != "library":
                raise LibraryCourseResolutionError(
                    "Nonstandard library layout requires repository_root"
                )
            repo = library_dir.parent.resolve()

        if not repo.is_dir():
            raise LibraryCourseResolutionError(f"Repository root does not exist: {repo}")

        try:
            library_dir.relative_to(repo)
        except ValueError as exc:
            raise LibraryCourseResolutionError(
                f"Library directory escapes repository root: {library_dir}"
            ) from exc
        return repo

    def _load(self) -> None:
        self._validate_manifest()
        self._open_courses()

    def _validate_manifest(self) -> None:
        if self.manifest.get("schema_version") != "library_manifest_v1":
            raise LibraryManifestError(
                "schema_version must be exactly 'library_manifest_v1'"
            )

        library_id = self.manifest.get("library_id")
        if not isinstance(library_id, str) or not library_id.strip():
            raise LibraryManifestError("library_id must be a non-empty string")

        name = self.manifest.get("name")
        if not isinstance(name, str) or not name.strip():
            raise LibraryManifestError("name must be a non-empty string")

        raw_courses = self.manifest.get("courses")
        if not isinstance(raw_courses, list) or not raw_courses:
            raise LibraryManifestError("courses must be a non-empty list")

        entries: list[LibraryCourseEntry] = []
        enabled_ids: set[str] = set()
        enabled_count = 0

        for position, raw in enumerate(raw_courses):
            if not isinstance(raw, dict):
                raise LibraryManifestError(f"courses[{position}] must be a JSON object")

            course_id = raw.get("course_id")
            if not isinstance(course_id, str) or not course_id.strip():
                raise LibraryManifestError(
                    f"courses[{position}].course_id must be a non-empty string"
                )

            course_name = raw.get("name")
            if not isinstance(course_name, str) or not course_name.strip():
                raise LibraryManifestError(
                    f"courses[{position}].name must be a non-empty string"
                )

            raw_path = raw.get("path")
            if not isinstance(raw_path, str) or not raw_path.strip():
                raise LibraryManifestError(
                    f"courses[{position}].path must be a non-empty string"
                )

            enabled = raw.get("enabled")
            if not isinstance(enabled, bool):
                raise LibraryManifestError(f"courses[{position}].enabled must be boolean")

            order = raw.get("order")
            if isinstance(order, bool) or not isinstance(order, int):
                raise LibraryManifestError(
                    f"courses[{position}].order must be an integer, not boolean"
                )

            entry = LibraryCourseEntry(
                course_id=course_id,
                name=course_name,
                path=Path(raw_path),
                enabled=enabled,
                order=order,
                position=position,
            )
            entries.append(entry)

            if enabled:
                enabled_count += 1
                if course_id in enabled_ids:
                    raise LibraryManifestError(
                        f"Duplicate enabled course_id: {course_id!r}"
                    )
                enabled_ids.add(course_id)

        if enabled_count == 0:
            raise LibraryManifestError("At least one enabled course is required")

        self.library_id = library_id
        self.name = name
        self.entries = tuple(entries)

    def _resolve_course_path(self, raw_path: str) -> Path:
        path = Path(raw_path)
        candidate = path.resolve() if path.is_absolute() else (self.library_dir / path).resolve()
        try:
            candidate.relative_to(self.repository_root)
        except ValueError as exc:
            raise LibraryCourseResolutionError(
                f"Configured course path escapes repository root: {raw_path!r} -> {candidate}"
            ) from exc

        if not candidate.is_dir():
            raise LibraryCourseResolutionError(
                f"Configured course directory does not exist: {candidate}"
            )
        return candidate

    def _open_courses(self) -> None:
        for entry in self.entries:
            if not entry.enabled:
                continue

            resolved_path = self._resolve_course_path(str(entry.path))
            try:
                course = CourseRuntime.open(resolved_path)
            except CourseRuntimeError as exc:
                raise LibraryRuntimeBlockedError(
                    entry.course_id,
                    resolved_path,
                    exc,
                ) from exc

            if course.course_id != entry.course_id:
                raise LibraryManifestError(
                    f"Library course_id {entry.course_id!r} does not match canonical "
                    f"CourseRuntime ID {course.course_id!r}"
                )

            self._courses[entry.course_id] = course

    def course_ids(self) -> list[str]:
        """Return enabled mounted course IDs in manifest order for the base contract."""

        return [entry.course_id for entry in self.entries if entry.enabled]
