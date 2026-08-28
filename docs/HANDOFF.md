# Book Handoff

Updated: 2026-08-28

## Start here

1. Read Google Drive root `全项目`.
2. Dynamically read every root file beginning `全项目_`.
3. Read `AGENTS.md` and `SECURITY_POLICY.md`.
4. Read:
   - `governance/project_state.json`
   - `docs/PROJECT_NORTH_STAR.md`
   - `docs/ARCHITECTURE_INVARIANTS.md`
   - `docs/CURRENT_STATE.md`
   - `docs/DECISION_LEDGER.md`
   - `docs/EVALUATION_LEDGER.md`
   - `governance/artifact_manifest.json`
   - `governance/pending_sync.json`
   - `docs/PRE_FLIGHT_CHECKLIST.md`
5. Then read the active phase Spec/Plan.

Repository evidence outranks chat memory.

## Current branch and phase

- Repository: `Jvust1/Book`
- Default protected branch: `main`
- Active development branch: `foundation/course-package-contract-a`
- Phase: `Foundation A — Course Package Contract`
- Main base for this branch: `a99d4638f959e04e54d91efe0ee0dd9ac50488a6`

Foundation A Tasks 1–4 are complete. The last implementation verification HEAD before the source-review documentation checkpoint was:

`df5346c0598495bf8e84f5d214afbf2e9cd55c63`

Source-level external comparison was then recorded at:

`16ee8acfafda4558dbbc30a2cfbd1f7d51a5d0d6`

## Current next task

**Task 5 — Course Package Validator**

Implement by TDD according to:

`docs/superpowers/plans/2026-08-28-foundation-a-course-package.md`

Validator hardening from the source-level review:

1. closed contract shape + forbidden secret-like keys
2. path boundary checks before referenced-file reads
3. exact required artifacts and exactly one primary
4. artifact SHA-256 / content identity verification
5. independent `package_identity` recomputation
6. structural baseline checks
7. Book/runtime readiness aggregation
8. deterministic diagnostics and final `PASS / WARN / FAIL`

A stored package `PASS` never overrides an independently discovered failure.

## Protected facts

Functional Analysis Golden Course:

- 8 chapters
- 132 sections
- 1493 search records
- 442 PDF pages
- final printed page 423
- `STRUCTURED_COMPLETE`
- Runtime `READY`

Foundation A must not write `books/functional-analysis/**` or migrate the existing Runtime/App consumer.

## Pending synchronization

`governance/pending_sync.json` currently contains no blocking item. External fixed-commit source archives are pending non-blocking until a verified archival execution path is available for Book. Do not mark them archived without exact snapshot hash + Drive file ID.

## Merge rule

Do not write `main` directly. Work on the non-default branch, verify exact final HEAD, open a reviewable PR, and merge only after explicit authorization for that specific PR and required checks.
