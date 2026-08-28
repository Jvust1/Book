"""Public contract surface for Foundation A Course Package support."""

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

__all__ = [
    "CANONICAL_BOOK_ROLES",
    "PACKAGE_FILENAMES",
    "PACKAGE_VERSION",
    "READINESS_STATUSES",
    "SCHEMA_VERSION",
    "PackageDiagnostic",
    "PackageValidationResult",
    "canonical_json_bytes",
    "sha256_bytes",
]
