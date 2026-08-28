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

Foundation A Tasks 1–9 are complete. Task 10 exact-final-HEAD / PR readiness is in progress.

### Task 7 — Executable architecture fitness functions

- RED: `ac9cdd62fe38d683079d6f5aa63a0895ea09c1b0`
- GREEN: `bf49326b0e54c20b4e24a36cb56c1485a5cd6a16`
- exact-head: `e0a303a51a3c4ac8cc1970ece067260b7d17a57c`
- Fitness 6 / 6; Python full 188 / 188; Runtime #154 all Python versions success; App UI #210 success; Chromium 11 / 11.

### Task 8 — Compiler and validator CLI entry points

- RED: `dc127a67f01bfdf7c8a786b2e7bab1ebc803d20c`
- Functional implementation completed through `1ef50ebe284adff6c33218e6d7d8d2a43f472756`.
- exact-head verification: `116cf4275b8006bc48860943c8e50987547cb5a5`.
- Course Package CLI focused tests: 4 / 4 PASS.
- Python 3.13 full discovery: 192 / 192 PASS.
- Runtime #156 Python 3.11 / 3.12 / 3.13 success; App UI #212 success; Chromium 11 / 11 PASS.
- pure Task 8 diff contains only the package public surface, two CLI scripts, and CLI tests; no canonical textbook path changed.

### Task 9 — Layered Course Package acceptance gates

- implementation HEAD: `94fee411b5f8d67a5db2ef5779657f39c226c220`.
- pure Task 9 diff from `03b23305710e361bde9caf17470c1a2e75510092` is exactly four workflow files.
- Course Package FAST #1: PASS; Foundation focused tests 46 / 46; Architecture Fitness PASS.
- Runtime reference #157: Python 3.11 / 3.12 / 3.13 all success; Python 3.13 Golden compile/validate + fitness PASS.
- Book App UI #213: app-api / web-client / browser-acceptance all success; real Chromium 11 / 11 PASS.
- HEAVY is `workflow_dispatch` only and rebuilds/recovery-checks an isolated `/tmp` Book copy before read-only canonical readiness / Golden / fitness checks. It does not use canonical `--promote-safe` writes.
- The current connector does not expose workflow dispatch, so no HEAVY execution result is claimed.

## Current task

**Task 10 — Exact-HEAD Full Regression, Documentation State, and PR Readiness**

Authoritative plan: `docs/superpowers/plans/2026-08-28-foundation-a-course-package.md`.

Completed in Task 10 so far:

- full Foundation A branch diff audit from base shows no `app/**` source changes and no `books/functional-analysis/**` canonical changes;
- `docs/CURRENT_STATE.md`, `docs/ROADMAP.md`, and the stale execution-priority section of `docs/DEVELOPMENT_STRATEGY.md` have been updated with evidence, not projections;
- governance now records Task 9 complete and Task 10 in progress.

Next action:

1. open `foundation/course-package-contract-a → main` as a reviewable PR;
2. require exact PR-head `Course Package FAST`, Runtime Python 3.11 / 3.12 / 3.13, Book App app-api / web-client / browser-acceptance success;
3. inspect final PR diff and review threads;
4. confirm no canonical Book changes, no App runtime migration, no secret/token, no tracked `.build` output;
5. only then request explicit user authorization for that specific PR. Never auto-merge.

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

Do not write `main` directly. Do not auto-merge. Merge is permitted only after the exact reviewed PR head passes required gates and the user gives explicit authorization for that specific PR.