# Foundation A Course Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, machine-verifiable Course Package v1 foundation around the existing read-only Runtime, freeze Functional Analysis as the Golden Course, and make the contract executable in CI without changing App consumption yet.

**Architecture:** Add a new root-level `course_package` package that reads existing `courses/**` and canonical `books/**`, normalizes the legacy course manifest, inventories and hashes canonical artifacts, compiles deterministic package documents, and validates them fail-closed. Keep `BookRuntime`, `CourseRuntime`, `LibraryRuntime`, FastAPI, and the React client on their existing paths; Foundation A is a validation/release layer first. Generated packages go only to `.build/course-packages/<course_id>/<package_identity>/` and never rewrite canonical textbook assets.

**Tech Stack:** Python 3.11–3.13 standard library (`dataclasses`, `hashlib`, `json`, `pathlib`, `unittest`, `tempfile`, `subprocess`), existing Book Runtime, JSON Schema documents, GitHub Actions, existing Node 22/Vitest/TypeScript/Vite/Playwright gates.

**Spec:** `docs/superpowers/specs/2026-08-28-foundation-a-course-package-design.md`

## Global Constraints

- Existing `course_manifest_v1`, `BookRuntime`, `CourseRuntime`, `LibraryRuntime`, FastAPI, and App remain the product runtime path during Foundation A.
- Canonical Course Package roles are exactly `primary / supplementary / reference / translation`.
- A valid package has exactly one enabled `primary` book.
- Legacy role aliases are normalized only at the compatibility boundary: `main -> primary`, `supplementary -> supplementary`, `reference -> reference`, `english -> translation`.
- Compiler and validator are read-only toward `books/**` and `courses/**`.
- No Foundation A implementation step may modify `books/functional-analysis/**` canonical assets.
- Generated output lives under `.build/course-packages/<course_id>/<package_identity>/`; an existing generated file may only be reused if bytes are identical, otherwise compilation fails closed.
- Package identity must exclude timestamps, random UUIDs, machine-specific absolute paths, and temporary-directory paths.
- Package identity is SHA-256 over canonical UTF-8 JSON using sorted keys and compact separators.
- The first implementation remains Python-standard-library-only; do not add a runtime or test dependency solely for JSON Schema validation.
- JSON Schema documents are the published contract; Python validation code and schema documents must be cross-checked by tests so their required fields/enums cannot drift silently.
- Package readiness is exactly `PASS / WARN / FAIL`; trust-breaking problems fail closed.
- Golden Course baseline is fixed at `functional_analysis_course`, `stein_shakarchi_functional_analysis_2011`, 8 chapters, 132 sections, 1493 search records, 442 PDF pages, printed final page 423, `STRUCTURED_COMPLETE`, Runtime `READY`.
- Do not implement PDF/OCR/AI extraction, Concept Graph, ConceptAlignment, Unified Retrieval, ExamPoint, Lecture/ASR, Drive Sync, Meeting, Android, multi-book UI, or App migration in this plan.
- Use TDD for every behavior change: RED test, verify RED, minimal GREEN implementation, verify GREEN, then commit.
- Before execution, create an isolated worktree or equivalent clean checkout for `foundation/course-package-contract-a`; do not work directly on `main`.
- Before each new write task/session, satisfy the repository security gate from `SECURITY_POLICY.md` and the Drive global safety baseline.
- No force push, history rewrite, canonical-asset cleanup, branch deletion, or automatic PR merge.

---

## File Structure Locked by This Plan

Create:

```text
course_package/
├── __init__.py              # public Foundation A API
├── contracts.py             # constants, dataclasses, canonical JSON helpers
├── manifest.py              # legacy course_manifest_v1 normalization
├── artifacts.py             # safe path resolution, SHA-256 inventory, content identity
├── compiler.py              # deterministic package assembly and additive write-out
├── validator.py             # fail-closed package validation and diagnostics
├── golden.py                # Functional Analysis Golden Course baseline/gate
└── fitness.py               # executable architecture fitness checks

schemas/course-package/
├── course-package-v1.schema.json
├── books-v1.schema.json
├── artifacts-v1.schema.json
└── readiness-v1.schema.json

tools/
├── compile_course_package.py
├── validate_course_package.py
└── check_architecture_fitness.py

tests/
├── test_course_package_schema.py
├── test_course_manifest_normalization.py
├── test_course_package_artifacts.py
├── test_course_package_compiler.py
├── test_course_package_validator.py
├── test_golden_course_package.py
├── test_architecture_fitness.py
└── test_course_package_cli.py

tests/golden/
└── functional_analysis_course_package_baseline.json

.github/workflows/
├── course-package-fast.yml
└── course-package-heavy.yml
```

Modify only when the corresponding task is reached:

```text
.gitignore
.github/workflows/runtime-reference-tests.yml
.github/workflows/app-ui-tests.yml
docs/CURRENT_STATE.md
docs/ROADMAP.md
docs/DEVELOPMENT_STRATEGY.md
```

Do not modify:

```text
books/functional-analysis/**
runtime/book_runtime.py
runtime/course_runtime.py
runtime/library_runtime.py
app/**         # except existing CI executes it; no source migration in Foundation A
```

---

### Task 1: Publish Course Package v1 Contract and Schema Documents

**Files:**
- Create: `course_package/__init__.py`
- Create: `course_package/contracts.py`
- Create: `schemas/course-package/course-package-v1.schema.json`
- Create: `schemas/course-package/books-v1.schema.json`
- Create: `schemas/course-package/artifacts-v1.schema.json`
- Create: `schemas/course-package/readiness-v1.schema.json`
- Create: `tests/test_course_package_schema.py`

**Interfaces:**
- Produces: `SCHEMA_VERSION: str = "course_package_v1"`
- Produces: `PACKAGE_VERSION: str = "1.0.0"`
- Produces: `CANONICAL_BOOK_ROLES: frozenset[str]`
- Produces: `READINESS_STATUSES: frozenset[str]`
- Produces: `PACKAGE_FILENAMES: tuple[str, ...]`
- Produces: `canonical_json_bytes(value: Any) -> bytes`
- Produces: `sha256_bytes(value: bytes) -> str`
- Produces: frozen `PackageDiagnostic(code: str, severity: str, detail: str, relative_path: str | None = None)`
- Produces: frozen `PackageValidationResult(status: str, diagnostics: tuple[PackageDiagnostic, ...])`

