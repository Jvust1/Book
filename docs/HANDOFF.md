## 2026-09-26 最新 Book App 接手点

- Windows 交付版本：`1.0.0-rc3`；EXE SHA-256 `6a3f6804c0ed4e561f9a714afb73dc0d1149dad77bb327b60b2ea6d4a6008a88`。
- 当前 App 学习内容：预习 / 学习 / 复习 / 刷题；7 本教材，26,195 条规范记录。
- Drive rc3 目录：`Book/03_Exports/Book-Windows-rc3-20260926`，folder ID `1X9s88Z9BYBpxeyJv8iuXr9Vzs9eqZ3d8`。
- 已归档：验证记录、交付检查报告、使用说明、SHA256SUMS。三个大文件使用 64 MiB 无损分片归档在 `large-files-split`；9 个分片已从 Drive 回读并逐片校验 SHA-256，重组后的 EXE/两个 ZIP 也与原始 SHA-256 完全一致。
- 数据修订仍在 `fix/structured-data-audit-20260924` / Draft PR #38；不自动合并、不改 main。
- 用户本人 Windows 真机验收与剩余内容级终验仍待完成。

## Six-textbook structured-data r2 handoff — 2026-09-25

For the six Chinese textbooks, the newest data overlay is `book-six-textbooks-enhancement-20260925-r2`, based on immutable r1. Read `governance/structured_data_enhancement_r2_current.json` first, then the r1 repair checkpoint. r2 preserves all r1 source_text/source_record identities and adds quality/search/QA gates rather than silently replacing raw provenance.

Public Finance: five additional numeric tables were fully re-transcribed from source scans; together with r1 table 13-1 there are six source-verified numeric tables. Four ratio tables passed 160 arithmetic consistency comparisons. Sixty-six table-part candidates remain explicitly unverified, not confirmed errors.

Financial Economics: 42 records across 26 source pages received bounded visual corrections. The martingale-variant OCR hotspot scan is now zero. Page 219 was adjudicated as sigma-field notation corruption, not a martingale substitution. Targeted corrections do not confer full-block OCR acceptance.

Drive overlay ZIP ID `1eKimb6q3BhCIOeTOtThdWSqQZFs35bwG`, SHA-256 `0d8efa419886ee2601a7a15e9470852f03ebd4a744bfa545d43627e57e1ed983`; report ID `1GrX4UWAchfjdFt6nB2FeR0lVzAG5cxTt`. Keep PR #38 Draft/Open/Unmerged unless explicitly authorized to merge. No Runtime/App migration occurred.

# Book Handoff

## Structured-data handoff: book-results-sync-20260925

For the seven-book audit/repair task, restore `fix/structured-data-audit-20260924` / Draft PR #38, then read `governance/structured_data_results_sync_20260925.json`. The immutable content checkpoint is `54b5ddc0eb5ba9cfaa370233a588614b86fd6c02`; subsequent sync metadata does not create a new textbook version or merge the branch.

Read the original audit together with `governance/structured_data_repair_audit_closure_20260924.json`; do not reopen already repaired findings merely because the historical audit retains them. The artifact manifest now identifies the audit ZIP/report and the original repair delivery receipt. Complete images/data use the eight parts in the v3 manifest; the text core intentionally excludes images. The pinned GitHub correction-source ZIP is already contained in the repair packages and needs no duplicate upload.

Current work is review of this data candidate and remaining source/math acceptance, not automatic App import. Public-finance remaining prose/tables, financial-economics remaining OCR and 110 draft derivations remain unaccepted where previously marked. Keep raw/correction/AI layers separate. Do not merge PR #38 without explicit authorization.

The engineering narrative below remains a historical checkpoint; do not mistake its old H4a-next wording for the current data task. The observed integrated main is `2675d2cecab63b28b6ab81a4554e9b7f010afd72`; its machine state and separately maintained engineering branches remain authoritative and unchanged by this sync.

Updated: 2026-08-29

## Start here

1. Read Google Drive root `全项目` and current `全项目_*` governance baselines.
2. Read `AGENTS.md` and `SECURITY_POLICY.md` on the exact target branch.
3. Read `governance/project_state.json`, project invariants/current state/decision and evaluation ledgers, pending sync, preflight, then the relevant approved phase design and plan.

Repository evidence outranks chat memory.

## Current branch and phase

- Repository: `Jvust1/Book`
- Default protected branch: `main`
- Current canonical integrated main: `f69166568839b7038b0f0472baefcee34299fa17`
- Foundation A PR: `#13`, merge commit `82f0cbbcfe5078d304ca7c163b81d4eb01b515f4`
- H0 PR: `#18`, merge commit `3dcc600c2c8a39e1ffc41c07fbf290adfba5035c`
- H1 PR: `#19`, merge commit `7e54e87b9674455e9f3d275016313f6c9e2487ac`
- H2 PR: `#20`, merge commit `410cede92bcc0783e4fca9b02faec79e5fe77112`
- H3a PR: `#21`, merge commit `f69166568839b7038b0f0472baefcee34299fa17`
- Phase: `Foundation B transition`
- Status: `H3a merged / H4a next approved stage`

