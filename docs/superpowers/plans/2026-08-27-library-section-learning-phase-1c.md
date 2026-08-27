# Phase 1C Library + Section Learning Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the App-level path `Library → independent single-book Course → SectionLearningSource → Preview/Learn/Review/Practice`, with Functional Analysis as the first real course.

**Architecture:** `LibraryRuntime` sits above the existing `CourseRuntime` and enforces the current product profile: one Book App may contain many independent courses, but each admitted product course has exactly one enabled main textbook. `SectionLearningRuntime` sits below a selected course and projects one Section from data already exposed by `CourseRuntime`/`BookRuntime`; all four learning modes reference this deterministic source and never invent textbook content.

**Tech Stack:** Python 3.11/3.12/3.13, standard library only, `unittest`, JSON manifests, existing `BookRuntime`/`CourseRuntime`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-library-section-learning-phase-1c-design.md`

## Global Constraints

- One Book App → many independent textbook courses.
- One admitted product course → exactly one enabled textbook, and it is that course's main book.
- Keep generic Phase 1B multi-book `CourseRuntime` behavior unchanged; the single-book rule belongs only to `LibraryRuntime`.
- Preserve the existing `STRUCTURED_COMPLETE` and `RUNTIME_READY` fail-closed gates.
- `BookRuntime` remains the only parser/normalizer for structured textbook assets.
- Phase 1C must not re-read raw `*_structure.json` files to duplicate `BookRuntime` logic.
- No AI-generated explanations, summaries, objectives, questions, answers, textbook facts, or source anchors.
- No UI, database, progress persistence, notes, mistakes, lectures, exams, mastery, cross-course search/QA, or CourseKnowledgeTree implementation.
- No Functional Analysis structured source asset may change.
- Existing BookRuntime/CourseRuntime tests must remain green.
- New tests must pass on Python 3.11, 3.12, and 3.13.
- Real Functional Analysis acceptance must retain 8 Chapters, 132 Sections, 442 PageMap rows, and 1493 final search records.
- No CI step may automatically commit generated files to `main`.

## File Map

- Create `library/library.json` — App-level catalog of independent courses.
- Create `runtime/library_runtime.py` — library manifest validation, root/path containment, fail-closed course mounting, single-book product-profile enforcement, catalog API.
- Create `runtime/section_learning_runtime.py` — deterministic Section evidence projection plus Preview/Learn/Review/Practice payloads.
- Modify `runtime/__init__.py` — public exports.
- Create `tests/runtime_fixture_factory.py` — reusable minimal ready Book/Course fixture writer used by the new tests only.
- Create `tests/test_library_runtime.py` — library contract, ordering, path, readiness, profile, and real fixture tests.
- Create `tests/test_section_learning_runtime.py` — source projection, mode policy, traceability, and real `ch01_s01` tests.
- Modify `.github/workflows/runtime-reference-tests.yml` — watch/compile/test the new runtime path and real fixture.
- Modify `runtime/README.md` — new runtime usage and evidence rules.
- Modify `README.md` — correct the App product model.

---

### Task 1: Shared Test Fixture + Fail-Closed Library Manifest Contract

**Files:**
- Create: `tests/runtime_fixture_factory.py`
- Create: `tests/test_library_runtime.py`
- Create: `runtime/library_runtime.py`

**Interfaces:**
- Consumes: `CourseRuntime.open(course_dir: str | Path) -> CourseRuntime` and `CourseRuntimeError`.
- Produces:
  - `LibraryRuntime.open(library_dir: str | Path, *, repository_root: str | Path | None = None) -> LibraryRuntime`
  - `LibraryRuntimeError`
  - `LibraryManifestError`
  - `LibraryCourseResolutionError`
  - `LibraryRuntimeBlockedError`
  - `LibraryCourseEntry(course_id, name, path, enabled, order, position)`.

- [ ] **Step 1: Add an exact reusable runtime fixture writer**

Create `tests/runtime_fixture_factory.py`:

```python
from __future__ import annotations

import json
from pathlib import Path


def dump_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_repo(root: Path) -> Path:
    repo = root.resolve()
    (repo / "runtime").mkdir(parents=True, exist_ok=True)
    (repo / "books").mkdir(parents=True, exist_ok=True)
    (repo / "courses").mkdir(parents=True, exist_ok=True)
    return repo