- [ ] **Step 1: Write failing contract/schema tests**

Create `tests/test_course_package_schema.py` with tests that parse all four schema files and assert constants cannot drift from the published enums/version:

```python
import json
import unittest
from pathlib import Path

from course_package.contracts import (
    CANONICAL_BOOK_ROLES,
    PACKAGE_FILENAMES,
    PACKAGE_VERSION,
    READINESS_STATUSES,
    SCHEMA_VERSION,
    canonical_json_bytes,
    sha256_bytes,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "course-package"


class CoursePackageSchemaTests(unittest.TestCase):
    def test_contract_constants_are_frozen(self):
        self.assertEqual(SCHEMA_VERSION, "course_package_v1")
        self.assertEqual(PACKAGE_VERSION, "1.0.0")
        self.assertEqual(
            CANONICAL_BOOK_ROLES,
            frozenset({"primary", "supplementary", "reference", "translation"}),
        )
        self.assertEqual(READINESS_STATUSES, frozenset({"PASS", "WARN", "FAIL"}))
        self.assertEqual(
            PACKAGE_FILENAMES,
            (
                "course_package.json",
                "books.json",
                "artifacts.json",
                "chapters.json",
                "sections.json",
                "readiness.json",
                "package.sha256",
            ),
        )

    def test_published_schemas_match_contract_enums(self):
        course_schema = json.loads(
            (SCHEMAS / "course-package-v1.schema.json").read_text(encoding="utf-8")
        )
        books_schema = json.loads(
            (SCHEMAS / "books-v1.schema.json").read_text(encoding="utf-8")
        )
        readiness_schema = json.loads(
            (SCHEMAS / "readiness-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(course_schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)
        self.assertEqual(course_schema["properties"]["package_version"]["const"], PACKAGE_VERSION)
        self.assertEqual(
            set(books_schema["$defs"]["book"]["properties"]["role"]["enum"]),
            set(CANONICAL_BOOK_ROLES),
        )
        self.assertEqual(
            set(readiness_schema["properties"]["status"]["enum"]),
            set(READINESS_STATUSES),
        )

    def test_canonical_json_is_stable(self):
        left = {"b": 2, "a": {"y": False, "x": 1}}
        right = {"a": {"x": 1, "y": False}, "b": 2}
        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(right))
        self.assertEqual(
            sha256_bytes(canonical_json_bytes(left)),
            sha256_bytes(canonical_json_bytes(right)),
        )
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python -m unittest tests.test_course_package_schema -v
```

Expected: FAIL because `course_package` and schema files do not exist.

- [ ] **Step 3: Implement the contract constants/helpers**

Create `course_package/contracts.py`:

```python
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "course_package_v1"
PACKAGE_VERSION = "1.0.0"
CANONICAL_BOOK_ROLES = frozenset({"primary", "supplementary", "reference", "translation"})
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
```

Create `course_package/__init__.py` exporting the public constants and later public compiler/validator entry points.

- [ ] **Step 4: Create the four JSON Schema documents with explicit closed-object contracts**

Use JSON Schema 2020-12 metadata and `additionalProperties: false` for contract objects. The required top-level shapes are:

```json
// course-package-v1.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "book://schemas/course-package/course-package-v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version", "package_version", "course_id", "course_name", "language",
    "primary_book_id", "book_ids", "chapter_count", "section_count",
    "search_record_count", "package_identity", "readiness"
  ],
  "properties": {
    "schema_version": {"const": "course_package_v1"},
    "package_version": {"const": "1.0.0"},
    "course_id": {"type": "string", "minLength": 1},
    "course_name": {"type": "string", "minLength": 1},
    "language": {"type": "string", "minLength": 1},
    "primary_book_id": {"type": "string", "minLength": 1},
    "book_ids": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
    "chapter_count": {"type": "integer", "minimum": 0},
    "section_count": {"type": "integer", "minimum": 0},
    "search_record_count": {"type": "integer", "minimum": 0},
    "package_identity": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "readiness": {"enum": ["PASS", "WARN", "FAIL"]}
  }
}
```

```json
// books-v1.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "book://schemas/course-package/books-v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "books"],
  "properties": {
    "schema_version": {"const": "course_package_v1"},
    "books": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/book"}}
  },
  "$defs": {
    "book": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "book_id", "logical_book_id", "book_version_id", "role", "canonical_path",
        "enabled", "required", "structured_status", "structured_version", "runtime_status",
        "pdf_page_count", "printed_final_page", "content_identity"
      ],
      "properties": {
        "book_id": {"type": "string", "minLength": 1},
        "logical_book_id": {"type": "string", "minLength": 1},
        "book_version_id": {"type": "string", "minLength": 1},
        "role": {"enum": ["primary", "supplementary", "reference", "translation"]},
        "canonical_path": {"type": "string", "minLength": 1},
        "enabled": {"type": "boolean"},
        "required": {"type": "boolean"},
        "structured_status": {"type": "string", "minLength": 1},
        "structured_version": {"type": "string", "minLength": 1},
        "runtime_status": {"type": "string", "minLength": 1},
        "pdf_page_count": {"type": "integer", "minimum": 0},
        "printed_final_page": {"type": ["integer", "string"]},
        "content_identity": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
      }
    }
  }
}
```

```json
// artifacts-v1.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "book://schemas/course-package/artifacts-v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "artifacts"],
  "properties": {
    "schema_version": {"const": "course_package_v1"},
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["artifact_type", "relative_path", "sha256", "size_bytes", "required", "book_id"],
        "properties": {
          "artifact_type": {"enum": ["book_metadata", "structured_complete", "audit_report", "toc", "page_map", "search_index", "qa_policy", "structure", "readiness"]},
          "relative_path": {"type": "string", "minLength": 1},
          "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
          "size_bytes": {"type": "integer", "minimum": 0},
          "required": {"type": "boolean"},
          "book_id": {"type": "string", "minLength": 1}
        }
      }
    }
  }
}
```

```json
// readiness-v1.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "book://schemas/course-package/readiness-v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "status", "diagnostics"],
  "properties": {
    "schema_version": {"const": "course_package_v1"},
    "status": {"enum": ["PASS", "WARN", "FAIL"]},
    "diagnostics": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["code", "severity", "detail"],
        "properties": {
          "code": {"type": "string", "minLength": 1},
          "severity": {"enum": ["WARN", "FAIL"]},
          "detail": {"type": "string", "minLength": 1},
          "relative_path": {"type": ["string", "null"]}
        }
      }
    }
  }
}
```

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
python -m unittest tests.test_course_package_schema -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

