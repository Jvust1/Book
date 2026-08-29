# H0 Neutral Book Identity Implementation Plan

> **For implementers:** Use Superpowers TDD. Follow the tasks in order. Do not begin H1 in the same PR.

**Goal:** Introduce a neutral, stdlib-only Book identity seam shared by Course Package and Runtime while preserving every legacy course/runtime observation.

**Architecture:** Add `book_core.identity` as the single owner of canonical roles and deterministic identity projection. Course Package consumes it instead of owning duplicate mapping logic. Runtime exposes read-only identity projection without changing `CourseBookEntry`, legacy manifest validation, ordering, summary output, or public App DTOs.

**Tech stack:** Python 3.11–3.13 stdlib, `unittest`, GitHub Actions YAML.

---

## Task 1: Freeze neutral identity behavior with RED tests

**Files:**
- Create: `tests/test_book_identity.py`
- Reference: `course_package/manifest.py`
- Reference: `runtime/course_runtime.py`

**Step 1: Write the failing neutral identity tests**

Create `tests/test_book_identity.py` with tests equivalent to:

```python
from __future__ import annotations

import unittest

from book_core.identity import (
    CANONICAL_BOOK_ROLES,
    LEGACY_BOOK_ROLE_ALIASES,
    BookIdentity,
    build_book_identity,
    canonical_role_from_legacy,
)


class BookIdentityTests(unittest.TestCase):
    def test_canonical_roles_are_frozen(self) -> None:
        self.assertEqual(
            CANONICAL_BOOK_ROLES,
            frozenset({"primary", "supplementary", "reference", "translation"}),
        )

    def test_legacy_roles_map_deterministically(self) -> None:
        self.assertEqual(
            LEGACY_BOOK_ROLE_ALIASES,
            {
                "main": "primary",
                "supplementary": "supplementary",
                "reference": "reference",
                "english": "translation",
            },
        )
        self.assertEqual(canonical_role_from_legacy("main"), "primary")
        self.assertEqual(canonical_role_from_legacy("english"), "translation")

    def test_build_identity_uses_current_compatibility_rule(self) -> None:
        identity = build_book_identity("book_a", "v7", "main")
        self.assertEqual(
            identity,
            BookIdentity(
                book_id="book_a",
                logical_book_id="book_a",
                book_version_id="book_a@v7",
                role="primary",
            ),
        )

    def test_canonical_input_role_is_not_a_legacy_alias(self) -> None:
        with self.assertRaises(ValueError):
            canonical_role_from_legacy("primary")

    def test_blank_identity_parts_fail_closed(self) -> None:
        for book_id, version, role in [
            ("", "v1", "main"),
            ("book", "", "main"),
            ("book", "v1", ""),
        ]:
            with self.subTest(book_id=book_id, version=version, role=role):
                with self.assertRaises(ValueError):
                    build_book_identity(book_id, version, role)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run the test to verify RED**

Run:

```bash
python -m unittest tests.test_book_identity -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'book_core'`.

**Step 3: Commit the RED test**

```bash
git add tests/test_book_identity.py
git commit -m "test: define neutral book identity contract"
```

---

## Task 2: Implement the stdlib-only neutral identity module

**Files:**
- Create: `book_core/__init__.py`
- Create: `book_core/identity.py`
- Test: `tests/test_book_identity.py`

**Step 1: Add the minimal identity implementation**

Implement `book_core/identity.py` with this public shape:

```python
from __future__ import annotations

from dataclasses import dataclass

CANONICAL_BOOK_ROLES = frozenset(
    {"primary", "supplementary", "reference", "translation"}
)
LEGACY_BOOK_ROLE_ALIASES = {
    "main": "primary",
    "supplementary": "supplementary",
    "reference": "reference",
    "english": "translation",
}


@dataclass(frozen=True)
class BookIdentity:
    book_id: str
    logical_book_id: str
    book_version_id: str
    role: str


def canonical_role_from_legacy(role: str) -> str:
    normalized = str(role).strip()
    if normalized not in LEGACY_BOOK_ROLE_ALIASES:
        raise ValueError(f"Unsupported legacy book role: {role!r}")
    return LEGACY_BOOK_ROLE_ALIASES[normalized]


def build_book_identity(
    book_id: str,
    structured_version: str,
    legacy_role: str,
) -> BookIdentity:
    normalized_book_id = str(book_id).strip()
    normalized_version = str(structured_version).strip()
    if not normalized_book_id:
        raise ValueError("book_id must be non-blank")
    if not normalized_version:
        raise ValueError("structured_version must be non-blank")
    role = canonical_role_from_legacy(legacy_role)
    return BookIdentity(
        book_id=normalized_book_id,
        logical_book_id=normalized_book_id,
        book_version_id=f"{normalized_book_id}@{normalized_version}",
        role=role,
    )
