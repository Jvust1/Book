# Book 当前状态

## 当前权威覆盖 — 2026-09-13

Phase 1H App 功能已在 PR #26 的 exact head `9fce2c794559ff8c1bfdd0beda8f1848f189b0e3` 完成并通过远端 CI。现有 App 范围包括教材浏览、Library/Course/Chapter/Section 导航、Preview/Learn/Review/Practice 四种学习切片、精确搜索、教材证据问答和 SQLite StudyRecord；Task 10 隔离/Golden/Chromium 验收与 Task 11 exact-head 回归均已完成。`books/functional-analysis/**`、`courses/**`、Search/QA Exact-only 行为和 StudyRecord 语义均未改动。结构化教材导入与新增教材注册暂缓，不属于本次 App 完成范围。PR #26 保持未合并，等待审阅。

更新时间：2026-08-30 17:45 +08

> 本文件只维护当前有效状态与下一步；历史细节通过 Git 历史、Decision/Evaluation Ledger 和独立 checkpoint 保留。若与旧聊天、旧 Drive CURRENT 或本文件的历史版本冲突，以当前分支的治理状态、已批准 Phase 1H Spec/Plan 和可回读验证证据为准。

## 1. 当前工程状态

- Repository：`Jvust2/Book`
- 稳定集成分支：`main`
- Phase 1H implementation base：`2675d2cecab63b28b6ab81a4554e9b7f010afd72`
- 当前实现分支：`design/phase-1h-learning-slices-20260830`
- 最新实现/测试变更 HEAD：`74c2e00b0e279b4cd3096783741ee0aada5a6b6c`
- 当前 PR：`#26`，OPEN / DRAFT / UNMERGED / mergeable
- 当前阶段：`PHASE_1H_IMPLEMENTATION`
- 当前状态：Tasks 1–9 COMPLETE；Tasks 10–11 PENDING
- 最后一个 exact-head 全绿实现：`74c2e00b0e279b4cd3096783741ee0aada5a6b6c`
- PR #26 不得自动合并；只有用户明确说“合并 PR #26”并且最终 exact-head gate 满足时才进入合并。

已批准依赖序列：

```text
H0 neutral Book identity                         COMPLETE_MERGED
→ H1 internal source provenance                  COMPLETE_MERGED
→ H2 Exact-only shared Retrieval seam            COMPLETE_MERGED
→ H3a Concept/ConceptAlignment contract          COMPLETE_MERGED
→ H4a shadow FTS5/BM25 evaluation                COMPLETE_MERGED
→ Phase 1H user-visible learning slices          IMPLEMENTATION_IN_PROGRESS
```

H4a 结论保持：`FTS_EVIDENCE_NOT_PROMISING`；public Search/QA 继续 `EXACT_ONLY_UNCHANGED`。

## 2. Phase 1H 目标与架构

批准设计：

- `docs/superpowers/specs/2026-08-30-phase-1h-learning-slices-design.md`
- `docs/superpowers/plans/2026-08-30-phase-1h-learning-slices.md`

核心架构：

```text
SectionLearningRuntime
    ↓ current source-backed candidates
LearningSliceRuntime
    ↓ deterministic reference-only presentation
BookAppService
    ↓ closure validation + typed ModeResponse.presentation
React focused learning-slice components
```

`LearningSliceRuntime` 只做确定性 presentation projection；教材正文、公式、标题、页码、Source identity 继续由既有 Runtime/SourceResolver 权威提供。派生 prompt 必须携带 source ref，不得冒充教材事实。

## 3. Phase 1H 任务进度

| Task | 内容 | 状态 |
| --- | --- | --- |
| 1 | LearningSliceRuntime + Preview contract | COMPLETE |
| 2 | Typed API contract + source-ref closure validation | COMPLETE |
| 3 | Preview React slice | COMPLETE |
| 4 | Review Runtime/API | COMPLETE |
| 5 | Review UI | COMPLETE |
| 6 | Practice Runtime/API | COMPLETE |
| 7 | Practice UI | COMPLETE |
| 8 | Learn type-aware grouping Runtime/API | COMPLETE |
| 9 | Learn grouped UI | COMPLETE |
| 10 | Isolation + frozen Golden + Chromium acceptance | PENDING |
| 11 | Exact-head regression + canonical-diff gate + PR readiness | PENDING |