```bash
git add course_package schemas/course-package tests/test_course_package_schema.py
git commit -m "feat: define course package v1 contract"
```

---

### Task 2: Normalize Legacy `course_manifest_v1` Into Canonical Package Roles

**Files:**
- Create: `course_package/manifest.py`
- Create: `tests/test_course_manifest_normalization.py`
- Test fixture source: `courses/functional-analysis/course.json`

**Interfaces:**
- Consumes: Task 1 role/version constants.
- Produces: frozen `NormalizedBookEntry`.
- Produces: frozen `NormalizedCourseManifest`.
- Produces: `normalize_course_manifest(course_dir: Path, repository_root: Path) -> NormalizedCourseManifest`.
- Compatibility identity rule: legacy `logical_book_id = book_id`; legacy `book_version_id = f"{book_id}@{structured_version}"` where `structured_version` comes from canonical `STRUCTURED_COMPLETE.json` and must be non-empty.
- `canonical_path` is POSIX repository-relative, e.g. `books/functional-analysis`; absolute paths are rejected.

- [ ] **Step 1: Write failing normalization tests**

Create tests covering real Functional Analysis plus synthetic role/path failures:

```python
import json
import tempfile
import unittest
from pathlib import Path

from course_package.manifest import ManifestNormalizationError, normalize_course_manifest

ROOT = Path(__file__).resolve().parents[1]


class CourseManifestNormalizationTests(unittest.TestCase):
    def test_real_legacy_manifest_normalizes_main_to_primary(self):
        normalized = normalize_course_manifest(
            ROOT / "courses" / "functional-analysis",
            ROOT,
        )
        self.assertEqual(normalized.course_id, "functional_analysis_course")
        self.assertEqual(normalized.primary_book_id, "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(len(normalized.books), 1)
        book = normalized.books[0]
        self.assertEqual(book.role, "primary")
        self.assertEqual(book.canonical_path, "books/functional-analysis")
        self.assertEqual(book.logical_book_id, book.book_id)
        self.assertEqual(book.book_version_id, f"{book.book_id}@v0.36")

    def test_path_escape_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            course = repo / "courses" / "bad"
            course.mkdir(parents=True)
            (course / "course.json").write_text(json.dumps({
                "schema_version": "course_manifest_v1",
                "course_id": "bad",
                "name": "Bad",
                "language": "en",
                "main_book_id": "bad_book",
                "books": [{
                    "book_id": "bad_book",
                    "role": "main",
                    "path": "../../../outside",
                    "required": True,
                    "enabled": True,
                }],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ManifestNormalizationError, "escapes repository root"):
                normalize_course_manifest(course, repo)
```

Also add explicit tests for unsupported legacy role, duplicate enabled book IDs, zero enabled primary, and two enabled primary books.

- [ ] **Step 2: Run focused tests and verify RED**

```bash
python -m unittest tests.test_course_manifest_normalization -v
```

Expected: FAIL because `course_package.manifest` does not exist.

- [ ] **Step 3: Implement dataclasses and normalization**

Create `course_package/manifest.py` with this public shape:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROLE_ALIASES = {
    "main": "primary",
    "supplementary": "supplementary",
    "reference": "reference",
    "english": "translation",
}


class ManifestNormalizationError(RuntimeError):
    pass


@dataclass(frozen=True)
class NormalizedBookEntry:
    book_id: str
    logical_book_id: str
    book_version_id: str
    role: str
    canonical_path: str
    required: bool
    enabled: bool
    structured_version: str


@dataclass(frozen=True)
class NormalizedCourseManifest:
    course_id: str
    course_name: str
    language: str
    primary_book_id: str
    books: tuple[NormalizedBookEntry, ...]
```

Normalization must resolve `(course_dir / raw_path).resolve()`, require `.relative_to(repository_root.resolve())`, require the target book directory, read `STRUCTURED_COMPLETE.json`, require matching `book_id`, require non-empty `version`, normalize separators with `.as_posix()`, and enforce exactly one enabled primary matching legacy `main_book_id`.

- [ ] **Step 4: Run normalization tests and verify GREEN**

```bash
python -m unittest tests.test_course_manifest_normalization -v
```

Expected: PASS.

- [ ] **Step 5: Run existing CourseRuntime tests to prove compatibility was not changed**

```bash
python -m unittest tests.test_course_runtime -v
```

Expected: PASS with the existing legacy manifest unchanged.

- [ ] **Step 6: Commit Task 2**

```bash
git add course_package/manifest.py tests/test_course_manifest_normalization.py
git commit -m "feat: normalize legacy course manifests"
```

---

### Task 3: Build Safe Canonical Artifact Inventory and Book Content Identity

**Files:**
- Create: `course_package/artifacts.py`
- Create: `tests/test_course_package_artifacts.py`
- Reuse read-only sources: `tools/check_runtime_readiness.py`, `runtime/book_runtime.py`

**Interfaces:**
- Produces: frozen `ArtifactRecord(artifact_type, relative_path, sha256, size_bytes, required, book_id)`.
- Produces: `sha256_file(path: Path) -> str`.
- Produces: `repository_relative(path: Path, repository_root: Path) -> str`.
- Produces: `build_book_artifact_inventory(repository_root: Path, canonical_book_path: str, book_id: str) -> tuple[ArtifactRecord, ...]`.
- Produces: `compute_content_identity(records: tuple[ArtifactRecord, ...]) -> str`.
- Required artifact set is derived from canonical metadata/completion, not guessed filenames.
- Structure artifacts include every sorted `*_structure.json` under the Book root, excluding `RUNTIME_READINESS.json`.

- [ ] **Step 1: Write failing inventory/hash tests**

Tests must assert the real Golden Book inventory contains all nine artifact categories and all paths stay under `books/functional-analysis`:

```python
from course_package.artifacts import (
    ArtifactInventoryError,
    build_book_artifact_inventory,
    compute_content_identity,
)


