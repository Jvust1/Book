# CourseRuntime Phase 1B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed `CourseRuntime` aggregation layer that mounts one or more existing `BookRuntime` instances and exposes deterministic `Course -> Book -> Chapter -> Section` navigation, using Functional Analysis v0.36 as the first real course fixture.

**Architecture:** `CourseRuntime` reads a repository-local `course.json`, validates the manifest, resolves enabled book directories within the repository root, and delegates all book-internal loading/readiness/navigation behavior to `BookRuntime`. Main-book chapter/section traversal is exposed at course level; non-main books remain separate handles so Phase 1B does not invent cross-book chapter/section namespaces before `CourseKnowledgeTree` exists.

**Tech Stack:** Python 3.11/3.12/3.13 standard library, `unittest`, JSON manifests, existing `runtime.book_runtime.BookRuntime`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-course-runtime-phase-1b-design.md`

## Global Constraints

- Do not duplicate `BookRuntime` parsing, readiness, PageMap, object normalization, search loading, or stable-ID validation.
- `CourseRuntime` is fail-closed: every enabled book must open successfully; no enabled book may silently degrade or disappear.
- Exactly one enabled book must have role `main`, and `main_book_id` must match it.
- Allowed initial roles are exactly `main`, `supplementary`, `english`, and `reference`.
- Manifest-controlled book paths must resolve under the repository root; external paths and path traversal are rejected.
- Phase 1B main-book navigation only: course-level chapters and sections delegate to the main `BookRuntime`.
- Do not add a database, UI layer, CourseKnowledgeTree, cross-book semantic alignment, progress persistence, or unified cross-book search.
- Keep implementation dependency-free; use Python standard library only.
- Extend the existing runtime workflow rather than creating a second workflow.
- Do not add any auto-generated commit behavior on `main`.
- Real fixture acceptance targets: book ID `stein_shakarchi_functional_analysis_2011`, 8 chapters, 132 sections, 442 PageMap rows, 1493 final search records, runtime status `READY`.

---

## File Structure

### Create

- `runtime/course_runtime.py` — manifest validation, path resolution, BookRuntime aggregation, course-level navigation, course-specific errors.
- `courses/functional-analysis/course.json` — first real course manifest.
- `tests/test_course_runtime.py` — isolated manifest/error tests plus real Functional Analysis fixture tests.

### Modify

- `runtime/__init__.py` — export `CourseRuntime` and course-specific exceptions.
- `.github/workflows/runtime-reference-tests.yml` — compile/test CourseRuntime and trigger on course manifest changes.
- `runtime/README.md` — replace obsolete BLOCKED text and document course-level usage.
- `README.md` — mark runtime recovery complete and Phase 1B as current software milestone.

### GitHub metadata after code is green

- Issue #2 — add final recovery evidence and close it; its original recovery blockers have been resolved by merged PR #3.

---

### Task 1: Manifest Contract and Fail-Closed Course Opening

**Files:**
- Create: `runtime/course_runtime.py`
- Create: `tests/test_course_runtime.py`

**Interfaces:**
- Consumes: `runtime.book_runtime.BookRuntime.open(root: str | Path) -> BookRuntime`
- Consumes: `BookRuntime.book_id: str`
- Produces: `CourseRuntime.open(course_dir: str | Path) -> CourseRuntime`
- Produces: `CourseRuntimeError`, `CourseManifestError`, `CourseBookResolutionError`, `CourseRuntimeBlockedError`
- Produces internal immutable `CourseBookEntry(book_id: str, role: str, path: Path, required: bool, enabled: bool)`

- [ ] **Step 1: Write failing tests for manifest validation**

Create `tests/test_course_runtime.py` with a `CourseRuntimeTests(unittest.TestCase)` class and helpers that create temporary course/book fixtures. Reuse the same minimum ready-book shape as `tests/test_book_runtime.py`, but keep the helper local to this file so the course tests can independently create malformed and blocked books.

The first tests must cover these cases:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.course_runtime import (
    CourseBookResolutionError,
    CourseManifestError,
    CourseRuntime,
    CourseRuntimeBlockedError,
)


class CourseRuntimeTests(unittest.TestCase):
    def test_valid_one_book_course_opens(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            book = repo / "books" / "fixture"
            course_dir = repo / "courses" / "fixture-course"
            self._write_ready_book(book, book_id="fixture_book_2026")
            self._write_course_manifest(
                course_dir,
                book_entries=[
                    {
                        "book_id": "fixture_book_2026",
                        "role": "main",
                        "path": "../../books/fixture",
                        "required": True,
                        "enabled": True,
                    }
                ],
                main_book_id="fixture_book_2026",
            )

            course = CourseRuntime.open(course_dir)

            self.assertEqual(course.course_id, "fixture_course")
            self.assertEqual(course.main_book_id, "fixture_book_2026")
            self.assertEqual(course.book_ids(), ["fixture_book_2026"])

    def test_missing_course_id_fails(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override({"course_id": ""})

    def test_empty_books_fails(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override({"books": []})

    def test_duplicate_enabled_book_id_fails(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override(
                {
                    "books": [
                        self._entry("fixture_book_2026", "main", "../../books/a"),
                        self._entry("fixture_book_2026", "supplementary", "../../books/b"),
                    ]
                }
            )

    def test_no_enabled_main_book_fails(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override(
                {"books": [self._entry("fixture_book_2026", "reference", "../../books/a")]}
            )

    def test_multiple_enabled_main_books_fail(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override(
                {
                    "books": [
                        self._entry("fixture_book_2026", "main", "../../books/a"),
                        self._entry("fixture_book_2027", "main", "../../books/b"),
                    ]
                }
            )

    def test_unsupported_role_fails(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override(
                {"books": [self._entry("fixture_book_2026", "primary", "../../books/a")]}
            )

    def test_main_book_id_must_match_enabled_main_entry(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override({"main_book_id": "other_book"})
```

