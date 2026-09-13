# Book Handoff

## Current authority override — 2026-09-13

The Phase 1H App implementation is complete and review-ready at exact head `9fce2c794559ff8c1bfdd0beda8f1848f189b0e3` on PR #26. Task 10 isolation/Golden/Chromium acceptance and Task 11 exact-head regression are complete; the protected-area diff is empty and GitHub checks are green. The current product scope is the existing Functional Analysis App: Runtime, Library/Course/Chapter/Section navigation, Preview/Learn/Review/Practice slices, deterministic Search, evidence-grounded QA, and durable StudyRecord. Structured textbook ingestion and additional book registration are explicitly deferred. PR #26 remains unmerged until the user explicitly authorizes that PR.

Updated: 2026-08-30 17:45 +08

## Start here

1. Read Google Drive root `全项目` and all current `全项目_*` governance baselines.
2. Read `AGENTS.md` and `SECURITY_POLICY.md` on the exact target branch.
3. Read `governance/project_state.json`, `docs/CURRENT_STATE.md`, `docs/PROJECT_NORTH_STAR.md`, `docs/ARCHITECTURE_INVARIANTS.md`, `governance/pending_sync.json`, and the active Phase 1H Spec/Plan.
4. Repository evidence outranks chat memory. Do not infer completion from prose when exact-head test evidence is absent.

## Current recovery point

- Repository: `Jvust2/Book`
- Protected default branch: `main`
- Phase 1H base: `2675d2cecab63b28b6ab81a4554e9b7f010afd72`
- Active branch: `design/phase-1h-learning-slices-20260830`
- Active PR: `#26` — OPEN / REVIEW-READY / UNMERGED / mergeable
- Latest exact implementation/test head before this governance sync: `74c2e00b0e279b4cd3096783741ee0aada5a6b6c`
- Last exact-head GREEN implementation/test head: `74c2e00b0e279b4cd3096783741ee0aada5a6b6c` (Learn UI implementation `5a64e7b58d9d97af81de8dd5564306124af54f21`)
- Current stage: Phase 1H complete — exact-head regression and PR review
- Current Task 8 state: GREEN and verified

PR #26 must remain unmerged unless the user explicitly authorizes `合并 PR #26` after final readiness.

## Approved Phase 1H documents

- Design: `docs/superpowers/specs/2026-08-30-phase-1h-learning-slices-design.md`
- Plan: `docs/superpowers/plans/2026-08-30-phase-1h-learning-slices.md`
- Task 7 checkpoint: `docs/superpowers/checkpoints/2026-08-30-phase-1h-task7-practice-ui.md`

Architecture:

```text
SectionLearningRuntime
  → LearningSliceRuntime deterministic reference-only projection
  → BookAppService closure validation / typed presentation DTO
  → focused React learning-slice component
```

Canonical body content stays in existing `ModeItem` / SourceResolver paths.

## Phase 1H task ledger

```text
Task 1  LearningSliceRuntime + Preview                         COMPLETE
Task 2  typed API + closure validation                         COMPLETE
Task 3  Preview UI                                             COMPLETE
Task 4  Review Runtime/API                                     COMPLETE
Task 5  Review UI                                              COMPLETE
Task 6  Practice Runtime/API                                   COMPLETE
Task 7  Practice UI                                            COMPLETE
Task 8  Learn type-aware grouping Runtime/API                  COMPLETE
Task 9  Learn grouped UI                                       COMPLETE
Task 10 isolation + frozen Golden + Chromium                   COMPLETE
Task 11 exact-head regression + canonical-diff + PR readiness  COMPLETE
```

## Last verified GREEN checkpoint

Verified exact head:

`9fce2c794559ff8c1bfdd0beda8f1848f189b0e3`

Learn UI implementation commit: `5a64e7b58d9d97af81de8dd5564306124af54f21`

Evidence:

- Runtime Reference Tests run `33304524899`: SUCCESS on Python 3.11 / 3.12 / 3.13; each matrix ran 345 tests.
- Book App UI Tests run `33304524902`: SUCCESS.
- app-api: Runtime 345, focused 147, full App 109: PASS.
- web-client: 17 files / 87 tests: PASS.
- TypeScript typecheck and production build: PASS.
- real Chromium acceptance: 12 / 12 PASS.

