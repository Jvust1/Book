"""Public contract surface for Foundation A Course Package support."""

from .compiler import CompiledCoursePackage, PackageCompileError, compile_course_package
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
from .golden import verify_golden_course
from .validator import validate_compiled_package, validate_course_package

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
    "CompiledCoursePackage",
    "PackageCompileError",
    "compile_course_package",
    "verify_golden_course",
    "validate_compiled_package",
    "validate_course_package",
]