The helper `_entry()` must return a complete entry with explicit `required=True` and `enabled=True`; `_open_manifest_override()` must create enough ready book directories for any supplied enabled entries so failures come from manifest validation rather than missing fixtures.

- [ ] **Step 2: Run the new tests and verify the expected import failure**

Run:

```bash
python -m unittest tests.test_course_runtime -v
```

Expected: FAIL during import because `runtime.course_runtime` does not exist.

- [ ] **Step 3: Implement the minimum manifest parser and error hierarchy**

Create `runtime/course_runtime.py` with this public foundation:

```python
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
    def __init__(self, course_dir: Path, manifest: dict[str, Any]):
        self.course_dir = course_dir
        self.manifest = dict(manifest)
        self.course_id = str(manifest["course_id"])
        self.name = str(manifest.get("name") or self.course_id)
        self.main_book_id = str(manifest["main_book_id"])
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
```

Implement `_validate_manifest()` before any book I/O. It must:

- require non-empty string `course_id`
- require non-empty string `main_book_id`
- require non-empty list `books`
- require each list element to be a JSON object
- require non-empty string `book_id`, supported `role`, non-empty string `path`, boolean `required`, boolean `enabled`
- reject duplicate `book_id` values among enabled entries
- require exactly one enabled `main` entry
- require the enabled main entry `book_id == main_book_id`

The parser should preserve manifest order in `self.entries`.

- [ ] **Step 4: Run manifest tests and verify only book-resolution tests remain unimplemented**

Run:

```bash
python -m unittest tests.test_course_runtime.CourseRuntimeTests.test_valid_one_book_course_opens \
  tests.test_course_runtime.CourseRuntimeTests.test_missing_course_id_fails \
  tests.test_course_runtime.CourseRuntimeTests.test_empty_books_fails \
  tests.test_course_runtime.CourseRuntimeTests.test_duplicate_enabled_book_id_fails \
  tests.test_course_runtime.CourseRuntimeTests.test_no_enabled_main_book_fails \
  tests.test_course_runtime.CourseRuntimeTests.test_multiple_enabled_main_books_fail \
  tests.test_course_runtime.CourseRuntimeTests.test_unsupported_role_fails \
  tests.test_course_runtime.CourseRuntimeTests.test_main_book_id_must_match_enabled_main_entry -v
```

Expected: validation-specific tests PASS; the valid course test may still fail until Step 6 adds book resolution/loading.

- [ ] **Step 5: Add failing tests for path security, readiness, and canonical identity**

Add:

```python
def test_missing_book_path_fails(self) -> None:
    with self.assertRaises(CourseBookResolutionError):
        self._open_course_with_entry(path="../../books/missing")


def test_book_path_cannot_escape_repository_root(self) -> None:
    with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
        repo = Path(temp)
        course_dir = repo / "courses" / "fixture-course"
        outside_book = Path(outside) / "book"
        self._write_ready_book(outside_book, book_id="fixture_book_2026")
        self._write_course_manifest(
            course_dir,
            book_entries=[self._entry("fixture_book_2026", "main", str(outside_book))],
            main_book_id="fixture_book_2026",
        )
        with self.assertRaises(CourseBookResolutionError):
            CourseRuntime.open(course_dir)


def test_manifest_book_id_must_match_canonical_runtime_id(self) -> None:
    with self.assertRaises(CourseManifestError):
        self._open_course_with_ready_book(
            manifest_book_id="wrong_id",
            canonical_book_id="fixture_book_2026",
        )


def test_blocked_enabled_book_fails_closed(self) -> None:
    with self.assertRaises(CourseRuntimeBlockedError):
        self._open_course_with_blocked_book()
```

A blocked fixture should contain `RUNTIME_READINESS.json` with `{"status": "BLOCKED", ...}` and enough identity metadata that the failure is specifically the existing `BookRuntimeBlockedError` wrapped by `CourseRuntimeBlockedError`.

- [ ] **Step 6: Implement repository-root resolution and BookRuntime delegation**

Define repository root as the nearest ancestor of `course_dir` that contains both `runtime/` and `books/`. If no such ancestor exists, raise `CourseBookResolutionError`.

Implement helpers with these signatures:

```python
def _find_repository_root(self) -> Path: ...
def _resolve_book_path(self, raw_path: str, repository_root: Path) -> Path: ...
def _open_books(self) -> None: ...
```

Path validation must use canonical paths:

```python
candidate = (self.course_dir / raw_path).resolve()
try:
    candidate.relative_to(repository_root)
except ValueError as exc:
    raise CourseBookResolutionError(...) from exc
if not candidate.is_dir():
    raise CourseBookResolutionError(...)
```

Absolute manifest paths must also pass `relative_to(repository_root)`; therefore an absolute path inside the repo is technically safe, while any external absolute path is rejected.

For each enabled entry:

```python
try:
    book = BookRuntime.open(resolved_path)
except (BookRuntimeBlockedError, BookRuntimeError) as exc:
    raise CourseRuntimeBlockedError(entry.book_id, resolved_path, exc) from exc
if book.book_id != entry.book_id:
    raise CourseManifestError(
        f"Manifest book_id {entry.book_id!r} does not match canonical BookRuntime ID {book.book_id!r}"
    )
self.books[entry.book_id] = book
```

Do not pass `allow_blocked=True` from CourseRuntime.

- [ ] **Step 7: Run the entire Task 1 test module**

Run:

```bash
python -m unittest tests.test_course_runtime -v
```

Expected: all Task 1 tests PASS.

- [ ] **Step 8: Run existing BookRuntime regression tests**

Run:

```bash
python -m unittest tests.test_book_runtime -v
```

Expected: PASS with no behavior changes to `BookRuntime`.