```

Keep `book_core/__init__.py` side-effect free. It may contain only a package docstring; consumers should import from `book_core.identity` directly during H0.

**Step 2: Run the neutral tests**

```bash
python -m unittest tests.test_book_identity -v
```

Expected: PASS.

**Step 3: Compile the neutral module**

```bash
python -m py_compile book_core/__init__.py book_core/identity.py
```

Expected: PASS with no output.

**Step 4: Commit**

```bash
git add book_core tests/test_book_identity.py
git commit -m "feat: add neutral book identity seam"
```

---

## Task 3: Make Course Package consume the neutral identity owner

**Files:**
- Modify: `course_package/contracts.py`
- Modify: `course_package/manifest.py`
- Modify: `tests/test_course_package_schema.py`
- Modify: `tests/test_course_manifest_normalization.py`

**Step 1: Add a characterization asserting Course Package uses the same constants**

In `tests/test_course_package_schema.py`, add:

```python
from book_core.identity import CANONICAL_BOOK_ROLES as CORE_BOOK_ROLES
from course_package.contracts import CANONICAL_BOOK_ROLES


def test_course_package_roles_share_core_owner(self):
    self.assertIs(CANONICAL_BOOK_ROLES, CORE_BOOK_ROLES)
```

In `tests/test_course_manifest_normalization.py`, retain/add tests proving:

```text
main -> primary
english -> translation
logical_book_id == book_id
book_version_id == f"{book_id}@{structured_version}"
legacy input role "primary" is rejected
```

**Step 2: Run targeted tests to verify the shared-owner test is RED**

```bash
python -m unittest tests.test_course_package_schema tests.test_course_manifest_normalization -v
```

Expected: the new identity-owner assertion fails before refactor; existing behavior tests remain GREEN.

**Step 3: Refactor without changing output bytes**

In `course_package/contracts.py`, replace the local role constant with:

```python
from book_core.identity import CANONICAL_BOOK_ROLES
```

In `course_package/manifest.py`, replace the local `ROLE_ALIASES` owner with imports:

```python
from book_core.identity import build_book_identity, canonical_role_from_legacy
```

For each legacy manifest entry, compute:

```python
identity = build_book_identity(book_id, structured_version, role_value)
```

Then construct `NormalizedBookEntry` from `identity.book_id`, `identity.logical_book_id`, `identity.book_version_id`, and `identity.role` while preserving every other field and manifest order exactly.

Convert neutral `ValueError` to the existing `ManifestNormalizationError` so Course Package error type remains stable.

**Step 4: Run Course Package tests**

```bash
python -m unittest \
  tests.test_book_identity \
  tests.test_course_package_schema \
  tests.test_course_manifest_normalization \
  tests.test_course_package_compiler \
  tests.test_course_package_validator \
  tests.test_golden_course_package -v
```

Expected: PASS.

**Step 5: Verify deterministic package output twice**

```bash
rm -rf /tmp/book-h0-package-a /tmp/book-h0-package-b
python tools/compile_course_package.py courses/functional-analysis --repository-root . --output-root /tmp/book-h0-package-a >/tmp/h0-a.json
python tools/compile_course_package.py courses/functional-analysis --repository-root . --output-root /tmp/book-h0-package-b >/tmp/h0-b.json
python - <<'PY'
import hashlib, json, pathlib

def files(report_path):
    report = json.loads(pathlib.Path(report_path).read_text())
    root = pathlib.Path(report["package_dir"])
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.iterdir()) if p.is_file()
    }

assert files('/tmp/h0-a.json') == files('/tmp/h0-b.json')
print(files('/tmp/h0-a.json'))
PY
```

Expected: assertion passes. Do not record a made-up fixed hash; only record hashes actually produced at the reviewed HEAD.

**Step 6: Commit**

```bash
git add course_package tests/test_course_package_schema.py tests/test_course_manifest_normalization.py
git commit -m "refactor: centralize course package book identity"
```

---

## Task 4: Add Runtime read-only identity projection without changing legacy APIs

**Files:**
- Modify: `runtime/course_runtime.py`
- Modify: `tests/test_course_runtime.py`

**Step 1: Write RED Runtime projection tests**

Add tests:

```python
def test_main_book_identity_projects_canonical_identity(self) -> None:
    course = self._open_two_book_course()
    identity = course.main_book_identity()
    self.assertEqual(identity.book_id, "fixture_main")
    self.assertEqual(identity.logical_book_id, "fixture_main")
    self.assertEqual(identity.book_version_id, "fixture_main@v1")
    self.assertEqual(identity.role, "primary")


def test_book_identity_preserves_legacy_role_api(self) -> None:
    course = self._open_two_book_course()
    identity = course.book_identity("fixture_supplementary")
    self.assertEqual(identity.role, "supplementary")
    self.assertEqual(
        [(row["book_id"], row["role"]) for row in course.summary()["books"]],
        [("fixture_main", "main"), ("fixture_supplementary", "supplementary")],
    )


