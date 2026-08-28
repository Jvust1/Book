# Book 当前状态

更新时间：2026-08-28

> 本文件记录当前有效成果、已确认产品决策和唯一下一步。若与旧聊天、旧 Drive CURRENT 或更早规划冲突，以当前分支中的本文件、`docs/MASTER_PLAN.md`、`docs/ROADMAP.md`、已批准 Phase Spec/Plan 和最新专项架构文档为准。

## 1. 当前工程状态

- Repository：`Jvust1/Book`
- 当前开发分支：`feature/study-record-phase-1g`
- Phase 1F：已合并到 `main`
- Phase 1G design：`docs/superpowers/specs/2026-08-28-study-record-phase-1g-design.md`
- Phase 1G implementation plan：`docs/superpowers/plans/2026-08-28-study-record-phase-1g.md`
- Phase 1G 业务实现：已完成
- 当前状态：最终文档同步与 exact-final-HEAD gate / review / PR 准备中；尚未合并到 `main`

当前跨阶段正式架构文档：

- `docs/MASTER_PLAN.md`
- `docs/ROADMAP.md`
- `docs/DEVELOPMENT_STRATEGY.md`
- `docs/LEARNING_INTELLIGENCE_ARCHITECTURE.md`

## 2. 当前教材 / Runtime 基线

当前 Golden Course 候选：Stein & Shakarchi《Functional Analysis》。

```text
course_id = functional_analysis_course
book_id = stein_shakarchi_functional_analysis_2011
8 Chapters
132 Sections
1493 unique search records
STRUCTURED_COMPLETE / RUNTIME_READY
PDF 442 / 442
final printed page 423
audit PASS 20 / WARN 1 / FAIL 0
```

Phase 1G 产品状态实现没有修改 `books/functional-analysis/**` canonical 教材资产；教材事实层与个人学习状态保持单向边界。

长期把这本教材固化为 Golden Course / Reference Course，用于 Course Package、Runtime、App、搜索、QA、StudyRecord、Concept、ExamPoint、Exam Sprint 和后续录音关联的自动回归。

## 3. 已完成产品能力

### Phase 1A–1C

- Runtime 导入契约
- Book / Course / Library Runtime
- Chapter / Section 树
- Preview / Learn / Review / Practice 四模式确定性教材投影
- SourceResolver 基础

### Phase 1D

- Local-first FastAPI + React/TypeScript/Vite PWA
- Library → Course → Chapter → Section
- 四学习模式
- 真实来源页、PDF/printed page identity
- Section → Source → Section 返回状态恢复
- 桌面和移动尺寸浏览器验收

### Phase 1E

- deterministic canonical search
- 中英文术语 / 定理 / 公式 / 例题 / 习题检索
- Search → Source → Search 恢复
- zero-result / query error / unavailable 分离

### Phase 1F

- Course / Section source-grounded textbook QA
- Section-first → book fallback
- server EvidenceGate
- citation verification
- 证据不足 fail closed
- QA → Source → QA 会话恢复
- OpenAI-compatible provider 仅服务端持有 key
- deterministic fake provider 支持 CI

### Phase 1G

- 本机 SQLite durable StudyRecord authority
- 首次初始化生成稳定隐藏 UUID `profile_id`
- 可移植数据库路径；支持 `BOOK_APP_DATA_DIR`
- `preview / learn / review / practice` 四模式独立记录
- 首次进入有效模式：`in_progress / progress=0`
- 再次进入更新 `last_studied_at`
- 手动 `标记完成`：`completed / progress=100`
- completed 再进入不倒退；重复完成幂等
- `last_studied_at` 驱动 recent learning
- 保留 `study_record_id / revision / updated_at / deleted_at / sync_status` 等 sync-ready metadata
- 1G 中 `sync_status=local`
- 服务器从 canonical Runtime 取得 `book_id`；浏览器不能伪造 `profile_id` 或 `book_id`
- 浏览器 StudyRecord DTO 不暴露内部 `profile_id / revision / sync_status`
- Section 页面只有在真实学习模式内容成功加载后才 touch StudyRecord
- StudyRecord 保存失败不阻断教材内容阅读，并提供重试
- completion 可跨页面 reload 持久化
- Source → Section 往返继续保持原有 route / scroll / expanded state 恢复
- SQLite read connections 有专门生命周期回归测试