def write_ready_book(
    root: Path,
    *,
    book_id: str,
    readiness: str = "READY",
    objects: list[dict[str, object]] | None = None,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    dump_json(
        root / "RUNTIME_READINESS.json",
        {
            "status": readiness,
            "book_id": book_id,
            "structured_version": "v1",
            "missing_required_files": [],
            "stale_files": [] if readiness == "READY" else ["search_index_v1.jsonl"],
        },
    )
    dump_json(
        root / "STRUCTURED_COMPLETE.json",
        {
            "status": "STRUCTURED_COMPLETE",
            "book_id": book_id,
            "pdf_pages": 2,
            "printed_final_page": 2,
            "version": "v1",
            "audit_fail_count": 0,
            "search_index": "search_index_v1.jsonl",
        },
    )
    dump_json(
        root / "book_metadata.json",
        {
            "book_id": book_id,
            "title_en": "Fixture",
            "title_zh": "测试教材",
            "pdf_total_pages": 2,
            "toc_file": "toc_bilingual.json",
            "page_map_file": "page_map.csv",
        },
    )
    dump_json(root / "qa_retrieval_policy.json", {"version": "1", "book_id": book_id})
    dump_json(
        root / "toc_bilingual.json",
        {
            "chapters": [
                {
                    "id": "chapter_01",
                    "number": "1",
                    "title_en": "Test chapter",
                    "title_zh": "测试章",
                    "sections": [{"id": "ch01_s01", "number": "1", "title_en": "Section", "title_zh": "小节"}],
                }
            ]
        },
    )
    dump_json(
        root / "chunk_001a_structure.json",
        {
            "chunk_id": "chunk_001a",
            "pdf_pages": [1, 2],
            "printed_pages": [1, 2],
            "chapter_id": "chapter_01",
            "sections": [
                {
                    "id": "ch01_s01",
                    "number": "1",
                    "title_en": "Section",
                    "title_zh": "小节",
                    "pdf_pages": [1, 2],
                    "printed_pages": [1, 2],
                }
            ],
            "key_objects": objects or [],
        },
    )
    (root / "chunk_001a_translation_zh.md").write_text("# 测试学习层\n", encoding="utf-8")
    (root / "page_map.csv").write_text(
        "pdf_page,printed_page,page_label\n1,1,1\n2,2,2\n",
        encoding="utf-8",
    )
    (root / "search_index_v1.jsonl").write_text(
        json.dumps({"id": "section_ch01_s01", "book_id": book_id, "type": "section"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_course(
    course_dir: Path,
    *,
    course_id: str,
    book_entries: list[dict[str, object]],
    main_book_id: str,
) -> None:
    dump_json(
        course_dir / "course.json",
        {
            "schema_version": "course_manifest_v1",
            "course_id": course_id,
            "name": course_id,
            "language": "bilingual",
            "status": "active",
            "main_book_id": main_book_id,
            "books": book_entries,
        },
    )


def main_book_entry(book_id: str, path: str) -> dict[str, object]:
    return {
        "book_id": book_id,
        "role": "main",
        "path": path,
        "required": True,
        "enabled": True,
    }
```

- [ ] **Step 2: Write the failing library contract tests**

Create `tests/test_library_runtime.py`:

```python
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.library_runtime import (
    LibraryCourseResolutionError,
    LibraryManifestError,
    LibraryRuntime,
    LibraryRuntimeBlockedError,
)
from tests.runtime_fixture_factory import (
    dump_json,
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


class LibraryRuntimeContractTests(unittest.TestCase):
    def _entry(
        self,
        *,
        course_id: str = "fixture_course",
        name: str = "Fixture Course",
        path: str = "../courses/fixture-course",
        enabled: bool = True,
        order: int = 10,
    ) -> dict[str, object]:
        return {"course_id": course_id, "name": name, "path": path, "enabled": enabled, "order": order}

    def _manifest(self) -> dict[str, object]:
        return {
            "schema_version": "library_manifest_v1",
            "library_id": "fixture_library",
            "name": "Fixture Library",
            "courses": [self._entry()],
        }

    def _ready_repo(self, root: Path, *, readiness: str = "READY") -> tuple[Path, Path]:
        repo = make_repo(root)
        write_ready_book(repo / "books" / "fixture", book_id="fixture_book", readiness=readiness)
        write_course(
            repo / "courses" / "fixture-course",
            course_id="fixture_course",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture")],
            main_book_id="fixture_book",
        )
        library_dir = repo / "library"
        dump_json(library_dir / "library.json", self._manifest())
        return repo, library_dir

    def _open_override(self, override: dict[str, object]) -> LibraryRuntime:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        _, library_dir = self._ready_repo(Path(temp.name))
        manifest = self._manifest()
        manifest.update(override)
        dump_json(library_dir / "library.json", manifest)
        return LibraryRuntime.open(library_dir)

    def test_valid_library_opens(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            library = LibraryRuntime.open(library_dir)
            self.assertEqual((library.library_id, library.name), ("fixture_library", "Fixture Library"))

    def test_unsupported_schema_version_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"schema_version": "library_manifest_v2"})

    def test_missing_library_id_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"library_id": ""})

    def test_missing_library_name_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"name": ""})

    def test_empty_courses_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"courses": []})

    def test_zero_enabled_courses_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"courses": [self._entry(enabled=False)]})

    def test_malformed_course_entry_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"courses": [{"course_id": "fixture_course"}]})

    def test_bool_order_is_not_accepted_as_integer(self) -> None:
        entry = self._entry()
        entry["order"] = True
        with self.assertRaises(LibraryManifestError):
            self._open_override({"courses": [entry]})

    def test_duplicate_enabled_course_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            write_course(
                repo / "courses" / "second-course",
                course_id="fixture_course",
                book_entries=[main_book_entry("fixture_book", "../../books/fixture")],
                main_book_id="fixture_book",
            )
            manifest = self._manifest()
            manifest["courses"] = [self._entry(), self._entry(path="../courses/second-course", order=20)]
            dump_json(library_dir / "library.json", manifest)
            with self.assertRaises(LibraryManifestError):
                LibraryRuntime.open(library_dir)

    def test_missing_enabled_course_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            manifest = self._manifest()
            manifest["courses"] = [self._entry(path="../courses/missing")]
            dump_json(library_dir / "library.json", manifest)
            with self.assertRaises(LibraryCourseResolutionError):
                LibraryRuntime.open(library_dir)

    def test_course_path_escape_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            _, library_dir = self._ready_repo(Path(temp))
            manifest = self._manifest()
            manifest["courses"] = [self._entry(path=str(Path(outside).resolve()))]
            dump_json(library_dir / "library.json", manifest)
            with self.assertRaises(LibraryCourseResolutionError):
                LibraryRuntime.open(library_dir)

    def test_nonstandard_layout_without_explicit_root_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, _ = self._ready_repo(Path(temp))
            custom = repo / "catalog"
            dump_json(custom / "library.json", self._manifest())
            with self.assertRaises(LibraryCourseResolutionError):
                LibraryRuntime.open(custom)

    def test_explicit_root_supports_nonstandard_library_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, _ = self._ready_repo(Path(temp))
            custom = repo / "catalog"
            manifest = self._manifest()
            manifest["courses"] = [self._entry(path="../courses/fixture-course")]
            dump_json(custom / "library.json", manifest)
            library = LibraryRuntime.open(custom, repository_root=repo)
            self.assertEqual(library.library_id, "fixture_library")

    def test_canonical_course_id_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            manifest = self._manifest()
            manifest["courses"] = [self._entry(course_id="wrong_course")]
            dump_json(library_dir / "library.json", manifest)
            with self.assertRaises(LibraryManifestError):
                LibraryRuntime.open(library_dir)

    def test_blocked_enabled_course_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp), readiness="BLOCKED")
            with self.assertRaises(LibraryRuntimeBlockedError):
                LibraryRuntime.open(library_dir)

    def test_disabled_incomplete_course_is_ignored_when_one_valid_course_remains(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            manifest = self._manifest()
            manifest["courses"].append(self._entry(course_id="future_course", path="../courses/not-created", enabled=False, order=20))
            dump_json(library_dir / "library.json", manifest)
            library = LibraryRuntime.open(library_dir)
            self.assertEqual(library.course_ids(), ["fixture_course"])
```

- [ ] **Step 3: Run RED**

```bash
python -m unittest tests.test_library_runtime -v
```

Expected: `ModuleNotFoundError` for `runtime.library_runtime`.

Regression baseline:

```bash
python -m unittest tests.test_book_runtime tests.test_course_runtime -v
```

Expected: PASS.

- [ ] **Step 4: Implement the minimum LibraryRuntime loader**

Create `runtime/library_runtime.py` with these public types:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .course_runtime import CourseRuntime, CourseRuntimeError


class LibraryRuntimeError(RuntimeError):
    """Base error for App-level course catalog loading."""


class LibraryManifestError(LibraryRuntimeError):
    """library.json violates the Phase 1C contract."""


class LibraryCourseResolutionError(LibraryRuntimeError):
    """Configured library/course paths are missing or untrusted."""


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
```

Implement this exact opening/root contract:

```python
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
        repo = cls._repository_root(root, repository_root)
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
    def _repository_root(library_dir: Path, explicit: str | Path | None) -> Path:
        if explicit is not None:
            repo = Path(explicit).resolve()
        else:
            if library_dir.name != "library":
                raise LibraryCourseResolutionError("Nonstandard library layout requires repository_root")
            repo = library_dir.parent.resolve()
        try:
            library_dir.relative_to(repo)
        except ValueError as exc:
            raise LibraryCourseResolutionError(f"Library directory escapes repository root: {library_dir}") from exc
        return repo
```

`_validate_manifest()` must enforce all RED cases above, including exact schema `library_manifest_v1`, required non-empty strings, boolean `enabled`, integer-but-not-bool `order`, non-empty courses, at least one enabled course, and unique enabled course IDs. Store every valid entry with its original manifest `position`.

`_resolve_course_path()` must resolve relative paths from `library_dir`, reject any resolved path outside `repository_root`, and require an enabled course path to be a directory.

`_open_courses()` must skip disabled entries, call `CourseRuntime.open(resolved_path)` for enabled entries, wrap `CourseRuntimeError` as `LibraryRuntimeBlockedError`, and reject `course.course_id != entry.course_id` as `LibraryManifestError`.

- [ ] **Step 5: Run GREEN + regressions**

```bash
python -m unittest tests.test_library_runtime -v
python -m unittest tests.test_book_runtime tests.test_course_runtime -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/runtime_fixture_factory.py tests/test_library_runtime.py runtime/library_runtime.py
git commit -m "feat: add fail-closed app library runtime"
```

---

### Task 2: Library Ordering, Catalog API, and Single-Book Product Profile

**Files:**
- Modify: `runtime/library_runtime.py`
- Modify: `tests/test_library_runtime.py`

**Interfaces:**
- Produces:
  - `course_ids() -> list[str]`
  - `courses() -> list[CourseRuntime]`
  - `course(course_id: str) -> CourseRuntime`
  - `summary() -> dict[str, Any]`
- Enforces `len(course.book_ids()) == 1` and `course.main_book().book_id == course.book_ids()[0]`.

- [ ] **Step 1: Add RED tests for deterministic catalog behavior and product profile**

Append:

```python
class LibraryRuntimeCatalogTests(LibraryRuntimeContractTests):
    def test_courses_are_ordered_by_order_then_manifest_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            write_ready_book(repo / "books" / "second", book_id="second_book")
            write_course(
                repo / "courses" / "second-course",
                course_id="second_course",
                book_entries=[main_book_entry("second_book", "../../books/second")],
                main_book_id="second_book",
            )
            manifest = self._manifest()
            manifest["courses"] = [
                self._entry(course_id="fixture_course", order=20),
                self._entry(course_id="second_course", path="../courses/second-course", order=10),
            ]
            dump_json(library_dir / "library.json", manifest)
            library = LibraryRuntime.open(library_dir)
            self.assertEqual(library.course_ids(), ["second_course", "fixture_course"])
            self.assertEqual([course.course_id for course in library.courses()], ["second_course", "fixture_course"])

    def test_equal_order_preserves_manifest_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            write_ready_book(repo / "books" / "second", book_id="second_book")
            write_course(
                repo / "courses" / "second-course",
                course_id="second_course",
                book_entries=[main_book_entry("second_book", "../../books/second")],
                main_book_id="second_book",
            )
            manifest = self._manifest()
            manifest["courses"] = [
                self._entry(course_id="fixture_course", order=10),
                self._entry(course_id="second_course", path="../courses/second-course", order=10),
            ]
            dump_json(library_dir / "library.json", manifest)
            self.assertEqual(LibraryRuntime.open(library_dir).course_ids(), ["fixture_course", "second_course"])

    def test_course_returns_already_mounted_course(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            library = LibraryRuntime.open(library_dir)
            self.assertIs(library.course("fixture_course"), library.courses()[0])

    def test_unknown_or_disabled_course_id_raises_library_error(self) -> None:
        from runtime.library_runtime import LibraryRuntimeError
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            library = LibraryRuntime.open(library_dir)
            with self.assertRaises(LibraryRuntimeError):
                library.course("missing")

    def test_multi_book_course_is_rejected_by_product_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            write_ready_book(repo / "books" / "supplementary", book_id="supp_book")
            course_path = repo / "courses" / "fixture-course" / "course.json"
            course = __import__("json").loads(course_path.read_text(encoding="utf-8"))
            course["books"].append(
                {
                    "book_id": "supp_book",
                    "role": "supplementary",
                    "path": "../../books/supplementary",
                    "required": True,
                    "enabled": True,
                }
            )
            dump_json(course_path, course)
            with self.assertRaises(LibraryManifestError):
                LibraryRuntime.open(library_dir)

    def test_exactly_one_main_book_course_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            course = LibraryRuntime.open(library_dir).course("fixture_course")
            self.assertEqual(course.book_ids(), ["fixture_book"])
            self.assertEqual(course.main_book().book_id, "fixture_book")

    def test_summary_reports_independent_courses(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            summary = LibraryRuntime.open(library_dir).summary()
            self.assertEqual(summary["library_id"], "fixture_library")
            self.assertEqual(summary["course_count"], 1)
            self.assertEqual(summary["courses"], [{"course_id": "fixture_course", "name": "fixture_course", "book_count": 1, "main_book_id": "fixture_book"}])
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_library_runtime.LibraryRuntimeCatalogTests -v
```

Expected: failures for missing catalog APIs/profile enforcement.

- [ ] **Step 3: Implement catalog API and profile gate**

Add:

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

    @staticmethod
    def _validate_product_profile(entry: LibraryCourseEntry, course: CourseRuntime) -> None:
        book_ids = course.book_ids()
        if len(book_ids) != 1:
            raise LibraryManifestError(
                f"Book App course {entry.course_id!r} must expose exactly one enabled book; found {len(book_ids)}"
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

Call `_validate_product_profile(entry, course)` after canonical course-ID validation and before adding the course to `_courses`.

- [ ] **Step 4: Run GREEN + regressions**

```bash
python -m unittest tests.test_library_runtime -v
python -m unittest tests.test_book_runtime tests.test_course_runtime -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

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
- Consumes `CourseRuntime.section()`, `CourseRuntime.main_book()`, `BookRuntime.objects_for_section()`, `BookRuntime.figures`, `BookRuntime.page_map_row()`, and `BookRuntime.translation_text()`.
- Produces:
  - `SectionLearningSource`
  - `SectionLearningRuntime.from_course(course: CourseRuntime, section_id: str)`
  - `source() -> SectionLearningSource`
  - `SectionLearningRuntimeError`, `SectionLearningSourceError`, `SectionLearningModeError`.

- [ ] **Step 1: Write RED source-projection tests with isolated fake runtime objects**

Create `tests/test_section_learning_runtime.py`:

```python
from __future__ import annotations

import unittest

from runtime.book_runtime import BookRuntimeError, RuntimeAnchor, RuntimeFigure, RuntimeObject, RuntimeSection
from runtime.section_learning_runtime import SectionLearningRuntime, SectionLearningSourceError


class FakeBook:
    book_id = "fixture_book"

    def __init__(self) -> None:
        self.figures = {
            "fig_2": RuntimeFigure(id="fig_2", anchor=RuntimeAnchor(pdf_page=2, source_anchor="fig-a2"), source_batch="b2"),
            "fig_out": RuntimeFigure(id="fig_out", anchor=RuntimeAnchor(pdf_page=9), source_batch="b9"),
            "fig_1": RuntimeFigure(id="fig_1", anchor=RuntimeAnchor(pdf_page=1, source_anchor="fig-a1"), source_batch="b1"),
        }
        self._objects = [
            RuntimeObject(id="def_1", type="definition", section_id="s1", name_en="Definition", anchor=RuntimeAnchor(pdf_page=1, printed_page=11, source_anchor="obj-a1"), source_batch="b1"),
            RuntimeObject(id="thm_1", type=" Theorem ", section_id="s1", name_en="Theorem", anchor=RuntimeAnchor(pdf_page=1, printed_page=11), source_batch="b1"),
            RuntimeObject(id="ex_1", type="exercise", section_id="s1", name_en="Exercise", anchor=RuntimeAnchor(pdf_page=2), source_batch="b2"),
            RuntimeObject(id="prob_1", type="PROBLEM", section_id="s1", name_en="Problem", anchor=RuntimeAnchor(pdf_page=2), source_batch="b2"),
            RuntimeObject(id="remark_1", type="remark", section_id="s1", name_en="Remark", anchor=RuntimeAnchor(pdf_page=2), source_batch="b2"),
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
            raise BookRuntimeError(f"Unknown section: {section_id}")
        return self._section


class SectionLearningSourceTests(unittest.TestCase):
    def test_known_section_builds_source_with_canonical_identity(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual((source.course_id, source.book_id, source.chapter_id, source.section_id), ("fixture_course", "fixture_book", "chapter_01", "s1"))

    def test_unknown_section_fails_explicitly(self) -> None:
        with self.assertRaises(SectionLearningSourceError):
            SectionLearningRuntime.from_course(FakeCourse(), "missing")

    def test_source_objects_preserve_book_runtime_order(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual([row["id"] for row in source.objects], ["def_1", "thm_1", "ex_1", "prob_1", "remark_1"])

    def test_figures_include_only_in_range_and_sort_by_page_then_id(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual([row["id"] for row in source.figures], ["fig_1", "fig_2"])

    def test_page_map_boundaries_are_preserved(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual(source.page_map_start["printed_page"], "11")
        self.assertEqual(source.page_map_end["printed_page"], "12")

    def test_missing_optional_anchor_is_not_fabricated(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        theorem = next(row for row in source.objects if row["id"] == "thm_1")
        self.assertIsNone(theorem["source_anchor"])

    def test_translation_availability_is_stable_deduplicated_and_contains_no_sliced_text(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual(source.translation_sources, [{"batch_id": "b1", "available": True}, {"batch_id": "b2", "available": False}])
        self.assertTrue(all(set(row) == {"batch_id", "available"} for row in source.translation_sources))
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_section_learning_runtime.SectionLearningSourceTests -v
```

Expected: module import failure.

- [ ] **Step 3: Implement source types and projection**

Create `runtime/section_learning_runtime.py`:

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

`SectionLearningRuntime.from_course()` must resolve only `course.section(section_id)`, wrap `BookRuntimeError` as `SectionLearningSourceError`, then use `course.main_book()` for evidence.

Object projection keys are exactly:

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

Figure projection keys are exactly:

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

Include a figure only when its anchored PDF page lies inside both non-null Section PDF boundaries. Missing boundaries or missing figure PDF page must not be guessed. Sort included figures by `(pdf_page, id)`.

Stable-deduplicate `section.source_batches` in original order and expose only:

```python
{"batch_id": batch_id, "available": book.translation_text(batch_id) is not None}
```

Never copy translation Markdown text into `SectionLearningSource`.

- [ ] **Step 4: Run GREEN + regressions**

```bash
python -m unittest tests.test_section_learning_runtime.SectionLearningSourceTests -v
python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/section_learning_runtime.py tests/test_section_learning_runtime.py
git commit -m "feat: project source-backed section learning data"
```

---

### Task 4: Deterministic Preview, Learn, Review, and Practice Payloads

**Files:**
- Modify: `runtime/section_learning_runtime.py`
- Modify: `tests/test_section_learning_runtime.py`

**Interfaces:**
- Produces:
  - `preview() -> dict[str, Any]`
  - `learn() -> dict[str, Any]`
  - `review() -> dict[str, Any]`
  - `practice() -> dict[str, Any]`
- Review policy after `strip().casefold()`: `definition`, `theorem`, `proposition`, `lemma`, `corollary`, `formula`.
- Practice policy after `strip().casefold()`: `exercise`, `problem`.
- Every item traces back by `(kind, source_id)`.

- [ ] **Step 1: Add RED mode tests**

Append:

```python
class SectionLearningModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.learning = SectionLearningRuntime.from_course(FakeCourse(), "s1")

    def test_preview_preserves_identity_and_compact_source_metadata(self) -> None:
        payload = self.learning.preview()
        self.assertEqual(payload["mode"], "preview")
        self.assertEqual((payload["course_id"], payload["book_id"], payload["chapter_id"], payload["section_id"]), ("fixture_course", "fixture_book", "chapter_01", "s1"))
        object_item = next(row for row in payload["items"] if row["kind"] == "object" and row["source_id"] == "def_1")
        translation_item = next(row for row in payload["items"] if row["kind"] == "translation" and row["source_id"] == "b1")
        self.assertEqual(object_item["object_type"], "definition")
        self.assertIs(translation_item["available"], True)

    def test_learn_references_all_source_objects_figures_and_translations_in_order(self) -> None:
        source = self.learning.source()
        payload = self.learning.learn()
        expected = (
            [("object", row["id"]) for row in source.objects]
            + [("figure", row["id"]) for row in source.figures]
            + [("translation", row["batch_id"]) for row in source.translation_sources]
        )
        self.assertEqual([(row["kind"], row["source_id"]) for row in payload["items"]], expected)

    def test_review_uses_exact_normalized_policy_and_preserves_source_type(self) -> None:
        payload = self.learning.review()
        source = self.learning.source()
        by_id = {row["id"]: row for row in source.objects}
        self.assertEqual([row["source_id"] for row in payload["items"]], ["def_1", "thm_1"])
        self.assertEqual(by_id["thm_1"]["type"], " Theorem ")

    def test_practice_uses_only_exact_exercise_problem_policy(self) -> None:
        payload = self.learning.practice()
        self.assertEqual([row["source_id"] for row in payload["items"]], ["ex_1", "prob_1"])

    def test_empty_review_and_practice_subsets_are_valid(self) -> None:
        course = FakeCourse()
        course._book._objects = [RuntimeObject(id="remark_only", type="remark", section_id="s1")]
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
                [{"kind": item["kind"], "source_id": item["source_id"]} for item in payload["items"]],
            )

    def test_modes_have_no_ordering_lock(self) -> None:
        fresh = SectionLearningRuntime.from_course(FakeCourse(), "s1")
        self.assertEqual(
            [fresh.practice()["mode"], fresh.preview()["mode"], fresh.review()["mode"], fresh.learn()["mode"]],
            ["practice", "preview", "review", "learn"],
        )
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_section_learning_runtime.SectionLearningModeTests -v
```

Expected: missing-mode-method failures.

- [ ] **Step 3: Implement exact mode contracts**

Add:

```python
REVIEW_TYPES = frozenset({"definition", "theorem", "proposition", "lemma", "corollary", "formula"})
PRACTICE_TYPES = frozenset({"exercise", "problem"})
```

Common envelope:

```python
    def _envelope(self, mode: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "mode": mode,
            "course_id": self._source.course_id,
            "book_id": self._source.book_id,
            "chapter_id": self._source.chapter_id,
            "section_id": self._source.section_id,
            "source_status": "available",
            "items": items,
            "source_refs": [
                {"kind": str(item["kind"]), "source_id": str(item["source_id"])}
                for item in items
            ],
        }
```

Preview must be a compact index, not a duplicate of Learn:

```python
    def preview(self) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        items.extend(
            {"kind": "object", "source_id": row["id"], "object_type": row["type"]}
            for row in self._source.objects
        )
        items.extend(
            {"kind": "figure", "source_id": row["id"]}
            for row in self._source.figures
        )
        items.extend(
            {"kind": "translation", "source_id": row["batch_id"], "available": row["available"]}
            for row in self._source.translation_sources
        )
        return self._envelope("preview", items)
```

Learn contains source references only and preserves source order:

```python
    def learn(self) -> dict[str, Any]:
        items = (
            [{"kind": "object", "source_id": row["id"]} for row in self._source.objects]
            + [{"kind": "figure", "source_id": row["id"]} for row in self._source.figures]
            + [{"kind": "translation", "source_id": row["batch_id"]} for row in self._source.translation_sources]
        )
        return self._envelope("learn", items)
```

Review/Practice:

```python
    def review(self) -> dict[str, Any]:
        items = [
            {"kind": "object", "source_id": row["id"]}
            for row in self._source.objects
            if str(row.get("type") or "").strip().casefold() in REVIEW_TYPES
        ]
        return self._envelope("review", items)

    def practice(self) -> dict[str, Any]:
        items = [
            {"kind": "object", "source_id": row["id"]}
            for row in self._source.objects
            if str(row.get("type") or "").strip().casefold() in PRACTICE_TYPES
        ]
        return self._envelope("practice", items)
```

Do not copy formula/text/anchor facts into mode items. Consumers dereference `(kind, source_id)` against `source()`.

- [ ] **Step 4: Run GREEN + regressions**

```bash
python -m unittest tests.test_section_learning_runtime -v
python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/section_learning_runtime.py tests/test_section_learning_runtime.py
git commit -m "feat: add deterministic section learning modes"
```

---

### Task 5: Real Functional Analysis Library Fixture + Package Exports

**Files:**
- Create: `library/library.json`
- Modify: `runtime/__init__.py`
- Modify: `tests/test_library_runtime.py`
- Modify: `tests/test_section_learning_runtime.py`

**Interfaces:**
- Produces clean-checkout path: `LibraryRuntime.open("library") → functional_analysis_course → ch01_s01 → four modes`.

- [ ] **Step 1: Add RED real-fixture tests**

Append to `tests/test_library_runtime.py`:

```python
class RealLibraryFixtureTests(unittest.TestCase):
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
class RealSectionLearningFixtureTests(unittest.TestCase):
    def test_real_ch01_s01_builds_all_modes(self) -> None:
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
        for payload in (learning.preview(), learning.learn(), learning.review(), learning.practice()):
            self.assertEqual(payload["course_id"], source.course_id)
            self.assertEqual(payload["book_id"], source.book_id)
            self.assertEqual(payload["chapter_id"], source.chapter_id)
            self.assertEqual(payload["section_id"], source.section_id)

    def test_runtime_package_exports_section_learning_runtime(self) -> None:
        from runtime import SectionLearningRuntime as ExportedSectionLearningRuntime
        self.assertIs(ExportedSectionLearningRuntime, SectionLearningRuntime)
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_library_runtime tests.test_section_learning_runtime -v
```

Expected: failures for missing `library/library.json` and package exports.

- [ ] **Step 3: Create exact real library manifest**

Create `library/library.json`:

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

- [ ] **Step 4: Export all new public runtime symbols**

Extend `runtime/__init__.py` without removing existing exports:

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

Add those names to `__all__`.

- [ ] **Step 5: Run GREEN + real acceptance**

```bash
python -m unittest tests.test_library_runtime tests.test_section_learning_runtime -v
python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime tests.test_section_learning_runtime -v
```

Expected: PASS, including 8 Chapters, 132 Sections, 442 PageMap rows, 1493 search records, and real `ch01_s01` learning source/modes.

- [ ] **Step 6: Commit**

```bash
git add library/library.json runtime/__init__.py tests/test_library_runtime.py tests/test_section_learning_runtime.py
git commit -m "feat: wire Functional Analysis into the app library"
```

---

### Task 6: CI + Documentation + Final Integration Gate

**Files:**
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Modify: `runtime/README.md`
- Modify: `README.md`

**Interfaces:**
- Consumes all Phase 1C runtime APIs.
- Produces CI evidence and product/runtime documentation suitable for a PR.

- [ ] **Step 1: Extend CI path filters**

Add to both `push.paths` and `pull_request.paths`:

```yaml
      - "library/**"
```

- [ ] **Step 2: Compile and test the new runtime modules in the existing workflow**

Add to `Compile reference runtime`:

```yaml
          python -m py_compile runtime/library_runtime.py
          python -m py_compile runtime/section_learning_runtime.py
```

Use this exact unit-test command:

```yaml
      - name: Run unit tests
        run: python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime tests.test_section_learning_runtime tests.test_functional_analysis_page_map tests.test_continuation_integrity tests.test_runtime_object_merge tests.test_functional_analysis_identity_normalizer tests.test_functional_analysis_figure_normalizer -v
```

- [ ] **Step 3: Extend Python 3.13 real acceptance without weakening recovery checks**

Keep all existing rebuild/readiness commands and PageMap assertions. Extend the final acceptance Python code with:

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

Add `library_runtime_open: true` and `section_learning_runtime_open: true` to printed CI evidence.

- [ ] **Step 4: Update `runtime/README.md`**

Document this chain:

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

Add this exact usage pattern:

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

State explicitly that Product-level LibraryRuntime admits one textbook per course, generic CourseRuntime keeps multi-book compatibility below it, and Phase 1C modes only reference source-backed data. Keep the `STRUCTURED_COMPLETE` vs `RUNTIME_READY` distinction intact.

- [ ] **Step 5: Correct root `README.md` product model**

Replace the outdated product principle:

```text
一门课程支持多本教材：主教材、辅助教材、英文教材、参考教材。
```

with:

```text
一个 Book App 支持多门彼此独立的教材课程；当前产品形态下每门课程对应一本教材，例如泛函分析、实分析分别作为独立课程加入同一个 App。
```

Mark Phase 1B as completed/integrated and Phase 1C as current. Preserve broader future architecture documents; describe generic CourseRuntime multi-book support only as lower-level compatibility.

- [ ] **Step 6: Run full verification**

```bash
python -m py_compile runtime/book_runtime.py runtime/course_runtime.py runtime/library_runtime.py runtime/section_learning_runtime.py
python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime tests.test_section_learning_runtime tests.test_functional_analysis_page_map tests.test_continuation_integrity tests.test_runtime_object_merge tests.test_functional_analysis_identity_normalizer tests.test_functional_analysis_figure_normalizer -v
python tools/check_runtime_readiness.py books/functional-analysis
python -c "from runtime import LibraryRuntime,SectionLearningRuntime; l=LibraryRuntime.open('library'); c=l.course('functional_analysis_course'); s=SectionLearningRuntime.from_course(c,'ch01_s01'); assert l.course_ids()==['functional_analysis_course']; assert c.book_ids()==['stein_shakarchi_functional_analysis_2011']; assert len(c.chapter_ids())==8; assert sum(len(c.sections_for_chapter(x)) for x in c.chapter_ids())==132; assert len(c.main_book().page_map)==442; assert sum(1 for _ in c.main_book().iter_search_records())==1493; assert [s.preview()['mode'],s.learn()['mode'],s.review()['mode'],s.practice()['mode']]==['preview','learn','review','practice']; print('Phase 1C acceptance PASS')"
```

Expected: all commands succeed and runtime readiness remains `READY`.

- [ ] **Step 7: Verify scope/no textbook source mutation**

```bash
git diff --name-only main...HEAD
```

Implementation diff may contain only the Phase 1C spec/plan and:

```text
library/library.json
runtime/library_runtime.py
runtime/section_learning_runtime.py
runtime/__init__.py
tests/runtime_fixture_factory.py
tests/test_library_runtime.py
tests/test_section_learning_runtime.py
.github/workflows/runtime-reference-tests.yml
runtime/README.md
README.md
```

No `books/functional-analysis/*_structure.json`, `books/functional-analysis/chunks/*`, PageMap, TOC, search index, or other textbook source asset may appear.

- [ ] **Step 8: Commit CI/docs**

```bash
git add .github/workflows/runtime-reference-tests.yml runtime/README.md README.md
git commit -m "docs: integrate Phase 1C runtime path"
```

- [ ] **Step 9: Require GitHub Actions evidence**

Push the feature branch and require the existing `Runtime reference tests` workflow to finish successfully on Python 3.11, 3.12, and 3.13. The 3.13 job must retain the real Functional Analysis rebuild/readiness checks and pass the new Library → Course → `ch01_s01` SectionLearning acceptance.

- [ ] **Step 10: Open PR, do not merge**

PR title:

```text
Add App library and Section learning runtime
```

PR body must report:

```text
- one App / many independent courses product model
- one enabled textbook per admitted product course
- Functional Analysis as first real library fixture
- ch01_s01 source-backed Preview/Learn/Review/Practice
- no AI-generated textbook content in Phase 1C
- Python 3.11/3.12/3.13 CI result
- 8 Chapters / 132 Sections / 442 PageMap rows / 1493 search records retained
- no Functional Analysis structured source assets changed
```

Do not merge without explicit user approval.

## Plan Self-Review

- **Spec coverage:** All 44 minimum test intentions are represented: library schema/name/entries/enabled/path/root/ID/readiness/disabled/order/profile; Section identity/object order/figures/PageMap/missing anchors/translations; Preview/Learn/Review/Practice policy/empty subsets/traceability/no lock; real library/course/book/chapter/section/PageMap/search acceptance.
- **Placeholder scan:** No `TBD`, `TODO`, “implement later”, “similar to Task N”, or unspecified validation/test steps remain.
- **Type consistency:** `LibraryRuntime.open(..., repository_root=...)`, `course_ids()`, `courses()`, `course()`, `summary()`, `SectionLearningRuntime.from_course()`, `source()`, `preview()`, `learn()`, `review()`, and `practice()` use one consistent spelling/signature throughout.
- **Preview/Learn distinction:** Preview explicitly carries compact object-type and translation-availability metadata; Learn is the ordered complete source-reference view.
- **Traceability:** All mode items preserve `(kind, source_id)` and `source_refs` strips any presentation metadata back to that canonical pair.
- **Scope:** LibraryRuntime and SectionLearningRuntime remain separate focused modules/tasks, but one implementation plan is appropriate because the acceptance deliverable is the single end-to-end App path `Library → Course → ch01_s01 → four modes`.