- [ ] **Step 9: Commit Task 1**

```bash
git add runtime/course_runtime.py tests/test_course_runtime.py
git commit -m "feat: add fail-closed CourseRuntime loader"
```

---

### Task 2: Course-Level Book and Main-Book Navigation API

**Files:**
- Modify: `runtime/course_runtime.py`
- Modify: `tests/test_course_runtime.py`

**Interfaces:**
- Consumes: `self.books: dict[str, BookRuntime]`, `self.entries: tuple[CourseBookEntry, ...]`
- Produces: `book_ids() -> list[str]`
- Produces: `book(book_id: str) -> BookRuntime`
- Produces: `books_by_role(role: str) -> list[BookRuntime]`
- Produces: `main_book() -> BookRuntime`
- Produces: `chapter_ids() -> list[str]`
- Produces: `chapters() -> list[dict[str, Any]]`
- Produces: `sections_for_chapter(chapter_id: str) -> list[RuntimeSection]`
- Produces: `section(section_id: str) -> RuntimeSection`
- Produces: `summary() -> dict[str, Any]`

- [ ] **Step 1: Add failing tests for deterministic book access and role filtering**

Add a two-book ready course fixture where manifest order is main then supplementary and assert:

```python
def test_book_ids_preserve_enabled_manifest_order(self) -> None:
    course = self._open_two_book_course()
    self.assertEqual(course.book_ids(), ["fixture_main", "fixture_supplementary"])


def test_main_book_returns_configured_main_runtime(self) -> None:
    course = self._open_two_book_course()
    self.assertEqual(course.main_book().book_id, "fixture_main")


def test_books_by_role_filters_enabled_books(self) -> None:
    course = self._open_two_book_course()
    self.assertEqual(
        [book.book_id for book in course.books_by_role("supplementary")],
        ["fixture_supplementary"],
    )


def test_unknown_book_raises_course_runtime_error(self) -> None:
    course = self._open_two_book_course()
    with self.assertRaises(CourseRuntimeError):
        course.book("missing")
```

Disabled entries should remain visible only in immutable manifest metadata/entries, not in `book_ids()` or `books_by_role()` because no BookRuntime is mounted for them.

- [ ] **Step 2: Run access tests and verify they fail**

Run the four new tests explicitly with `python -m unittest ... -v`.

Expected: FAIL because the public methods do not exist.

- [ ] **Step 3: Implement book access methods**

Add:

```python
def book_ids(self) -> list[str]:
    return [entry.book_id for entry in self.entries if entry.enabled]


def book(self, book_id: str) -> BookRuntime:
    try:
        return self.books[book_id]
    except KeyError as exc:
        raise CourseRuntimeError(f"Unknown or disabled course book: {book_id}") from exc


def books_by_role(self, role: str) -> list[BookRuntime]:
    if role not in ALLOWED_BOOK_ROLES:
        raise CourseManifestError(f"Unsupported book role: {role}")
    return [self.books[entry.book_id] for entry in self.entries if entry.enabled and entry.role == role]


def main_book(self) -> BookRuntime:
    return self.book(self.main_book_id)
```

- [ ] **Step 4: Add failing tests for main-book chapter/section delegation**

Use a main fixture whose TOC/structure contains `chapter_01` and `ch01_s01`:

```python
def test_chapter_ids_delegate_to_main_book(self) -> None:
    course = self._open_two_book_course()
    self.assertEqual(course.chapter_ids(), ["chapter_01"])


def test_sections_for_chapter_delegate_to_main_book(self) -> None:
    course = self._open_two_book_course()
    self.assertEqual(
        [section.id for section in course.sections_for_chapter("chapter_01")],
        ["ch01_s01"],
    )


def test_section_resolves_only_against_main_book(self) -> None:
    course = self._open_two_book_course()
    self.assertEqual(course.section("ch01_s01").id, "ch01_s01")
```

