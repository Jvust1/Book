# Book Handoff

Updated: 2026-08-29

## Start here

1. Read Google Drive root `全项目` and current `全项目_*` governance baselines.
2. Read `AGENTS.md` and `SECURITY_POLICY.md` on the exact target branch.
3. Read `governance/project_state.json`, project invariants/current state/decision and evaluation ledgers, pending sync, preflight, then the approved design and plan set named below.

Repository evidence outranks chat memory.

## Current branch and phase

- Repository: `Jvust1/Book`
- Default protected branch: `main`
- Current `main` HEAD: `6c8734658a25c8b27cff33252a520d80e25cc704` (PR #14 post-Foundation-A state reconciliation)
- Integrated Foundation A merge commit: `82f0cbbcfe5078d304ca7c163b81d4eb01b515f4`
- Foundation A reviewed head: `f1eb4ebd144ccb233e5b8b74e97001af214c60bb`
- Foundation A PR: `#13`
- Active design/planning branch: `design/hybrid-h0-h4a-phase1h`
- Approved route: `H0 → H1 → H2 → H3a → H4a → Phase 1H`
- Current status: **approved design + implementation plan set ready; implementation has not started**
- Selected execution mode: **Superpowers Subagent-Driven Development in Codex**

Foundation A Tasks 1–10 are complete and merged. The next architecture route has now passed the design gate and the written spec gate. The implementation plan set is complete and ready for execution, but this design branch remains documentation-only.

## Approved hybrid design and implementation plan

Approved design:

- `docs/superpowers/specs/2026-08-29-hybrid-h0-h4a-phase1h-design.md`

Plan-set entry point:

- `docs/superpowers/plans/2026-08-29-hybrid-h0-h4a-phase1h-plan-set.md`

Plan-set execution order:

0. `docs/superpowers/plans/2026-08-29-post-foundation-a-governance-reconciliation.md`
1. `docs/superpowers/plans/2026-08-29-h0-neutral-book-identity.md`
2. `docs/superpowers/plans/2026-08-29-h1-internal-source-provenance.md`
3. `docs/superpowers/plans/2026-08-29-h2-exact-retrieval-seam.md`
4. `docs/superpowers/plans/2026-08-29-h3a-concept-contract.md`
5. `docs/superpowers/plans/2026-08-29-h4a-shadow-fts-evaluation.md`
6. `docs/superpowers/plans/2026-08-29-phase1h-learning-slices.md`

Planning artifact checkpoint before this handoff/state synchronization:

- `8dce16754cd8cc4bf0600e05e939e2ea2b8cbb00`

The plan set is intentionally staged and reviewable. Each implementation stage should use its own non-default branch/PR, TDD, exact-HEAD verification, and explicit human merge authorization. Do not collapse the route into one giant implementation PR.

## Hard stops outside the approved route

The following are **not authorized by the current design/plan** and require a new design approval before implementation:

- H3b production Concept authority/lifecycle
- B4b public FTS/fusion/ranking activation
- B5 public multi-book API/DTO/browser/session migration
- StudyRecord book-version migration

Through H4a, public Search remains Exact-only. H4a is shadow evaluation only. The current single-primary-book public product behavior remains frozen until a later separately approved migration.

## Foundation A completion evidence

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
- No HEAVY execution result is claimed unless a real manual dispatch is later verified.

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

**Execute the approved hybrid plan set with Superpowers Subagent-Driven Development in Codex.**

Start with the documentation-only post-Foundation-A governance reconciliation, then H0. Before the first write in each implementation branch/session, re-run the mandatory Drive + repository security gate. Follow the plan-set ledger, task briefs, implementer/reviewer loop, and exact-HEAD review requirements.

Do not treat design approval as merge authorization. Every implementation PR remains separately reviewable and requires explicit human authorization for merge.

## Protected facts and boundaries

Functional Analysis Golden Course remains:

- `functional_analysis_course`
- `stein_shakarchi_functional_analysis_2011`
- 8 chapters / 132 sections / 1493 search records / 442 PDF pages / printed final page 423
- `STRUCTURED_COMPLETE` / Runtime `READY`

Foundation A did not modify `books/functional-analysis/**` and did not migrate Runtime/App consumers.

The current hybrid planning branch adds design/planning/governance status only. It does not authorize canonical textbook mutation.

## Pending synchronization

`governance/pending_sync.json` has no blocking item. External fixed-commit source archives and Drive raw-source SHA-256 remain pending non-blocking and must not be marked complete without verified evidence.

The plan set includes a dedicated post-Foundation-A narrative reconciliation step for any remaining stale wording. Preserve historical evidence; update only objectively stale current-state wording.

## Merge rule

Do not write `main` directly. Do not auto-merge. Merge is permitted only after the exact reviewed PR head passes required gates and the user gives explicit authorization for that specific PR.
