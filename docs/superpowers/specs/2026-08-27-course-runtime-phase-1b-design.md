# CourseRuntime Phase 1B Design

Date: 2026-08-27
Status: proposed
Target branch: `feature/course-runtime-phase-1b`

## 1. Context

The Functional Analysis fixture is now production-importable on `main`:

- `STRUCTURED_COMPLETE`
- runtime readiness `READY`
- 442 physical PDF pages mapped
- 8 chapters / 132 sections
- 1493 unique final search records with source anchors
- `BookRuntime.open()` succeeds

The next product milestone in the repository baseline is to connect the completed single-book runtime to the Course OS navigation model:

```text
Course -> Book -> Chapter -> Section
```

The repository already has a mature single-book reader in `runtime/book_runtime.py`. Phase 1B must not duplicate its parsing, readiness checks, PageMap logic, object normalization, search loading, or stable-ID validation.

## 2. Goals

Phase 1B will introduce a small course aggregation layer that:

1. Opens a course from a declarative course manifest.
2. Resolves one or more book entries to existing repository book directories.
3. Opens each enabled book through `BookRuntime.open()`.
4. Exposes deterministic Course -> Book -> Chapter -> Section navigation.
5. Preserves book roles so the model supports main, supplementary, English, and reference books from the beginning.
6. Fails closed when any enabled book cannot be opened as runtime-ready; Phase 1B never silently drops an enabled book.
7. Uses the current Functional Analysis v0.36 book as the first real course fixture.

## 3. Non-goals

Phase 1B will not implement:

- UI screens or frontend framework selection
- preview / learn / review / practice content generation
- progress persistence
- notes, mistakes, lectures, exams, or mastery
- CourseKnowledgeTree construction
- semantic cross-book concept alignment
- database storage
- automatic version migration
- cross-book unified search

Those capabilities depend on a stable course-level read contract and belong to later milestones.

## 4. Recommended architecture

Use a thin `CourseRuntime` aggregation layer over `BookRuntime`.

```text
course.json
    |
    v
CourseRuntime.open(course_dir)
    |
    +-- validate course manifest
    +-- resolve configured book directories
    +-- BookRuntime.open(book_dir)
    +-- validate course/book identities and roles
    |
    v
CourseRuntime
    |
    +-- Course metadata
    +-- Book handles
    +-- Main-book handle
    +-- Chapter traversal
    +-- Section traversal
```

`BookRuntime` remains the authoritative implementation for all book-internal behavior.

## 5. Repository layout

Add the following minimum structure:

```text
runtime/
  course_runtime.py

courses/
  functional-analysis/
    course.json

runtime/__init__.py

tests/
  test_course_runtime.py
```

No new storage engine is introduced.

## 6. Course manifest

The first manifest is intentionally small and explicit.

Example:

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

### Required manifest fields

Top level:

- `schema_version`
- `course_id`
- `name`
- `main_book_id`
- `books`

Book entry:

- `book_id`
- `role`
- `path`
- `required`
- `enabled`

Allowed initial roles:

- `main`
- `supplementary`
- `english`
- `reference`

### Manifest invariants

`CourseRuntime.open()` must reject the manifest when:

- `schema_version != "course_manifest_v1"`
- `course_id` is missing or empty
- `books` is empty
- there is not exactly one enabled `main` role
- `main_book_id` does not identify that enabled main entry
- enabled book IDs are duplicated
- a role is outside the allowed role set
- a configured path escapes the repository root after normalization
- any enabled book cannot be opened through the normal `BookRuntime` readiness gate
- the manifest `book_id` differs from the canonical `BookRuntime.book_id`

A disabled book is configuration only and is not opened. The `required` flag is retained now because it belongs to the long-term course manifest model, but in Phase 1B it does not permit degraded loading: every enabled book must open successfully. Future admission policies may distinguish required and optional books explicitly in a later spec.

## 7. Runtime model

Introduce simple immutable metadata records where useful, but do not mirror the full BookRuntime model.

Suggested public surface:

```python
from runtime import CourseRuntime

course = CourseRuntime.open("courses/functional-analysis")

course.course_id
course.name
course.main_book_id
course.book_ids()
course.main_book()
course.book("stein_shakarchi_functional_analysis_2011")
course.books_by_role("main")
course.chapter_ids()
course.chapters()
course.sections_for_chapter("chapter_01")
course.section("ch01_s01")
course.summary()
```

`CourseRuntime.open()` may also accept an explicit `repository_root` for tests or nonstandard embedding:

```python
course = CourseRuntime.open(course_dir, repository_root=repo_root)
```

### Delegation rules

For Phase 1B:

- `chapter_ids()` means chapters of the main book.
- `chapters()` means chapters of the main book.
- `sections_for_chapter()` delegates to the main book.
- `section()` resolves against the main book only.

Cross-book chapter or section namespaces are not merged in Phase 1B. Consumers that need a non-main book must first obtain that book handle through `course.book(book_id)`.

This avoids inventing ambiguous global chapter/section identities before the course knowledge tree exists.

## 8. Error model

Add course-specific exceptions while preserving BookRuntime errors as causes.

Suggested hierarchy:

```text
CourseRuntimeError
├── CourseManifestError
├── CourseBookResolutionError
└── CourseRuntimeBlockedError
```

Rules:

- malformed or unsupported manifest -> `CourseManifestError`
- invalid/missing repository-relative path -> `CourseBookResolutionError`
- any enabled book fails the BookRuntime readiness gate -> `CourseRuntimeBlockedError`
- disabled books are never opened and cannot block the course

Phase 1B is strictly fail-closed. A course must not silently present a partial set of enabled books.

## 9. Path and trust boundary

The manifest path is data, not trusted code.

Resolution algorithm:

