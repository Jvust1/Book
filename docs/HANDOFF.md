# Book Handoff

Updated: 2026-08-30 17:28 +08

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
- Active PR: `#26` — OPEN / DRAFT / UNMERGED / mergeable
- Latest implementation head before this governance sync: `7a29a74cf97ea593de17edc8a14ef2b1989bd564`
- Last exact-head GREEN implementation: `7a29a74cf97ea593de17edc8a14ef2b1989bd564`
- Current stage: Phase 1H Task 9 — Learn grouped UI
- Current Task 8 state: GREEN and verified on exact implementation head `7a29a74cf97ea593de17edc8a14ef2b1989bd564`

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
Task 9  Learn grouped UI                                       PENDING
Task 10 isolation + frozen Golden + Chromium                   PENDING
Task 11 exact-head regression + canonical-diff + PR readiness  PENDING
```

## Last verified GREEN checkpoint

Verified implementation head:

`7a29a74cf97ea593de17edc8a14ef2b1989bd564`

Evidence:

- Runtime Reference Tests run `33304001568`: SUCCESS on Python 3.11 / 3.12 / 3.13; each matrix ran 345 tests.
- Book App UI Tests run `33304001491`: SUCCESS.
- app-api: Runtime 345, focused 147, full App 109: PASS.
- web-client: 16 files / 81 tests: PASS.
- TypeScript typecheck and production build: PASS.
- real Chromium acceptance: 12 / 12 PASS.

Task 8 is GREEN and the next ordinary step is Task 9 Learn grouped UI. PR #26 remains Draft / unmerged.

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

1. Start Task 9 Learn grouped UI from the approved plan.
2. Write focused Learn UI RED tests first; then implement the minimum source-backed grouped presentation.
3. Run focused web/API/runtime regression and keep `learning_slice_v1`, Source round-trip, Search/QA Exact-only, and StudyRecord invariants unchanged.
4. After Task 9 GREEN, proceed to Task 10 isolation + frozen Golden + Chromium acceptance.
5. Keep PR #26 Draft/unmerged; only an explicit `合并 PR #26` may authorize a later merge.

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
