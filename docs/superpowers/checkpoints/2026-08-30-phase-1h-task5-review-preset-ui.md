# Phase 1H Task 5 Checkpoint — Review Preset UI

Date: 2026-08-30  
Repository: `Jvust2/Book`  
Branch: `design/phase-1h-learning-slices-20260830`  
Pull request: #26 (Draft, open, unmerged)

## Scope

Task 5 only: render the deterministic Review learning slice and make preset selection a URL-owned presentation state while preserving the existing Section source round-trip and StudyRecord contracts.

Implemented scope:

- Add `ReviewLearningSlice` for the three runtime-provided presets:
  - `one_minute` / `1 分钟`
  - `five_minute` / `5 分钟`
  - `full` / `完整复习`
- Render the deterministic recall prompt supplied by `presentation.prompts`.
- Keep textbook body hidden until an explicit reveal action.
- Resolve displayed rows strictly from the selected preset's `source_refs` and the current mode payload.
- Fail closed with `学习内容暂不可用` if the Review projection cannot be closed against the current items/prompts.
- Add `review_preset` URL state to the Section page.
- Normalize missing or invalid Review preset values to `full` with replace-style navigation.
- Remove `review_preset` when leaving Review mode.
- Preserve the existing source-navigation round trip, including selected preset plus frozen Section view state.
- Add real Chromium acceptance coverage for Review preset selection, reveal, textbook-source navigation, and restoration.

Out of scope and unchanged:

- Practice Runtime/API/UI.
- Learn slice UI.
- StudyRecord schema or progress semantics.
- Search/QA Exact-only behavior.
- FTS/BM25 production ranking.
- H3b, B4b, B5, multi-book consumer migration, StudyRecord book-version migration, Lecture authority, and other separately gated designs.
- Canonical textbook/course data.

## RED checkpoint

RED was established before production implementation with additive tests:

- `d76079d569b7ed7a81dc8a0bb099b294d51cc782` — `test: define Phase 1H review preset component behavior`
- `3e2998e7f4ec0345daee101f5bbf95573cd446d6` — `test: define Phase 1H review preset URL behavior`
- `ba7c59e133ed7da0a4c6779995c1fa01a48ef571` — `test: add real Review preset source round trip`

At `3e2998e7f4ec0345daee101f5bbf95573cd446d6`, Book App UI workflow run `33298874682` failed in the web-client test step while the App/API regression job remained green. Runtime reference tests also remained green. The failure was the intended product gap: the Review preset component/page URL behavior had not yet been implemented.

## GREEN implementation

Production and regression-alignment commits:

- `b5456c818b59edeaa62c483276342dac61adb469` — `feat: add Review preset learning slice`
- `38450663f7b24f1f97f9cb5e350b5e0dd6e5bd9e` — `test: align SectionPage review fixtures with presentation`
- `1c5f22474de510a38d2ea787c9e78227a9d6dcc0` — `test: align Review regression expectations`
- `2fac7b272b201a75d278b080f7c3e1ab7c9e05f3` — `fix: align Review preset UI with existing API types`
- `dcad0f6ad77a4a23e2b9d1b9a0b0b0cc76bf341a` — `fix: export Review preset id type`
- `5967c9964735acdf5ef6de1304f6bc64136ab3bd` — `test: align Review desktop URL assertion`

`ReviewPresetId` is a compile-time TypeScript alias derived from `LearningSlicePreset['id']`; it does not change the JSON/API DTO shape.

## URL and state contract

Canonical Review URL state:

```text
?mode=review&review_preset=<one_minute|five_minute|full>
```

Rules:

- Missing `review_preset` in Review mode normalizes to `full`.
- Invalid `review_preset` in Review mode normalizes to `full`.
- Preset selection changes URL state only; it does not trigger another Review mode fetch and does not touch StudyRecord.
- Leaving Review mode removes `review_preset`.
- Preset selection is not copied into sessionStorage or localStorage.
- Reveal state continues to use the existing frozen `expandedSourceIds` field.
- The frozen Section sessionStorage shape remains exactly:
  - `route`
  - `scrollY`
  - `expandedSourceIds`
  - `activeSourceId`

