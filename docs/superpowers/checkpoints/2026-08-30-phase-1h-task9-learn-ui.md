# Phase 1H Task 9 — Learn grouped UI checkpoint

Date: 2026-08-30
Repository: Jvust2/Book
Branch: design/phase-1h-learning-slices-20260830
PR: #26 (OPEN / DRAFT / UNMERGED)
Learn UI implementation: 5a64e7b58d9d97af81de8dd5564306124af54f21
Exact verified head: 74c2e00b0e279b4cd3096783741ee0aada5a6b6c

## RED evidence

- RED test commit: 5d7f29e1fe8f2d16eac86ba2ed9ac6cb9fdf3b39
- Real UI RED: the new Learn component import was unresolved and the existing SectionPage test fixture still supplied items with empty Learn groups.
- The pre-existing web suite otherwise remained green (81 tests before the new contract).

## GREEN implementation

- Added LearnLearningSlice to render only non-empty source-backed groups in presentation order.
- Reused LearningObjectCard for object groups, preserving canonical formula/content and Source navigation.
- Added metadata-only FigureReferenceCard; no image discovery or fabricated img.
- Added translation availability card and generic fail-closed handling for missing/mismatched refs.
- SectionPage now dispatches one focused Learn branch and no longer renders the old flat Learn list alongside grouped presentation.
- Updated only the old test fixture to satisfy the now-required grouped Learn contract; product schema and runtime authority are unchanged.

## Exact-head verification

- Runtime Reference Tests run 33304524899: SUCCESS on Python 3.11 / 3.12 / 3.13 (345 tests each).
- Book App UI Tests run 33304524902: SUCCESS.
- web-client: 17 files / 87 tests; typecheck and production build: PASS.
- app-api: Runtime 345, focused 147, full App 109: PASS.
- real Chromium acceptance: 12 / 12 PASS.

Task 10 isolation + frozen Golden/Chromium acceptance is the next ordinary step. PR #26 remains Draft/unmerged; no merge is implied.