For `chapters()`, derive rows from the loaded main book TOC rather than introducing a new chapter dataclass. The method should return the TOC chapter dictionaries in source order when `toc` has a top-level `chapters` list; otherwise fall back to minimal dictionaries built from `chapter_ids()`.

- [ ] **Step 5: Implement navigation delegates and summary**

Add:

```python
def chapter_ids(self) -> list[str]:
    return self.main_book().chapter_ids()


def chapters(self) -> list[dict[str, Any]]:
    toc = self.main_book().toc
    if isinstance(toc, dict) and isinstance(toc.get("chapters"), list):
        return [dict(row) for row in toc["chapters"] if isinstance(row, dict)]
    return [{"id": chapter_id} for chapter_id in self.chapter_ids()]


def sections_for_chapter(self, chapter_id: str):
    return self.main_book().sections_for_chapter(chapter_id)


def section(self, section_id: str):
    return self.main_book().section(section_id)


def summary(self) -> dict[str, Any]:
    main = self.main_book()
    return {
        "course_id": self.course_id,
        "name": self.name,
        "main_book_id": self.main_book_id,
        "book_count": len(self.books),
        "books": [
            {
                "book_id": entry.book_id,
                "role": entry.role,
                "runtime_status": self.books[entry.book_id].readiness.get("status"),
            }
            for entry in self.entries
            if entry.enabled
        ],
        "main_chapter_count": len(main.chapter_ids()),
        "main_section_count": len(main.sections),
    }
```

Use `RuntimeSection` return annotations imported from `.book_runtime` if type annotations are added; do not re-declare the type.

- [ ] **Step 6: Run Task 2 tests**

Run:

```bash
python -m unittest tests.test_course_runtime -v
```

Expected: PASS.

- [ ] **Step 7: Run BookRuntime regressions again**

Run:

```bash
python -m unittest tests.test_book_runtime -v
```

Expected: PASS.

- [ ] **Step 8: Commit Task 2**

```bash
git add runtime/course_runtime.py tests/test_course_runtime.py
git commit -m "feat: expose CourseRuntime navigation"
```

---

### Task 3: Real Functional Analysis Course Fixture and Public Runtime Exports

**Files:**
- Create: `courses/functional-analysis/course.json`
- Modify: `runtime/__init__.py`
- Modify: `tests/test_course_runtime.py`

**Interfaces:**
- Produces repository fixture: `CourseRuntime.open("courses/functional-analysis")`
- Produces package imports: `from runtime import CourseRuntime, CourseRuntimeError, CourseManifestError, CourseBookResolutionError, CourseRuntimeBlockedError`

- [ ] **Step 1: Add failing real-fixture test**

Add:

```python
def test_real_functional_analysis_course_fixture(self) -> None:
    repo = Path(__file__).resolve().parents[1]
    course_dir = repo / "courses" / "functional-analysis"
    if not (repo / "books" / "functional-analysis").exists():
        self.skipTest("repository Functional Analysis fixture not present")

    course = CourseRuntime.open(course_dir)
    book = course.main_book()

    self.assertEqual(course.course_id, "functional_analysis_course")
    self.assertEqual(course.main_book_id, "stein_shakarchi_functional_analysis_2011")
    self.assertEqual(book.book_id, "stein_shakarchi_functional_analysis_2011")
    self.assertTrue(book.is_ready)
    self.assertEqual(len(course.chapter_ids()), 8)
    self.assertEqual(sum(len(course.sections_for_chapter(cid)) for cid in course.chapter_ids()), 132)
    self.assertEqual(len(book.page_map), 442)
    self.assertEqual(sum(1 for _ in book.iter_search_records()), 1493)
    self.assertEqual(course.section("ch01_s01").id, "ch01_s01")
```

Also add a package-export smoke test:

```python
def test_runtime_package_exports_course_runtime(self) -> None:
    from runtime import CourseRuntime as ExportedCourseRuntime
    self.assertIs(ExportedCourseRuntime, CourseRuntime)
```

