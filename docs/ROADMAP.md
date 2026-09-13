# Book 开发路线图

## 当前权威覆盖 — 2026-09-13

现有 App 功能线已完成到 Phase 1H exact head `9fce2c794559ff8c1bfdd0beda8f1848f189b0e3`，PR #26 待审阅未合并。结构化教材导入、新教材注册以及后续多教材迁移继续保持单独范围，暂不启动。

> 状态同步：2026-08-30 17:45 +08  
> 当前执行权威：`governance/project_state.json` + `docs/CURRENT_STATE.md` + 已批准 Phase Spec/Plan。历史路线与详细阶段证据保存在 Git 历史、Ledger 和对应 PR/checkpoint 中。

## 当前总状态

Golden Course：Stein & Shakarchi《Functional Analysis》

```text
course_id = functional_analysis_course
book_id = stein_shakarchi_functional_analysis_2011
8 Chapters / 132 Sections / 1493 search records
442 PDF pages / printed final page 423
STRUCTURED_COMPLETE / Runtime READY
```

当前稳定 Phase 1H base：`main@2675d2cecab63b28b6ab81a4554e9b7f010afd72`。

当前开发：

- branch `design/phase-1h-learning-slices-20260830`
- PR #26 OPEN / DRAFT / UNMERGED
- Tasks 1–7 COMPLETE
- Task 8 Learn Runtime/API grouping COMPLETE
- Task 9 GREEN; Tasks 10–11 PENDING
- last exact GREEN `74c2e00b0e279b4cd3096783741ee0aada5a6b6c`

## 已完成阶段

### Phase 1A–1C — Runtime / content navigation

- [x] Runtime import/readiness contract
- [x] Book / Course / Library Runtime
- [x] Chapter / Section tree
- [x] Preview / Learn / Review / Practice base deterministic source projections
- [x] SourceResolver

### Phase 1D — Local-first App MVP

- [x] FastAPI + React/TypeScript/Vite PWA
- [x] Library → Course → Chapter → Section
- [x] real Source pages and printed/PDF page identity
- [x] Section → Source → Section recovery
- [x] desktop/mobile Chromium acceptance

### Phase 1E — deterministic textbook Search

- [x] canonical Exact search
- [x] bilingual term/theorem/formula/example/practice retrieval
- [x] Search → Source → Search recovery
- [x] zero-result/error/unavailable distinction

### Phase 1F — source-grounded textbook QA

- [x] Course / Section QA
- [x] Section-first → whole-book fallback
- [x] EvidenceGate + citation verification
- [x] insufficient-evidence fail closed
- [x] QA → Source → QA recovery

### Phase 1G — durable StudyRecord

- [x] SQLite local durable authority
- [x] hidden stable profile identity
- [x] four independent mode records
- [x] `in_progress=0`, `completed=100`
- [x] manual completion only; completed never regresses
- [x] recent learning
- [x] storage errors do not block textbook reading
- [x] sync-ready metadata without implementing sync

### Foundation A — Course Package v1

- [x] package schema/version and roles
- [x] legacy manifest normalization
- [x] deterministic artifact/content identity
- [x] deterministic compiler
- [x] fail-closed validator
- [x] compiler/validator CLI
- [x] Functional Analysis Golden gate
- [x] Architecture Fitness Functions
- [x] FAST / PR FULL / manual HEAVY CI layering
- [x] exact-head review/merge gate

Foundation A remains a package/compiler trust boundary; it did not migrate Runtime/App into general multi-book package consumption.

### Foundation B transition — H0/H1/H2/H3a/H4a

```text
H0 neutral Book identity                         COMPLETE_MERGED
H1 internal source provenance                    COMPLETE_MERGED
H2 shared Exact-only Retrieval seam              COMPLETE_MERGED
H3a inert Concept/ConceptAlignment contract      COMPLETE_MERGED
H4a shadow FTS5/BM25 evaluation                  COMPLETE_MERGED
```

H4a final evidence classification：`FTS_EVIDENCE_NOT_PROMISING`。Public Search/QA remains `EXACT_ONLY_UNCHANGED`；no production FTS/BM25/fusion activation followed.

## Phase 1H — user-visible learning slices

Approved design：`docs/superpowers/specs/2026-08-30-phase-1h-learning-slices-design.md`

Implementation plan：`docs/superpowers/plans/2026-08-30-phase-1h-learning-slices.md`

Goal：在不改变教材 authority、Search/QA、StudyRecord 或冻结浏览器 persistence shape 的前提下，把四模式从平铺 source objects 升级为确定性、可审计的学习体验。

