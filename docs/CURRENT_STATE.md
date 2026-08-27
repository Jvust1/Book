# Book 当前状态

更新时间：2026-08-28

> 本文件记录当前有效成果、已确认产品决策和唯一下一步。若与旧聊天、旧 Drive CURRENT 或更早规划冲突，以当前分支中的本文件、`docs/MASTER_PLAN.md`、`docs/ROADMAP.md`、已批准 Phase Spec/Plan 和最新专项架构文档为准。

## 1. 当前工程状态

- Repository：`Jvust1/Book`
- `main` 当前已知 HEAD：`2fe6758d65a3317691922964e644f3a681571d24`
- Phase 1F merge commit：`8d78b5beea8339f4326749ffebd123d1903f1a2b`
- 当前开发分支：`feature/study-record-phase-1g`
- Phase 1G governance sync merge：`8b184ba459b64a6928b1fc66b419f8cb3d9c8884`
- Phase 1G design：`docs/superpowers/specs/2026-08-28-study-record-phase-1g-design.md`
- Phase 1G implementation plan：`docs/superpowers/plans/2026-08-28-study-record-phase-1g.md`
- implementation plan commit：`229e5369c80412a66d1e37bba252d9bb817d3991`
- Phase 1G 状态：设计和详细实施计划均已完成；业务代码实现尚未开始。

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

Phase 1F 未修改 `books/functional-analysis/**` canonical 教材资产。

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

## 4. 当前唯一工程主线：Phase 1G

Phase 1G 不扩大范围，只实现：

```text
StudyRecord
+ SQLite
+ hidden profile_id
+ recent learning
+ sync-ready metadata
```

规则：

- 本机 SQLite 是 durable StudyRecord authority
- UI 单用户；每个安装生成稳定隐藏 UUID `profile_id`
- logical key：`profile_id + course_id + section_id + mode`
- preview / learn / review / practice 独立
- 无记录 = 未开始
- 首次进入 = `in_progress / progress 0`
- 手动完成 = `completed / progress 100`
- completed 再进入不回退
- `last_studied_at` 决定 recent learning
- `sessionStorage` 只负责短期返回状态
- 预留 revision / updated_at / deleted_at / sync_status
- 1G 中 `sync_status=local`
- 不提前实现 Drive / SyncEvent / 录音 / Meeting / ExamPoint / Unified Retrieval / Mastery

## 5. 当前确认的课程产品模型

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

## 6. 同一课程多教材：已确认方案

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

## 7. Course Compiler / Course Package

Phase 1G 后优先冻结统一 Course Package Contract。

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

Functional Analysis 作为 Golden Course 验证“换教材不换程序”。

## 8. Unified Retrieval：已确认长期搜索架构

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

数学查询逐步支持中英文术语别名、Unicode/LaTeX/数学符号归一。

Search 与 QA 共用 Retrieval Engine；Search 返回证据，QA 基于同一 retrieval 构造 Evidence Pack。

结果明确标记来源：主教材 / 辅助教材 / 课堂 / 老师重点 / 考试 / 个人 / AI Derived / Meeting。

Meeting retrieval 与 Learning retrieval 授权和索引隔离。

## 9. Concept Graph / Concept 360

Chapter/Section 是阅读骨架，Concept Graph 是知识依赖骨架。

Concept 连接：

- 主教材定义/定理/公式/证明/例题
- 辅助教材解释/其他证明/补充题
- prerequisite / dependent concepts
- 课堂讲解与老师强调
- ExamPoint / Exam
- Questions / Mistakes
- Mastery

Concept 360 View 最终展示“一个知识点的一生”，但每条内容保留独立 provenance，不生成不可追踪的融合原文。

## 10. 课堂录音与教材协同

桌面/PWA 和手机/Android 的业务功能一致，都保留录音能力；只允许因平台权限、后台策略、布局和算力造成实现差异。

课堂录音 local-first：

```text
Audio
→ VAD / local ASR
→ raw_transcript
→ local_refined
→ Section / Concept matching
→ LectureEvents / pending_ai
```

即时初加工尽量识别：老师重点、考点、考试范围、分值/占比、成绩规则、作业、Deadline、老师扩展，以及“不考 / 不要求证明 / 了解即可”等信号。

