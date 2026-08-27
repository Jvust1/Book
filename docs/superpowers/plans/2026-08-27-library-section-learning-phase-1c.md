# Phase 1C Library + Section Learning Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Book App runtime path `Library → independent single-book Course → SectionLearningSource → Preview/Learn/Review/Practice` using the existing Functional Analysis course as the first real fixture.

**Architecture:** Add a thin `LibraryRuntime` above `CourseRuntime` to enforce the current product profile of one App containing many independent one-book courses. Add a separate `SectionLearningRuntime` below the selected course that projects source-backed Section data already exposed by `CourseRuntime`/`BookRuntime`; the four learning modes are deterministic references to that source and do not invent textbook content.

**Tech Stack:** Python 3.11/3.12/3.13 standard library only, `unittest`, JSON manifests, existing `BookRuntime`/`CourseRuntime`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-library-section-learning-phase-1c-design.md`

## Global Constraints

- Product model: one Book App → many independent textbook courses; one admitted product course → exactly one enabled textbook.
- Keep generic Phase 1B multi-book `CourseRuntime` capability unchanged; enforce single-book product policy only in `LibraryRuntime`.
- Preserve existing `STRUCTURED_COMPLETE` and `RUNTIME_READY` fail-closed behavior.
- `BookRuntime` remains the only parser/normalizer for structured textbook assets; Phase 1C must not re-read raw `*_structure.json` to duplicate BookRuntime logic.
- `SectionLearningRuntime` may use only source data already exposed through `CourseRuntime` and `BookRuntime`.
- No AI-authored explanations, summaries, objectives, questions, answers, textbook facts, or anchors in Phase 1C.
- No UI, database, progress persistence, notes, mistakes, lectures, exams, mastery, cross-course search, cross-course QA, or CourseKnowledgeTree implementation.
- No Functional Analysis structured textbook source files may change.
- Runtime code remains standard-library-only.
- Existing `tests.test_book_runtime` and `tests.test_course_runtime` must remain green.
- New tests must run on Python 3.11, 3.12, and 3.13.
- Real Functional Analysis acceptance must retain 8 Chapters, 132 Sections, 442 PageMap rows, and 1493 final search records.
- No CI step may commit generated files back to `main`.

## File Map

- Create `library/library.json` — declarative App-level catalog of independent courses.
- Create `runtime/library_runtime.py` — library manifest validation, trusted path resolution, enabled course mounting, single-book product-profile enforcement, deterministic catalog API.
- Create `runtime/section_learning_runtime.py` — Section source projection and deterministic Preview/Learn/Review/Practice payloads.
- Modify `runtime/__init__.py` — export new public runtime types/errors.
- Create `tests/test_library_runtime.py` — manifest/path/readiness/catalog/product-profile tests plus real library fixture checks.
- Create `tests/test_section_learning_runtime.py` — source projection, mode traceability, policy filtering, and real `ch01_s01` tests.
- Modify `.github/workflows/runtime-reference-tests.yml` — watch `library/**`, compile new modules, run new tests, add real Library → Course → SectionLearning acceptance.
- Modify `runtime/README.md` — document LibraryRuntime and SectionLearningRuntime contracts.
- Modify `README.md` — replace outdated product statement “one course supports multiple textbooks” with “one App contains multiple independent one-book courses”, while documenting generic CourseRuntime multi-book capability as lower-level compatibility only.

---

### Task 1: Library Manifest Contract, Trusted Paths, and Fail-Closed Course Opening

**Files:**
- Create: `runtime/library_runtime.py`
- Create: `tests/test_library_runtime.py`

**Interfaces:**
- Consumes: `CourseRuntime.open(course_dir: str | Path) -> CourseRuntime`, `CourseRuntimeError` subclasses.
- Produces:
  - `LibraryRuntime.open(library_dir: str | Path, *, repository_root: str | Path | None = None) -> LibraryRuntime`
  - `LibraryManifestError(LibraryRuntimeError)`
  - `LibraryCourseResolutionError(LibraryRuntimeError)`
  - `LibraryRuntimeBlockedError(LibraryRuntimeError)`
  - `LibraryCourseEntry` dataclass with `course_id`, `name`, `path`, `enabled`, `order`, `position`.

- [ ] **Step 1: Write failing manifest/path/readiness tests**

Create `tests/test_library_runtime.py` with a self-contained minimal ready-course fixture and these RED cases:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.library_runtime import (
    LibraryCourseResolutionError,
    LibraryManifestError,
    LibraryRuntime,
    LibraryRuntimeBlockedError,
)


class LibraryRuntimeTests(unittest.TestCase):
    def test_valid_library_opens(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            library = LibraryRuntime.open(library_dir)
            self.assertEqual(library.library_id, "fixture_library")
            self.assertEqual(library.name, "Fixture Library")

    def test_unsupported_schema_version_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_with_library_override({"schema_version": "library_manifest_v2"})

    def test_missing_library_id_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_with_library_override({"library_id": ""})

    def test_empty_courses_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_with_library_override({"courses": []})

    def test_zero_enabled_courses_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_with_library_override(
                {"courses": [self._course_entry(enabled=False)]}
            )

    def test_duplicate_enabled_course_id_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_with_library_override(
                {
                    "courses": [
                        self._course_entry(path="../courses/fixture-course"),
                        self._course_entry(path="../courses/fixture-course-2"),
                    ]
                }
            )

    def test_bool_order_is_rejected(self) -> None:
        entry = self._course_entry()
        entry["order"] = True
        with self.assertRaises(LibraryManifestError):
            self._open_with_library_override({"courses": [entry]})

    def test_missing_enabled_course_path_fails(self) -> None:
        entry = self._course_entry(path="../courses/missing")
        with self.assertRaises(LibraryCourseResolutionError):
            self._open_with_library_override({"courses": [entry]})

    def test_course_path_cannot_escape_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            repo, library_dir = self._ready_repo(Path(temp))
            manifest = self._library_manifest()
            manifest["courses"][0]["path"] = str(Path(outside))
            self._dump(library_dir / "library.json", manifest)
            with self.assertRaises(LibraryCourseResolutionError):
                LibraryRuntime.open(library_dir)

    def test_nonstandard_layout_without_explicit_root_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, _ = self._ready_repo(root / "repo")
            custom_library = repo / "catalog"
            custom_library.mkdir(parents=True)
            self._dump(custom_library / "library.json", self._library_manifest(path="../courses/fixture-course"))
            with self.assertRaises(LibraryCourseResolutionError):
                LibraryRuntime.open(custom_library)

    def test_explicit_repository_root_supports_nonstandard_library_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, _ = self._ready_repo(Path(temp))
            custom_library = repo / "catalog"
            custom_library.mkdir(parents=True)
            self._dump(custom_library / "library.json", self._library_manifest(path="../courses/fixture-course"))
            library = LibraryRuntime.open(custom_library, repository_root=repo)
            self.assertEqual(library.library_id, "fixture_library")

    def test_canonical_course_id_mismatch_fails(self) -> None:
        entry = self._course_entry(course_id="wrong_course")
        with self.assertRaises(LibraryManifestError):
            self._open_with_library_override({"courses": [entry]})

    def test_blocked_enabled_course_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp), readiness="BLOCKED")
            with self.assertRaises(LibraryRuntimeBlockedError):
                LibraryRuntime.open(library_dir)

    def test_disabled_incomplete_course_is_not_opened(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            manifest = self._library_manifest()
            manifest["courses"].append(
                {
                    "course_id": "future_course",
                    "name": "Future Course",
                    "path": "../courses/not-yet-created",
                    "enabled": False,
                    "order": 20,
                }
            )
            self._dump(library_dir / "library.json", manifest)
            library = LibraryRuntime.open(library_dir)
            self.assertEqual(library.course_ids(), ["fixture_course"])
```

Add exact fixture helpers in the same test file so the test does not depend on private methods from another test class:

```python
    @staticmethod
    def _dump(path: Path, data: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _course_entry(
        *,
        course_id: str = "fixture_course",
        path: str = "../courses/fixture-course",
        enabled: bool = True,
        order: int = 10,
    ) -> dict[str, object]:
        return {
            "course_id": course_id,
            "name": "Fixture Course",
            "path": path,
            "enabled": enabled,
            "order": order,
        }

    def _library_manifest(self, *, path: str = "../courses/fixture-course") -> dict[str, object]:
        return {
            "schema_version": "library_manifest_v1",
            "library_id": "fixture_library",
            "name": "Fixture Library",
            "courses": [self._course_entry(path=path)],
        }

    def _ready_repo(self, root: Path, *, readiness: str = "READY") -> tuple[Path, Path]:
        repo = root.resolve()
        (repo / "runtime").mkdir(parents=True, exist_ok=True)
        (repo / "books").mkdir(parents=True, exist_ok=True)
        (repo / "courses").mkdir(parents=True, exist_ok=True)
        library_dir = repo / "library"
        library_dir.mkdir(parents=True, exist_ok=True)
        book = repo / "books" / "fixture"
        course = repo / "courses" / "fixture-course"
        self._write_book(book, readiness=readiness)
        self._write_course(course)
        self._dump(library_dir / "library.json", self._library_manifest())
        return repo, library_dir

    def _write_course(self, course_dir: Path) -> None:
        self._dump(
            course_dir / "course.json",
            {
                "schema_version": "course_manifest_v1",
                "course_id": "fixture_course",
                "name": "Fixture Course",
                "main_book_id": "fixture_book",
                "books": [
                    {
                        "book_id": "fixture_book",
                        "role": "main",
                        "path": "../../books/fixture",
                        "required": True,
                        "enabled": True,
                    }
                ],
            },
        )

    def _write_book(self, root: Path, *, readiness: str) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self._dump(root / "RUNTIME_READINESS.json", {"status": readiness, "book_id": "fixture_book", "missing_required_files": [], "stale_files": []})
        self._dump(root / "STRUCTURED_COMPLETE.json", {"status": "STRUCTURED_COMPLETE", "book_id": "fixture_book", "pdf_pages": 2, "version": "v1", "search_index": "search_index_v1.jsonl"})
        self._dump(root / "book_metadata.json", {"book_id": "fixture_book", "pdf_total_pages": 2, "toc_file": "toc_bilingual.json", "page_map_file": "page_map.csv"})
        self._dump(root / "qa_retrieval_policy.json", {"book_id": "fixture_book"})
        self._dump(root / "toc_bilingual.json", {"chapters": [{"id": "chapter_01", "sections": [{"id": "ch01_s01"}]}]})
        self._dump(root / "chunk_001a_structure.json", {"chunk_id": "chunk_001a", "pdf_pages": [1, 2], "chapter_id": "chapter_01", "sections": [{"id": "ch01_s01", "number": "1", "title_en": "Section", "title_zh": "小节", "pdf_pages": [1, 2]}], "key_objects": []})
        (root / "chunk_001a_translation_zh.md").write_text("# 测试学习层\n", encoding="utf-8")
        (root / "page_map.csv").write_text("pdf_page,printed_page\n1,1\n2,2\n", encoding="utf-8")
        (root / "search_index_v1.jsonl").write_text(json.dumps({"id": "ch01_s01", "type": "section"}) + "\n", encoding="utf-8")

    def _open_with_library_override(self, override: dict[str, object]) -> LibraryRuntime:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        repo, library_dir = self._ready_repo(Path(temp.name))
        manifest = self._library_manifest()
        manifest.update(override)
        courses = manifest.get("courses")
        if isinstance(courses, list):
            for index, row in enumerate(courses):
                if not isinstance(row, dict) or row.get("enabled") is not True:
                    continue
                path = row.get("path")
                course_id = row.get("course_id")
                if not isinstance(path, str) or not isinstance(course_id, str):
                    continue
                target = (library_dir / path).resolve()
                try:
                    target.relative_to(repo)
                except ValueError:
                    continue
                if not target.exists() and path != "../courses/missing":
                    self._write_course(target)
                    data = json.loads((target / "course.json").read_text(encoding="utf-8"))
                    data["course_id"] = "fixture_course" if course_id == "wrong_course" else course_id
                    self._dump(target / "course.json", data)
        self._dump(library_dir / "library.json", manifest)
        return LibraryRuntime.open(library_dir)
```

- [ ] **Step 2: Run Task 1 tests and confirm RED**

Run:

```bash
python -m unittest tests.test_library_runtime -v
```

Expected: import failure such as `ModuleNotFoundError: No module named 'runtime.library_runtime'`. Existing runtime tests must still be independently runnable:

```bash
python -m unittest tests.test_book_runtime tests.test_course_runtime -v
```

Expected: PASS.

- [ ] **Step 3: Implement the minimal LibraryRuntime loading contract**

Create `runtime/library_runtime.py` with these exact public shapes and validation flow:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .course_runtime import CourseRuntime, CourseRuntimeError


class LibraryRuntimeError(RuntimeError):
    pass


class LibraryManifestError(LibraryRuntimeError):
    pass


class LibraryCourseResolutionError(LibraryRuntimeError):
    pass


class LibraryRuntimeBlockedError(LibraryRuntimeError):
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
        repo = cls._resolve_repository_root(root, repository_root)
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
    def _resolve_repository_root(library_dir: Path, explicit: str | Path | None) -> Path:
        if explicit is not None:
            repo = Path(explicit).resolve()
        else:
            if library_dir.name != "library":
                raise LibraryCourseResolutionError(
                    "Nonstandard library layout requires repository_root"
                )
            repo = library_dir.parent.resolve()
        try:
            library_dir.relative_to(repo)
        except ValueError as exc:
            raise LibraryCourseResolutionError(
                f"Library directory is outside repository root: {library_dir}"
            ) from exc
        return repo
```

Implement `_validate_manifest()` so it requires exact schema `library_manifest_v1`, non-empty `library_id`/`name`, a non-empty list of courses, at least one enabled entry, non-empty strings for `course_id`/`name`/`path`, boolean `enabled`, integer `order` with `isinstance(order, int) and not isinstance(order, bool)`, and no duplicate enabled course IDs.

Implement `_resolve_course_path()` by resolving relative to `library_dir`, requiring `candidate.relative_to(repository_root)` to succeed, and requiring an existing directory for enabled entries.

Implement `_open_courses()` only for enabled entries. Wrap any `CourseRuntimeError` as `LibraryRuntimeBlockedError`. After open, reject canonical `course.course_id != entry.course_id` as `LibraryManifestError`.

- [ ] **Step 4: Run Task 1 tests and confirm GREEN**

Run:

```bash
python -m unittest tests.test_library_runtime -v
```

Expected: all Task 1 tests PASS.

Then run regression tests:

```bash
python -m unittest tests.test_book_runtime tests.test_course_runtime -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add runtime/library_runtime.py tests/test_library_runtime.py
git commit -m "feat: add fail-closed library runtime"
```

---

### Task 2: Library Catalog API, Ordering, and Single-Book Product Profile

**Files:**
- Modify: `runtime/library_runtime.py`
- Modify: `tests/test_library_runtime.py`

**Interfaces:**
- Consumes: `LibraryRuntime.entries`, mounted `CourseRuntime` objects from Task 1.
- Produces:
  - `LibraryRuntime.course_ids() -> list[str]`
  - `LibraryRuntime.courses() -> list[CourseRuntime]`
  - `LibraryRuntime.course(course_id: str) -> CourseRuntime`
  - `LibraryRuntime.summary() -> dict[str, Any]`
  - Book App profile check: each enabled course must have exactly one mounted book and that book must be its main book.

- [ ] **Step 1: Add failing catalog/profile tests**

Append:

```python
    def test_course_ids_are_sorted_by_order_then_manifest_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            second_course = repo / "courses" / "second-course"
            second_book = repo / "books" / "second"
            self._write_book(second_book, readiness="READY")
            course_data = json.loads((repo / "courses" / "fixture-course" / "course.json").read_text(encoding="utf-8"))
            course_data["course_id"] = "second_course"
            course_data["main_book_id"] = "fixture_book"
            course_data["books"][0]["path"] = "../../books/second"
            self._dump(second_course / "course.json", course_data)
            manifest = self._library_manifest()
            manifest["courses"] = [
                self._course_entry(course_id="fixture_course", order=20),
                self._course_entry(course_id="second_course", path="../courses/second-course", order=10),
            ]
            self._dump(library_dir / "library.json", manifest)
            library = LibraryRuntime.open(library_dir)
            self.assertEqual(library.course_ids(), ["second_course", "fixture_course"])
            self.assertEqual([c.course_id for c in library.courses()], ["second_course", "fixture_course"])

    def test_course_returns_mounted_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            library = LibraryRuntime.open(library_dir)
            self.assertEqual(library.course("fixture_course").course_id, "fixture_course")

    def test_unknown_or_disabled_course_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            library = LibraryRuntime.open(library_dir)
            with self.assertRaises(LibraryRuntimeError):
                library.course("missing")

    def test_multi_book_course_is_rejected_by_product_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            second_book = repo / "books" / "second"
            self._write_book(second_book, readiness="READY")
            course_path = repo / "courses" / "fixture-course" / "course.json"
            course_data = json.loads(course_path.read_text(encoding="utf-8"))
            course_data["books"].append(
                {
                    "book_id": "second_book",
                    "role": "supplementary",
                    "path": "../../books/second",
                    "required": True,
                    "enabled": True,
                }
            )
            second_meta = json.loads((second_book / "book_metadata.json").read_text(encoding="utf-8"))
            second_meta["book_id"] = "second_book"
            self._dump(second_book / "book_metadata.json", second_meta)
            for filename in ("RUNTIME_READINESS.json", "STRUCTURED_COMPLETE.json", "qa_retrieval_policy.json"):
                data = json.loads((second_book / filename).read_text(encoding="utf-8"))
                data["book_id"] = "second_book"
                self._dump(second_book / filename, data)
            self._dump(course_path, course_data)
            with self.assertRaises(LibraryManifestError):
                LibraryRuntime.open(library_dir)

    def test_summary_reports_enabled_independent_courses(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            summary = LibraryRuntime.open(library_dir).summary()
            self.assertEqual(summary["library_id"], "fixture_library")
            self.assertEqual(summary["course_count"], 1)
            self.assertEqual(summary["courses"][0]["course_id"], "fixture_course")
            self.assertEqual(summary["courses"][0]["book_count"], 1)
```

Also import `LibraryRuntimeError` in the test import list.

- [ ] **Step 2: Run Task 2 tests and confirm RED**

```bash
python -m unittest tests.test_library_runtime -v
```

Expected: failures for missing catalog methods and missing single-book profile rejection.

- [ ] **Step 3: Implement deterministic catalog API and profile enforcement**

Use this ordering helper and API shape:

```python
    def _enabled_entries(self) -> list[LibraryCourseEntry]:
        return sorted(
            (entry for entry in self.entries if entry.enabled),
            key=lambda entry: (entry.order, entry.position),
        )

    def course_ids(self) -> list[str]:
        return [entry.course_id for entry in self._enabled_entries()]

    def courses(self) -> list[CourseRuntime]:
        return [self._courses[course_id] for course_id in self.course_ids()]

    def course(self, course_id: str) -> CourseRuntime:
        try:
            return self._courses[course_id]
        except KeyError as exc:
            raise LibraryRuntimeError(f"Unknown or disabled course: {course_id}") from exc

    def _validate_product_profile(self, entry: LibraryCourseEntry, course: CourseRuntime) -> None:
        book_ids = course.book_ids()
        if len(book_ids) != 1:
            raise LibraryManifestError(
                f"Book App course {entry.course_id!r} must expose exactly one enabled book; "
                f"found {len(book_ids)}"
            )
        if course.main_book().book_id != book_ids[0]:
            raise LibraryManifestError(
                f"Book App course {entry.course_id!r} main book does not match its sole mounted book"
            )

    def summary(self) -> dict[str, Any]:
        return {
            "library_id": self.library_id,
            "name": self.name,
            "course_count": len(self._courses),
            "courses": [
                {
                    "course_id": course.course_id,
                    "name": course.name,
                    "book_count": len(course.book_ids()),
                    "main_book_id": course.main_book_id,
                }
                for course in self.courses()
            ],
        }
```

Call `_validate_product_profile(entry, course)` immediately after canonical `course_id` verification and before storing the mounted course.

- [ ] **Step 4: Run Task 2 tests and regression tests**

```bash
python -m unittest tests.test_library_runtime -v
python -m unittest tests.test_book_runtime tests.test_course_runtime -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add runtime/library_runtime.py tests/test_library_runtime.py
git commit -m "feat: enforce independent single-book course catalog"
```

---

### Task 3: SectionLearningSource Evidence Projection

**Files:**
- Create: `runtime/section_learning_runtime.py`
- Create: `tests/test_section_learning_runtime.py`

**Interfaces:**
- Consumes:
  - `CourseRuntime.section(section_id: str) -> RuntimeSection`
  - `CourseRuntime.main_book() -> BookRuntime`
  - `BookRuntime.objects_for_section(section_id)`
  - `BookRuntime.page_map_row(pdf_page)`
  - `BookRuntime.translation_text(batch_id)`
  - `BookRuntime.figures`
- Produces:
  - `SectionLearningSource` dataclass
  - `SectionLearningRuntime.from_course(course: CourseRuntime, section_id: str) -> SectionLearningRuntime`
  - `SectionLearningRuntime.source() -> SectionLearningSource`
  - `SectionLearningRuntimeError`, `SectionLearningSourceError`, `SectionLearningModeError`.

- [ ] **Step 1: Write failing source-projection tests**

Create `tests/test_section_learning_runtime.py` using a `FakeBook`/`FakeCourse` so source tests isolate this layer and do not re-test JSON parsing:

```python
from __future__ import annotations

import unittest

from runtime.book_runtime import RuntimeAnchor, RuntimeFigure, RuntimeObject, RuntimeSection
from runtime.section_learning_runtime import (
    SectionLearningRuntime,
    SectionLearningSourceError,
)


class FakeBook:
    book_id = "fixture_book"

    def __init__(self) -> None:
        self.figures = {
            "fig_in_2": RuntimeFigure(id="fig_in_2", anchor=RuntimeAnchor(pdf_page=2, source_anchor="a2"), source_batch="b1"),
            "fig_out": RuntimeFigure(id="fig_out", anchor=RuntimeAnchor(pdf_page=9), source_batch="b9"),
            "fig_in_1": RuntimeFigure(id="fig_in_1", anchor=RuntimeAnchor(pdf_page=1, source_anchor="a1"), source_batch="b1"),
        }
        self._objects = [
            RuntimeObject(id="def_1", type="definition", section_id="s1", name_en="Definition", anchor=RuntimeAnchor(pdf_page=1, printed_page=11, source_anchor="obj-a"), source_batch="b1"),
            RuntimeObject(id="ex_1", type="exercise", section_id="s1", name_en="Exercise", anchor=RuntimeAnchor(pdf_page=2), source_batch="b2"),
        ]

    def objects_for_section(self, section_id: str):
        if section_id != "s1":
            raise AssertionError(section_id)
        return list(self._objects)

    def page_map_row(self, pdf_page: int):
        return {"pdf_page": str(pdf_page), "printed_page": str(pdf_page + 10)}

    def translation_text(self, batch_id: str):
        return "translated" if batch_id == "b1" else None


class FakeCourse:
    course_id = "fixture_course"

    def __init__(self) -> None:
        self._book = FakeBook()
        self._section = RuntimeSection(
            id="s1",
            number="1.1",
            title_en="Section One",
            title_zh="第一节",
            chapter_id="chapter_01",
            pdf_page_start=1,
            pdf_page_end=2,
            printed_page_start=11,
            printed_page_end=12,
            source_batches=["b1", "b2", "b1"],
        )

    def main_book(self):
        return self._book

    def section(self, section_id: str):
        if section_id != "s1":
            from runtime.book_runtime import BookRuntimeError
            raise BookRuntimeError(f"Unknown section: {section_id}")
        return self._section


class SectionLearningSourceTests(unittest.TestCase):
    def test_known_section_builds_source_with_canonical_identity(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual((source.course_id, source.book_id, source.chapter_id, source.section_id), ("fixture_course", "fixture_book", "chapter_01", "s1"))

    def test_unknown_section_fails(self) -> None:
        with self.assertRaises(SectionLearningSourceError):
            SectionLearningRuntime.from_course(FakeCourse(), "missing")

    def test_objects_preserve_book_runtime_order(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual([row["id"] for row in source.objects], ["def_1", "ex_1"])

    def test_figures_are_in_range_and_sorted_by_page_then_id(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual([row["id"] for row in source.figures], ["fig_in_1", "fig_in_2"])

    def test_page_map_boundaries_are_preserved(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual(source.page_map_start["printed_page"], "11")
        self.assertEqual(source.page_map_end["printed_page"], "12")

    def test_missing_optional_anchor_stays_none(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        exercise = next(row for row in source.objects if row["id"] == "ex_1")
        self.assertIsNone(exercise["source_anchor"])

    def test_translation_sources_are_stably_deduplicated_without_text_slicing(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual(source.translation_sources, [{"batch_id": "b1", "available": True}, {"batch_id": "b2", "available": False}])
        self.assertFalse(any("text" in row for row in source.translation_sources))
```

- [ ] **Step 2: Run source tests and confirm RED**

```bash
python -m unittest tests.test_section_learning_runtime.SectionLearningSourceTests -v
```

Expected: import failure because `runtime.section_learning_runtime` does not exist.

- [ ] **Step 3: Implement SectionLearningSource and source builder**

Create these public types:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .book_runtime import BookRuntimeError
from .course_runtime import CourseRuntime


class SectionLearningRuntimeError(RuntimeError):
    pass


class SectionLearningSourceError(SectionLearningRuntimeError):
    pass


class SectionLearningModeError(SectionLearningRuntimeError):
    pass


@dataclass
class SectionLearningSource:
    course_id: str
    book_id: str
    chapter_id: str | None
    section_id: str
    number: str | None
    title_en: str | None
    title_zh: str | None
    pdf_page_start: int | None
    pdf_page_end: int | None
    printed_page_start: int | str | None
    printed_page_end: int | str | None
    source_batches: list[str]
    page_map_start: dict[str, str] | None
    page_map_end: dict[str, str] | None
    objects: list[dict[str, Any]]
    figures: list[dict[str, Any]]
    translation_sources: list[dict[str, Any]]
```

Implement `SectionLearningRuntime.from_course()` so it resolves the Section only through the selected course and wraps `BookRuntimeError` as `SectionLearningSourceError`.

Project objects with exact keys:

```python
{
    "kind": "object",
    "id": obj.id,
    "type": obj.type,
    "number": obj.number,
    "name_en": obj.name_en,
    "name_zh": obj.name_zh,
    "formula": obj.formula,
    "pdf_page": obj.anchor.pdf_page,
    "printed_page": obj.anchor.printed_page,
    "source_anchor": obj.anchor.source_anchor,
    "source_batch": obj.source_batch,
}
```

Project figures only when `pdf_page_start <= figure.anchor.pdf_page <= pdf_page_end`; if either Section boundary is missing, do not guess and return no figures. Sort included figures by `(pdf_page if not None else 10**9, id)`.

Project figures with exact keys:

```python
{
    "kind": "figure",
    "id": figure.id,
    "title_en": figure.title_en,
    "title_zh": figure.title_zh,
    "pdf_page": figure.anchor.pdf_page,
    "printed_page": figure.anchor.printed_page,
    "source_anchor": figure.anchor.source_anchor,
    "source_batch": figure.source_batch,
}
```

Stable-deduplicate `RuntimeSection.source_batches` in original order and map each to:

```python
{"batch_id": batch_id, "available": book.translation_text(batch_id) is not None}
```

Do not store the returned translation text in `SectionLearningSource`.

- [ ] **Step 4: Run source tests and regressions**

```bash
python -m unittest tests.test_section_learning_runtime.SectionLearningSourceTests -v
python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 3**

```bash
git add runtime/section_learning_runtime.py tests/test_section_learning_runtime.py
git commit -m "feat: project source-backed section learning data"
```

---

### Task 4: Deterministic Preview, Learn, Review, and Practice Modes

**Files:**
- Modify: `runtime/section_learning_runtime.py`
- Modify: `tests/test_section_learning_runtime.py`

**Interfaces:**
- Consumes: `SectionLearningSource` from Task 3.
- Produces:
  - `SectionLearningRuntime.preview() -> dict[str, Any]`
  - `SectionLearningRuntime.learn() -> dict[str, Any]`
  - `SectionLearningRuntime.review() -> dict[str, Any]`
  - `SectionLearningRuntime.practice() -> dict[str, Any]`
- Exact review type set: `definition`, `theorem`, `proposition`, `lemma`, `corollary`, `formula` after `strip().casefold()`.
- Exact practice type set: `exercise`, `problem` after `strip().casefold()`.

- [ ] **Step 1: Add failing mode tests**

Extend the fake objects with theorem/problem coverage and append:

```python
class SectionLearningModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.learning = SectionLearningRuntime.from_course(FakeCourse(), "s1")

    def test_preview_preserves_identity(self) -> None:
        payload = self.learning.preview()
        self.assertEqual(payload["mode"], "preview")
        self.assertEqual((payload["course_id"], payload["book_id"], payload["chapter_id"], payload["section_id"]), ("fixture_course", "fixture_book", "chapter_01", "s1"))

    def test_learn_references_all_objects_figures_and_translations(self) -> None:
        source = self.learning.source()
        payload = self.learning.learn()
        expected = (
            [("object", row["id"]) for row in source.objects]
            + [("figure", row["id"]) for row in source.figures]
            + [("translation", row["batch_id"]) for row in source.translation_sources]
        )
        self.assertEqual([(row["kind"], row["source_id"]) for row in payload["items"]], expected)

    def test_review_uses_exact_normalized_policy_types(self) -> None:
        payload = self.learning.review()
        source = self.learning.source()
        by_id = {row["id"]: row for row in source.objects}
        for item in payload["items"]:
            self.assertIn(by_id[item["source_id"]]["type"].strip().casefold(), {"definition", "theorem", "proposition", "lemma", "corollary", "formula"})

    def test_practice_uses_only_exercise_and_problem(self) -> None:
        payload = self.learning.practice()
        source = self.learning.source()
        by_id = {row["id"]: row for row in source.objects}
        for item in payload["items"]:
            self.assertIn(by_id[item["source_id"]]["type"].strip().casefold(), {"exercise", "problem"})

    def test_empty_review_and_practice_are_valid(self) -> None:
        course = FakeCourse()
        course._book._objects = [RuntimeObject(id="remark_1", type="remark", section_id="s1")]
        learning = SectionLearningRuntime.from_course(course, "s1")
        self.assertEqual(learning.review()["items"], [])
        self.assertEqual(learning.practice()["items"], [])

    def test_every_mode_item_maps_to_source_by_kind_and_source_id(self) -> None:
        source = self.learning.source()
        source_keys = (
            {("object", row["id"]) for row in source.objects}
            | {("figure", row["id"]) for row in source.figures}
            | {("translation", row["batch_id"]) for row in source.translation_sources}
        )
        for payload in (self.learning.preview(), self.learning.learn(), self.learning.review(), self.learning.practice()):
            for item in payload["items"]:
                self.assertIn((item["kind"], item["source_id"]), source_keys)
            self.assertEqual(
                payload["source_refs"],
                [{"kind": row["kind"], "source_id": row["source_id"]} for row in payload["items"]],
            )

    def test_modes_are_independently_callable(self) -> None:
        first = SectionLearningRuntime.from_course(FakeCourse(), "s1").practice()
        second = SectionLearningRuntime.from_course(FakeCourse(), "s1").preview()
        third = SectionLearningRuntime.from_course(FakeCourse(), "s1").review()
        fourth = SectionLearningRuntime.from_course(FakeCourse(), "s1").learn()
        self.assertEqual([first["mode"], second["mode"], third["mode"], fourth["mode"]], ["practice", "preview", "review", "learn"])
```

- [ ] **Step 2: Run mode tests and confirm RED**

```bash
python -m unittest tests.test_section_learning_runtime.SectionLearningModeTests -v
```

Expected: failures because mode methods do not exist.

- [ ] **Step 3: Implement common mode envelope and exact policies**

Add constants:

```python
REVIEW_TYPES = frozenset({"definition", "theorem", "proposition", "lemma", "corollary", "formula"})
PRACTICE_TYPES = frozenset({"exercise", "problem"})
```

Use references only:

```python
    @staticmethod
    def _ref(kind: str, source_id: str) -> dict[str, str]:
        return {"kind": kind, "source_id": source_id}

    def _envelope(self, mode: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        source = self._source
        refs = [{"kind": str(item["kind"]), "source_id": str(item["source_id"])} for item in items]
        return {
            "mode": mode,
            "course_id": source.course_id,
            "book_id": source.book_id,
            "chapter_id": source.chapter_id,
            "section_id": source.section_id,
            "source_status": "available",
            "items": items,
            "source_refs": refs,
        }
```

Implement deterministic reference sequences:

```python
    def _all_refs(self) -> list[dict[str, str]]:
        return (
            [self._ref("object", row["id"]) for row in self._source.objects]
            + [self._ref("figure", row["id"]) for row in self._source.figures]
            + [self._ref("translation", row["batch_id"]) for row in self._source.translation_sources]
        )

    def preview(self) -> dict[str, Any]:
        return self._envelope("preview", self._all_refs())

    def learn(self) -> dict[str, Any]:
        return self._envelope("learn", self._all_refs())

    def review(self) -> dict[str, Any]:
        items = [
            self._ref("object", row["id"])
            for row in self._source.objects
            if str(row.get("type") or "").strip().casefold() in REVIEW_TYPES
        ]
        return self._envelope("review", items)

    def practice(self) -> dict[str, Any]:
        items = [
            self._ref("object", row["id"])
            for row in self._source.objects
            if str(row.get("type") or "").strip().casefold() in PRACTICE_TYPES
        ]
        return self._envelope("practice", items)
```

Do not copy formula/text/anchor fields into mode items; consumers dereference `(kind, source_id)` against `source()`.

- [ ] **Step 4: Run mode/source/regression tests**

```bash
python -m unittest tests.test_section_learning_runtime -v
python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 4**

```bash
git add runtime/section_learning_runtime.py tests/test_section_learning_runtime.py
git commit -m "feat: add deterministic section learning modes"
```

---

### Task 5: Real Functional Analysis Library Fixture and Public Runtime Exports

**Files:**
- Create: `library/library.json`
- Modify: `runtime/__init__.py`
- Modify: `tests/test_library_runtime.py`
- Modify: `tests/test_section_learning_runtime.py`

**Interfaces:**
- Consumes: Tasks 1–4 public APIs.
- Produces: clean-checkout real path `LibraryRuntime.open("library") → functional_analysis_course → ch01_s01 → four modes` and package-level exports from `runtime`.

- [ ] **Step 1: Add failing real-fixture and package-export tests**

Append to `tests/test_library_runtime.py`:

```python
    def test_real_functional_analysis_library_fixture(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        if not (repo / "books" / "functional-analysis").exists():
            self.skipTest("repository Functional Analysis fixture not present")
        library = LibraryRuntime.open(repo / "library")
        self.assertEqual(library.course_ids(), ["functional_analysis_course"])
        course = library.course("functional_analysis_course")
        self.assertEqual(course.book_ids(), ["stein_shakarchi_functional_analysis_2011"])
        self.assertEqual(course.main_book().book_id, "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(len(course.chapter_ids()), 8)
        self.assertEqual(sum(len(course.sections_for_chapter(cid)) for cid in course.chapter_ids()), 132)
        self.assertEqual(len(course.main_book().page_map), 442)
        self.assertEqual(sum(1 for _ in course.main_book().iter_search_records()), 1493)

    def test_runtime_package_exports_library_runtime(self) -> None:
        from runtime import LibraryRuntime as ExportedLibraryRuntime
        self.assertIs(ExportedLibraryRuntime, LibraryRuntime)
```

Append to `tests/test_section_learning_runtime.py`:

```python
    def test_real_ch01_s01_builds_all_learning_modes(self) -> None:
        from pathlib import Path
        from runtime import LibraryRuntime

        repo = Path(__file__).resolve().parents[1]
        if not (repo / "books" / "functional-analysis").exists():
            self.skipTest("repository Functional Analysis fixture not present")
        course = LibraryRuntime.open(repo / "library").course("functional_analysis_course")
        learning = SectionLearningRuntime.from_course(course, "ch01_s01")
        source = learning.source()
        self.assertEqual(source.course_id, "functional_analysis_course")
        self.assertEqual(source.book_id, "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(source.section_id, "ch01_s01")
        for mode in (learning.preview(), learning.learn(), learning.review(), learning.practice()):
            self.assertEqual(mode["course_id"], source.course_id)
            self.assertEqual(mode["book_id"], source.book_id)
            self.assertEqual(mode["section_id"], source.section_id)

    def test_runtime_package_exports_section_learning_runtime(self) -> None:
        from runtime import SectionLearningRuntime as ExportedSectionLearningRuntime
        self.assertIs(ExportedSectionLearningRuntime, SectionLearningRuntime)
```

- [ ] **Step 2: Run integration tests and confirm RED**

```bash
python -m unittest tests.test_library_runtime tests.test_section_learning_runtime -v
```

Expected: failures because `library/library.json` and package exports do not yet exist.

- [ ] **Step 3: Create the real library manifest**

Create `library/library.json` exactly as:

```json
{
  "schema_version": "library_manifest_v1",
  "library_id": "book_app_library",
  "name": "Book",
  "courses": [
    {
      "course_id": "functional_analysis_course",
      "name": "Functional Analysis",
      "path": "../courses/functional-analysis",
      "enabled": true,
      "order": 10
    }
  ]
}
```

- [ ] **Step 4: Export new runtime APIs**

Extend `runtime/__init__.py` imports and `__all__` with:

```python
from .library_runtime import (
    LibraryCourseResolutionError,
    LibraryManifestError,
    LibraryRuntime,
    LibraryRuntimeBlockedError,
    LibraryRuntimeError,
)
from .section_learning_runtime import (
    SectionLearningModeError,
    SectionLearningRuntime,
    SectionLearningRuntimeError,
    SectionLearningSource,
    SectionLearningSourceError,
)
```

Add the same names to `__all__` without removing existing BookRuntime/CourseRuntime exports.

- [ ] **Step 5: Run real integration and full runtime tests**

```bash
python -m unittest tests.test_library_runtime tests.test_section_learning_runtime -v
python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime tests.test_section_learning_runtime -v
```

Expected: PASS, with real fixture asserting one library course, one canonical book, 8 Chapters, 132 Sections, 442 PageMap rows, and 1493 search records.

- [ ] **Step 6: Commit Task 5**

```bash
git add library/library.json runtime/__init__.py tests/test_library_runtime.py tests/test_section_learning_runtime.py
git commit -m "feat: wire Functional Analysis into the app library"
```

---

### Task 6: CI, Documentation, and Final Phase 1C Verification

**Files:**
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Modify: `runtime/README.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: all runtime APIs and tests from Tasks 1–5.
- Produces: CI coverage for the new runtime path, corrected product documentation, and final integration evidence suitable for a PR.

- [ ] **Step 1: Extend CI path filters, compilation, and unit test command**

In both `push.paths` and `pull_request.paths`, add:

```yaml
      - "library/**"
```

In `Compile reference runtime`, add:

```yaml
          python -m py_compile runtime/library_runtime.py
          python -m py_compile runtime/section_learning_runtime.py
```

Replace the unit-test command with the existing modules plus the two new modules:

```yaml
      - name: Run unit tests
        run: python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime tests.test_section_learning_runtime tests.test_functional_analysis_page_map tests.test_continuation_integrity tests.test_runtime_object_merge tests.test_functional_analysis_identity_normalizer tests.test_functional_analysis_figure_normalizer -v
```

- [ ] **Step 2: Extend the Python 3.13 real acceptance command**

Keep the existing rebuild/readiness checks intact and extend the final Python command to import and assert the App-level chain:

```python
from runtime import BookRuntime, CourseRuntime, LibraryRuntime, SectionLearningRuntime

runtime = BookRuntime.open(root)
course = CourseRuntime.open("courses/functional-analysis")
library = LibraryRuntime.open("library")
library_course = library.course("functional_analysis_course")
learning = SectionLearningRuntime.from_course(library_course, "ch01_s01")

assert runtime.is_ready
assert len(course.chapter_ids()) == 8
assert sum(len(course.sections_for_chapter(cid)) for cid in course.chapter_ids()) == 132
assert library.course_ids() == ["functional_analysis_course"]
assert library_course.book_ids() == ["stein_shakarchi_functional_analysis_2011"]
assert learning.source().section_id == "ch01_s01"
assert [learning.preview()["mode"], learning.learn()["mode"], learning.review()["mode"], learning.practice()["mode"]] == ["preview", "learn", "review", "practice"]
```

Retain the existing PageMap assertions for PDF 20 → printed 1 and PDF 442 → printed 423 and the existing readiness diagnostics printout; add `library_runtime_open: true` and `section_learning_runtime_open: true` to printed evidence.

- [ ] **Step 3: Update runtime documentation**

In `runtime/README.md`, update the runtime chain to:

```text
结构化教材资产
        ↓
Runtime readiness gate
        ↓
BookRuntime
        ↓
CourseRuntime
        ↓
LibraryRuntime
        ↓
SectionLearningRuntime
        ↓
Preview / Learn / Review / Practice
```

Add a runnable example:

```python
from runtime import LibraryRuntime, SectionLearningRuntime

library = LibraryRuntime.open("library")
course = library.course("functional_analysis_course")
learning = SectionLearningRuntime.from_course(course, "ch01_s01")

print(learning.source())
print(learning.preview())
print(learning.learn())
print(learning.review())
print(learning.practice())
```

Document explicitly:

```text
Book App 产品层：一个 App 包含多个独立课程；当前每个课程只接入一本教材。
CourseRuntime 底层仍保留多书能力，但 LibraryRuntime 不接纳多书课程进入当前产品入口。
四种学习模式只引用 SectionLearningSource 中可追溯的教材来源；Phase 1C 不生成 AI 教学内容或题目。
```

Keep the `STRUCTURED_COMPLETE` vs `RUNTIME_READY` distinction unchanged.

- [ ] **Step 4: Correct root product documentation**

In root `README.md`, replace the outdated principle:

```text
一门课程支持多本教材：主教材、辅助教材、英文教材、参考教材。
```

with:

```text
一个 Book App 支持多门彼此独立的教材课程；当前产品形态下每门课程对应一本教材，例如泛函分析、实分析分别作为独立课程加入同一个 App。
```

Update “当前状态” so Phase 1B is described as merged/completed and Phase 1C is the current milestone. Do not delete the broader future architecture documentation; identify generic CourseRuntime multi-book support as lower-level compatibility rather than the current App product model.

- [ ] **Step 5: Run full local-equivalent verification**

Run syntax compilation:

```bash
python -m py_compile runtime/book_runtime.py runtime/course_runtime.py runtime/library_runtime.py runtime/section_learning_runtime.py
```

Run the complete runtime suite:

```bash
python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime tests.test_section_learning_runtime tests.test_functional_analysis_page_map tests.test_continuation_integrity tests.test_runtime_object_merge tests.test_functional_analysis_identity_normalizer tests.test_functional_analysis_figure_normalizer -v
```

Run real runtime readiness without changing textbook source files:

```bash
python tools/check_runtime_readiness.py books/functional-analysis
```

Run direct real acceptance:

```bash
python -c "from runtime import LibraryRuntime,SectionLearningRuntime; l=LibraryRuntime.open('library'); c=l.course('functional_analysis_course'); s=SectionLearningRuntime.from_course(c,'ch01_s01'); assert l.course_ids()==['functional_analysis_course']; assert c.book_ids()==['stein_shakarchi_functional_analysis_2011']; assert len(c.chapter_ids())==8; assert sum(len(c.sections_for_chapter(x)) for x in c.chapter_ids())==132; assert len(c.main_book().page_map)==442; assert sum(1 for _ in c.main_book().iter_search_records())==1493; assert [s.preview()['mode'],s.learn()['mode'],s.review()['mode'],s.practice()['mode']]==['preview','learn','review','practice']; print('Phase 1C acceptance PASS')"
```

Expected: all commands succeed and readiness remains `READY`.

- [ ] **Step 6: Verify no textbook source assets changed**

Run:

```bash
git diff --name-only main...HEAD
```

Expected changed paths are limited to the Phase 1C spec/plan plus:

```text
library/library.json
runtime/library_runtime.py
runtime/section_learning_runtime.py
runtime/__init__.py
tests/test_library_runtime.py
tests/test_section_learning_runtime.py
.github/workflows/runtime-reference-tests.yml
runtime/README.md
README.md
```

No `books/functional-analysis/*_structure.json`, `books/functional-analysis/chunks/*`, PageMap, TOC, or search-index source asset should appear in the implementation diff.

- [ ] **Step 7: Commit CI/docs changes**

```bash
git add .github/workflows/runtime-reference-tests.yml runtime/README.md README.md
git commit -m "docs: integrate Phase 1C runtime path"
```

- [ ] **Step 8: Push branch and require GitHub Actions evidence before PR completion claims**

Require `Runtime reference tests` to complete successfully on Python 3.11, 3.12, and 3.13. On 3.13, verify the real Functional Analysis rebuild/readiness step and the Library → Course → SectionLearning acceptance both succeed. Do not claim Phase 1C complete from local-equivalent reasoning alone.

- [ ] **Step 9: Open a PR without merging**

Use a PR title equivalent to:

```text
Add App library and Section learning runtime
```

PR body must report:

```text
- one App / many independent courses product model
- one enabled textbook per admitted product course
- Functional Analysis as the first real library fixture
- ch01_s01 source-backed Preview/Learn/Review/Practice path
- no AI-generated textbook content in Phase 1C
- Python 3.11/3.12/3.13 CI result
- 8 Chapters / 132 Sections / 442 PageMap rows / 1493 search records retained
- no Functional Analysis structured source assets changed
```

Do not merge the PR without explicit user approval.

## Plan Self-Review

- **Spec coverage:** Library schema/root/path trust, disabled-course behavior, canonical ID verification, single-book product profile, Section evidence projection, deterministic ordering, PageMap/translation/figure handling, exact Review/Practice policies, `(kind, source_id)` traceability, real Functional Analysis fixture, CI, docs, and no-textbook-source-change acceptance are all mapped to Tasks 1–6.
- **Placeholder scan:** No `TBD`, `TODO`, “implement later”, or unspecified error/testing steps remain.
- **Type consistency:** `LibraryRuntime.open(..., repository_root=...)`, `course_ids()`, `courses()`, `course()`, `summary()`, `SectionLearningRuntime.from_course()`, `source()`, `preview()`, `learn()`, `review()`, and `practice()` use the same names throughout the plan.
- **Scope check:** LibraryRuntime and SectionLearningRuntime are separate files/tasks but intentionally remain one Phase 1C plan because the acceptance deliverable is the single end-to-end App path `Library → Course → ch01_s01 → four modes`; neither introduces UI or persistence.