Task 7 durable checkpoint：

- `docs/superpowers/checkpoints/2026-08-30-phase-1h-task7-practice-ui.md`
- checkpoint commit：`3896b0bc096df14f58c761034a48640040939d1b`

Task 8 GREEN checkpoint：

- RED test commit：`4b03a40398dbbe23c3fe57f5750299f27b5c5e0e`
- 真实 RED：Runtime 全量发现 345 tests，4 failures + 2 errors，失败集中在 `LearningSliceRuntime.learn()` 的空 groups/缺失分组。
- GREEN implementation commit：`7a29a74cf97ea593de17edc8a14ef2b1989bd564`
- Learn groups 已按固定顺序互斥分组；只输出 source refs；theorem-with-formula 不重复进 formulas；空组省略；extensions 保持 unavailable。
- 精确 HEAD CI：Runtime Reference 3.11/3.12/3.13 全绿（345 tests）；Book App UI 全绿（web 81/81、App Runtime 345、focused 147、full App 109、Chromium 12/12）。
Task 9 GREEN checkpoint：

- Learn UI implementation commit：`5a64e7b58d9d97af81de8dd5564306124af54f21`
 - LearnLearningSlice 按 API presentation 的固定顺序渲染互斥分组；对象复用现有 LearningObjectCard，图示使用 metadata-only FigureReferenceCard，翻译卡显示可用性。
- SectionPage 仅保留一个 Learn focused branch，不再同时渲染旧平铺对象列表；缺失或错配 source refs fail closed。
- 不创建图片、不改变 Search/QA、StudyRecord 或 sessionStorage 合同。


## 4. Task 7 已交付行为

Practice 已从通用平铺卡片升级为 source-backed filter workflow：

- route state：`?mode=practice&practice_kind=all|exercise|problem`
- 缺失/非法 `practice_kind` → replace-normalize 到 `all`
- 只渲染 API presentation 实际存在的 subtype filter
- filter refs 必须闭合于当前 Practice ModeItems，违反则 fail closed
- filter 切换只改 URL，不重新请求 mode、不重复 touch StudyRecord
- Source round-trip 通过冻结的 `route` 字段保留 `practice_kind`
- 当前筛选数量可见
- 教材题目正文来自既有 ModeItem，不生成题目或答案
- 每题明确显示：`教材数据中暂未提供可验证解析`
- 不存在答案输入框、correctness control、AI solution、localStorage answer store 或 durable answer write

## 5. 最后 exact-head GREEN 证据

已验证 exact HEAD：

`74c2e00b0e279b4cd3096783741ee0aada5a6b6c`

Learn UI implementation：`5a64e7b58d9d97af81de8dd5564306124af54f21`

GitHub Actions：

- Runtime Reference Tests run `33304524899`：SUCCESS（Python 3.11 / 3.12 / 3.13；每个矩阵 345 tests）
- Book App UI Tests run `33304524902`：SUCCESS
- app-api：Runtime 345、focused App/API/Search/QA/StudyRecord 147、full App 109 全绿
- web-client：17 files / 87 tests PASS
- TypeScript typecheck：PASS
- production build：PASS
- real Chromium acceptance：12 / 12 PASS

Tasks 8–9 已完成；下一普通步骤是 Task 10 isolation + frozen Golden + Chromium acceptance。PR #26 仍保持 Draft / unmerged。

## 6. Golden Course / Runtime 基线

当前 Golden Course：Stein & Shakarchi《Functional Analysis》。

```text
course_id = functional_analysis_course
book_id = stein_shakarchi_functional_analysis_2011
8 Chapters
132 Sections
1493 search records
442 PDF pages
final printed page 423
STRUCTURED_COMPLETE / Runtime READY
```

Phase 1H 不修改：

- `books/functional-analysis/**`
- `courses/**`