永久分层：

```text
Textbook fact
Lecture fact
Derived / AI fusion
```

以及：

```text
raw_audio
raw_transcript
local_refined
ai_refined
```

教材补充不能伪装成老师原话，AI refinement 不能覆盖 raw source。

## 11. 每日 GPT 精加工 / Processing Job

第一版由用户每天手动触发，不做自动定时。

```text
App local first-pass
→ Drive pending_ai
+ GitHub schema/rules/current state
+ canonical Course Package
→ GPT versioned Processing Job
→ refined transcript / LectureEvents / concept links / exam signals / textbook supplements / derived notes
→ processed revision
→ Drive / Sync API
→ App
```

每次保留 `input_revision / processor_version / schema_version / textbook_version / processed_at`。

同时逐步生成 Course Timeline 和 What Changed 增量摘要。

## 12. ExamPoint / Exam Sprint / Exam Digital Twin

ExamPoint 第一版只用教材真实结构化证据计算基础重要度，保存 priority/reasons/prerequisites/canonical anchors。

Exam Sprint：

```text
30 min 保命版
2 h 核心版
6 h 考试版
完整速通
```

按 ExamPoint + 最小 prerequisite closure 组织。

Exam Digital Twin 后续保存考试日期、范围、总分、章节/主题占比、题型、老师明确考试信号、confirmed/probable/unknown、当前覆盖率和风险区域。

## 13. Mistake / Mastery / Next Best Action

StudyRecord 记录学习行为，不等于真正掌握。

Mastery 长期根据复习、刷题、错题、回忆、时间间隔和明确自评等证据更新。

Mistake 映射 Concept 和 prerequisite，识别 definition gap / theorem condition / formula misuse / prerequisite gap / reasoning break / calculation / careless 等根因，并生成最短修复路径。

Next Best Action 最终组合：

```text
ExamPoint
+ teacher emphasis
+ Exam Digital Twin
+ StudyRecord
+ Mastery
+ Mistakes
+ remaining time
+ prerequisite graph
```

输出“现在最应该学什么”，并显示 reason/evidence；AI 不得无证据直接修改事实或 Mastery。

## 14. 多设备同步

长期：

```text
App(s)
→ Book Sync API
→ owner-controlled Drive
```

每台设备保持自己的 SQLite / profile_id；同步增量 record/event，不共享整个 SQLite。

`event_id` 全局唯一，远端幂等应用。

朋友端不持有 owner Drive Token/Google 凭证。

桌面与手机共享同一业务 contract 和允许同步的数据语义。

## 15. Private Meeting

Meeting 与 Course/Book/Section 独立，默认私有。

复用 Audio/VAD/ASR/SQLite/profile_id/sync/ProcessingJob，但不参与教材知识融合，不进入朋友 shared Learning feed。

Meeting retrieval 与 Learning retrieval 隔离。

## 16. 开发系统策略

正式策略：

```text
ChatGPT chat = 主开发
GitHub Actions = 自动测试 / 构建 / regression
Functional Analysis = Golden Course
Codex = 完整版本后的独立审计 + targeted upgrade
```

开发采用 Spec/Schema/Acceptance Contract、Vertical Slice、TDD、Architecture Fitness Functions、分层 CI 和 exact-head gate。

GitHub-hosted runner 主要跑快速/PR gate；重型教材 rebuild、ASR、本地模型、Android/Windows 特殊验证后续可使用 self-hosted runner。

## 17. 当前明确未实现

以下均已进入正式计划，但当前不能当作已完成：

- Phase 1G StudyRecord / SQLite 业务代码
- Course Compiler / Course Package v2
- 多教材 ConceptAlignment
- Golden Course 自动 gate
- Architecture Fitness Functions
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

## 18. 当前唯一下一步

保持 `feature/study-record-phase-1g`，直接按：

`docs/superpowers/plans/2026-08-28-study-record-phase-1g.md`

进行 TDD，实现：

```text
StudyRecord + SQLite + hidden profile_id + recent learning + sync-ready metadata
```

当前不提前实现后续架构能力。