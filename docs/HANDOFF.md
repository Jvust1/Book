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

Foundation A Tasks 1–5 are complete.

Task 5 TDD/verification checkpoints:

- RED contract commit: `b198f97068137e6deb787c60762501cd0440decc`; Runtime #149 and Book App UI #205 concluded `failure` before validator implementation.
- GREEN validator implementation: `9d92a166d45aaf6493ae2ab9466031a0d69d62b6`.
- exact-head verification: `b133e32c3355f0cac8478beaea960e81c2144b61`.
- Runtime reference tests #150: Python 3.11 / 3.12 / 3.13 all `success`; Python 3.13 full discovery 179 / 179 PASS.
- validator coverage: 12 / 12 PASS, including schema, primary-role, path escape, artifact missing/hash mismatch, identity drift, structural drift, readiness, and secret-key fail-closed cases.
- Book App UI tests #206: App API, Web tests, TypeScript typecheck, production build, and real Chromium acceptance all `success`.
- Functional Analysis Runtime remained `READY`; Task 5 implementation did not modify `books/functional-analysis/**`.

## Current next task

**Task 6 — Freeze Functional Analysis as the Golden Course Gate**

Implement by TDD according to:

`docs/superpowers/plans/2026-08-28-foundation-a-course-package.md`

Task 6 must add only:

- `tests/golden/functional_analysis_course_package_baseline.json`
- `course_package/golden.py`
- `tests/test_golden_course_package.py`

The gate must verify the frozen Functional Analysis baseline, require validator `PASS`, prove deterministic compile/package bytes, and prove canonical `books/functional-analysis/**` remains byte-identical before/after verification. Baseline mismatch must fail closed; the gate must never repair or rewrite canonical textbook evidence.

## Protected facts

Functional Analysis Golden Course:

- course: `functional_analysis_course`
- book: `stein_shakarchi_functional_analysis_2011`
- 8 chapters
- 132 sections
- 1493 search records
- 442 PDF pages
- final printed page 423
- `STRUCTURED_COMPLETE`
- Runtime `READY`

Foundation A must not write `books/functional-analysis/**` or migrate the existing Runtime/App consumer.

## Pending synchronization

`governance/pending_sync.json` currently contains no blocking item. External fixed-commit source archives and the Drive raw-source SHA-256 remain pending non-blocking. Do not mark them complete without the required verified hashes/Drive evidence.

## Merge rule

Do not write `main` directly. Work on the non-default branch, verify the implementation HEAD, open a reviewable PR when the Foundation A branch reaches its planned integration checkpoint, and merge only after explicit authorization for that specific PR and required checks.
