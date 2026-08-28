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

Foundation A Tasks 1–6 are complete.

### Task 5 — Fail-closed Course Package validator

- RED: `b198f97068137e6deb787c60762501cd0440decc`.
- GREEN: `9d92a166d45aaf6493ae2ab9466031a0d69d62b6`.
- exact-head verification: `b133e32c3355f0cac8478beaea960e81c2144b61`.
- Runtime #150 and Book App UI #206: success.
- validator coverage: 12 / 12 PASS; Python full discovery: 179 / 179 PASS.

### Task 6 — Functional Analysis Golden Course gate

- RED: `9b68187c2c0adf4b364c41b42c47ab1a3756219b`; new Golden test failed because `course_package.golden` did not yet exist.
- GREEN: `6823c9c806a9175b4e4444345b40cf406fa5dde2`.
- exact-head verification: `eeb2d4adee699d44924ed2ebfc2207df595f9ed6`.
- Runtime reference tests #152: success on Python 3.11 / 3.12 / 3.13; Python 3.13 full discovery 182 / 182 PASS and Golden gate 3 / 3 PASS.
- Book App UI tests #208: App API, Web tests, TypeScript typecheck, production build, and real Chromium acceptance all success; Chromium 11 / 11 PASS.
- Golden gate verifies frozen values, validator PASS, deterministic package identity/bytes, and canonical tree byte identity.
- Task 6 implementation diff contains only `course_package/golden.py`, the Golden baseline JSON, and Golden tests; no `books/functional-analysis/**` path changed.

## Current next task

**Task 7 — Add Executable Architecture Fitness Functions**

Implement by TDD according to:

`docs/superpowers/plans/2026-08-28-foundation-a-course-package.md`

Task 7 files:

- `course_package/fitness.py`
- `tools/check_architecture_fitness.py`
- `tests/test_architecture_fitness.py`

Active Foundation A fitness rules now:

1. browser source under `app/web/src/**` must not use Python `sqlite3`, direct `sqlite://` URLs, or `.sqlite3` durable-storage filenames;
2. compiler/validator outputs must remain outside canonical `books/**` and `courses/**`;
3. real Golden compile/validation must leave the canonical Functional Analysis Book tree byte-identical;
4. compiled package must contain no absolute paths;
5. compiled package must contain no secret-like fields;
6. primary-role, artifact-hash, deterministic identity and Golden identity checks delegate to the existing validator/Golden gate.

The fitness runner must aggregate diagnostics rather than repair or mutate project evidence. CLI JSON exit contract: PASS/WARN => 0, FAIL => 1, invalid invocation => 2.

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