1. Resolve the course directory to an absolute canonical path.
2. Determine the repository root:
   - if `repository_root` was explicitly supplied, canonicalize and use it;
   - otherwise require the normal layout `<repository_root>/courses/<course-directory>` and infer the root as the parent of `courses`.
3. Resolve each configured book path relative to the course directory.
4. Canonicalize the resulting filesystem path.
5. Verify that the path remains under the repository root.
6. Pass the canonical book directory to `BookRuntime.open()`.

If the course directory is not in the normal `courses/<name>` layout and no explicit `repository_root` is supplied, opening fails with `CourseBookResolutionError` rather than guessing.

No manifest-controlled Python import, URL, shell execution, or arbitrary external path is allowed.

## 10. Data flow

Normal open path:

```text
course directory
    -> course.json
    -> manifest validation
    -> repository-root resolution
    -> book-entry validation
    -> canonical book paths
    -> BookRuntime.open() for every enabled book
    -> canonical book_id verification
    -> main book verification
    -> CourseRuntime object
```

Navigation path:

```text
CourseRuntime
    -> main_book()
    -> BookRuntime chapter/section APIs
    -> existing normalized chapter/section objects
```

No book content is reparsed at the course layer.

## 11. Compatibility with multiple books

Although the first fixture contains only one book, the manifest and runtime must support multiple entries immediately.

Example future shape:

```json
"books": [
  {"book_id": "a", "role": "main", "path": "...", "required": true, "enabled": true},
  {"book_id": "b", "role": "supplementary", "path": "...", "required": false, "enabled": true},
  {"book_id": "c", "role": "english", "path": "...", "required": false, "enabled": true}
]
```

The aggregation layer stores book handles independently. It does not combine chapter trees across books.

This preserves the architecture baseline that one course can mount multiple textbooks while avoiding premature cross-book ontology work.

## 12. Functional Analysis real fixture

Create:

`courses/functional-analysis/course.json`

Its enabled main book must reference:

`books/functional-analysis`

Canonical ID:

`stein_shakarchi_functional_analysis_2011`

Acceptance facts from the current finalized runtime:

- runtime status `READY`
- 8 chapters
- 132 sections
- 442 PageMap rows
- 1493 final search records

The CourseRuntime test must use this real fixture in addition to isolated temporary fixtures.

## 13. Test strategy

Use TDD for implementation.

Minimum tests:

### Manifest validation

1. valid one-book course opens
2. unsupported `schema_version` fails
3. missing `course_id` fails
4. empty `books` fails
5. duplicate enabled `book_id` fails
6. no enabled main book fails
7. multiple enabled main books fail
8. unsupported role fails
9. mismatched `main_book_id` fails

### Book resolution and readiness

10. missing book path fails
11. path escaping repository root fails
12. nonstandard course layout without explicit repository root fails
13. explicit repository root supports an isolated fixture
14. manifest ID mismatching canonical BookRuntime ID fails
15. blocked enabled book fails closed regardless of `required`
16. disabled blocked book is ignored

### Navigation

17. `main_book()` returns the configured main BookRuntime
18. `book_ids()` is deterministic
19. `books_by_role()` filters correctly
20. `chapter_ids()` delegates to the main book
21. `sections_for_chapter()` delegates to the main book
22. `section()` resolves a main-book section

### Real fixture

23. Functional Analysis course opens from the repository fixture
24. main book canonical ID matches
25. chapter count is 8
26. total section count is 132
27. representative section `ch01_s01` resolves
28. course summary reports the mounted book and main role

## 14. Public API stability

Phase 1B should expose only APIs required for current navigation.

Avoid exposing internal manifest dictionaries directly as mutable state.

The first stable contract is:

- open course
- enumerate mounted books
- get main book
- get book by ID/role
- traverse main book chapters and sections
- retrieve summary metadata

Search, QA, study modes, and progress should be separate additions later rather than overloaded into this class now.

## 15. Documentation updates

Implementation should update:

- `runtime/README.md`
  - remove obsolete statement that Functional Analysis is expected to be `BLOCKED`
  - document `CourseRuntime`
  - add Course -> Book -> Chapter -> Section example
- repository `README.md`
  - mark runtime import recovery complete
  - mark CourseRuntime Phase 1B as current milestone or completed when merged
- Issue #2
  - add final recovery evidence and close it because PR #3 is merged and `main` is `READY`

Do not rewrite unrelated roadmap sections.

## 16. CI

Extend the existing runtime workflow rather than creating a second independent workflow.

The workflow should run `tests.test_course_runtime` on Python 3.11, 3.12, and 3.13 together with the existing runtime tests.

The implementation must not add auto-generated commits on `main`.

## 17. Acceptance criteria

Phase 1B is complete when all of the following are true:

1. `CourseRuntime.open("courses/functional-analysis")` succeeds on a clean checkout.
2. The mounted main book ID is `stein_shakarchi_functional_analysis_2011`.
3. Course navigation exposes the real 8-chapter / 132-section tree through the existing BookRuntime data.
4. Every enabled book must be runtime-ready; no silent degraded course is produced.
5. Course manifest paths cannot escape the repository root.
6. Existing `BookRuntime` tests remain green.
7. New CourseRuntime tests pass on Python 3.11, 3.12, and 3.13.
8. No duplicate parsing or alternative readiness logic is added outside BookRuntime.
9. Runtime documentation no longer claims the finalized Functional Analysis fixture is blocked.

## 18. Follow-on milestone

After Phase 1B, the next isolated feature should be the Section learning-shell contract:

```text
Section
├── Preview
├── Learn
├── Review
└── Practice
```

That milestone should consume CourseRuntime/BookRuntime data and define progress boundaries, but it should not be folded into Phase 1B.