教材事实、Course identity 与 canonical source provenance 均保持 read-only。

## 7. 冻结兼容合同

### Search / QA

- public Search/QA：`EXACT_ONLY_UNCHANGED`
- 不激活 production FTS5/BM25/fusion/semantic ranking
- H4a 只作为历史 shadow evaluation evidence

### StudyRecord

```text
无记录        = not started
in_progress   = progress 0
completed     = progress 100
```

- Mode content 成功加载后才执行既有 touch
- Review preset / Practice filter / reveal / view 不创建新 StudyRecord identity
- completed 不因 Phase 1H UI interaction 回退
- 不新增 schema，不把答案/子进度塞入 StudyRecord

### Section sessionStorage

冻结 shape 只有：

```text
route
scrollY
expandedSourceIds
activeSourceId
```

Review / Practice 长期到足以影响返回的 selection 状态只用 URL query：

```text
mode
review_preset
practice_kind
```

## 8. Phase 1H Learn 分组合同

Task 8 必须使用以下固定顺序，并省略空组：

```text
definitions       定义 / 概念入口
theorem_family    定理与命题
formulas          公式
examples          例题
other_objects     其他教材对象
figures           教材图示
translations      中文学习层
```

对象 membership 必须互斥：

- definition → `definitions`
- theorem / proposition / lemma / corollary → `theorem_family`
- explicit formula object → `formulas`
- example → `examples`
- proof / remark / concept / exercise / problem / unknown 等剩余 object → `other_objects`
- figures → `figures`
- translation batches → `translations`

带 canonical formula 的 theorem 仍只归 `theorem_family`；formula 继续作为既有 ModeItem 的展示属性，不以重复 source membership 表示。

Learn presentation 只放 source refs，不复制正文。`supplementary` 与 `lecture` extension 在 Phase 1H v1 必须继续 `status=unavailable`。

## 9. 已完成历史基础

以下阶段均已进入稳定集成线：

- Phase 1A–1F：Runtime / App MVP / Search / source-grounded QA
- Phase 1G：SQLite durable StudyRecord
- Foundation A：Course Package v1 / deterministic compiler / validator / Golden / fitness / layered CI
- H0：neutral Book identity
- H1：internal source provenance
- H2：shared Exact-only Retrieval seam
- H3a：inert deterministic Concept contract/reference validation
- H4a：shadow FTS5/BM25 evaluation，最终证据不支持 production activation

这些阶段的详细实现、RED/GREEN、CI、merge SHA 继续保存在 Git 历史、Ledger、旧 checkpoint 与对应 PR 中，不在本 CURRENT 文件重复展开。

## 10. 明确未激活 / 独立 Human Gate

以下均不因 Phase 1H 或“继续/更新所有成果”自动获得授权：

- H3b production Concept authority/lifecycle
- B4b public FTS/fusion/ranking activation
- B5 public multi-book API/DTO/browser/session migration
- StudyRecord book-version migration
- multi-book Runtime consumer migration
- Lecture authority
- durable per-question answer store
- PR #26 merge
- 任何 destructive / protected operation

## 11. Pending sync

`governance/pending_sync.json` 当前 `blocking_count = 0`。

仍保留的 non-blocking 债务包括：

- 已源码级研究的外部 GitHub fixed-commit source snapshots 尚待可信传输链路归档到 Drive
- Functional Analysis 原始 Drive ZIP 已验证 ID/bytes，但 SHA-256 尚未补齐
- H4a sqlite-utils / Datasette fixed-commit snapshots 尚待归档

本轮同步不得把这些项目伪报为完成。

## 12. 当前唯一下一步

1. 进入 Task 10：新增 Phase 1H isolation tests，并扩展 frozen Golden/Chromium acceptance。
2. 先运行真实 RED（仅记录新验收缺口），再做必要的 acceptance-level 最小修复。
3. Task 10 GREEN 后进入 Task 11 exact-head regression、canonical-diff gate 与 PR review readiness。
4. PR #26 仍不得自动合并；只有明确的 合并 PR #26 授权才可进入后续合并门。
