from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runtime.course_runtime import CourseRuntime, CourseRuntimeError

from .artifacts import (
    ArtifactInventoryError,
    ArtifactRecord,
    build_book_artifact_inventory,
    compute_content_identity,
)
from .contracts import (
    PACKAGE_FILENAMES,
    PACKAGE_VERSION,
    SCHEMA_VERSION,
    canonical_json_bytes,
    sha256_bytes,
)
from .manifest import ManifestNormalizationError, normalize_course_manifest


class PackageCompileError(RuntimeError):
    """Raised when a Course Package cannot be compiled or written safely."""


@dataclass(frozen=True)
class CompiledCoursePackage:
    course_id: str
    package_identity: str
    documents: dict[str, Any]

    def file_bytes(self) -> dict[str, bytes]:
        rendered = {
            name: json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            ).encode("utf-8")
            + b"\n"
            for name, value in self.documents.items()
        }
        rendered["package.sha256"] = (self.package_identity + "\n").encode("ascii")
        if set(rendered) != set(PACKAGE_FILENAMES):
            raise PackageCompileError(
                "compiled package file set does not match the frozen Course Package contract"
            )
        return rendered

    def write(self, output_root: Path) -> Path:
        root = Path(output_root).resolve()
        target = (root / self.course_id / self.package_identity).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise PackageCompileError("generated package path escapes output root") from exc

        payloads = self.file_bytes()

        # Preflight every existing file before creating anything so a conflict
        # cannot leave a partially updated generated package directory.
        if target.exists() and not target.is_dir():
            raise PackageCompileError("generated package target exists and is not a directory")
        for name, payload in payloads.items():
            path = target / name
            if not path.exists():
                continue
            if not path.is_file():
                raise PackageCompileError(f"generated target is not a file: {name}")
            try:
                existing = path.read_bytes()
            except OSError as exc:
                raise PackageCompileError(f"cannot read generated file: {name}") from exc
            if existing != payload:
                raise PackageCompileError(f"conflicting generated file: {name}")

        try:
            target.mkdir(parents=True, exist_ok=True)
            for name, payload in payloads.items():
                path = target / name
                if path.exists():
                    continue
                path.write_bytes(payload)
        except OSError as exc:
            raise PackageCompileError("cannot write generated Course Package") from exc
        return target


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageCompileError(f"cannot read {label}") from exc
    if not isinstance(value, dict):
        raise PackageCompileError(f"{label} must be a JSON object")
    return value