### Task status

- [x] Task 1 — `LearningSliceRuntime` + Preview contract
- [x] Task 2 — strongly typed API `presentation` + source-ref closure validation
- [x] Task 3 — Preview React slice
- [x] Task 4 — Review Runtime/API
- [x] Task 5 — Review preset recall UI
- [x] Task 6 — Practice Runtime/API filters + explicit no-solution state
- [x] Task 7 — Practice filter UI
- [x] Task 8 — Learn type-aware grouping Runtime/API
- [x] Task 9 — grouped Learn UI
- [ ] Task 10 — isolation + frozen real-Golden + browser acceptance
- [ ] Task 11 — exact-head regression + canonical-diff gate + PR readiness

### Delivered Phase 1H behavior so far

Preview：

- deterministic overview/objectives/core refs/quick checks
- no fake prerequisites
- source-linked presentation

Review：

- `1 分钟 / 5 分钟 / 完整复习` deterministic coverage presets
- recall-before-reveal workflow
- `review_preset` in URL; no StudyRecord identity churn

Practice：

- `all / exercise / problem` source-backed filters
- `practice_kind` in URL
- source round-trip preserves filter
- exact explicit state `教材数据中暂未提供可验证解析`
- no generated answer, answer persistence, correctness scoring, or AI solution

### Task 8 contract

Learn groups are source-reference-only and emitted in this order when non-empty：

```text
definitions       定义 / 概念入口
theorem_family    定理与命题
formulas          公式
examples          例题
other_objects     其他教材对象
figures           教材图示
translations      中文学习层
```

Object membership is mutually exclusive. A theorem that already carries a canonical formula remains in `theorem_family`; the formula remains a ModeItem property and must not duplicate the source into `formulas`.

## Product invariants during Phase 1H

### Canonical data

Read-only：

- `books/functional-analysis/**`
- `courses/**`

### Search / QA

- [x] continue Exact-only public behavior
- [ ] no FTS/BM25/fusion production activation without separate B4b approval

### StudyRecord

- [x] no row = not started
- [x] in_progress = 0
- [x] completed = 100
- [x] mode payload loads before touch
- [x] preset/filter/reveal/view do not create new durable progress
- [x] no Phase 1H schema migration

### Section browser state

Frozen sessionStorage keys only：

```text
route
scrollY
expandedSourceIds
activeSourceId
```

New Review/Practice selection state uses URL query only.

## Post-Phase 1H roadmap / separately gated work

These are not authorized by current Phase 1H implementation：

- [ ] H3b production Concept authority/lifecycle
- [ ] B4b public FTS/fusion/ranking activation
- [ ] B5 public multi-book API/DTO/browser/session migration
- [ ] StudyRecord book-version migration
- [ ] multi-book Runtime consumer migration
- [ ] production Lecture authority / recording learning pipeline
- [ ] durable per-question answers / Mistake / Mastery
- [ ] ExamPoint / Exam Sprint / Exam Digital Twin
- [ ] Drive Sync / SyncEvent / owner-controlled multi-device sync
- [ ] Private Meeting product path
- [ ] Android product implementation
- [ ] generalized arbitrary-book upload → automatic structure → validation → readiness → registration product flow

Every item above requires its own approved design/gate when reached; Phase 1H must not pre-activate it.

## Current verification baseline

Last exact GREEN implementation/test head：`74c2e00b0e279b4cd3096783741ee0aada5a6b6c` (Learn UI implementation `5a64e7b58d9d97af81de8dd5564306124af54f21`)

```text
Runtime Reference Tests 33304001568    SUCCESS (3.11/3.12/3.13; 345 tests each)
Book App UI Tests 33304001491          SUCCESS
Web tests                              81 / 81 PASS
App focused tests                      147 PASS
Full App discovery                    109 PASS
TypeScript typecheck                   PASS
Production build                       PASS
Chromium acceptance                    12 / 12 PASS
```

Task 8 is now GREEN on implementation head `7a29a74cf97ea593de17edc8a14ef2b1989bd564`; next is Task 9 Learn grouped UI.

## 当前唯一下一步

1. 进入 Task 10：写 isolation RED tests，扩展 frozen Golden Runtime/API 与 Chromium acceptance。
2. 只做 acceptance-level 最小修复，保持 canonical 数据、Search/QA Exact-only、StudyRecord 与 sessionStorage 合同。
3. Task 10 GREEN 后进入 Task 11 exact-head regression、canonical-diff gate 与 PR review readiness。
4. PR #26 仍不合并；合并必须有明确 合并 PR #26 授权。
