from __future__ import annotations

import re
import tempfile
from pathlib import Path, PureWindowsPath
from typing import Any

from .artifacts import sha256_file
from .compiler import PackageCompileError, compile_course_package
from .contracts import PackageDiagnostic, PackageValidationResult
from .golden import GOLDEN_COURSE_DIR, verify_golden_course
from .validator import validate_compiled_package, validate_course_package


_BROWSER_EXTENSIONS = frozenset({".ts", ".tsx", ".js", ".jsx"})
_BROWSER_FORBIDDEN = (
    re.compile(r"\bsqlite3\b", re.IGNORECASE),
    re.compile(r"sqlite:\/\/", re.IGNORECASE),
    re.compile(r"\.sqlite3\b", re.IGNORECASE),
)
_BROWSER_SECRET_PATTERNS = (
    re.compile(
        r"\b(?:owner|google)?_?drive_?(?:access_?|refresh_?)?token\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bclient_?secret\b", re.IGNORECASE),
)
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
_GOLDEN_BOOK_DIR = Path("books/functional-analysis")


def _diagnostic(
    code: str,
    detail: str,
    relative_path: str | None = None,
    *,
    severity: str = "FAIL",
) -> PackageDiagnostic:
    return PackageDiagnostic(code, severity, detail, relative_path)


def _ordered_diagnostics(
    diagnostics: list[PackageDiagnostic] | tuple[PackageDiagnostic, ...],
) -> tuple[PackageDiagnostic, ...]:
    unique = {
        (item.code, item.severity, item.detail, item.relative_path): item
        for item in diagnostics
    }
    return tuple(
        sorted(
            unique.values(),
            key=lambda item: (
                0 if item.severity == "FAIL" else 1,
                item.code,
                item.relative_path or "",
                item.detail,
            ),
        )
    )


def _result(diagnostics: list[PackageDiagnostic]) -> PackageValidationResult:
    ordered = _ordered_diagnostics(diagnostics)
    status = (
        "FAIL"
        if any(item.severity == "FAIL" for item in ordered)
        else "WARN"
        if ordered
        else "PASS"
    )
    return PackageValidationResult(status, ordered)


def _snapshot_tree(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise OSError("canonical Golden Book directory is unavailable")
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    }


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def check_browser_source(repository_root: Path) -> tuple[PackageDiagnostic, ...]:
    root = Path(repository_root).resolve()
    source_root = root / "app" / "web" / "src"
    if not source_root.is_dir():
        return (
            _diagnostic(
                "browser_source_unavailable",
                "Browser source tree cannot be inspected safely.",
                "app/web/src",
            ),
        )

    diagnostics: list[PackageDiagnostic] = []
    for path in sorted(source_root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or path.suffix.casefold() not in _BROWSER_EXTENSIONS:
            continue
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            diagnostics.append(
                _diagnostic(
                    "browser_source_unreadable",
                    "Browser source file cannot be inspected safely.",
                    relative,
                )
            )
            continue
        if any(pattern.search(text) for pattern in _BROWSER_FORBIDDEN):
            diagnostics.append(
                _diagnostic(
                    "browser_durable_storage_forbidden",
                    "Browser source contains a forbidden durable SQLite dependency or filename.",
                    relative,
                )
            )
        if any(pattern.search(text) for pattern in _BROWSER_SECRET_PATTERNS):
            diagnostics.append(
                _diagnostic(
                    "browser_secret_material_forbidden",
                    "Browser source contains forbidden owner Drive credential material.",
                    relative,
                )
            )
    return _ordered_diagnostics(diagnostics)


def _looks_absolute_path(value: str) -> bool:
    return Path(value).is_absolute() or PureWindowsPath(value).is_absolute()


def check_compiled_documents(
    documents: dict[str, Any],
) -> tuple[PackageDiagnostic, ...]:
    diagnostics: list[PackageDiagnostic] = []

    def visit(value: Any, filename: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if isinstance(key, str) and key.casefold() in _SECRET_KEYS:
                    diagnostics.append(
                        _diagnostic(
                            "compiled_secret_key",
                            "Compiled package contains a forbidden secret-like field.",
                            filename,
                        )
                    )
                visit(nested, filename)
            return
        if isinstance(value, list):
            for nested in value:
                visit(nested, filename)
            return
        if isinstance(value, str) and _looks_absolute_path(value):
            diagnostics.append(
                _diagnostic(
                    "compiled_absolute_path",
                    "Compiled package contains an absolute path.",
                    filename,
                )
            )

    for filename, value in sorted(documents.items()):
        visit(value, filename)
    return _ordered_diagnostics(diagnostics)


def run_architecture_fitness(repository_root: Path) -> PackageValidationResult:
    root = Path(repository_root).resolve()
    diagnostics: list[PackageDiagnostic] = list(check_browser_source(root))
    book_root = root / _GOLDEN_BOOK_DIR

    try:
        before = _snapshot_tree(book_root)
    except OSError:
        diagnostics.append(
            _diagnostic(
                "golden_canonical_unavailable",
                "Canonical Golden Book tree cannot be snapshotted safely.",
                _GOLDEN_BOOK_DIR.as_posix(),
            )
        )
        before = None

    package = None
    try:
        package = compile_course_package(root, root / GOLDEN_COURSE_DIR)
    except (PackageCompileError, OSError, ValueError):
        diagnostics.append(
            _diagnostic(
                "architecture_compile_failed",
                "Golden Course Package cannot be compiled for architecture fitness.",
                GOLDEN_COURSE_DIR.as_posix(),
            )
        )

    if package is not None:
        diagnostics.extend(check_compiled_documents(package.documents))
        diagnostics.extend(validate_compiled_package(package, root).diagnostics)

        try:
            with tempfile.TemporaryDirectory(prefix="book-course-package-fitness-") as tmp:
                output_root = Path(tmp).resolve()
                package_dir = package.write(output_root)
                protected = (root / "books", root / "courses")
                if any(_is_within(package_dir, candidate) for candidate in protected):
                    diagnostics.append(
                        _diagnostic(
                            "canonical_output_boundary",
                            "Generated Course Package targeted a canonical books/courses tree.",
                        )
                    )
                diagnostics.extend(validate_course_package(package_dir, root).diagnostics)
        except (PackageCompileError, OSError, ValueError):
            diagnostics.append(
                _diagnostic(
                    "generated_package_verification_failed",
                    "Generated Course Package cannot be written and validated in an isolated output root.",
                )
            )

    golden = verify_golden_course(root)
    diagnostics.extend(golden.diagnostics)

    if before is not None:
        try:
            after = _snapshot_tree(book_root)
        except OSError:
            diagnostics.append(
                _diagnostic(
                    "golden_canonical_mutation",
                    "Canonical Golden Book tree cannot be verified after architecture fitness.",
                    _GOLDEN_BOOK_DIR.as_posix(),
                )
            )
        else:
            if before != after:
                diagnostics.append(
                    _diagnostic(
                        "golden_canonical_mutation",
                        "Architecture fitness changed canonical Golden Book bytes.",
                        _GOLDEN_BOOK_DIR.as_posix(),
                    )
                )

    return _result(diagnostics)