- [ ] **Step 2: Run real-fixture tests and verify they fail**

Run:

```bash
python -m unittest \
  tests.test_course_runtime.CourseRuntimeTests.test_real_functional_analysis_course_fixture \
  tests.test_course_runtime.CourseRuntimeTests.test_runtime_package_exports_course_runtime -v
```

Expected: FAIL because the manifest/export does not exist yet.

- [ ] **Step 3: Add the real course manifest**

Create `courses/functional-analysis/course.json` exactly as:

```json
{
  "schema_version": "course_manifest_v1",
  "course_id": "functional_analysis_course",
  "name": "Functional Analysis",
  "language": "bilingual",
  "status": "active",
  "main_book_id": "stein_shakarchi_functional_analysis_2011",
  "books": [
    {
      "book_id": "stein_shakarchi_functional_analysis_2011",
      "role": "main",
      "path": "../../books/functional-analysis",
      "required": true,
      "enabled": true
    }
  ]
}
```

- [ ] **Step 4: Export CourseRuntime from `runtime/__init__.py`**

Add imports:

```python
from .course_runtime import (
    CourseBookResolutionError,
    CourseManifestError,
    CourseRuntime,
    CourseRuntimeBlockedError,
    CourseRuntimeError,
)
```

Add all five names to `__all__` while preserving current BookRuntime exports.

- [ ] **Step 5: Run real fixture and package export tests**

Run the Step 2 command again.

Expected: PASS with 8 chapters / 132 sections / 442 PageMap rows / 1493 search records.

- [ ] **Step 6: Run all runtime tests currently in the workflow**

Run:

```bash
python -m unittest \
  tests.test_book_runtime \
  tests.test_course_runtime \
  tests.test_functional_analysis_page_map \
  tests.test_continuation_integrity \
  tests.test_runtime_object_merge \
  tests.test_functional_analysis_identity_normalizer \
  tests.test_functional_analysis_figure_normalizer -v
```

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

```bash
git add courses/functional-analysis/course.json runtime/__init__.py tests/test_course_runtime.py
git commit -m "feat: mount Functional Analysis in CourseRuntime"
```

---

### Task 4: CI Coverage and Runtime Documentation

**Files:**
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Modify: `runtime/README.md`
- Modify: `README.md`

**Interfaces:**
- CI must compile `runtime/course_runtime.py`.
- CI must run `tests.test_course_runtime` on Python 3.11, 3.12, and 3.13.
- CI path filters must include `courses/**` and the Phase 1B plan/spec paths if desired for runtime-documentation validation, but the essential executable trigger is `courses/**`.

- [ ] **Step 1: Update CI path triggers and compile step**

In both `push.paths` and `pull_request.paths`, add:

```yaml
      - "courses/**"
```

In `Compile reference runtime`, add:

```yaml
          python -m py_compile runtime/course_runtime.py
```

Do not alter the existing finalized Functional Analysis recovery checks.

- [ ] **Step 2: Add CourseRuntime tests to the existing matrix command**

Change the unit-test command so `tests.test_course_runtime` runs beside `tests.test_book_runtime`:

```yaml
      - name: Run unit tests
        run: python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_functional_analysis_page_map tests.test_continuation_integrity tests.test_runtime_object_merge tests.test_functional_analysis_identity_normalizer tests.test_functional_analysis_figure_normalizer -v
```

Do not create a new workflow.

- [ ] **Step 3: Update `runtime/README.md` to match current reality**

Replace the obsolete sentence saying Functional Analysis is expected to be `BLOCKED` with a current statement that the finalized v0.36 fixture is `READY` on `main` after runtime recovery.

Add this usage example after the existing BookRuntime section:

```python
from runtime import CourseRuntime

course = CourseRuntime.open("courses/functional-analysis")
print(course.summary())

book = course.main_book()
for chapter_id in course.chapter_ids():
    for section in course.sections_for_chapter(chapter_id):
        print(book.book_id, chapter_id, section.id, section.title_zh)
```