The stored `route` includes the Review URL, so the source round trip naturally restores the selected preset without adding a new persistence field.

## Review presentation contract

`ReviewLearningSlice` treats the API projection as authoritative:

- `presentation.presets` defines the available preset labels and source-reference membership.
- `presentation.prompts` supplies the deterministic recall prompt for each referenced object.
- The component does not derive a competing Review subset from local heuristics.
- Textbook body is hidden until the user explicitly selects `显示教材内容`.
- Reveal/collapse is presentation state only and does not create or advance StudyRecord progress.
- A source link saves the existing Section view state before navigation.
- Returning from the source restores the Review URL/preset plus the existing reveal/scroll/active-source state.
- Missing/mismatched projection references fail closed with the stable user message `学习内容暂不可用`.

## Exact-head verification

Verified code head:

`5967c9964735acdf5ef6de1304f6bc64136ab3bd`

### Runtime reference tests

Workflow run: `33299719369` — success.

- Python 3.11 — success
- Python 3.12 — success
- Python 3.13 — success

### Book App UI tests

Workflow run: `33299719380` — success.

`app-api` job:

- Full Runtime regression discovery — success
- Canonical Functional Analysis readiness — success
- App service/API/source/search/QA/StudyRecord tests — success
- Full App regression discovery — success

`web-client` job:

- Vitest test files: 14 passed
- Vitest tests: 71 passed
- TypeScript typecheck — success
- Production build — success

`browser-acceptance` job:

- Chromium acceptance tests: 12 passed / 12 total
- Includes `real Review preset URL and source round trip preserve selected preset and reveal state`
- Existing Functional Analysis source/search/QA/narrow-layout round trips remain green.
- Existing StudyRecord persistence acceptance remains green.

Before the final assertion alignment, Chromium already passed the new Review round-trip test; its sole failure was an older desktop test still expecting `?mode=review` instead of the new canonical `?mode=review&review_preset=full`. Commit `5967c9964735acdf5ef6de1304f6bc64136ab3bd` changed only that stale assertion, after which the exact-head browser suite passed 12/12.

## Preserved invariants

- Search/QA remains `EXACT_ONLY_UNCHANGED`.
- StudyRecord semantics remain unchanged:
  - no row = not started
  - `in_progress` = 0
  - `completed` = 100
  - mode payload loads before touch
  - preset/reveal/view actions do not create progress
  - completion remains explicit/manual and non-regressing
- No StudyRecord schema change.
- Frozen Section sessionStorage shape is unchanged; Review preset ownership is URL-only.
- Canonical `books/functional-analysis/**` and `courses/**` data were not modified.
- No backend Runtime/API behavior was changed by Task 5.
- H3b, B4b, B5, StudyRecord book-version migration, multi-book consumer migration, FTS/BM25 production ranking, Lecture authority, and other separate gates remain inactive.
- PR #26 remains Draft/open/unmerged.

## Scope diff

Compared from Task 4 checkpoint `461999e...` to Task 5 verified code head `5967c9964735acdf5ef6de1304f6bc64136ab3bd`:

- 9 commits
- 8 changed files
- `+703 / -70`
- All changed product/test files are under `app/web/**`.
- No backend Runtime, API service/model, canonical textbook data, or StudyRecord schema file changed.

Changed files:

- `app/web/e2e/functional-analysis.spec.ts`
- `app/web/e2e/review-presets.spec.ts`
- `app/web/src/api/types.ts`
- `app/web/src/components/ReviewLearningSlice.test.tsx`
- `app/web/src/components/ReviewLearningSlice.tsx`
- `app/web/src/pages/SectionPage.review.test.tsx`
- `app/web/src/pages/SectionPage.test.tsx`
- `app/web/src/pages/SectionPage.tsx`

## Next checkpoint

Task 5 is GREEN and checkpointed at code head `5967c9964735acdf5ef6de1304f6bc64136ab3bd`.

The next implementation-plan item is Task 6 — Practice Runtime/API — but it is not started by this checkpoint. It requires a separate ordinary continuation instruction. No merge is authorized by this checkpoint.