def test_real_inventory(self):
    records = build_book_artifact_inventory(
        ROOT,
        "books/functional-analysis",
        "stein_shakarchi_functional_analysis_2011",
    )
    categories = {record.artifact_type for record in records}
    self.assertTrue({
        "book_metadata", "structured_complete", "audit_report", "toc",
        "page_map", "search_index", "qa_policy", "structure", "readiness",
    }.issubset(categories))
    self.assertTrue(all(r.relative_path.startswith("books/functional-analysis/") for r in records))
    self.assertRegex(compute_content_identity(records), r"^[0-9a-f]{64}$")
```

Add tests that a missing required artifact raises `ArtifactInventoryError`, a symlink/path escape is rejected where supported by the platform, and the same records in different input order produce the same content identity.

- [ ] **Step 2: Run focused tests and verify RED**

```bash
python -m unittest tests.test_course_package_artifacts -v
```

Expected: FAIL because `course_package.artifacts` does not exist.

- [ ] **Step 3: Implement safe path and hash helpers**

Core behavior:

```python
def repository_relative(path: Path, repository_root: Path) -> str:
    root = repository_root.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ArtifactInventoryError(f"artifact path escapes repository root: {resolved}") from exc
    return relative.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
```

Build required paths from:

```text
book_metadata.json
STRUCTURED_COMPLETE.json
completion.audit_report
metadata.toc_file
metadata.page_map_file
completion.search_index
qa_retrieval_policy.json
RUNTIME_READINESS.json
sorted *_structure.json files
```

Every record gets exact file size from `stat().st_size` and SHA-256 over raw bytes.

- [ ] **Step 4: Compute deterministic book content identity**

Identity input is only:

```python
[
    {
        "artifact_type": r.artifact_type,
        "relative_path": r.relative_path,
        "sha256": r.sha256,
        "size_bytes": r.size_bytes,
        "required": r.required,
        "book_id": r.book_id,
    }
    for r in sorted(records, key=lambda x: (x.relative_path, x.artifact_type))
]
```

Hash `canonical_json_bytes(identity_input)` with `sha256_bytes`.

- [ ] **Step 5: Run focused tests and existing readiness checker**

```bash
python -m unittest tests.test_course_package_artifacts -v
python tools/check_runtime_readiness.py books/functional-analysis
```

Expected: tests PASS; readiness prints `"status": "READY"` and exits 0.

- [ ] **Step 6: Commit Task 3**

```bash
git add course_package/artifacts.py tests/test_course_package_artifacts.py
git commit -m "feat: inventory canonical course artifacts"
```

---

### Task 4: Compile Deterministic In-Memory Course Package and Additive Output

**Files:**
- Create: `course_package/compiler.py`
- Create: `tests/test_course_package_compiler.py`
- Modify: `.gitignore:1-3` to add `.build/`

**Interfaces:**
- Consumes: normalized manifest, artifact inventory, existing `BookRuntime`/`CourseRuntime` read-only APIs.
- Produces: frozen `CompiledCoursePackage(course_id: str, package_identity: str, documents: dict[str, Any])`.
- Produces: `CompiledCoursePackage.file_bytes() -> dict[str, bytes]`.
- Produces: `CompiledCoursePackage.write(output_root: Path) -> Path`.
- Produces: `compile_course_package(repository_root: Path, course_dir: Path) -> CompiledCoursePackage`.
- Write path is exactly `<output_root>/<course_id>/<package_identity>/`.
- Write behavior is additive/idempotent: absent file -> create; identical file -> reuse; conflicting bytes -> raise `PackageCompileError`; never delete stale output.

- [ ] **Step 1: Write failing compiler determinism tests**

Tests must compile the real Functional Analysis Course twice in memory and compare every generated byte:

```python
from course_package.compiler import compile_course_package


class CoursePackageCompilerTests(unittest.TestCase):
    def test_real_golden_course_compiles_deterministically(self):
        first = compile_course_package(ROOT, ROOT / "courses" / "functional-analysis")
        second = compile_course_package(ROOT, ROOT / "courses" / "functional-analysis")
        self.assertEqual(first.package_identity, second.package_identity)
        self.assertEqual(first.file_bytes(), second.file_bytes())
        self.assertEqual(first.documents["course_package.json"]["chapter_count"], 8)
        self.assertEqual(first.documents["course_package.json"]["section_count"], 132)
        self.assertEqual(first.documents["course_package.json"]["search_record_count"], 1493)
        self.assertNotIn(str(ROOT.resolve()), first.file_bytes()["course_package.json"].decode("utf-8"))
```

Add a write test using `TemporaryDirectory` that writes twice to the same output root and returns the same directory without byte changes; then alter one generated file and assert the third write raises `PackageCompileError` rather than overwriting it.

- [ ] **Step 2: Run compiler tests and verify RED**

```bash
python -m unittest tests.test_course_package_compiler -v
```

Expected: FAIL because compiler does not exist.

- [ ] **Step 3: Implement structural extraction using existing Runtime**

Use `CourseRuntime.open(course_dir)` as the production-readiness proof. Extract deterministic chapters/sections without modifying Runtime:

```python
course = CourseRuntime.open(course_dir)
chapters = [
    {
        "chapter_id": chapter_id,
        "title_en": row.get("title_en"),
        "title_zh": row.get("title_zh"),
    }
    for row in course.chapters()
    if (chapter_id := str(row.get("id") or ""))
]
sections = []
for chapter_id in course.chapter_ids():
    for section in course.sections_for_chapter(chapter_id):
        sections.append({
            "section_id": section.id,
            "chapter_id": chapter_id,
            "number": section.number,
            "title_en": section.title_en,
            "title_zh": section.title_zh,
            "pdf_page_start": section.pdf_page_start,
            "pdf_page_end": section.pdf_page_end,
            "printed_page_start": section.printed_page_start,
            "printed_page_end": section.printed_page_end,
        })