Document these Phase 1B semantics explicitly:

- one course can mount multiple enabled books
- exactly one enabled main book
- all enabled books must be runtime-ready
- course-level Chapter/Section traversal currently delegates to the main book
- non-main book trees are accessed through `course.book(book_id)`

- [ ] **Step 4: Update repository `README.md` milestone text**

In `当前状态`, mark runtime import/readiness recovery as complete and make `Course -> Book -> Chapter -> Section` the active Phase 1B milestone. Do not claim Preview/Learn/Review/Practice or progress persistence is implemented.

The status should distinguish:

```text
Runtime import/readiness: complete
CourseRuntime Phase 1B: in implementation / complete only after tests and CI are green
Section learning shell: next milestone
```

- [ ] **Step 5: Run workflow-equivalent tests locally**

Run:

```bash
python -m py_compile runtime/book_runtime.py runtime/course_runtime.py
python -m unittest \
  tests.test_book_runtime \
  tests.test_course_runtime \
  tests.test_functional_analysis_page_map \
  tests.test_continuation_integrity \
  tests.test_runtime_object_merge \
  tests.test_functional_analysis_identity_normalizer \
  tests.test_functional_analysis_figure_normalizer -v
```

Expected: PASS.

- [ ] **Step 6: Verify the recovery tools still reproduce READY on the real book**

Run the same 3.13 validation sequence used by CI:

```bash
python tools/rebuild_runtime_artifacts.py books/functional-analysis --toc
python tools/recover_functional_analysis_search.py books/functional-analysis --promote-safe
python tools/recover_functional_analysis_page_map.py books/functional-analysis --promote-safe
python tools/check_runtime_readiness.py books/functional-analysis --write
python -c "from runtime import BookRuntime, CourseRuntime; b=BookRuntime.open('books/functional-analysis'); c=CourseRuntime.open('courses/functional-analysis'); assert b.is_ready; assert len(c.chapter_ids()) == 8; assert sum(len(c.sections_for_chapter(x)) for x in c.chapter_ids()) == 132; print(c.summary())"
```

Expected: all commands exit 0; runtime remains `READY`; course opens successfully.

- [ ] **Step 7: Commit Task 4**

```bash
git add .github/workflows/runtime-reference-tests.yml runtime/README.md README.md
git commit -m "ci: verify CourseRuntime across supported Python versions"
```

---

### Task 5: Final Verification, Issue #2 Closure, and Integration Readiness

**Files:**
- No new runtime files expected.
- GitHub Issue #2 metadata/comment update after verification.

**Interfaces:**
- Final branch must remain based on `main` and be integration-ready through a PR.
- Do not merge without explicit user approval.

- [ ] **Step 1: Run the complete relevant test suite from a clean branch checkout**

Run:

```bash
python -m unittest \
  tests.test_book_runtime \
  tests.test_course_runtime \
  tests.test_functional_analysis_page_map \
  tests.test_continuation_integrity \
  tests.test_runtime_object_merge \
  tests.test_functional_analysis_identity_normalizer \
  tests.test_functional_analysis_figure_normalizer \
  tests.test_search_identity_replay \
  tests.test_search_recovery_diagnostics -v
```

Expected: PASS.

- [ ] **Step 2: Run direct real-fixture acceptance assertions**

Run:

```bash
python - <<'PY'
from runtime import CourseRuntime

course = CourseRuntime.open("courses/functional-analysis")
book = course.main_book()

assert course.course_id == "functional_analysis_course"
assert course.main_book_id == "stein_shakarchi_functional_analysis_2011"
assert book.book_id == "stein_shakarchi_functional_analysis_2011"
assert book.is_ready
assert len(course.chapter_ids()) == 8
assert sum(len(course.sections_for_chapter(cid)) for cid in course.chapter_ids()) == 132
assert len(book.page_map) == 442
assert sum(1 for _ in book.iter_search_records()) == 1493
assert course.section("ch01_s01").id == "ch01_s01"
print(course.summary())
PY
```