def _parse_nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise PackageCompileError(f"{field} must be a non-negative integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise PackageCompileError(f"{field} must be a non-negative integer") from exc
    if parsed < 0:
        raise PackageCompileError(f"{field} must be a non-negative integer")
    return parsed


def _printed_final_page(value: Any) -> int | str:
    if isinstance(value, bool) or value is None:
        raise PackageCompileError("main_text_printed_pages must identify a final page")
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        raise PackageCompileError("main_text_printed_pages must identify a final page")
    final = text.rsplit("-", 1)[-1].strip()
    if final.isdigit():
        return int(final)
    return final


def _artifact_rows(records: list[ArtifactRecord]) -> list[dict[str, Any]]:
    return [
        asdict(record)
        for record in sorted(
            records,
            key=lambda item: (item.relative_path, item.artifact_type),
        )
    ]


def _count_search_records(path: Path | None) -> int:
    if path is None:
        raise PackageCompileError("primary book final search index is unavailable")
    try:
        with path.open("r", encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())
    except OSError as exc:
        raise PackageCompileError("cannot read primary book final search index") from exc


def compile_course_package(
    repository_root: Path,
    course_dir: Path,
) -> CompiledCoursePackage:
    root = Path(repository_root).resolve()
    course_root = Path(course_dir).resolve()
    try:
        course_root.relative_to(root)
    except ValueError as exc:
        raise PackageCompileError("course directory escapes repository root") from exc

    try:
        normalized = normalize_course_manifest(course_root, root)
        course = CourseRuntime.open(course_root)
    except (ManifestNormalizationError, CourseRuntimeError) as exc:
        raise PackageCompileError("course is not compile-ready") from exc

    chapters: list[dict[str, Any]] = []
    for row in course.chapters():
        chapter_id = str(row.get("id") or "")
        if not chapter_id:
            continue
        chapters.append(
            {
                "chapter_id": chapter_id,
                "title_en": row.get("title_en"),
                "title_zh": row.get("title_zh"),
            }
        )

    sections: list[dict[str, Any]] = []
    for chapter_id in course.chapter_ids():
        for section in course.sections_for_chapter(chapter_id):
            sections.append(
                {
                    "section_id": section.id,
                    "chapter_id": chapter_id,
                    "number": section.number,
                    "title_en": section.title_en,
                    "title_zh": section.title_zh,
                    "pdf_page_start": section.pdf_page_start,
                    "pdf_page_end": section.pdf_page_end,
                    "printed_page_start": section.printed_page_start,
                    "printed_page_end": section.printed_page_end,
                }
            )

    all_records: list[ArtifactRecord] = []
    book_rows: list[dict[str, Any]] = []
    for book in normalized.books:
        book_root = root / book.canonical_path
        try:
            records = build_book_artifact_inventory(
                root,
                book.canonical_path,
                book.book_id,
            )
        except ArtifactInventoryError as exc:
            raise PackageCompileError(
                f"canonical artifact inventory failed for book {book.book_id!r}"
            ) from exc
        all_records.extend(records)

        metadata = _load_json_object(book_root / "book_metadata.json", "book_metadata")
        completion = _load_json_object(
            book_root / "STRUCTURED_COMPLETE.json",
            "STRUCTURED_COMPLETE",
        )
        readiness = _load_json_object(
            book_root / "RUNTIME_READINESS.json",
            "RUNTIME_READINESS",
        )
        runtime_status = readiness.get("status")
        if not isinstance(runtime_status, str) or not runtime_status.strip():
            raise PackageCompileError("RUNTIME_READINESS.status must be non-empty")
        structured_status = completion.get("status")
        if not isinstance(structured_status, str) or not structured_status.strip():
            raise PackageCompileError("STRUCTURED_COMPLETE.status must be non-empty")

        book_rows.append(
            {
                "book_id": book.book_id,
                "logical_book_id": book.logical_book_id,
                "book_version_id": book.book_version_id,
                "role": book.role,
                "canonical_path": book.canonical_path,
                "enabled": book.enabled,
                "required": book.required,
                "structured_status": structured_status.strip(),
                "structured_version": book.structured_version,
                "runtime_status": runtime_status.strip(),
                "pdf_page_count": _parse_nonnegative_int(
                    metadata.get("pdf_total_pages"),
                    "book_metadata.pdf_total_pages",
                ),
                "printed_final_page": _printed_final_page(
                    metadata.get("main_text_printed_pages")
                ),
                "content_identity": compute_content_identity(records),
            }
        )

    search_record_count = _count_search_records(course.main_book().search_index_path)
    artifacts = _artifact_rows(all_records)

    course_package_doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "package_version": PACKAGE_VERSION,
        "course_id": normalized.course_id,
        "course_name": normalized.course_name,
        "language": normalized.language,
        "primary_book_id": normalized.primary_book_id,
        "book_ids": [book.book_id for book in normalized.books if book.enabled],
        "chapter_count": len(chapters),
        "section_count": len(sections),
        "search_record_count": search_record_count,
        "package_identity": "",
        "readiness": "PASS",
    }
    books_doc = {"schema_version": SCHEMA_VERSION, "books": book_rows}
    artifacts_doc = {"schema_version": SCHEMA_VERSION, "artifacts": artifacts}
    chapters_doc = {"schema_version": SCHEMA_VERSION, "chapters": chapters}
    sections_doc = {"schema_version": SCHEMA_VERSION, "sections": sections}
    readiness_doc = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "diagnostics": [],
    }

    identity_payload = {
        "schema_version": SCHEMA_VERSION,
        "package_version": PACKAGE_VERSION,
        "course": {
            key: value
            for key, value in course_package_doc.items()
            if key != "package_identity"
        },
        "books": books_doc["books"],
        "artifacts": artifacts_doc["artifacts"],
        "structural_baseline": {
            "chapter_count": len(chapters),
            "section_count": len(sections),
            "search_record_count": search_record_count,
        },
    }
    package_identity = sha256_bytes(canonical_json_bytes(identity_payload))
    course_package_doc["package_identity"] = package_identity

    documents = {
        "course_package.json": course_package_doc,
        "books.json": books_doc,
        "artifacts.json": artifacts_doc,
        "chapters.json": chapters_doc,
        "sections.json": sections_doc,
        "readiness.json": readiness_doc,
    }
    return CompiledCoursePackage(
        course_id=normalized.course_id,
        package_identity=package_identity,
        documents=documents,
    )