Task 10 and Task 11 are GREEN at `9fce2c794559ff8c1bfdd0beda8f1848f189b0e3`. PR #26 is review-ready and remains unmerged; review and merge are separate gates.

## Task 7 product checkpoint

Practice now has:

- `practice_kind=all|exercise|problem` URL state
- deterministic missing/invalid normalization to `all`
- subtype filters only when corresponding source refs exist
- no mode refetch or duplicate StudyRecord touch when changing filters
- source round-trip preservation through existing frozen `route`
- source-backed textbook content and canonical Source links
- exact unavailable-solution wording: `教材数据中暂未提供可验证解析`
- no answer textbox, correctness scoring, AI solution generation, localStorage answer store, or durable answer persistence

Task 7 checkpoint commit: `3896b0bc096df14f58c761034a48640040939d1b`.

## Task 8 exact contract

Current RED test commit:

`4b03a40398dbbe23c3fe57f5750299f27b5c5e0e`

Required Learn group order:

```text
definitions       定义 / 概念入口
theorem_family    定理与命题
formulas          公式
examples          例题
other_objects     其他教材对象
figures           教材图示
translations      中文学习层
```

Rules:

- omit empty groups;
- preserve source order within each group;
- object refs are mutually exclusive across groups;
- `definition` → definitions;
- theorem/proposition/lemma/corollary → theorem_family;
- explicit type `formula` → formulas;
- `example` → examples;
- all remaining object types, including proof/remark/concept/exercise/problem/unknown → other_objects;
- figures preserve existing page/id order;
- translations preserve stable deduplicated source-batch order;
- theorem carrying formula stays theorem_family only; formula remains a ModeItem property, not duplicate membership;
- presentation contains refs/derived metadata only, never canonical body/formula text;
- supplementary and lecture extensions stay `{status: "unavailable"}`;
- every emitted presentation ref must close over current Learn mode items.

## Next exact actions

1. Review PR #26 at exact head `9fce2c794559ff8c1bfdd0beda8f1848f189b0e3`.
2. Keep Search/QA Exact-only, StudyRecord schema/semantics, canonical data, and frozen session state unchanged.
3. Keep structured textbook ingestion deferred until separately requested.
4. Keep PR #26 unmerged; only an explicit 合并 PR #26 may authorize a later merge.

## Frozen product invariants

Golden Course:

```text
course_id = functional_analysis_course
book_id = stein_shakarchi_functional_analysis_2011
8 chapters / 132 sections / 1493 search records / 442 PDF pages / printed final page 423
STRUCTURED_COMPLETE / Runtime READY
```

Canonical read-only during Phase 1H:

- `books/functional-analysis/**`
- `courses/**`

Search / QA:

- `EXACT_ONLY_UNCHANGED`
- H4a evidence = `FTS_EVIDENCE_NOT_PROMISING`
- no production FTS/BM25/fusion/semantic ranking activation

StudyRecord:

```text
no row       = not started
in_progress  = 0
completed    = 100
```

No schema migration, no derived progress percentage, no per-question answer persistence.

Frozen Section sessionStorage shape:

```text
route
scrollY
expandedSourceIds
activeSourceId
```

Review/Practice selections stay in URL (`review_preset`, `practice_kind`).

## Separate gates / out of scope

Do not activate or silently implement:

- H3b production Concept authority/lifecycle
- B4b public FTS/fusion/ranking
- B5 public multi-book API/DTO/browser/session migration
- StudyRecord book-version migration
- multi-book Runtime consumer migration
- Lecture authority
- durable answer storage / mastery / correctness
- unrelated recording/Meeting/Exam/Sync work

Do not write `main` directly. Do not delete branches/files, force-push, reset/rewrite history, weaken security, overwrite frozen evidence, or auto-merge any PR.

## Pending sync

`governance/pending_sync.json` has `blocking_count = 0`.

Non-blocking items remain intentionally pending:

- fixed-commit source snapshots for previously studied external repositories;
- Functional Analysis raw Drive ZIP SHA-256 completion;
- H4a sqlite-utils / Datasette source snapshots.

Do not mark these resolved without Drive artifact identity/read-back evidence.
