# Phase 1H Task 6 Checkpoint — Practice Runtime/API

Date: 2026-08-30  
Repository: `Jvust2/Book`  
Branch: `design/phase-1h-learning-slices-20260830`  
Pull request: #26 (Draft, open, unmerged)

## Scope

Task 6 only: implement the deterministic Practice learning-slice projection and its typed API contract without starting Practice UI work.

Implemented scope:

- Treat `SectionLearningRuntime.practice()` as the sole Practice candidate authority.
- Preserve the existing candidate order.
- Emit the `all` filter unconditionally with label `全部`.
- Emit the `exercise` filter with label `练习` only when an exercise candidate exists.
- Emit the `problem` filter with label `习题` only when a problem candidate exists.
- Attach ordered `source_refs` to every emitted Practice filter.
- Emit one Practice presentation item per current Practice candidate.
- Mark every Practice item explicitly as `solution_status = "unavailable"`.
- Keep an empty Practice projection valid: empty `all.source_refs`, no subtype filters, and no items.
- Keep all Practice presentation refs closed over the current Practice mode items.
- Extend the existing typed `LearningSlicePracticeFilter` API DTO with the required `source_refs` field so filter membership survives Pydantic serialization.
- Add Runtime, service, and HTTP serialization tests for the Practice contract.

Out of scope and unchanged:

- Practice React/UI and URL filter state (Task 7).
- Learn Runtime/API/UI.
- Search/QA behavior.
- StudyRecord schema or progress semantics.
- Canonical textbook/course data.
- FTS/BM25 production ranking.
- H3b, B4b, B5, multi-book consumer migration, StudyRecord book-version migration, Lecture authority, and other separately gated designs.

## Source and solution semantics

Practice does not infer solutions from textbook body text or any other free text.

The projection does not inspect `content_zh`, translations, Search, QA, or other text to decide whether a solution exists. Test fixtures deliberately place `solution` / `解析` sentinel text in canonical source bodies; the resulting `presentation` still contains only source references and `solution_status = "unavailable"`.

Canonical mode items continue to carry their existing source body fields. The no-inference/no-duplication guarantee applies to the deterministic Practice `presentation`, not to removal of canonical source content from the parent mode response.

## RED checkpoint

RED was established before production implementation with additive tests:

- `3e1e968e5fd2857fbe092b6a2b36e8d8e2bcf607` — `test: define Practice learning slice runtime filters`
- `91df996a3b730027d95ed1633918c80cc65b841b` — `test: define Practice learning slice API contract`

At RED head `91df996a3b730027d95ed1633918c80cc65b841b`, Runtime workflow run `33300804790` produced the intended failures in the new Practice contract tests:

- Practice filters had no `source_refs`.
- Conditional `exercise` / `problem` filters did not exist.
- Practice presentation items were empty.
- Projection-level Practice source references were absent.
- Empty Practice did not expose the required empty `all.source_refs` contract.

Existing Review and other Runtime regression tests remained green. The RED therefore isolated the missing Task 6 behavior rather than an unrelated regression.

## GREEN implementation

Production commits:

- `eae23e25fc65e7f7030b16b7a048cf7a986c8baf` — `feat: add Practice filters with explicit solution state`
- `7c67d01be4fd57b00de2451aef473c467e8be91b` — `feat: expose Practice filter source refs`

Implementation details:

- `LearningSliceRuntime.practice()` resolves the current Practice candidates through a dedicated `_practice_rows()` path.
- Candidate identity is mapped back to current source objects without changing candidate order.
- A candidate must resolve as an object whose normalized type is exactly `exercise` or `problem`; otherwise projection fails closed with `LearningSliceIntegrityError`.
- Filter membership is represented by `source_refs`; no body text is copied into `presentation`.
- Practice items contain only their canonical `source_ref` plus `solution_status = "unavailable"`.
- The existing generic projection walker collects the nested filter/item refs for service closure validation.
- `LearningSlicePracticeFilter` gains only `source_refs: list[SourceRef]`; no unrelated API DTO is changed.

## Test-only assertion corrections during GREEN

Two GREEN runs exposed overly broad assertions in the new tests, not product defects. Both corrections were test-only:

1. `1898f3dc0c583da1e2e2314f892eea2bf8999152` — `test: narrow Practice no-solution body assertion`
   - The original Runtime test prohibited the substring `solution`, which incorrectly matched the legitimate field name `solution_status`.
   - The assertion was narrowed to the injected body sentinel text.

2. `53aa03bd50195eaaaa0c54994231c0b33b91cb90` — `test: scope Practice API body assertion to presentation`
   - The original API test prohibited the sentinel in the whole HTTP response even though canonical top-level `items[].content_zh` intentionally preserves textbook body text.
   - The assertion was correctly scoped to `payload["presentation"]`, which is the surface governed by the Practice no-solution-inference contract.

No production code changed in either correction.

## Exact-head verification

Verified code head:

`53aa03bd50195eaaaa0c54994231c0b33b91cb90`

### Runtime reference tests

Workflow run: `33301144069` — success.

- Python 3.11 — success
- Python 3.12 — success
- Python 3.13 — success
- Full Runtime regression discovery — success
- Functional Analysis runtime rebuild and Golden package gates — success on Python 3.13

The App/API workflow independently reran full Runtime discovery at the same Task 6 code state: **337 tests passed**.

### Book App UI tests

Workflow run: `33301144134` — success.

`app-api` job:

- Full Runtime regression discovery: **337 tests passed**
- Canonical Functional Analysis readiness: **READY**
- Focused App service/API/source/search/QA/StudyRecord suite: **147 tests passed**
- Full `app_tests` discovery: **109 tests passed**
- New Practice service/API serialization tests passed.

`web-client` job:

- Vitest files: **14 passed / 14 total**
- Vitest tests: **71 passed / 71 total**
- TypeScript typecheck — success
- Production build — success

`browser-acceptance` job:

- Chromium Playwright: **12 passed / 12 total**
- Existing Functional Analysis source/search/QA/narrow-layout round trips remain green.
- Existing Review preset URL/source round trip remains green.
- Existing StudyRecord persistence acceptance remains green.

Task 6 intentionally adds no Practice UI or Task 7 browser behavior, so the browser suite is regression/isolation evidence for this backend/API-only task.

## Preserved invariants

- Search/QA remains `EXACT_ONLY_UNCHANGED`.
- H4a remains `FTS_EVIDENCE_NOT_PROMISING`.
- StudyRecord semantics remain unchanged:
  - no row = not started
  - `in_progress` = 0
  - `completed` = 100
  - mode payload loads before touch
  - filter/preset/reveal/view actions do not create or advance progress
  - completion remains explicit/manual and non-regressing
- No StudyRecord schema change.
- Frozen Section sessionStorage shape remains unchanged:
  - `route`
  - `scrollY`
  - `expandedSourceIds`
  - `activeSourceId`
- Canonical `books/functional-analysis/**` and `courses/**` were not modified.
- No Search/QA implementation was modified.
- No frontend implementation was modified.
- H3b, B4b, B5, StudyRecord book-version migration, multi-book consumer migration, FTS/BM25 production ranking, Lecture authority, and other separate gates remain inactive.
- PR #26 remains Draft/open/unmerged.

## Scope diff

Compared from the Task 5 checkpoint commit `860fd31cdfe7c0530fa662ec11254044d69c8519` to verified Task 6 code head `53aa03bd50195eaaaa0c54994231c0b33b91cb90`:

- 6 commits
- 4 changed files
- `+336 / -2`

Changed files:

- `runtime/learning_slice_runtime.py`
- `app/api/models.py`
- `tests/test_learning_slice_practice.py`
- `app_tests/test_practice_learning_slice.py`

No frontend, service, StudyRecord, Search/QA, canonical textbook, or course-data file changed.

## Next checkpoint

Task 6 is GREEN and checkpointed at verified code head `53aa03bd50195eaaaa0c54994231c0b33b91cb90`.

The next implementation-plan item is **Task 7 — Practice UI and URL/source-round-trip state**. It is not started by this checkpoint and requires a separate ordinary continuation instruction.

No merge is requested or authorized by this checkpoint.