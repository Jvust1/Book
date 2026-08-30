# Phase 1H Task 8 — Learn grouped Runtime/API checkpoint

Date: 2026-08-30
Repository: `Jvust2/Book`
Branch: `design/phase-1h-learning-slices-20260830`
PR: `#26` (OPEN / DRAFT / UNMERGED)
Implementation commit: `7a29a74cf97ea593de17edc8a14ef2b1989bd564`

## RED evidence

- Test commit: `4b03a40398dbbe23c3fe57f5750299f27b5c5e0e`
- Runtime Reference at the PR integration ref observed the intended failure: 345 tests with 4 failures and 2 errors.
- Failures were confined to the new Learn grouping contract: `LearningSliceRuntime.learn()` still returned empty `groups`, causing missing groups/refs and closure assertions to fail.
- Existing Search/QA Exact-only behavior and unrelated Runtime tests remained green at the RED checkpoint.

## GREEN implementation

`LearningSliceRuntime.learn()` now:

- partitions current Learn candidates into mutually exclusive groups in fixed order: definitions, theorem_family, formulas, examples, other_objects, figures, translations;
- preserves source order inside each group and omits empty groups;
- keeps formula-bearing theorems/definitions in their type group instead of duplicating them into formulas;
- emits only source refs/derived metadata and keeps supplementary/lecture extensions explicitly unavailable;
- validates candidate identities and fails closed on unavailable/duplicate Learn source refs.

## Exact-head verification

- Runtime Reference Tests run `33304001568`: SUCCESS on Python 3.11 / 3.12 / 3.13 (345 tests each).
- Book App UI Tests run `33304001491`: SUCCESS.
- web-client: 16 files / 81 tests; typecheck and production build: PASS.
- app-api: Runtime 345, focused 147, full App 109: PASS.
- real Chromium acceptance: 12 / 12 PASS.

Task 9 Learn grouped UI is the next ordinary step. PR `#26` remains Draft/unmerged; no merge is implied by this checkpoint.