```

Count search records by reading the primary book final search JSONL and counting non-empty lines. Do not create a second search index.

- [ ] **Step 4: Build the six deterministic JSON documents**

Exact top-level document names and shapes:

```python
course_package_doc = {
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
    "package_identity": "",  # filled after identity payload is hashed
    "readiness": "PASS",
}
books_doc = {"schema_version": SCHEMA_VERSION, "books": book_rows}
artifacts_doc = {"schema_version": SCHEMA_VERSION, "artifacts": artifact_rows}
chapters_doc = {"schema_version": SCHEMA_VERSION, "chapters": chapters}
sections_doc = {"schema_version": SCHEMA_VERSION, "sections": sections}
readiness_doc = {"schema_version": SCHEMA_VERSION, "status": "PASS", "diagnostics": []}
```

The identity payload excludes `package_identity` itself and hashes:

```python
identity_payload = {
    "schema_version": SCHEMA_VERSION,
    "package_version": PACKAGE_VERSION,
    "course": {key: value for key, value in course_package_doc.items() if key != "package_identity"},
    "books": books_doc["books"],
    "artifacts": artifacts_doc["artifacts"],
    "structural_baseline": {
        "chapter_count": len(chapters),
        "section_count": len(sections),
        "search_record_count": search_record_count,
    },
}
```

Set `course_package_doc["package_identity"] = sha256_bytes(canonical_json_bytes(identity_payload))`.

- [ ] **Step 5: Serialize deterministically and implement additive write**

Each JSON file byte representation is:

```python
json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
```

`package.sha256` bytes are:

```python
(package_identity + "\n").encode("ascii")
```

When writing, create parent directories with `mkdir(parents=True, exist_ok=True)`; if a target file exists, compare exact bytes before deciding to reuse or fail.

- [ ] **Step 6: Add `.build/` to `.gitignore` and run compiler tests**

`.gitignore` becomes:

```text
.env
.env.local
.env.*.local
.build/
```

Run:

```bash
python -m unittest tests.test_course_package_compiler -v
```

Expected: PASS.

- [ ] **Step 7: Run existing Runtime tests**

```bash
python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime -v
```

Expected: PASS.

- [ ] **Step 8: Commit Task 4**

```bash
git add .gitignore course_package/compiler.py tests/test_course_package_compiler.py
git commit -m "feat: compile deterministic course packages"
```

---

### Task 5: Implement Fail-Closed Package Validator and Readiness Diagnostics

**Files:**
- Create: `course_package/validator.py`
- Create: `tests/test_course_package_validator.py`

**Interfaces:**
- Produces error codes exactly: `schema_error`, `identity_error`, `artifact_missing`, `artifact_hash_mismatch`, `path_escape`, `book_not_ready`, `structural_baseline_mismatch`, `package_nondeterministic`.
- Produces: `validate_course_package(package_dir: Path, repository_root: Path) -> PackageValidationResult`.
- Produces: `validate_compiled_package(package: CompiledCoursePackage, repository_root: Path) -> PackageValidationResult`.
- `PASS` means zero diagnostics; `WARN` means at least one WARN and zero FAIL; `FAIL` means at least one FAIL.
- No diagnostic may expose secrets or unnecessary machine-absolute paths; paths are repository-relative/package-relative.

- [ ] **Step 1: Write failing validator tests for the trust-breaking cases**

Use a freshly compiled package in a temporary output root for each test, then mutate only the temporary package or a copied repository fixture. Required tests:

```text
valid Golden package -> PASS
missing package file -> schema_error / FAIL
primary count != 1 -> schema_error / FAIL
absolute canonical_path -> path_escape / FAIL
../ escape canonical_path -> path_escape / FAIL
artifact file missing -> artifact_missing / FAIL
artifact SHA changed -> artifact_hash_mismatch / FAIL
package.sha256 changed -> identity_error / FAIL
chapter/section/search count changed -> structural_baseline_mismatch / FAIL
book runtime status not READY -> book_not_ready / FAIL
secret-like key added anywhere -> schema_error / FAIL
```

The secret-key detector must reject case-insensitive keys matching:

```python
{"api_key", "apikey", "token", "access_token", "refresh_token", "password", "secret", "client_secret"}
```

- [ ] **Step 2: Run validator tests and verify RED**

```bash
python -m unittest tests.test_course_package_validator -v
```

Expected: FAIL because validator does not exist.

- [ ] **Step 3: Implement package document loading and closed-shape checks**

Validator must require all `PACKAGE_FILENAMES`, parse the six JSON files, and enforce the same required keys and enums published by Task 1. Keep the checks explicit and small instead of implementing a partial generic JSON Schema engine.

Example helper:

```python
def require_exact_keys(
    value: dict[str, Any],
    required: set[str],
    allowed: set[str],
    *,
    context: str,
) -> list[PackageDiagnostic]:
    diagnostics = []
    missing = sorted(required - value.keys())
    extra = sorted(value.keys() - allowed)
    if missing:
        diagnostics.append(PackageDiagnostic("schema_error", "FAIL", f"{context}: missing keys={missing}"))
    if extra:
        diagnostics.append(PackageDiagnostic("schema_error", "FAIL", f"{context}: unknown keys={extra}"))
    return diagnostics
```

- [ ] **Step 4: Implement repository-boundary and artifact hash checks**

For each `artifacts.json` row, resolve `repository_root / relative_path`, require `.relative_to(repository_root.resolve())`, require file existence, compare `stat().st_size`, then compare SHA-256.

Book rows must use relative `canonical_path`, remain inside repository root, and corresponding canonical `RUNTIME_READINESS.json` must parse with `status == "READY"`.

- [ ] **Step 5: Recompute package identity independently**

Rebuild the same identity payload from parsed package documents, blank/exclude the stored `package_identity`, hash canonical JSON, and compare both `course_package.json.package_identity` and `package.sha256`. This proves the validator does not trust the compiler's stored identity.

- [ ] **Step 6: Run validator + compiler tests and verify GREEN**

```bash
python -m unittest tests.test_course_package_validator tests.test_course_package_compiler -v
```

Expected: PASS.

- [ ] **Step 7: Commit Task 5**

```bash
git add course_package/validator.py tests/test_course_package_validator.py
git commit -m "feat: validate course packages fail closed"
```

---

### Task 6: Freeze Functional Analysis as the Golden Course Gate

**Files:**
- Create: `tests/golden/functional_analysis_course_package_baseline.json`
- Create: `course_package/golden.py`
- Create: `tests/test_golden_course_package.py`

**Interfaces:**
- Produces: `GOLDEN_COURSE_DIR = Path("courses/functional-analysis")`.
- Produces: `load_golden_baseline(repository_root: Path) -> dict[str, Any]`.
- Produces: `verify_golden_course(repository_root: Path) -> PackageValidationResult`.
- Golden baseline file is test/release evidence only; canonical Book remains the source of textbook facts.

- [ ] **Step 1: Create the exact Golden baseline file**

`tests/golden/functional_analysis_course_package_baseline.json`:

```json
{
  "course_id": "functional_analysis_course",
  "book_id": "stein_shakarchi_functional_analysis_2011",
  "chapter_count": 8,
  "section_count": 132,
  "search_record_count": 1493,
  "pdf_page_count": 442,
  "printed_final_page": 423,
  "structured_status": "STRUCTURED_COMPLETE",
  "runtime_status": "READY"
}
```

- [ ] **Step 2: Write failing Golden gate tests**

The test must prove all baseline values, validator PASS, deterministic compile, and canonical zero mutation:

```python
def snapshot_tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_golden_course_gate(self):
    book_root = ROOT / "books" / "functional-analysis"
    before = snapshot_tree(book_root)
    result = verify_golden_course(ROOT)
    after = snapshot_tree(book_root)
    self.assertEqual(result.status, "PASS")
    self.assertEqual(before, after)
