# Book Handoff

Updated: 2026-08-29

## Start here

1. Read Google Drive root `全项目` and current `全项目_*` governance baselines.
2. Read `AGENTS.md` and `SECURITY_POLICY.md` on the exact target branch.
3. Read `governance/project_state.json`, project invariants/current state/decision and evaluation ledgers, pending sync, preflight, then the relevant approved phase design and plan.

Repository evidence outranks chat memory.

## Current branch and phase

- Repository: `Jvust1/Book`
- Default protected branch: `main`
- Integrated Foundation A merge commit: `82f0cbbcfe5078d304ca7c163b81d4eb01b515f4`
- Foundation A reviewed head: `f1eb4ebd144ccb233e5b8b74e97001af214c60bb`
- Foundation A PR: `#13`
- Phase: `Post-Foundation A transition`
- Current canonical integrated state: `main`

Foundation A Tasks 1–10 are complete and PR #13 has been merged into `main`. No next architectural implementation branch is approved yet.

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

### Task 10 — Exact-HEAD PR gate and merge

Final PR #13 exact head: `f1eb4ebd144ccb233e5b8b74e97001af214c60bb`.

Final automatic acceptance evidence before merge:

- Course Package FAST: 46 / 46 focused tests + Architecture Fitness PASS.
- Runtime reference tests: Python 3.11 / 3.12 / 3.13 PASS; Python 3.13 full discovery 192 / 192; Golden compile/validate + fitness PASS.
- Book App UI: app-api / web-client / browser-acceptance PASS.
- real Chromium: 11 / 11 PASS.
- final diff audit: no `books/functional-analysis/**` canonical changes, no App Runtime consumer migration, no tracked `.build` output, no unresolved review thread.
- user explicitly authorized merge of PR #13.
- merge commit: `82f0cbbcfe5078d304ca7c163b81d4eb01b515f4`.

## Current task

**Post-Foundation A transition / next-phase selection**

Foundation A is no longer an in-progress branch. The immediate safe work is to reconcile post-merge governance and then select the next roadmap phase.

The next genuinely new subsystem is an architectural decision and must pass a fresh design approval gate before implementation. Safe repository inspection, comparison, evidence gathering, and non-destructive governance reconciliation may continue automatically.

Some long-form narrative docs can still contain pre-merge wording because they were authored before PR #13 merged. Until those lines are reconciled, use `governance/project_state.json`, this handoff, PR #13, and merge commit `82f0cbbc...` as the authoritative post-merge evidence rather than interpreting stale “awaiting PR” sentences literally.

## Protected facts and boundaries

Functional Analysis Golden Course remains:
- `functional_analysis_course`
- `stein_shakarchi_functional_analysis_2011`
- 8 chapters / 132 sections / 1493 search records / 442 PDF pages / printed final page 423
- `STRUCTURED_COMPLETE` / Runtime `READY`

Foundation A did not modify `books/functional-analysis/**` and did not migrate Runtime/App consumers.

## Pending synchronization

`governance/pending_sync.json` has no blocking item. External fixed-commit source archives and Drive raw-source SHA-256 remain pending non-blocking and must not be marked complete without verified evidence.

Post-merge wording in `docs/CURRENT_STATE.md`, `docs/ROADMAP.md`, and any other narrative document that still says Foundation A is awaiting PR merge is a non-blocking documentation reconciliation item. Preserve historical sections; update only current-state wording when touched.

## Merge rule

Do not write `main` directly. Do not auto-merge. Merge is permitted only after the exact reviewed PR head passes required gates and the user gives explicit authorization for that specific PR.
