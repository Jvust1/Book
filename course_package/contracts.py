from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from book_core.identity import CANONICAL_BOOK_ROLES

SCHEMA_VERSION = "course_package_v1"
PACKAGE_VERSION = "1.0.0"
READINESS_STATUSES = frozenset({"PASS", "WARN", "FAIL"})
PACKAGE_FILENAMES = (
    "course_package.json",
    "books.json",
    "artifacts.json",
    "chapters.json",
    "sections.json",
    "readiness.json",
    "package.sha256",
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class PackageDiagnostic:
    code: str
    severity: str
    detail: str
    relative_path: str | None = None


@dataclass(frozen=True)
class PackageValidationResult:
    status: str
    diagnostics: tuple[PackageDiagnostic, ...]