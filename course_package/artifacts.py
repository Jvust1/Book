from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .contracts import canonical_json_bytes, sha256_bytes


class ArtifactInventoryError(RuntimeError):
    """Raised when canonical course artifacts cannot be inventoried safely."""


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_type: str
    relative_path: str
    sha256: str
    size_bytes: int
    required: bool
    book_id: str


def repository_relative(path: Path, repository_root: Path) -> str:
    root = Path(repository_root).resolve()
    resolved = Path(path).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ArtifactInventoryError(
            f"artifact path escapes repository root: {resolved}"
        ) from exc
    return relative.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as fh:
            for block in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise ArtifactInventoryError(f"cannot hash artifact {path}: {exc}") from exc
    return digest.hexdigest()


def _load_json_object(path: Path, repository_root: Path, label: str) -> dict[str, Any]:
    repository_relative(path, repository_root)
    if not path.is_file():
        raise ArtifactInventoryError(f"required artifact missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactInventoryError(f"cannot read {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ArtifactInventoryError(f"{label} must be a JSON object: {path}")
    return value


def _require_reference(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ArtifactInventoryError(f"{field} must be a non-empty relative path")
    candidate = Path(value.strip())
    if candidate.is_absolute():
        raise ArtifactInventoryError(f"{field} must not be an absolute path: {value!r}")
    return value.strip()


def _record(
    *,
    artifact_type: str,
    path: Path,
    repository_root: Path,
    book_id: str,
    required: bool = True,
) -> ArtifactRecord:
    relative = repository_relative(path, repository_root)
    if not path.is_file():
        raise ArtifactInventoryError(f"required artifact missing: {relative}")
    return ArtifactRecord(
        artifact_type=artifact_type,
        relative_path=relative,
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        required=required,
        book_id=book_id,
    )


def build_book_artifact_inventory(
    repository_root: Path,
    canonical_book_path: str,
    book_id: str,
) -> tuple[ArtifactRecord, ...]:
    root = Path(repository_root).resolve()
    raw_book_path = Path(canonical_book_path)
    if raw_book_path.is_absolute():
        raise ArtifactInventoryError(
            f"canonical book path must be repository-relative: {canonical_book_path!r}"
        )

    book_root = (root / raw_book_path).resolve()
    repository_relative(book_root, root)
    if not book_root.is_dir():
        raise ArtifactInventoryError(f"canonical book directory missing: {canonical_book_path}")

    metadata_path = book_root / "book_metadata.json"
    completion_path = book_root / "STRUCTURED_COMPLETE.json"
    metadata = _load_json_object(metadata_path, root, "book_metadata")
    completion = _load_json_object(completion_path, root, "STRUCTURED_COMPLETE")

    metadata_book_id = metadata.get("book_id")
    completion_book_id = completion.get("book_id")
    if metadata_book_id != book_id or completion_book_id != book_id:
        raise ArtifactInventoryError(
            "canonical book identity mismatch: "
            f"expected={book_id!r}, metadata={metadata_book_id!r}, "
            f"completion={completion_book_id!r}"
        )

    required_paths = (
        ("book_metadata", metadata_path),
        ("structured_complete", completion_path),
        (
            "audit_report",
            book_root
            / _require_reference(completion.get("audit_report"), "STRUCTURED_COMPLETE.audit_report"),
        ),
        (
            "toc",
            book_root / _require_reference(metadata.get("toc_file"), "book_metadata.toc_file"),
        ),
        (
            "page_map",
            book_root
            / _require_reference(metadata.get("page_map_file"), "book_metadata.page_map_file"),
        ),
        (
            "search_index",
            book_root
            / _require_reference(completion.get("search_index"), "STRUCTURED_COMPLETE.search_index"),
        ),
        ("qa_policy", book_root / "qa_retrieval_policy.json"),
        ("readiness", book_root / "RUNTIME_READINESS.json"),
    )

    records = [
        _record(
            artifact_type=artifact_type,
            path=path,
            repository_root=root,
            book_id=book_id,
        )
        for artifact_type, path in required_paths
    ]

    structure_paths = sorted(
        path
        for path in book_root.rglob("*_structure.json")
        if path.name != "RUNTIME_READINESS.json"
    )
    if not structure_paths:
        raise ArtifactInventoryError(
            f"required structure artifacts missing under {canonical_book_path}"
        )
    records.extend(
        _record(
            artifact_type="structure",
            path=path,
            repository_root=root,
            book_id=book_id,
        )
        for path in structure_paths
    )

    return tuple(sorted(records, key=lambda item: (item.relative_path, item.artifact_type)))


def compute_content_identity(records: Iterable[ArtifactRecord]) -> str:
    identity_input = [
        {
            "artifact_type": record.artifact_type,
            "relative_path": record.relative_path,
            "sha256": record.sha256,
            "size_bytes": record.size_bytes,
            "required": record.required,
            "book_id": record.book_id,
        }
        for record in sorted(
            tuple(records),
            key=lambda item: (item.relative_path, item.artifact_type),
        )
    ]
    return sha256_bytes(canonical_json_bytes(identity_input))
