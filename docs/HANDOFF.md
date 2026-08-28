# Book Handoff

Updated: 2026-08-29

## Start here

1. Read Google Drive root `全项目` and current `全项目_*` governance baselines.
2. Read `AGENTS.md` and `SECURITY_POLICY.md` on the exact target branch.
3. Read `governance/project_state.json`, project invariants/current state/decision and evaluation ledgers, pending sync, preflight, then the active Foundation A design and plan.

Repository evidence outranks chat memory.

## Current branch and phase

- Repository: `Jvust1/Book`
- Default protected branch: `main`
- Active development branch: `foundation/course-package-contract-a`
- Phase: `Foundation A — Course Package Contract`
- Main base: `a99d4638f959e04e54d91efe0ee0dd9ac50488a6`

Foundation A Tasks 1–7 are complete.

### Task 5 — Fail-closed Course Package validator

- RED: `b198f97068137e6deb787c60762501cd0440decc`
- GREEN: `9d92a166d45aaf6493ae2ab9466031a0d69d62b6`
- exact-head: `b133e32c3355f0cac8478beaea960e81c2144b61`
- Runtime #150 and Book App UI #206: success
- validator 12 / 12; Python full discovery 179 / 179

### Task 6 — Functional Analysis Golden Course gate

- RED: `9b68187c2c0adf4b364c41b42c47ab1a3756219b`
- GREEN: `6823c9c806a9175b4e4444345b40cf406fa5dde2`
- exact-head: `eeb2d4adee699d44924ed2ebfc2207df595f9ed6`
- Runtime #152 and Book App UI #208: success
- Golden 3 / 3; Python full discovery 182 / 182; Chromium 11 / 11

### Task 7 — Executable architecture fitness functions

- RED: `ac9cdd62fe38d683079d6f5aa63a0895ea09c1b0`; expected failure because `course_package.fitness` did not yet exist.
- GREEN: `bf49326b0e54c20b4e24a36cb56c1485a5cd6a16`.
- exact-head: `e0a303a51a3c4ac8cc1970ece067260b7d17a57c`.
- Architecture fitness focused coverage: 6 / 6 PASS.
- Python 3.13 full discovery: 188 / 188 PASS.
- Runtime #154: Python 3.11 / 3.12 / 3.13 jobs all success; Functional Analysis remained `READY` with 8 chapters, 132 sections, 1493 search records, 442 PDF pages, final printed page 423, and no identity/readiness drift.
- Book App UI #210: App API, Web tests, TypeScript typecheck, production build and real Chromium acceptance all success; Chromium 11 / 11 PASS.
- Task 7 diff from the Task 6 governance checkpoint contains only `course_package/fitness.py`, `tools/check_architecture_fitness.py`, and `tests/test_architecture_fitness.py`; it does not modify `books/functional-analysis/**`.

## Current next task

**Task 8 — Add Compiler and Validator CLI Entry Points**

Authoritative plan: `docs/superpowers/plans/2026-08-28-foundation-a-course-package.md`.

Files:
- create `tools/compile_course_package.py`
- create `tools/validate_course_package.py`
- create `tests/test_course_package_cli.py`
- modify `course_package/__init__.py`

Required CLI contracts:
- compile: `python tools/compile_course_package.py courses/functional-analysis --repository-root . --output-root .build/course-packages`
- compile JSON: `status`, `course_id`, `package_identity`, `package_dir`; exit 0 success, 1 compile/validation failure, 2 invalid invocation
- validate: `python tools/validate_course_package.py <package-dir> --repository-root .`
- validate JSON: `status`, `diagnostics`; exit 0 PASS/WARN, 1 FAIL, 2 invalid invocation
- invalid paths must return 2 without Python traceback leakage in stdout JSON
- `course_package.__init__` exports compiler, Golden, and validator public APIs specified by the plan

Use TDD RED -> GREEN, then focused Foundation tests and exact-head Runtime/App regression verification.

## Protected facts and boundaries

Functional Analysis Golden Course remains:
- `functional_analysis_course`
- `stein_shakarchi_functional_analysis_2011`
- 8 chapters / 132 sections / 1493 search records / 442 PDF pages / printed final page 423
- `STRUCTURED_COMPLETE` / Runtime `READY`

Foundation A must not modify `books/functional-analysis/**` and must not migrate Runtime/App consumers.

## Pending synchronization

`governance/pending_sync.json` has no blocking item. External fixed-commit source archives and the Drive raw-source SHA-256 remain pending non-blocking and must not be marked complete without verified evidence.

## Merge rule

Do not write `main` directly. Continue on the non-default branch. Open a reviewable PR only at the planned integration checkpoint and merge only after explicit authorization for that specific PR and required checks.
