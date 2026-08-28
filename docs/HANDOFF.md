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

Foundation A Tasks 1–8 are complete.

### Task 7 — Executable architecture fitness functions

- RED: `ac9cdd62fe38d683079d6f5aa63a0895ea09c1b0`
- GREEN: `bf49326b0e54c20b4e24a36cb56c1485a5cd6a16`
- exact-head: `e0a303a51a3c4ac8cc1970ece067260b7d17a57c`
- Fitness 6 / 6; Python full 188 / 188; Runtime #154 all Python versions success; App UI #210 success; Chromium 11 / 11.

### Task 8 — Compiler and validator CLI entry points

- RED: `dc127a67f01bfdf7c8a786b2e7bab1ebc803d20c`; 192-test discovery showed the intended missing CLI/public-export failures.
- Functional implementation completed through `1ef50ebe284adff6c33218e6d7d8d2a43f472756`.
- exact-head verification: `116cf4275b8006bc48860943c8e50987547cb5a5`.
- Course Package CLI focused tests: 4 / 4 PASS.
- Python 3.13 full discovery: 192 / 192 PASS.
- Runtime reference tests #156: Python 3.11 / 3.12 / 3.13 all success; Functional Analysis remained `READY` with 8 chapters, 132 sections, 1493 search records, 442 PDF pages and printed final page 423.
- Book App UI tests #212: App API, Web tests, TypeScript typecheck, production build and browser acceptance all success.
- real Chromium acceptance: 11 / 11 PASS.
- Task 8 diff from the Task 7 governance checkpoint contains only `course_package/__init__.py`, `tests/test_course_package_cli.py`, `tools/compile_course_package.py`, and `tools/validate_course_package.py`; no `books/functional-analysis/**` path changed.
- Compile CLI returns stable JSON/exit contracts and confines CLI output roots to the repository; validator CLI independently validates generated packages; invalid paths return argparse exit 2 without traceback leakage.

## Current next task

**Task 9 — Layer CI Into FAST, PR FULL, and HEAVY Gates**

Authoritative plan: `docs/superpowers/plans/2026-08-28-foundation-a-course-package.md`.

Files:
- create `.github/workflows/course-package-fast.yml`
- create `.github/workflows/course-package-heavy.yml`
- modify `.github/workflows/runtime-reference-tests.yml`
- modify `.github/workflows/app-ui-tests.yml`

Required behavior:
- FAST: Python 3.13 syntax + focused Foundation tests + architecture fitness for Foundation-path pushes/PRs.
- Runtime PR FULL: Foundation paths trigger existing 3.11/3.12/3.13 matrix; Python 3.13 also compiles/validates the Golden Course Package and runs architecture fitness.
- App PR FULL: Foundation paths trigger existing app-api/web-client/browser-acceptance jobs with no App source changes.
- HEAVY: manual clean-checkout rebuild/recovery/readiness + Golden compile/validate + fitness; never commits rebuilt canonical candidates back to the repository.

## Protected facts and boundaries

Functional Analysis Golden Course remains:
- `functional_analysis_course`
- `stein_shakarchi_functional_analysis_2011`
- 8 chapters / 132 sections / 1493 search records / 442 PDF pages / printed final page 423
- `STRUCTURED_COMPLETE` / Runtime `READY`

Foundation A must not modify `books/functional-analysis/**` and must not migrate Runtime/App consumers.

## Pending synchronization

`governance/pending_sync.json` has no blocking item. External fixed-commit source archives and Drive raw-source SHA-256 remain pending non-blocking and must not be marked complete without verified evidence.

## Merge rule

Do not write `main` directly. Continue on the non-default branch. Open a reviewable PR only at the planned integration checkpoint and merge only after explicit authorization for that specific PR and required checks.