## 4. Phase 1G API / storage contract

当前 StudyRecord 产品接口：

```text
POST /api/courses/{course_id}/sections/{section_id}/study/{mode}/touch
POST /api/courses/{course_id}/sections/{section_id}/study/{mode}/complete
GET  /api/courses/{course_id}/study-records
GET  /api/study/recent
```

逻辑唯一键：

```text
profile_id + course_id + section_id + mode
```

状态只有：

```text
无记录 = 未开始
in_progress = progress 0
completed = progress 100
```

不使用滚动距离或停留时间伪造百分比。

`sessionStorage` 仍只负责短期 Section / Search / QA 返回状态，不能替代 SQLite StudyRecord。

## 5. Phase 1G 最新验证证据

代码 HEAD 的完整 GitHub Actions 验证已通过：

```text
Runtime discovery            146 / 146 PASS
Functional Analysis readiness READY
App discovery                 86 / 86 PASS
Web tests                     PASS
TypeScript typecheck          PASS
Web production build          PASS
real Chromium acceptance      PASS
```

真实浏览器验收覆盖：

- StudyRecord 首次 touch
- `learn` 标记完成
- reload 后 completion 仍存在
- `preview` 与 `learn` 状态独立
- `/api/study/recent`
- 内部身份/同步字段不泄露给浏览器
- Source → Section 往返
- 390×844 窄屏无 body 横向溢出

Python 3.13 暴露的 SQLite connection `ResourceWarning` 已通过 RED → GREEN 生命周期测试修复；最新日志不再出现 `unclosed database`。目前仍可见 FastAPI/Starlette 自身的第三方弃用提示，不属于 Phase 1G 数据连接泄漏。

## 6. 当前确认的课程产品模型

Book 的核心单位是 Course。

```text
Course
├── primary textbook
├── supplementary / reference / translation books
├── Chapter / Section reading structure
├── Concept Graph learning structure
├── Lectures
├── Exam model
└── Personal learning state
```

按节：预习 / 学习 / 复习 / 刷题。

按章：核心考点 / 章节总结 / 可点击思维导图 / 章节测试。

按整本/课程：Exam Sprint / 期末速通。

最终原则：**App 通用，教材是数据。** 新课程主要走“上传资料 → Course Compiler/结构化 → readiness → 注册”，不是为每本书重新开发 App。

## 7. 同一课程多教材：已确认方案

如果上传两本泛函分析教材，默认放在同一个 Functional Analysis Course 中，而不是简单创建两个孤立课程，也不把原文融合成一本书。

```text
Course
├── Book A: primary
├── Book B: supplementary / reference
└── Concept Graph
```

每本 Book 保持独立 `book_id / book_version_id / chapter / section / page / source_anchor / proof / notation`。

课程级统一发生在 Concept 层，通过 `ConceptAlignment` 连接：

```text
concept_id
book_id
book_version_id
section_id
source_anchor
relation
confidence
revision
```

第一版仍由 primary book 提供课程 Section 主骨架；辅助教材作为同 Concept/Section 的补充证据源。

同一本教材不同 edition 使用 `logical_book_id + book_version_id + Version Mapping`，新版不能覆盖旧版。

## 8. Foundation A：下一工程阶段

Phase 1G 完成最终文档 HEAD gate、review 和 PR 后，优先冻结统一 Course Package Contract。

目标：

```text
主教材 + 辅助教材
→ Course Compiler
→ identity / version / PageMap
→ Chapter / Section / objects
→ source anchors
→ terminology / search index
→ Concept candidates / dependency
→ readiness PASS/WARN/FAIL
→ Course Package
→ App
```

Foundation A 同时推进：