The approved dependency sequence is:

```text
H0 → H1 → H2 → H3a → H4a → Phase 1H
```

H0 through H3a are now complete and merged. H4a is the next approved stage and is limited to shadow FTS5/BM25 evaluation; public Search remains Exact-only. `H3b`, `B4b`, `B5`, and StudyRecord book-version migration remain separate human gates.

## Foundation A historical checkpoint

Foundation A Tasks 1–10 are complete and PR #13 is integrated.

- reviewed head: `f1eb4ebd144ccb233e5b8b74e97001af214c60bb`
- merge commit: `82f0cbbcfe5078d304ca7c163b81d4eb01b515f4`

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
- No HEAVY execution result is claimed without an actual run record.

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

## Foundation B transition evidence

### H0 — neutral Book identity

- PR: `#18`
- reviewed head: `56c289ccdb5bd692efcbd642dfd9267278f5e5af`
- merge commit: `3dcc600c2c8a39e1ffc41c07fbf290adfba5035c`
- Course Package FAST #22, Runtime #185 Python 3.11/3.12/3.13, Book App UI #241 and Chromium acceptance passed.
- no canonical textbook, StudyRecord, H1+, or public product migration entered the scope.

### H1 — internal source provenance and serialization freezes

- PR: `#19`
- reviewed head: `a225f899fb93faca22c2b1f9ad0c2b1ae2a2fed2`
- merge commit: `7e54e87b9674455e9f3d275016313f6c9e2487ac`
- Course Package FAST #38, Runtime #209 Python 3.11/3.12/3.13, Book App UI #271 and Chromium acceptance passed.
- public Search/Source/QA DTO shapes remained frozen; provenance remained internal.

### H2 — Exact-only shared Retrieval seam

- PR: `#20`
- reviewed head: `66ac966c5dfe59ebeea82b168b2ee67fc85f9474`
- merge commit: `410cede92bcc0783e4fca9b02faec79e5fe77112`
- Runtime #220 and Book App UI #287 passed, including Python 3.11/3.12/3.13 and browser acceptance.
- Search and QA evidence retrieval now share an injectable internal Exact-only Retrieval seam; no FTS/BM25/semantic retrieval or public DTO migration was introduced.

### H3a — deterministic Concept graph contract

- PR: `#21`
- reviewed head: `1ed4fc6574417b56b4342ae639f81a69dd842c6b`
- merge commit: `f69166568839b7038b0f0472baefcee34299fa17`
- review-repair RED checkpoint: `2bc7fb6b215b618298e6d860450087a7ef4c67af`
- final exact-head gates: Course Package FAST #45, Runtime #236, Foundation B contract #8, Book App UI #303, Python 3.11/3.12/3.13, App API, Web build/typecheck/tests and real Chromium acceptance all passed.
- H3a remains inert: no real Concept dataset, no Search/QA/App activation, no StudyRecord change, no H3b work.

## Current task

**H4a shadow FTS5/BM25 evaluation.**

The post-Foundation-A/post-H3a governance reconciliation is carried by PR #17 and is historical once integrated. The durable next implementation stage is H4a:

```text
shadow FTS5/BM25 evaluation
```

H4a must preserve public Exact-only Search/QA behavior. It may collect shadow ranking/coverage/evaluation evidence, but must not silently activate FTS5/BM25 in the user-visible path. Any activation belongs to a later separately reviewed stage.

Before implementation, define deterministic evaluation datasets/queries, metrics, provenance checks, failure semantics, and exact-head acceptance evidence. Use the existing H2 Retrieval boundary rather than bypassing it.

## Protected facts and boundaries

Functional Analysis Golden Course remains:
- `functional_analysis_course`
- `stein_shakarchi_functional_analysis_2011`
- 8 chapters / 132 sections / 1493 search records / 442 PDF pages / printed final page 423
- `STRUCTURED_COMPLETE` / Runtime `READY`

Foundation A, H0, H1, H2 and H3a did not rewrite `books/functional-analysis/**` canonical textbook facts.

H3a does not authorize H3b. H4a does not authorize public FTS5/BM25 activation. StudyRecord book-version migration is still separately gated.

## Pending synchronization

`governance/pending_sync.json` has no blocking item. External fixed-commit source archives and Drive raw-source SHA-256 remain pending non-blocking and must not be marked complete without verified evidence.

Narrative state that predates H0–H3a integration should be reconciled only when touched; historical checkpoints must remain historical rather than being rewritten as if they were produced later.

## Merge rule

Do not write `main` directly. Do not auto-merge. Merge is permitted only after the exact reviewed PR head passes required gates and the user gives explicit authorization for that specific PR.
