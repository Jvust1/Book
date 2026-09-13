# Phase 1H Task 4 verified checkpoint

Task 4 — deterministic Review presets in Runtime/API — is complete by TDD at branch head `a3f198ff38827cf73fa22bcc8b4a772e7922ace9` before this documentation-only checkpoint commit.

## RED evidence

- Additive Review Runtime test module commit: `a621bba6c5da8a57b2df2ae31674a1da575d1227`.
- Additive Review service/API test module commit: `3cb76ee3dcfe6ef95c07915ed9f1a8fcb160c830`.
- Initial RED run `33297404411`: Runtime discovery had 330 tests with 5 intended failures because Review projection was still the empty scaffold.
- Contract audit re-read the authoritative Task 4 plan and confirmed `five_minute` must fill to 10, not 5.
- Corrective contract test commits:
  - `635630291aac10a4d69a79abb89a4cae48a0d4a7`
  - `62b009d6a1d69f029cd738ee356b327dfe036256`
- Corrective RED run `33297591055`: 330 Runtime tests with exactly 1 intended failure, `test_five_minute_uses_same_diversity_seed_then_fills_to_ten`, proving the interim cap=5 violated the accepted plan.

## GREEN implementation

- `202b3898c6aca89cb861e3b9e45082af0f86a858` implemented deterministic Review projection using only existing `SectionLearningRuntime.review()` candidates, fixed prompt templates, `one_minute` diversity cap 3, full source-order coverage, and closure-safe refs.
- `a3f198ff38827cf73fa22bcc8b4a772e7922ace9` corrected `five_minute` to the authoritative cap 10.
- Presets are:
  - `one_minute` / `1 分钟`
  - `five_minute` / `5 分钟`
  - `full` / `完整复习`

No inferred textbook facts are introduced. No candidate outside the existing Review whitelist is re-included. Search/QA behavior remains unchanged and Exact-only.

## Fresh verification at implementation exact head

- Runtime Reference run `33297639502`: Python 3.11 / 3.12 / 3.13 all success; Python 3.13 runtime rebuild and Golden Course Package gates success.
- Book App UI run `33297639475`: `app-api`, `web-client`, and `browser-acceptance` all success.
- Full Runtime discovery: 330 tests OK.
- Focused App/API/Search/QA/StudyRecord: 147 tests OK.
- Full `app_tests`: 106 tests OK.
- Chromium Playwright: 11/11 passed.
- Web tests, TypeScript typecheck, and production build: success.

## Task 4 delta from Task 3 implementation head `581fd7e...`

Implementation/test delta before this documentation checkpoint is exactly three paths:

- `runtime/learning_slice_runtime.py`
- `tests/test_learning_slice_review.py`
- `app_tests/test_review_learning_slice.py`

The two test files are additive Task 4-specific modules to keep connected remote writes narrow and reviewable instead of rewriting unrelated large test modules.

No `books/functional-analysis/**`, `courses/**`, frontend implementation, Search/QA implementation, or StudyRecord implementation changed in Task 4.

PR #26 remains Draft/unmerged. The next approved ordinary step is **Task 5: Review preset UI and URL/source-round-trip state only**. A generic `下一步` / `继续` after this checkpoint authorizes Task 5 only; it does not authorize merging PR #26 or any destructive/protected action.