```

Also compile twice and assert `package_identity` and all generated bytes are identical.

- [ ] **Step 3: Run Golden tests and verify RED**

```bash
python -m unittest tests.test_golden_course_package -v
```

Expected: FAIL because `course_package.golden` does not exist.

- [ ] **Step 4: Implement `verify_golden_course`**

Open the existing `CourseRuntime`, compare course/book identity, chapter and section counts, primary Book metadata/completion/readiness, final search JSONL count, PDF page count, printed final page, then compile and call `validate_compiled_package`.

When a baseline value differs, return `PackageValidationResult(status="FAIL", diagnostics=(PackageDiagnostic("structural_baseline_mismatch", ...),))`; do not rewrite the textbook or baseline automatically.

- [ ] **Step 5: Run Golden, readiness, and existing Runtime discovery**

```bash
python -m unittest tests.test_golden_course_package -v
python tools/check_runtime_readiness.py books/functional-analysis
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: Golden PASS, readiness READY, all Runtime/Foundation tests PASS.

- [ ] **Step 6: Commit Task 6**

```bash
git add course_package/golden.py tests/golden tests/test_golden_course_package.py
git commit -m "test: freeze functional analysis golden course"
```

---

### Task 7: Add Executable Architecture Fitness Functions

**Files:**
- Create: `course_package/fitness.py`
- Create: `tools/check_architecture_fitness.py`
- Create: `tests/test_architecture_fitness.py`

**Interfaces:**
- Produces: `run_architecture_fitness(repository_root: Path) -> PackageValidationResult`.
- Foundation A checks implemented now:
  1. Browser source under `app/web/src/**` must not import/use Python `sqlite3`, direct SQLite URLs, or `.sqlite3` durable-storage filenames.
  2. Course Package compiler/validator must not target canonical `books/**` or `courses/**` for output.
  3. Real Golden compile must leave canonical Book tree byte-identical.
  4. Compiled package must contain no absolute paths.
  5. Compiled package must contain no secret-key fields.
  6. Exactly one primary, artifact hashes, deterministic identity, and Golden identity are delegated to validator/Golden gate.
- Future-only raw-audio/Meeting/ExamPoint/Sync rules are not activated before their code exists.

- [ ] **Step 1: Write failing architecture fitness tests**

Use focused tests for each active invariant. For browser source, inspect only repository files under `app/web/src` with extensions `.ts`, `.tsx`, `.js`, `.jsx` and reject these regexes case-insensitively:

```text
\bsqlite3\b
sqlite:\/\/
\.sqlite3\b
```

Do not scan docs/tests/node lockfiles, because explanatory text is not a browser dependency violation.

- [ ] **Step 2: Run fitness tests and verify RED**

```bash
python -m unittest tests.test_architecture_fitness -v
```

Expected: FAIL because the fitness module/CLI does not exist.

- [ ] **Step 3: Implement architecture checks by composing existing compiler/validator/Golden functions**

`run_architecture_fitness` should aggregate diagnostics rather than throw on the first problem. Status calculation:

```python
status = "FAIL" if any(d.severity == "FAIL" for d in diagnostics) else (
    "WARN" if diagnostics else "PASS"
)
```

Canonical mutation proof is behavioral: snapshot `books/functional-analysis/**`, compile in memory and to a `TemporaryDirectory`, validate, then compare tree hashes.

- [ ] **Step 4: Implement CLI exit contract**

`tools/check_architecture_fitness.py` prints JSON:

```json
{
  "status": "PASS",
  "diagnostics": []
}
```

Exit 0 for PASS/WARN, 1 for FAIL, 2 for invalid invocation.

- [ ] **Step 5: Run fitness tests and CLI**

```bash
python -m unittest tests.test_architecture_fitness -v
python tools/check_architecture_fitness.py
```

Expected: PASS and exit 0.

- [ ] **Step 6: Commit Task 7**

```bash
git add course_package/fitness.py tools/check_architecture_fitness.py tests/test_architecture_fitness.py
git commit -m "test: add foundation architecture fitness gates"
```

---

### Task 8: Add Compiler and Validator CLI Entry Points

**Files:**
- Create: `tools/compile_course_package.py`
- Create: `tools/validate_course_package.py`
- Create: `tests/test_course_package_cli.py`
- Modify: `course_package/__init__.py`

**Interfaces:**
- `python tools/compile_course_package.py courses/functional-analysis --repository-root . --output-root .build/course-packages`
- Compile CLI stdout JSON fields: `status`, `course_id`, `package_identity`, `package_dir`.
- Compile exit: 0 success, 1 compile/validation failure, 2 invalid invocation.
- `python tools/validate_course_package.py <package-dir> --repository-root .`
- Validate CLI stdout JSON fields: `status`, `diagnostics`.
- Validate exit: 0 PASS/WARN, 1 FAIL, 2 invalid invocation.

- [ ] **Step 1: Write failing subprocess CLI tests**

Use `subprocess.run(..., cwd=ROOT, text=True, capture_output=True)` in a temporary output root. The compile test parses stdout, opens `package_dir`, then invokes validator CLI on it and expects PASS.

Also test invalid paths return code 2 without Python traceback leakage in stdout JSON.

- [ ] **Step 2: Run CLI tests and verify RED**

```bash
python -m unittest tests.test_course_package_cli -v
```