- Functional Analysis 固化为 Golden Course
- 8 Chapters / 132 Sections / 1493 search records 自动基线
- canonical identity / source integrity regression
- Architecture Fitness Functions
- Contract-first / OpenAPI 或 JSON Schema 权威边界
- FAST / PR FULL / HEAVY 分层 CI

## 9. Unified Retrieval：已确认长期搜索架构

现有 Phase 1E deterministic search 保留为 Exact 高可信层。

长期组合：

```text
Query Normalizer
↓
Canonical Exact
+ SQLite FTS5 / BM25
+ Formula
+ Concept
+ Semantic
+ LectureEvent
+ ExamPoint
+ Personal
+ isolated Meeting
↓
RRF / equivalent fusion
↓
source-aware reranking
↓
provenance-preserving hits
```

Search 与 QA 共用 Retrieval Engine；Meeting retrieval 与 Learning retrieval 授权和索引隔离。

## 10. Concept Graph / Concept 360

Chapter/Section 是阅读骨架，Concept Graph 是知识依赖骨架。

Concept 连接主教材、辅助教材、prerequisites、课堂、ExamPoint、Questions/Mistakes 与 Mastery。Concept 360 View 最终展示一个知识点从教材到个人学习状态的完整生命周期，但每条内容保持独立 provenance。

## 11. 课堂录音与教材协同

桌面/PWA 和手机/Android 的业务功能一致，都保留录音能力；只允许因平台权限、后台策略、布局和算力造成实现差异。

```text
Audio
→ VAD / local ASR
→ raw_transcript
→ local_refined
→ Section / Concept matching
→ LectureEvents / pending_ai
```

永久分层：`Textbook fact / Lecture fact / Derived AI fusion`，并保留 `raw_audio / raw_transcript / local_refined / ai_refined`。AI refinement 不覆盖 raw source。

## 12. Exam / Mistake / Mastery / Next Best Action

- ExamPoint 第一版只用真实教材结构化证据计算基础重要度。
- Exam Sprint 按 ExamPoint + 最小 prerequisite closure 组织。
- Exam Digital Twin 后续保存考试日期、范围、分值、题型与可信状态。
- StudyRecord 记录学习行为，不等于真正掌握。
- Mastery 根据复习、刷题、错题、回忆和时间等证据更新。
- Next Best Action 最终输出可解释的下一学习动作，AI 不得无证据直接修改事实或 Mastery。

## 13. 多设备同步

长期：

```text
App(s)
→ Book Sync API
→ owner-controlled Drive
```

每台设备保持自己的 SQLite / profile_id；同步增量 record/event，不共享整个 SQLite。朋友端不持有 owner Drive Token/Google 凭证。

## 14. Private Meeting

Meeting 与 Course/Book/Section 独立，默认私有。可复用 Audio/VAD/ASR/SQLite/profile_id/sync/ProcessingJob，但不参与教材知识融合，不进入 shared Learning feed；Meeting retrieval 与 Learning retrieval 隔离。

## 15. 当前明确未实现

以下均已进入正式计划，但当前不能当作已完成：

- Course Compiler / Course Package v2
- 同 Course 多教材运行时支持与 ConceptAlignment
- Golden Course 完整自动 gate
- Architecture Fitness Functions 完整集合
- Unified Retrieval v1/扩展
- Minimal Concept Graph / Concept 360
- Chapter Hub / 思维导图
- ExamPoint / Exam Sprint / Exam Digital Twin
- 录音 UI / VAD / ASR / LectureEvent
- Drive Sync / SyncEvent / SyncEngine
- GPT Processing pipeline 真实写回
- Course Timeline / What Changed
- Mistake / Mastery / Next Best Action
- Meeting UI / storage
- Android APK
- raw PDF Reader

## 16. 当前唯一下一步

1. 完成 Phase 1G 最终文档 HEAD 的 full gate。
2. 对 Phase 1G 做独立 code review / diff review。
3. 创建或更新 Phase 1G PR；**不得自动合并到 `main`**。
4. 获得明确合并授权并完成集成后，进入 Foundation A。

当前不提前实现录音、Drive Sync、Meeting、ExamPoint、Unified Retrieval、Mastery 或 Next Best Action。