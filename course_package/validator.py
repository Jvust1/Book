from __future__ import annotations

import json
import re
from pathlib import Path, PureWindowsPath
from typing import Any

from .artifacts import (
    ArtifactInventoryError,
    ArtifactRecord,
    compute_content_identity,
    sha256_file,
)
from .compiler import CompiledCoursePackage
from .contracts import (
    CANONICAL_BOOK_ROLES,
    PACKAGE_FILENAMES,
    PACKAGE_VERSION,
    READINESS_STATUSES,
    SCHEMA_VERSION,
    PackageDiagnostic,
    PackageValidationResult,
    canonical_json_bytes,
    sha256_bytes,
)


_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SECRET_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "token",
        "access_token",
        "refresh_token",
        "password",
        "secret",
        "client_secret",
    }
)
_ARTIFACT_TYPES = frozenset(
    {
        "book_metadata",
        "structured_complete",
        "audit_report",
        "toc",
        "page_map",
        "search_index",
        "qa_policy",
        "structure",
        "readiness",
    }
)
_REQUIRED_SINGLE_ARTIFACT_TYPES = frozenset(
    {
        "book_metadata",
        "structured_complete",
        "audit_report",
        "toc",
        "page_map",
        "search_index",
        "qa_policy",
        "readiness",
    }
)
_JSON_FILENAMES = tuple(name for name in PACKAGE_FILENAMES if name.endswith(".json"))

_COURSE_KEYS = frozenset(
    {
        "schema_version",
        "package_version",
        "course_id",
        "course_name",
        "language",
        "primary_book_id",
        "book_ids",
        "chapter_count",
        "section_count",
        "search_record_count",
        "package_identity",
        "readiness",
    }
)
_BOOK_KEYS = frozenset(
    {
        "book_id",
        "logical_book_id",
        "book_version_id",
        "role",
        "canonical_path",
        "enabled",
        "required",
        "structured_status",
        "structured_version",
        "runtime_status",
        "pdf_page_count",
        "printed_final_page",
        "content_identity",
    }
)
_ARTIFACT_KEYS = frozenset(
    {
        "artifact_type",
        "relative_path",
        "sha256",
        "size_bytes",
        "required",
        "book_id",
    }
)
_CHAPTER_KEYS = frozenset({"chapter_id", "title_en", "title_zh"})
_SECTION_KEYS = frozenset(
    {
        "section_id",
        "chapter_id",
        "number",
        "title_en",
        "title_zh",
        "pdf_page_start",
        "pdf_page_end",
        "printed_page_start",
        "printed_page_end",
    }
)


def _diag(
    code: str,
    detail: str,
    relative_path: str | None = None,
    *,
    severity: str = "FAIL",
) -> PackageDiagnostic:
    return PackageDiagnostic(code, severity, detail, relative_path)


def _result(diagnostics: list[PackageDiagnostic]) -> PackageValidationResult:
    ordered = tuple(
        sorted(
            diagnostics,
            key=lambda item: (
                0 if item.severity == "FAIL" else 1,
                item.code,
                item.relative_path or "",
                item.detail,
            ),
        )
    )
    status = (
        "FAIL"
        if any(item.severity == "FAIL" for item in ordered)
        else "WARN"
        if ordered
        else "PASS"
    )
    return PackageValidationResult(status, ordered)


