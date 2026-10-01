# Book Handoff

Updated: 2026-10-01

## 2026-10-01 01:56 UTC 阅读器候选检查点（尚未合并）

- 实时核对 `main`：`805510f86546709b6f67c9e9079943f205c2c245`，仍为 PR #57 合并结果；下列新增能力目前只在 Draft 分支。
- 已验证代码基线：PR [#75](https://github.com/Jvust1/Book/pull/75)，`5616246fbf88c8a3a0a8732d0e36c5a11c6c6f3b`。整合交接分支 `docs/coherent-reader-candidate-20261001` 以此为父提交，目标为 `main`，自身 exact-head gates 必须另行通过。
- 七个新接入项目为 KaTeX、PDF.js、react-markdown、math.js、Fuse.js、Zod、TanStack Query，均实际进入阅读器运行路径；既有 SymPy 做安全加固，既有 Playwright 用于验收，不重复计入新项目数。
- 原创单章贯通预习/学习/复习/刷题、来源 PDF 本地检索、引用问答、数值计算与显式进度回执恢复。#75 exact head 已通过 Linux/Windows 干净源码提取、403 个 Web 测试、类型/构建、40 个提取后 Python 测试及五条原创浏览器旅程；完整 UI gate 为 38 条常规 + 5 条原创旅程，平台重跑不累计为新用例。
- #71 目录验证/导航恢复分支六条新浏览器用例失败，未纳入该候选；旧 PR 与其他教材审校分支均保留。不得以候选通过推断 #71 已修复。
- 外部[六书审计报告](https://github.com/Jvust1/Book/blob/6d7ecf5969ed1feffc1061dc6bdb68aff77fd708/audits/2026-10-01/six-books_0800_acceptance.md)报告 24 PDF / 3477 页，其中五书 2733 页非 A4、当代中国经济文本层 578 个 NUL、逐书审校/同步证据仍有缺口；这是另一分支的报告，非本次重跑。原创代码验收不替代教材、排版、字体或来源重排验收。
- 交付为 code-only 源码，包含原创合成章节，不含用户教材全文、扫描 PDF、私有资产或原生安装器。详细复现、上游出处和边界见 [阅读器交接](upstream/reader-integration-handoff-2026-10-01.md)。

以下旧阶段和导出记录按当时证据保留。出现“当前 main / 唯一下一步 / H4a 下一步”等旧表述时，按其历史日期理解；实时分支状态以上方检查点和最新 GitHub 记录为准，不将旧记录重新解释为本次授权。

## Historical artifact/state checkpoint — 2026-10-01

- Repository: `Jvust1/Book`; verified base main `6e5782b23c49943a263dfad7ee490147d57b2f0e`.
- Consolidated Drive snapshot: `Book/03_Exports/Book-All-Results-20261001/`.
- Six books have verified 10px reading sets; five repaired r2 sets have final QA with 20/20 PDFs and zero targeted small-prose/noise residue.
- Six books have verified 15px reading sets; PR #56 is already in main.
- These are derived reading/export artifacts only; do not infer canonical textbook mutation or complete Runtime registration.
- Main contains the 2026-09-30 FSRS/retrieval/ingestion increments through MinerU (#55). Re-read main before new implementation work because historical phase text below predates these merges.


## Start here

1. Read the latest user instructions and `AGENTS.md` on the exact target branch.
2. Inspect live main, open PRs and the reader handoff linked above before editing shared files. Read any applicable security policy if present; this candidate has no root `SECURITY_POLICY.md`.
3. Use `governance/project_state.json`, current evidence and relevant architecture invariants. Historical global/phase records do not reinstate obsolete startup or approval requirements.

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