Expected: exit 0 and summary shows one mounted main book.

- [ ] **Step 3: Inspect git diff for scope creep**

Run:

```bash
git diff --stat main...HEAD
git diff --name-only main...HEAD
```

Expected implementation-scope files only:

```text
.github/workflows/runtime-reference-tests.yml
README.md
courses/functional-analysis/course.json
docs/superpowers/plans/2026-08-27-course-runtime-phase-1b.md
docs/superpowers/specs/2026-08-27-course-runtime-phase-1b-design.md
runtime/README.md
runtime/__init__.py
runtime/course_runtime.py
tests/test_course_runtime.py
```

If unrelated files appear, investigate before proceeding; do not silently include them.

- [ ] **Step 4: Push the feature branch and verify GitHub Actions**

Push:

```bash
git push -u origin feature/course-runtime-phase-1b
```

Wait for `Runtime reference tests` to complete on Python 3.11, 3.12, and 3.13. All matrix jobs must be green before the branch is presented as integration-ready.

- [ ] **Step 5: Close the obsolete recovery issue only after branch verification confirms main recovery remains intact**

Add a final comment to Issue #2 containing these facts from merged PR #3 / current `main`:

```text
Phase 1A runtime recovery is complete.
- PR #3 merged to main at cc38421e3314adfd81045e85dc6b269803b556bd
- RUNTIME_READINESS = READY
- 442 PageMap rows
- 8 chapters / 132 sections
- 1493 unique final search records with source anchors
- BookRuntime.open() succeeds
- post-merge Runtime reference tests run #48 succeeded

CourseRuntime Phase 1B is tracked separately on feature/course-runtime-phase-1b.
```

Then close Issue #2. Do not edit its historical body to erase the earlier recovery state; preserve history and close with final evidence.

- [ ] **Step 6: Create a Phase 1B pull request against `main`**

PR title:

```text
Add CourseRuntime and Functional Analysis course fixture
```

PR body must summarize:

- thin CourseRuntime aggregation over BookRuntime
- fail-closed enabled-book readiness
- repository-root path confinement
- multi-book role-ready manifest
- main-book Chapter/Section delegation
- real Functional Analysis fixture with 8 chapters / 132 sections
- Python 3.11/3.12/3.13 CI result
- no database/UI/CourseKnowledgeTree added in this phase

Do not merge the PR. Present its URL and merge-gate state to the user for explicit integration approval.

---

## Plan Self-Review

### Spec coverage

- Course manifest and role model: Task 1 + Task 3.
- Fail-closed readiness: Task 1.
- Repository-root path confinement: Task 1.
- BookRuntime delegation/no duplicate parsing: Tasks 1–2.
- Main-book Course -> Chapter -> Section navigation: Task 2.
- Multiple-book-ready architecture without merged namespaces: Task 2.
- Functional Analysis real fixture: Task 3.
- Public package API: Task 3.
- Python 3.11/3.12/3.13 CI: Task 4.
- Runtime/repository docs: Task 4.
- Issue #2 historical closure: Task 5.
- Explicit non-goals are not implemented by any task.

### Placeholder scan

The plan contains no TBD/TODO/"implement later" placeholders. Each code task names concrete files, interfaces, tests, commands, and expected outcomes.

### Type and naming consistency

The plan consistently uses `CourseRuntime`, `CourseRuntimeError`, `CourseManifestError`, `CourseBookResolutionError`, `CourseRuntimeBlockedError`, `CourseBookEntry`, `book_ids()`, `book()`, `books_by_role()`, `main_book()`, `chapter_ids()`, `chapters()`, `sections_for_chapter()`, `section()`, and `summary()` throughout all tasks.