def test_primary_role_remains_invalid_legacy_manifest_input(self) -> None:
    with self.assertRaises(CourseManifestError):
        self._open_manifest_override(
            {"books": [self._entry("fixture_book_2026", "primary", "../../books/a")]}
        )
```

Also add a fail-closed test for a ready BookRuntime whose structured version is blank/missing when identity projection is requested.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_course_runtime -v
```

Expected: new `book_identity`/`main_book_identity` tests fail with missing attributes; existing legacy tests pass.

**Step 3: Implement only the projection methods**

Import:

```python
from book_core.identity import BookIdentity, build_book_identity
```

Add:

```python
def book_identity(self, book_id: str) -> BookIdentity:
    entry = next(
        (row for row in self.entries if row.enabled and row.book_id == book_id),
        None,
    )
    if entry is None:
        raise CourseRuntimeError(f"Unknown or disabled course book: {book_id}")
    book = self.book(book_id)
    version = book.structured_version
    if not version or not str(version).strip():
        raise CourseRuntimeError(
            f"Book {book_id!r} has no usable structured version for identity projection"
        )
    try:
        return build_book_identity(book_id, str(version), entry.role)
    except ValueError as exc:
        raise CourseRuntimeError(str(exc)) from exc


def main_book_identity(self) -> BookIdentity:
    return self.book_identity(self.main_book_id)
```

Do not change `CourseBookEntry`, `_validate_manifest`, `book_ids`, `books_by_role`, `main_book`, or `summary` output.

**Step 4: Run Runtime + Golden characterization**

```bash
python -m unittest tests.test_book_identity tests.test_course_runtime tests.test_library_runtime -v
```

Expected: PASS, including legacy `primary` rejection and Golden 8/132/1493/442 checks.

**Step 5: Commit**

```bash
git add runtime/course_runtime.py tests/test_course_runtime.py
git commit -m "feat: expose runtime book identity projection"
```

---

## Task 5: Wire `book_core/**` into FAST/Runtime/App CI

**Files:**
- Modify: `.github/workflows/course-package-fast.yml`
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Modify: `.github/workflows/app-ui-tests.yml`

**Step 1: Add path-trigger tests by inspection before editing**

Confirm all three workflows currently omit `book_core/**`:

```bash
grep -n 'book_core' .github/workflows/course-package-fast.yml .github/workflows/runtime-reference-tests.yml .github/workflows/app-ui-tests.yml
```

Expected before change: no matches.

**Step 2: Add `book_core/**` to push and pull_request paths**

For all three workflows, add:

```yaml
- "book_core/**"
```

In Course Package FAST compile step, include:

```bash
python -m py_compile book_core/*.py course_package/*.py tools/compile_course_package.py tools/validate_course_package.py tools/check_architecture_fitness.py
```

In Runtime compile step, add:

```bash
python -m py_compile book_core/*.py
```

Add `tests.test_book_identity` to an appropriate FAST/Runtime unittest invocation.

Do not change `course-package-heavy.yml`; it remains manual-only.

**Step 3: Validate YAML text and run local equivalents**

```bash
python -m py_compile book_core/*.py course_package/*.py runtime/*.py
python -m unittest \
  tests.test_book_identity \
  tests.test_course_manifest_normalization \
  tests.test_course_runtime \
  tests.test_course_package_schema \
  tests.test_course_package_compiler \
  tests.test_course_package_validator \
  tests.test_golden_course_package -v
```

Expected: PASS.

**Step 4: Commit**

```bash
git add .github/workflows/course-package-fast.yml .github/workflows/runtime-reference-tests.yml .github/workflows/app-ui-tests.yml
git commit -m "ci: run shared identity checks for book core changes"
```

---

## Task 6: Exact-HEAD H0 verification and PR readiness

**Files:**
- No product file changes expected.

**Step 1: Run Runtime full discovery**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: PASS.

**Step 2: Run App regression discovery**

Install API dependencies if needed, then:

```bash
python -m pip install -r app/api/requirements.txt
python -m unittest discover -s app_tests -p "test_*.py" -v
```

Expected: PASS.

**Step 3: Run web tests/typecheck/build**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
```

Expected: PASS.

**Step 4: Verify canonical tree is not part of the diff**

```bash
git diff --name-only <H0_BASE_SHA>...HEAD
```

Expected: no `books/**`, `courses/**`, `library/**`, or StudyRecord storage files in the H0 diff. Replace `<H0_BASE_SHA>` with the actual implementation-branch base SHA when executing; do not guess it.

**Step 5: Record exact HEAD and open reviewable PR**

```bash
git rev-parse HEAD
```

Record that SHA with the test evidence. Do not merge automatically. Do not start H1 until H0 review/merge governance is satisfied.