def _exact_dict(
    value: Any,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> bool:
    return (
        isinstance(value, dict)
        and required.issubset(value)
        and set(value).issubset(required | optional)
    )


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _uint(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _sha(value: Any) -> bool:
    return isinstance(value, str) and _HEX64.fullmatch(value) is not None


def _optional_text(value: Any) -> bool:
    return value is None or isinstance(value, str)


def _page(value: Any) -> bool:
    return value is None or isinstance(value, str) or (
        isinstance(value, int) and not isinstance(value, bool)
    )


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            (isinstance(key, str) and key.casefold() in _SECRET_KEYS)
            or _contains_secret_key(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(_contains_secret_key(item) for item in value)
    return False


def _safe_path(root: Path, value: str) -> Path | None:
    if Path(value).is_absolute() or PureWindowsPath(value).is_absolute():
        return None
    root = root.resolve()
    resolved = (root / value).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def _load_package(
    package_dir: Path,
) -> tuple[dict[str, dict[str, Any]] | None, str | None, list[PackageDiagnostic]]:
    diagnostics: list[PackageDiagnostic] = []
    root = Path(package_dir)
    if not root.is_dir():
        return None, None, [
            _diag("schema_error", "Course Package directory is unavailable.")
        ]

    try:
        entries = {entry.name for entry in root.iterdir()}
    except OSError:
        return None, None, [
            _diag("schema_error", "Course Package directory cannot be read.")
        ]

    if entries != set(PACKAGE_FILENAMES):
        return None, None, [
            _diag(
                "schema_error",
                "Course Package file set does not match the frozen contract.",
            )
        ]

    documents: dict[str, dict[str, Any]] = {}
    for name in _JSON_FILENAMES:
        try:
            value = json.loads((root / name).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            diagnostics.append(
                _diag(
                    "schema_error",
                    "Course Package document is not valid UTF-8 JSON.",
                    name,
                )
            )
            continue
        if not isinstance(value, dict):
            diagnostics.append(
                _diag(
                    "schema_error",
                    "Course Package document must be a JSON object.",
                    name,
                )
            )
            continue
        documents[name] = value

    try:
        sidecar = (root / "package.sha256").read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
        diagnostics.append(
            _diag(
                "schema_error",
                "Package identity sidecar cannot be read.",
                "package.sha256",
            )
        )
        sidecar = None
    if sidecar is not None and not _sha(sidecar):
        diagnostics.append(
            _diag(
                "schema_error",
                "Package identity sidecar is not a canonical SHA-256 value.",
                "package.sha256",
            )
        )
    return (None if diagnostics else documents), sidecar, diagnostics


def _validate_schema(
    documents: dict[str, dict[str, Any]],
) -> list[PackageDiagnostic]:
    diagnostics: list[PackageDiagnostic] = []
    if set(documents) != set(_JSON_FILENAMES):
        return [_diag("schema_error", "Course Package JSON set is incomplete.")]

    for name, document in documents.items():
        if _contains_secret_key(document):
            diagnostics.append(
                _diag(
                    "schema_error",
                    "Forbidden secret-like key is present in a Course Package document.",
                    name,
                )
            )

    course = documents["course_package.json"]
    course_ok = _exact_dict(course, _COURSE_KEYS)
    if course_ok:
        course_ok = (
            course["schema_version"] == SCHEMA_VERSION
            and course["package_version"] == PACKAGE_VERSION
            and all(
                _text(course[field])
                for field in ("course_id", "course_name", "language", "primary_book_id")
            )
            and isinstance(course["book_ids"], list)
            and bool(course["book_ids"])
            and all(_text(item) for item in course["book_ids"])
            and len(course["book_ids"]) == len(set(course["book_ids"]))
            and all(
                _uint(course[field])
                for field in ("chapter_count", "section_count", "search_record_count")
            )
            and _sha(course["package_identity"])
            and course["readiness"] in READINESS_STATUSES
        )
    if not course_ok:
        diagnostics.append(
            _diag(
                "schema_error",
                "course_package.json violates the frozen contract.",
                "course_package.json",
            )
        )

    books_doc = documents["books.json"]
    raw_books = (
        books_doc.get("books")
        if _exact_dict(books_doc, frozenset({"schema_version", "books"}))
        else None
    )
    books_ok = (
        books_doc.get("schema_version") == SCHEMA_VERSION
        and isinstance(raw_books, list)
        and bool(raw_books)
    )
    books: list[dict[str, Any]] = []
    if books_ok:
        for book in raw_books:
            item_ok = _exact_dict(book, _BOOK_KEYS)
            if item_ok:
                item_ok = (
                    all(
                        _text(book[field])
                        for field in (
                            "book_id",
                            "logical_book_id",
                            "book_version_id",
                            "canonical_path",
                            "structured_status",
                            "structured_version",
                            "runtime_status",
                        )
                    )
                    and book["role"] in CANONICAL_BOOK_ROLES
                    and isinstance(book["enabled"], bool)
                    and isinstance(book["required"], bool)
                    and _uint(book["pdf_page_count"])
                    and not isinstance(book["printed_final_page"], bool)
                    and isinstance(book["printed_final_page"], (int, str))
                    and _sha(book["content_identity"])
                )
            if not item_ok:
                books_ok = False
                break
            books.append(book)
        if len({book["book_id"] for book in books}) != len(books):
            books_ok = False
    if not books_ok:
        diagnostics.append(
            _diag("schema_error", "books.json violates the frozen contract.", "books.json")
        )
    elif course_ok:
        enabled_ids = [book["book_id"] for book in books if book["enabled"]]
        primary = [
            book for book in books if book["enabled"] and book["role"] == "primary"
        ]
        if (
            len(primary) != 1
            or primary[0]["book_id"] != course["primary_book_id"]
            or enabled_ids != course["book_ids"]
        ):
            diagnostics.append(
                _diag(
                    "schema_error",
                    "Exactly one enabled primary Book and matching enabled Book order are required.",
                    "books.json",
                )
            )

    artifacts_doc = documents["artifacts.json"]
    raw_artifacts = (
        artifacts_doc.get("artifacts")
        if _exact_dict(artifacts_doc, frozenset({"schema_version", "artifacts"}))
        else None
    )
    artifacts_ok = (
        artifacts_doc.get("schema_version") == SCHEMA_VERSION
        and isinstance(raw_artifacts, list)
        and bool(raw_artifacts)
    )
    artifacts: list[dict[str, Any]] = []
    if artifacts_ok:
        known_books = {book["book_id"] for book in books}
        seen: set[tuple[str, str]] = set()
        for artifact in raw_artifacts:
            item_ok = _exact_dict(artifact, _ARTIFACT_KEYS)
            if item_ok:
                item_ok = (
                    artifact["artifact_type"] in _ARTIFACT_TYPES
                    and _text(artifact["relative_path"])
                    and _sha(artifact["sha256"])
                    and _uint(artifact["size_bytes"])
                    and isinstance(artifact["required"], bool)
                    and _text(artifact["book_id"])
                    and artifact["book_id"] in known_books
                )
            if not item_ok:
                artifacts_ok = False
                break
            key = (artifact["relative_path"], artifact["artifact_type"])
            if key in seen:
                artifacts_ok = False
                break
            seen.add(key)
            artifacts.append(artifact)

        if artifacts_ok:
            for book in books:
                counts: dict[str, int] = {}
                for artifact in artifacts:
                    if artifact["book_id"] == book["book_id"]:
                        kind = artifact["artifact_type"]
                        counts[kind] = counts.get(kind, 0) + 1
                if (
                    any(
                        counts.get(kind) != 1
                        for kind in _REQUIRED_SINGLE_ARTIFACT_TYPES
                    )
                    or counts.get("structure", 0) < 1
                ):
                    artifacts_ok = False
                    break
    if not artifacts_ok:
        diagnostics.append(
            _diag(
                "schema_error",
                "artifacts.json violates the frozen inventory contract.",
                "artifacts.json",
            )
        )

    chapters_doc = documents["chapters.json"]
    raw_chapters = (
        chapters_doc.get("chapters")
        if _exact_dict(chapters_doc, frozenset({"schema_version", "chapters"}))
        else None
    )
    chapters_ok = (
        chapters_doc.get("schema_version") == SCHEMA_VERSION
        and isinstance(raw_chapters, list)
    )
    chapters: list[dict[str, Any]] = []
    if chapters_ok:
        for chapter in raw_chapters:
            if not (
                _exact_dict(chapter, _CHAPTER_KEYS)
                and _text(chapter["chapter_id"])
                and _optional_text(chapter["title_en"])
                and _optional_text(chapter["title_zh"])
            ):
                chapters_ok = False
                break
            chapters.append(chapter)
        if len({chapter["chapter_id"] for chapter in chapters}) != len(chapters):
            chapters_ok = False
    if not chapters_ok:
        diagnostics.append(
            _diag(
                "schema_error",
                "chapters.json violates the frozen package shape.",
                "chapters.json",
            )
        )

    sections_doc = documents["sections.json"]
    raw_sections = (
        sections_doc.get("sections")
        if _exact_dict(sections_doc, frozenset({"schema_version", "sections"}))
        else None
    )
    sections_ok = (
        sections_doc.get("schema_version") == SCHEMA_VERSION
        and isinstance(raw_sections, list)
    )
    sections: list[dict[str, Any]] = []
    if sections_ok:
        chapter_ids = {chapter["chapter_id"] for chapter in chapters}
        for section in raw_sections:
            if not (
                _exact_dict(section, _SECTION_KEYS)
                and _text(section["section_id"])
                and _text(section["chapter_id"])
                and section["chapter_id"] in chapter_ids
                and _page(section["number"])
                and all(
                    _optional_text(section[field])
                    for field in ("title_en", "title_zh")
                )
                and all(
                    _page(section[field])
                    for field in (
                        "pdf_page_start",
                        "pdf_page_end",
                        "printed_page_start",
                        "printed_page_end",
                    )
                )
            ):
                sections_ok = False
                break
            sections.append(section)
        if len({section["section_id"] for section in sections}) != len(sections):
            sections_ok = False
    if not sections_ok:
        diagnostics.append(
            _diag(
                "schema_error",
                "sections.json violates the frozen package shape.",
                "sections.json",
            )
        )

    readiness = documents["readiness.json"]
    raw_readiness_diagnostics = (
        readiness.get("diagnostics")
        if _exact_dict(
            readiness,
            frozenset({"schema_version", "status", "diagnostics"}),
        )
        else None
    )
    readiness_ok = (
        readiness.get("schema_version") == SCHEMA_VERSION
        and readiness.get("status") in READINESS_STATUSES
        and isinstance(raw_readiness_diagnostics, list)
    )
    severities: list[str] = []
    if readiness_ok:
        for item in raw_readiness_diagnostics:
            if not (
                _exact_dict(
                    item,
                    frozenset({"code", "severity", "detail"}),
                    frozenset({"relative_path"}),
                )
                and _text(item["code"])
                and item["severity"] in {"WARN", "FAIL"}
                and _text(item["detail"])
                and (
                    item.get("relative_path") is None
                    or isinstance(item.get("relative_path"), str)
                )
            ):
                readiness_ok = False
                break
            severities.append(item["severity"])
        derived = (
            "FAIL"
            if "FAIL" in severities
            else "WARN"
            if "WARN" in severities
            else "PASS"
        )
        if readiness.get("status") != derived:
            readiness_ok = False
        if course_ok and course["readiness"] != readiness.get("status"):
            readiness_ok = False
    if not readiness_ok:
        diagnostics.append(
            _diag(
                "schema_error",
                "readiness.json violates the frozen readiness contract.",
                "readiness.json",
            )
        )

    return diagnostics


def _path_stage(
    documents: dict[str, dict[str, Any]],
    repository_root: Path,
) -> tuple[dict[str, Path], list[PackageDiagnostic]]:
    diagnostics: list[PackageDiagnostic] = []
    root = Path(repository_root)
    for book in documents["books.json"]["books"]:
        if _safe_path(root, book["canonical_path"]) is None:
            diagnostics.append(
                _diag(
                    "path_escape",
                    "Canonical Book path escapes the repository boundary.",
                    "books.json",
                )
            )

    artifact_paths: dict[str, Path] = {}
    for artifact in documents["artifacts.json"]["artifacts"]:
        resolved = _safe_path(root, artifact["relative_path"])
        if resolved is None:
            diagnostics.append(
                _diag(
                    "path_escape",
                    "Artifact path escapes the repository boundary.",
                    "artifacts.json",
                )
            )
        else:
            artifact_paths[artifact["relative_path"]] = resolved
    return artifact_paths, diagnostics


def _artifact_stage(
    documents: dict[str, dict[str, Any]],
    artifact_paths: dict[str, Path],
) -> tuple[dict[str, Path], list[PackageDiagnostic]]:
    diagnostics: list[PackageDiagnostic] = []
    readable: dict[str, Path] = {}
    records: dict[str, list[ArtifactRecord]] = {}

    for artifact in documents["artifacts.json"]["artifacts"]:
        relative = artifact["relative_path"]
        path = artifact_paths[relative]
        if not path.is_file():
            diagnostics.append(
                _diag(
                    "artifact_missing",
                    "Required canonical artifact is unavailable.",
                    relative,
                )
            )
            continue
        try:
            size = path.stat().st_size
            digest = sha256_file(path)
        except (OSError, ArtifactInventoryError):
            diagnostics.append(
                _diag(
                    "artifact_missing",
                    "Canonical artifact cannot be read.",
                    relative,
                )
            )
            continue

        readable[relative] = path
        if size != artifact["size_bytes"] or digest != artifact["sha256"]:
            diagnostics.append(
                _diag(
                    "artifact_hash_mismatch",
                    "Canonical artifact bytes do not match the package inventory.",
                    relative,
                )
            )
        records.setdefault(artifact["book_id"], []).append(
            ArtifactRecord(
                artifact_type=artifact["artifact_type"],
                relative_path=relative,
                sha256=digest,
                size_bytes=size,
                required=artifact["required"],
                book_id=artifact["book_id"],
            )
        )

    for book in documents["books.json"]["books"]:
        expected = sum(
            artifact["book_id"] == book["book_id"]
            for artifact in documents["artifacts.json"]["artifacts"]
        )
        actual_records = records.get(book["book_id"], [])
        if (
            len(actual_records) == expected
            and compute_content_identity(actual_records) != book["content_identity"]
        ):
            diagnostics.append(
                _diag(
                    "identity_error",
                    "Book content identity does not match canonical artifact bytes.",
                    "books.json",
                )
            )
    return readable, diagnostics


def _structural_counts(
    documents: dict[str, dict[str, Any]],
    readable: dict[str, Path],
) -> tuple[dict[str, int] | None, list[PackageDiagnostic]]:
    primary = documents["course_package.json"]["primary_book_id"]
    search_rows = [
        artifact
        for artifact in documents["artifacts.json"]["artifacts"]
        if artifact["book_id"] == primary
        and artifact["artifact_type"] == "search_index"
    ]
    if len(search_rows) != 1:
        return None, [
            _diag(
                "structural_baseline_mismatch",
                "Primary Book search index is not uniquely identifiable.",
                "artifacts.json",
            )
        ]
    relative = search_rows[0]["relative_path"]
    path = readable.get(relative)
    if path is None:
        return None, []
    try:
        with path.open("r", encoding="utf-8") as handle:
            search_count = sum(1 for line in handle if line.strip())
    except (OSError, UnicodeError):
        return None, [
            _diag(
                "structural_baseline_mismatch",
                "Primary Book search index cannot be counted safely.",
                relative,
            )
        ]
    return {
        "chapter_count": len(documents["chapters.json"]["chapters"]),
        "section_count": len(documents["sections.json"]["sections"]),
        "search_record_count": search_count,
    }, []


def _identity_stage(
    documents: dict[str, dict[str, Any]],
    package_sha: str,
    counts: dict[str, int] | None,
) -> list[PackageDiagnostic]:
    diagnostics: list[PackageDiagnostic] = []
    course = documents["course_package.json"]
    if package_sha != course["package_identity"]:
        diagnostics.append(
            _diag(
                "identity_error",
                "package.sha256 does not match course_package.json identity.",
                "package.sha256",
            )
        )
    if counts is not None:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "package_version": PACKAGE_VERSION,
            "course": {
                key: value
                for key, value in course.items()
                if key != "package_identity"
            },
            "books": documents["books.json"]["books"],
            "artifacts": documents["artifacts.json"]["artifacts"],
            "structural_baseline": counts,
        }
        recomputed = sha256_bytes(canonical_json_bytes(payload))
        if recomputed != course["package_identity"]:
            diagnostics.append(
                _diag(
                    "identity_error",
                    "Package identity does not match independent recomputation.",
                    "course_package.json",
                )
            )
    return diagnostics


def _structural_stage(
    documents: dict[str, dict[str, Any]],
    counts: dict[str, int] | None,
) -> list[PackageDiagnostic]:
    if counts is None:
        return []
    course = documents["course_package.json"]
    return [
        _diag(
            "structural_baseline_mismatch",
            f"{field} does not match independently observed package structure.",
            "course_package.json",
        )
        for field, actual in counts.items()
        if course[field] != actual
    ]


def _readiness_stage(
    documents: dict[str, dict[str, Any]],
) -> list[PackageDiagnostic]:
    diagnostics: list[PackageDiagnostic] = []
    for book in documents["books.json"]["books"]:
        if (book["enabled"] or book["required"]) and (
            book["structured_status"] != "STRUCTURED_COMPLETE"
            or book["runtime_status"] != "READY"
        ):
            diagnostics.append(
                _diag(
                    "book_not_ready",
                    "A required or enabled Book is not compile/runtime ready.",
                    "books.json",
                )
            )

    stored = documents["readiness.json"]["status"]
    if stored == "FAIL":
        diagnostics.append(
            _diag(
                "book_not_ready",
                "Stored package readiness reports a failure.",
                "readiness.json",
            )
        )
    elif stored == "WARN":
        diagnostics.append(
            _diag(
                "book_not_ready",
                "Stored package readiness reports warnings.",
                "readiness.json",
                severity="WARN",
            )
        )
    return diagnostics


def _validate_documents(
    documents: dict[str, dict[str, Any]],
    package_sha: str,
    repository_root: Path,
) -> PackageValidationResult:
    schema = _validate_schema(documents)
    if schema:
        return _result(schema)

    artifact_paths, path_diagnostics = _path_stage(
        documents,
        Path(repository_root),
    )
    if path_diagnostics:
        return _result(path_diagnostics)

    readable, artifact_diagnostics = _artifact_stage(documents, artifact_paths)
    counts, count_diagnostics = _structural_counts(documents, readable)

    diagnostics = list(artifact_diagnostics)
    diagnostics.extend(count_diagnostics)
    diagnostics.extend(_identity_stage(documents, package_sha, counts))
    diagnostics.extend(_structural_stage(documents, counts))
    diagnostics.extend(_readiness_stage(documents))
    return _result(diagnostics)


def validate_course_package(
    package_dir: Path,
    repository_root: Path,
) -> PackageValidationResult:
    documents, sidecar, diagnostics = _load_package(Path(package_dir))
    if diagnostics or documents is None or sidecar is None:
        return _result(diagnostics)
    return _validate_documents(documents, sidecar, Path(repository_root))


def validate_compiled_package(
    package: CompiledCoursePackage,
    repository_root: Path,
) -> PackageValidationResult:
    course = package.documents.get("course_package.json")
    if isinstance(course, dict) and (
        package.course_id != course.get("course_id")
        or package.package_identity != course.get("package_identity")
    ):
        return _result(
            [
                _diag(
                    "package_nondeterministic",
                    "Compiled package wrapper identity disagrees with its documents.",
                    "course_package.json",
                )
            ]
        )
    documents = {
        name: value
        for name, value in package.documents.items()
        if isinstance(value, dict)
    }
    return _validate_documents(
        documents,
        package.package_identity,
        Path(repository_root),
    )