Expected: FAIL because CLI files do not exist.

- [ ] **Step 3: Implement compile CLI**

Core flow:

```python
package = compile_course_package(repository_root, course_dir)
validation = validate_compiled_package(package, repository_root)
if validation.status == "FAIL":
    print(json.dumps({"status": "FAIL", "diagnostics": [asdict(d) for d in validation.diagnostics]}, ensure_ascii=False))
    return 1
package_dir = package.write(output_root)
print(json.dumps({
    "status": validation.status,
    "course_id": package.course_id,
    "package_identity": package.package_identity,
    "package_dir": package_dir.resolve().relative_to(repository_root.resolve()).as_posix()
}, ensure_ascii=False))
return 0
```

Require `output_root` to remain inside repository root when using the default `.build` path. Explicit temporary output outside repository root is permitted only in tests/library calls, not as the CLI default.

- [ ] **Step 4: Implement validator CLI and export public API**

`course_package/__init__.py` must export:

```python
from .compiler import CompiledCoursePackage, PackageCompileError, compile_course_package
from .golden import verify_golden_course
from .validator import validate_compiled_package, validate_course_package
```

- [ ] **Step 5: Run CLI and full focused Foundation tests**

```bash
python -m unittest \
  tests.test_course_package_schema \
  tests.test_course_manifest_normalization \
  tests.test_course_package_artifacts \
  tests.test_course_package_compiler \
  tests.test_course_package_validator \
  tests.test_golden_course_package \
  tests.test_architecture_fitness \
  tests.test_course_package_cli -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 8**

```bash
git add tools/compile_course_package.py tools/validate_course_package.py course_package/__init__.py tests/test_course_package_cli.py
git commit -m "feat: add course package command line gates"
```

---

### Task 9: Layer CI Into FAST, PR FULL, and HEAVY Gates

**Files:**
- Create: `.github/workflows/course-package-fast.yml`
- Create: `.github/workflows/course-package-heavy.yml`
- Modify: `.github/workflows/runtime-reference-tests.yml:1-205`
- Modify: `.github/workflows/app-ui-tests.yml:1-130`

**Interfaces:**
- FAST: focused Foundation contract/compiler/validator/fitness tests on Python 3.13.
- PR FULL backend: existing Python 3.11/3.12/3.13 Runtime matrix plus Golden Course compile/validate on 3.13.
- PR FULL product: existing App API/Web/Chromium workflow still runs when Foundation paths change.
- HEAVY: manual `workflow_dispatch` plus optional release-oriented trigger; performs current canonical rebuild/recovery/readiness sequence in a clean checkout, then Golden package validation. It does not commit rebuilt candidates back to the repository.

- [ ] **Step 1: Create FAST workflow**

`.github/workflows/course-package-fast.yml` must trigger on pull requests and pushes touching:

```text
course_package/**
schemas/course-package/**
tools/compile_course_package.py
tools/validate_course_package.py
tools/check_architecture_fitness.py
tests/test_course_package_*.py
tests/test_golden_course_package.py
tests/test_architecture_fitness.py
tests/golden/**
.github/workflows/course-package-fast.yml
```

Job steps:

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: "3.13"
- name: Compile Foundation modules
  run: python -m py_compile course_package/*.py tools/compile_course_package.py tools/validate_course_package.py tools/check_architecture_fitness.py
- name: Run Foundation FAST tests
  run: python -m unittest tests.test_course_package_schema tests.test_course_manifest_normalization tests.test_course_package_artifacts tests.test_course_package_compiler tests.test_course_package_validator tests.test_golden_course_package tests.test_architecture_fitness tests.test_course_package_cli -v
- name: Run architecture fitness
  run: python tools/check_architecture_fitness.py
```

- [ ] **Step 2: Extend Runtime PR FULL path filters and 3.13 Golden step**

Add `course_package/**`, `schemas/course-package/**`, the three new tools, Golden tests, and FAST workflow path to `runtime-reference-tests.yml` triggers.

In the Python 3.13 job after existing Runtime discovery/readiness, add:

```yaml
- name: Compile and validate Golden Course Package
  if: matrix.python-version == '3.13'
  run: |
    python tools/compile_course_package.py courses/functional-analysis --repository-root . --output-root .build/course-packages > /tmp/course-package.json
    PACKAGE_DIR=$(python -c "import json; print(json.load(open('/tmp/course-package.json'))['package_dir'])")
    python tools/validate_course_package.py "$PACKAGE_DIR" --repository-root .
    python tools/check_architecture_fitness.py
```

Do not remove the current Runtime rebuild/readiness evidence sequence.

- [ ] **Step 3: Extend App PR FULL trigger paths without changing App source**

Add these paths to both `push.paths` and `pull_request.paths` in `app-ui-tests.yml`:

```text
course_package/**
schemas/course-package/**
tools/compile_course_package.py
tools/validate_course_package.py
tools/check_architecture_fitness.py
tests/golden/**
.github/workflows/course-package-fast.yml
.github/workflows/course-package-heavy.yml
```

Keep existing `app-api`, `web-client`, and `browser-acceptance` jobs unchanged.

- [ ] **Step 4: Create HEAVY workflow without automated canonical writes**

`.github/workflows/course-package-heavy.yml`:

```yaml
name: Course Package heavy gate

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  golden-heavy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Rebuild candidates in clean checkout
        run: |
          python tools/rebuild_runtime_artifacts.py books/functional-analysis --toc
          python tools/recover_functional_analysis_search.py books/functional-analysis --promote-safe
          python tools/recover_functional_analysis_page_map.py books/functional-analysis --promote-safe
      - name: Validate canonical readiness and Golden Package
        run: |
          python tools/check_runtime_readiness.py books/functional-analysis
          python tools/compile_course_package.py courses/functional-analysis --repository-root . --output-root .build/course-packages > /tmp/course-package.json
          PACKAGE_DIR=$(python -c "import json; print(json.load(open('/tmp/course-package.json'))['package_dir'])")
          python tools/validate_course_package.py "$PACKAGE_DIR" --repository-root .
          python tools/check_architecture_fitness.py
```

Do not use `--write` for readiness in HEAVY and do not upload or commit modified canonical files as repository changes. Existing recovery candidate artifacts may be uploaded only as workflow artifacts if later explicitly required.

- [ ] **Step 5: Locally parse/test all Python and inspect workflow diff**

Run:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python tools/check_runtime_readiness.py books/functional-analysis
python tools/check_architecture_fitness.py
git diff --check
```

Expected: all tests PASS, readiness READY, fitness PASS, `git diff --check` clean.

- [ ] **Step 6: Commit Task 9**

```bash
git add .github/workflows
git commit -m "ci: layer course package acceptance gates"
```

---

### Task 10: Exact-HEAD Full Regression, Documentation State, and PR Readiness

**Files:**
- Modify: `docs/CURRENT_STATE.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/DEVELOPMENT_STRATEGY.md` only to replace the stale Phase 1G execution-priority paragraph with current Foundation A status; preserve all historical/architectural content.
- No canonical Book changes.

**Interfaces:**
- Current-state docs may claim Foundation A implementation complete only after the exact final HEAD passes the full gate.
- The branch remains reviewable; do not merge automatically.

- [ ] **Step 1: Run exact local full Python regressions before status-doc edits**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s app_tests -p "test_*.py" -v
python tools/check_runtime_readiness.py books/functional-analysis
python tools/check_architecture_fitness.py
```

Expected: all PASS / READY.

- [ ] **Step 2: Run web gates**

From `app/web`:

```bash
npm ci
npm test
npm run typecheck
npm run build
npx playwright install chromium
```

Then run API/Web exactly as CI with `BOOK_QA_PROVIDER=fake` and a temporary `BOOK_APP_DATA_DIR`, followed by:

```bash
npm run e2e
```

Expected: Vitest PASS, typecheck PASS, production build PASS, real Chromium acceptance PASS.

- [ ] **Step 3: Prove canonical textbook zero-diff**

Run:

```bash
git diff -- books/functional-analysis
git status --short books/functional-analysis
```

Expected: no output.

Also compare branch to its Foundation A starting base and verify only intended Foundation files/docs/workflows changed:

```bash
git diff --name-status a99d4638f959e04e54d91efe0ee0dd9ac50488a6...HEAD
```

Expected: no unexpected App source or canonical textbook files.

- [ ] **Step 4: Update current-state documentation with evidence, not projections**

After Steps 1–3 pass, update docs to state:

```text
Foundation A Course Package v1 implemented on foundation/course-package-contract-a
Course Package schema: course_package_v1
Package version: 1.0.0
Canonical roles: primary / supplementary / reference / translation
Functional Analysis Golden gate: 8 / 132 / 1493 / 442 / printed 423 PASS
Deterministic compile: same source -> identical package_identity and bytes PASS
Canonical books/functional-analysis/** mutation: 0
Architecture Fitness: PASS
Existing Runtime/App/Web/Chromium regression: PASS
Next action: exact-final-HEAD PR gate/review; App still consumes existing Runtime
```

In `docs/DEVELOPMENT_STRATEGY.md`, replace only the stale section that still says `feature/study-record-phase-1g` is the current execution priority; set the priority to the active Foundation A branch and plan path. Do not rewrite the rest of the strategy.

- [ ] **Step 5: Commit documentation state**

```bash
git add docs/CURRENT_STATE.md docs/ROADMAP.md docs/DEVELOPMENT_STRATEGY.md
git commit -m "docs: record Foundation A implementation state"
```

- [ ] **Step 6: Re-run exact-final-HEAD focused and full gates after the docs commit**

Because CI/path state changed with the final commit, rerun:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s app_tests -p "test_*.py" -v
python tools/check_runtime_readiness.py books/functional-analysis
python tools/check_architecture_fitness.py
git diff --check
```

Then rerun web `npm test`, `npm run typecheck`, `npm run build`, and `npm run e2e` against the exact HEAD if local execution environment permits. If browser execution is unavailable locally, do not claim Chromium PASS until GitHub Actions on the exact PR head succeeds.

- [ ] **Step 7: Push branch and open a reviewable PR**

Before push, record exact HEAD:

```bash
git rev-parse HEAD
```

Push only `foundation/course-package-contract-a`, open a PR to `main`, and wait for:

```text
Course Package FAST = success
Runtime reference tests = success on Python 3.11 / 3.12 / 3.13
Book App UI tests app-api = success
Book App UI tests web-client = success
Book App UI tests browser-acceptance = success
```

Do not use a green run from an older commit as evidence for a newer HEAD.

- [ ] **Step 8: Review PR diff and threads before any merge request**

Verify:

```text
no books/functional-analysis/** changes
no App runtime migration
no secrets/tokens
no force-push/history rewrite
no unexpected generated .build files tracked
all review threads resolved or explicitly addressed
PR mergeable on exact reviewed head
```

Only after these conditions are true may the user be asked for explicit authorization to merge that specific PR. Do not auto-merge.

---

## Plan Self-Review Checklist

Before execution begins, confirm this plan still covers every approved spec requirement:

```text
Contract/schema version                    -> Task 1
canonical roles + legacy normalization     -> Task 2
repository-relative artifacts + SHA-256    -> Task 3
deterministic package identity             -> Task 4
additive .build output                      -> Task 4
PASS/WARN/FAIL fail-closed validator        -> Task 5
path/hash/identity negative tests           -> Task 5
Functional Analysis Golden Course           -> Task 6
8/132/1493/442/423 baseline                 -> Task 6
canonical zero mutation                     -> Tasks 6-7
Architecture Fitness                        -> Task 7
CLI compile/validate                        -> Task 8
FAST / PR FULL / HEAVY CI                   -> Task 9
existing Runtime/App compatibility          -> Tasks 2,4,9,10
exact-final-HEAD regression                 -> Task 10
no App migration / no future feature creep -> Global Constraints + Task 10
```

Type/signature consistency to preserve across all tasks:

```text
normalize_course_manifest(Path, Path) -> NormalizedCourseManifest
build_book_artifact_inventory(Path, str, str) -> tuple[ArtifactRecord, ...]
compile_course_package(Path, Path) -> CompiledCoursePackage
validate_compiled_package(CompiledCoursePackage, Path) -> PackageValidationResult
validate_course_package(Path, Path) -> PackageValidationResult
verify_golden_course(Path) -> PackageValidationResult
run_architecture_fitness(Path) -> PackageValidationResult
```

No task may silently rename these interfaces. If implementation evidence requires a signature change, update the approved plan/spec explicitly before dependent tasks proceed.
