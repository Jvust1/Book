# Phase 1H Task 7 Checkpoint — Practice UI

Date: 2026-08-30  
Repository: `Jvust2/Book`  
Branch: `design/phase-1h-learning-slices-20260830`  
PR: #26 (Draft/open/unmerged)

## Scope

Task 7 only: source-backed Practice filtering and URL/source-round-trip state. No answer store, correctness scoring, AI solution generation, StudyRecord schema change, or canonical-data mutation.

## RED

- `1b679f4278e4cb8e38723b840086a3dc7cd92dec` — component interaction RED tests.
- `1289595f432e4f36d1c3d9bb4c11494daffacbe1` — page URL-state RED tests / RED head.
- Book App UI run `33301561823` failed for the intended missing behavior: no `PracticeLearningSlice`, no `practice_kind` normalization, no dedicated filter rendering, stale selector state, and old generic Practice presentation.
- Existing backend Runtime/App behavior stayed green.

A test-design correction was made before product implementation:
- `a3c5426f11928cabd0c327cfe17424e735619269` — remove an unnecessary expand/collapse requirement and keep Practice textbook body directly visible, consistent with the approved contract.

## GREEN implementation

- `8a237dbfa3d9cc49a055f5d37417a33ee22ad6a8` — add typed Practice filter `source_refs` / `PracticeFilterId` to the web contract.
- `d4e991a167f3f5e4aad769cd36ed9a20ecc45476` — add source-grounded `PracticeLearningSlice`.
- `29b7fbed8f3199756f1f1c0e774e33111f93d02b` — wire `practice_kind` URL state into `SectionPage`.

Behavior:
- valid route states are `all`, `exercise`, `problem`;
- missing/invalid `practice_kind` replace-normalizes to `all`;
- `review_preset` and `practice_kind` never leak across modes;
- filter changes update URL only and do not refetch the mode or retouch StudyRecord;
- Source round-trip preserves the selected filter inside the existing frozen `route` field;
- filters render only refs supplied by the API and fail closed if closure is violated;
- visible count is based on selected source refs;
- cards show canonical textbook content and Source links;
- every item says exactly `教材数据中暂未提供可验证解析`;
- no answer textbox, correctness control, AI answer, localStorage answer state, or durable answer write exists.

## Regression corrections during GREEN

Two existing tests were stale relative to already-approved contracts:

1. `3dc389d1cabff1980d6f9d7d7e31d13e710ad062` — update the old empty-Practice fixture to include required `source_refs: []`. The new Task 7 tests were already green; only the pre-Task6 fixture was malformed.
2. `a803f8f1446fb728a09ef031e318db18b21e78d1` — update an existing Chromium URL assertion from `?mode=practice` to the approved normalized `?mode=practice&practice_kind=all`.

No product behavior was weakened to satisfy these stale assertions.

## Exact-head verification

Verified Task 7 code/test head:

`a803f8f1446fb728a09ef031e318db18b21e78d1`

- Runtime Reference Tests run `33302247337`: completed / success.
- Book App UI Tests run `33302247332`: completed / success.
- `app-api`: success, including full Runtime discovery, canonical readiness, focused App/API/Search/QA/StudyRecord suite, and full App discovery.
- `web-client`: 81/81 tests passed, TypeScript typecheck success, production build success.
- `browser-acceptance`: Chromium success; all 12 existing real-browser scenarios passed.

## Scope diff from Task 6 checkpoint

Compared from `950ca7018692506fd32cf94c46903015d666e5a2` to verified Task 7 head `a803f8f1446fb728a09ef031e318db18b21e78d1`:

- 8 commits
- 7 changed files

Changed paths:
- `app/web/src/api/types.ts`
- `app/web/src/components/PracticeLearningSlice.tsx`
- `app/web/src/components/PracticeLearningSlice.test.tsx`
- `app/web/src/pages/SectionPage.tsx`
- `app/web/src/pages/SectionPage.test.tsx`
- `app/web/src/pages/SectionPage.practice.test.tsx`
- `app/web/e2e/functional-analysis.spec.ts` (test-only normalized URL expectation)

No backend Runtime/API implementation, Search/QA implementation, StudyRecord implementation/schema, `books/functional-analysis/**`, or `courses/**` file changed in Task 7.

## Preserved invariants

- Search/QA = `EXACT_ONLY_UNCHANGED`.
- H4a = `FTS_EVIDENCE_NOT_PROMISING`.
- StudyRecord semantics/schema unchanged.
- frozen Section sessionStorage shape unchanged: `route`, `scrollY`, `expandedSourceIds`, `activeSourceId`.
- canonical textbook/course data unchanged.
- H3b/B4b/B5, book-version migration, multi-book consumer migration, FTS/BM25 production ranking, Lecture authority remain inactive.
- PR #26 remains Draft/open/unmerged.

## Next

Task 7 is complete. Next plan item: **Task 8 — Learn type-aware grouping in Runtime/API**. Broad continuation authorization permits this ordinary reversible next task; it does not authorize PR merge or any destructive/protected operation.