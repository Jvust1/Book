from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .artifacts import sha256_file
from .compiler import PackageCompileError, compile_course_package
from .contracts import PackageDiagnostic, PackageValidationResult
from .validator import validate_compiled_package


GOLDEN_COURSE_DIR = Path("courses/functional-analysis")
_GOLDEN_BOOK_DIR = Path("books/functional-analysis")
_GOLDEN_BASELINE = Path("tests/golden/functional_analysis_course_package_baseline.json")
_BASELINE_KEYS = frozenset(
    {
        "course_id",
        "book_id",
        "chapter_count",
        "section_count",
        "search_record_count",
        "pdf_page_count",
        "printed_final_page",
        "structured_status",
        "runtime_status",
    }
)


def _diagnostic(code: str, detail: str, relative_path: str | None = None) -> PackageDiagnostic:
    return PackageDiagnostic(code, "FAIL", detail, relative_path)


def _result(diagnostics: list[PackageDiagnostic]) -> PackageValidationResult:
    ordered = tuple(
        sorted(
            diagnostics,
            key=lambda item: (item.code, item.relative_path or "", item.detail),
        )
    )
    return PackageValidationResult("FAIL" if ordered else "PASS", ordered)


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def load_golden_baseline(repository_root: Path) -> dict[str, Any]:
    path = Path(repository_root).resolve() / _GOLDEN_BASELINE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Golden Course baseline cannot be read") from exc

    if not isinstance(value, dict) or set(value) != _BASELINE_KEYS:
        raise ValueError("Golden Course baseline violates the frozen contract")

    if not all(
        isinstance(value[field], str) and bool(value[field].strip())
        for field in ("course_id", "book_id", "structured_status", "runtime_status")
    ):
        raise ValueError("Golden Course baseline contains invalid identity/status fields")

    if not all(
        _nonnegative_int(value[field])
        for field in (
            "chapter_count",
            "section_count",
            "search_record_count",
            "pdf_page_count",
            "printed_final_page",
        )
    ):
        raise ValueError("Golden Course baseline contains invalid count/page fields")

    return value


def _snapshot_tree(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise ValueError("Golden canonical Book directory is unavailable")
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    }


def _actual_baseline(package_documents: dict[str, Any]) -> dict[str, Any] | None:
    course = package_documents.get("course_package.json")
    books_document = package_documents.get("books.json")
    if not isinstance(course, dict) or not isinstance(books_document, dict):
        return None

    books = books_document.get("books")
    if not isinstance(books, list):
        return None
    enabled_primary = [
        book
        for book in books
        if isinstance(book, dict)
        and book.get("enabled") is True
        and book.get("role") == "primary"
    ]
    if len(enabled_primary) != 1:
        return None
    primary = enabled_primary[0]

    return {
        "course_id": course.get("course_id"),
        "book_id": primary.get("book_id"),
        "chapter_count": course.get("chapter_count"),
        "section_count": course.get("section_count"),
        "search_record_count": course.get("search_record_count"),
        "pdf_page_count": primary.get("pdf_page_count"),
        "printed_final_page": primary.get("printed_final_page"),
        "structured_status": primary.get("structured_status"),
        "runtime_status": primary.get("runtime_status"),
    }


def verify_golden_course(repository_root: Path) -> PackageValidationResult:
    root = Path(repository_root).resolve()
    book_root = root / _GOLDEN_BOOK_DIR

    try:
        baseline = load_golden_baseline(root)
        before = _snapshot_tree(book_root)
        first = compile_course_package(root, root / GOLDEN_COURSE_DIR)
        second = compile_course_package(root, root / GOLDEN_COURSE_DIR)
    except (ValueError, OSError, PackageCompileError):
        return _result(
            [
                _diagnostic(
                    "golden_baseline_error",
                    "Golden Course inputs cannot be verified safely.",
                )
            ]
        )

    diagnostics: list[PackageDiagnostic] = []

    validation = validate_compiled_package(first, root)
    if validation.status != "PASS":
        diagnostics.extend(validation.diagnostics)

    if first.package_identity != second.package_identity or first.file_bytes() != second.file_bytes():
        diagnostics.append(
            _diagnostic(
                "golden_package_nondeterministic",
                "Golden Course compilation is not deterministic.",
            )
        )

    actual = _actual_baseline(first.documents)
    if actual != baseline:
        diagnostics.append(
            _diagnostic(
                "golden_baseline_mismatch",
                "Compiled Golden Course facts differ from the frozen baseline.",
                _GOLDEN_BASELINE.as_posix(),
            )
        )

    try:
        after = _snapshot_tree(book_root)
    except (ValueError, OSError):
        diagnostics.append(
            _diagnostic(
                "golden_canonical_mutation",
                "Canonical Golden Book state cannot be verified after the gate.",
                _GOLDEN_BOOK_DIR.as_posix(),
            )
        )
    else:
        if before != after:
            diagnostics.append(
                _diagnostic(
                    "golden_canonical_mutation",
                    "Golden Course verification changed canonical Book bytes.",
                    _GOLDEN_BOOK_DIR.as_posix(),
                )
            )

    return _result(diagnostics)
