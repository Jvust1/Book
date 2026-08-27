# Book 总体产品计划

更新时间：2026-08-28

## 1. 产品目标

Book 的目标不是做“PDF + AI 聊天”，而是构建一个长期可更新、来源可追溯、跨设备同步的个人 Course OS，并在同一产品中提供独立私有的 Meeting 域。

核心原则：

```text
App 通用，教材是数据
教材告诉系统“知识是什么”
课堂告诉系统“老师怎么教、怎么考”
个人数据告诉系统“我掌握到哪里”
AI 负责连接、解释和推荐，但不覆盖事实来源
```

长期输入：

- 主教材 / 辅助教材 / 参考教材及版本更新
- 教材结构化数据
- 课堂录音与逐字稿
- 老师重点、考试范围、成绩规则、作业、Deadline
- 个人笔记、题目、错题、StudyRecord、Mastery
- 私有 Meeting 录音与会议数据

## 2. 顶层产品结构

```text
Book
├── Learning / Course OS
│   ├── Courses
│   ├── Books / Versions
│   ├── Course Package / Compiler
│   ├── Chapters / Sections
│   ├── Concepts / ConceptAlignment
│   ├── StudyRecords / Mastery
│   ├── Unified Retrieval / QA
│   ├── Lectures / LectureEvents
│   ├── ExamPoints / Exam Sprint
│   ├── Exam Digital Twin
│   ├── Questions / Mistakes
│   ├── Timeline / What Changed
│   └── Next Best Action
│
├── Meeting (private)
│   ├── Meetings / Transcripts
│   ├── Decisions / ActionItems
│   ├── Deadlines / FollowUps
│   └── private retrieval
│
└── Shared Infrastructure
    ├── local SQLite
    ├── hidden profile_id
    ├── Audio / VAD / ASR
    ├── local-first processing
    ├── Sync transport
    └── versioned AI Processing Jobs
```

Learning 与 Meeting 可以复用技术基础，但业务事实和授权域必须分开。

## 3. Canonical 教材与来源原则

教材结构化数据是教材事实层 canonical source。

任何教材对象至少保留：

```text
course_id
book_id
logical_book_id
book_version_id
chapter_id
section_id
pdf_page_index
printed_page
content_anchor_id
element_type
element_id
```

PDF 页与纸质页分离。缺失内容、页码、几何位置或来源不得由 AI 静默编造。

教材新版本不能覆盖旧版本；历史课堂、引用、笔记、StudyRecord 和 ExamPoint 必须仍能定位到当时版本。

## 4. 一门课程支持多本教材

同一课程的多本教材保持 Book 级独立，在 Concept 层对齐。

教材角色：

```text
primary
supplementary
reference
translation
```

第一版由 primary book 决定课程 Chapter/Section 主骨架；辅助教材通过 ConceptAlignment 和 Section/Concept 关系提供补充定义、解释、证明、例题和习题。

多本教材不能强制融合成“唯一原文”，必须保留各自：

- 定义写法
- 定理编号
- 符号体系
- 证明方式
- 页码与 source anchor

如果未来确实存在两本同等权威教材，再增加独立 CourseSyllabus / Concept-first 课程骨架。

详细规则见：`docs/LEARNING_INTELLIGENCE_ARCHITECTURE.md`。

## 5. Course Compiler / Course Package

长期新增教材应通过统一编译流程进入系统：

```text
上传主教材 / 辅助教材
→ Course Compiler
→ 结构化 + identity + source anchors
→ search / terminology / Concept candidates
→ readiness PASS/WARN/FAIL
→ Course Package
→ 注册 Course / Library
→ 自动获得 App 学习能力
```

Course Package 至少包含 schema version、content hashes、books/versions、chapters、sections、objects、source map、search records、terminology、dependency information 和 readiness。

Functional Analysis 作为 Golden Course / Reference Course，长期用于验证 Course Package 与 App 行为。

## 6. Section 四模式与 StudyRecord

每一节固定提供：

```text
预习 / 学习 / 复习 / 刷题
```

四模式自由进入、互不锁定、独立记录。

Phase 1G 第一版：

```text
无记录 = 未开始
in_progress = progress 0
completed = progress 100
```

本地 SQLite 是 durable StudyRecord authority；sessionStorage 只负责短期返回状态。

每台安装生成稳定隐藏 UUID `profile_id`，浏览器不能自行指定身份。

## 7. Unified Retrieval 与 QA

现有 deterministic canonical search 保留为 Exact 高可信层。

长期统一检索组合：

```text
Exact
+ SQLite FTS5 / BM25
+ Formula
+ Concept
+ Semantic
+ LectureEvent
+ ExamPoint
+ Personal
+ isolated Meeting
→ rank fusion / source-aware reranking
```

数学查询需处理术语别名、Unicode/LaTeX/数学符号归一。

Search 和 QA 共用同一个 Retrieval Engine：Search 返回来源证据，QA 在同一检索结果上构建 Evidence Pack，经 EvidenceGate 后再交给 LLM。

结果必须显式区分主教材、辅助教材、课堂、考试、个人资料和 AI Derived。AI Derived 不能覆盖 canonical exact evidence。

Meeting 检索与 Learning 检索保持授权/索引隔离。

## 8. Concept Graph 与 Concept 360 View

Chapter/Section 是阅读骨架；Concept Graph 是学习依赖骨架。

Concept 可连接：

```text
prerequisites / dependents
主教材 evidence
辅助教材 evidence
课堂 evidence
ExamPoint / Exam
Questions / Mistakes
Mastery
```

Concept Graph 为多教材对齐、思维导图、Exam Sprint、错题诊断、Mastery 和 Next Best Action 提供基础。

Concept 360 View 最终展示一个知识点从教材、课堂、考试到个人学习状态的完整生命周期，但每一条信息必须保留来源。

## 9. Chapter Hub / ExamPoint / Exam Sprint

### Chapter Hub

按章提供：核心知识点、公式、考点、章节总结、可点击思维导图、章节测试。

### ExamPoint

第一版只根据教材真实结构化证据形成基础重要度：定义、定理、公式、证明、例题、习题、重复引用、依赖关系和教材显式强调。

每个考点保留 priority、reasons、prerequisites、canonical source anchors。

### Exam Sprint

```text
30 分钟：保命版
2 小时：核心版
6 小时：考试版
完整速通
```

按 ExamPoint + 最小必要前置依赖组织，不按章节机械截断。

老师强调、考试范围、错题和 Mastery 可以作为后续独立信号叠加，但不能改写教材基础证据。

## 10. Learning 课堂录音

桌面/PWA 与手机/Android 均提供录音业务能力。平台可以采用不同权限、后台录音和 UI 实现，但不人为把桌面端做成无录音精简版。

课堂录音 local-first：

```text
Audio
→ VAD / local ASR
→ raw_transcript
→ local refinement / terminology correction
→ Section / Concept initial linking
→ LectureEvents / pending_ai
```

即时初加工尽量提取：

- IMPORTANT / EXAM_POINT
- EXAM_SCOPE
- GRADE_WEIGHT / GRADE_RULE
- HOMEWORK / DEADLINE
- NO_PROOF_REQUIRED / NOT_EXAMINED
- TEACHER_EXTENSION
- TEXTBOOK_REFERENCE / QUESTION

## 11. 教材事实、老师事实、AI 派生永久分层

永远保留：

```text
Textbook fact
Lecture fact
Derived / AI fusion
```

老师没有讲完整时，可以用教材补定义、定理、公式、证明、例题和习题，但必须显示教材来源，不能显示成老师原话。

录音层至少分：

```text
raw_audio
raw_transcript
local_refined
ai_refined
```

raw source 永久保留；精加工只能生成新 revision。

## 12. 每日 GPT Processing Job

第一版人工触发，不做后台定时。

```text
App local first-pass
→ Drive pending_ai
+ GitHub schema/rules/current state
+ canonical Course Package
→ GPT Processing Job
→ refined transcript / LectureEvents / concept links / exam signals / textbook supplements / derived notes
→ processed revision
→ Drive / Sync API
→ App
```

每次 Processing Job 保留 input revision、processor version、schema/rule version、教材版本和 processed time。以后模型升级可重新处理历史录音，但不覆盖 raw source。

同时生成 What Changed 增量摘要和 Course Timeline 更新。

## 13. 多设备同步

每台设备保持自己的 SQLite 和 `profile_id`。

```text
App(s)
→ Book Sync API
→ owner-controlled Drive
```

未来按增量 record/event 同步；每个 event 使用全局唯一 `event_id`，远端幂等应用。禁止两台设备直接编辑同一个 SQLite。

朋友端不持有 owner Drive Token / Google 凭证。

桌面和手机共享同一业务 contract，允许同步的数据语义一致。

## 14. Private Meeting

Meeting 与 Course / Book / Section 独立，默认私有。

可复用 Audio / VAD / ASR / SQLite / profile_id / Sync transport / ProcessingJob，但：

- 不参与教材知识融合
- 不进入朋友 shared Learning feed
- Meeting retrieval 与 Learning retrieval 隔离
- 精加工输出 Decision / ActionItem / Deadline / Risk / FollowUp 等会议对象

## 15. Exam Digital Twin

考试中心最终建立可追踪 Exam 模型：日期、范围、总分、章节/主题占比、题型、老师明确提示、confirmed/probable/unknown 状态、覆盖率和风险区域。

LectureEvent 中的考试信号是证据之一，不直接覆盖用户确认事实。

Exam Digital Twin 是 Exam Sprint 和 Next Best Action 的目标约束。

## 16. Mistake / Mastery

StudyRecord 只表示学习行为，不等于真正掌握。

Mastery 应根据复习测试、刷题正确率、重复错误、回忆能力、时间间隔和明确自评等证据逐步估计。

错题不仅保存题目，还映射到 Concept 和 prerequisite，区分：definition gap、theorem condition、formula misuse、prerequisite gap、reasoning break、calculation/careless 等错误，并生成最短修复路径。

## 17. Next Best Action

长期系统应回答“现在最应该学什么”，而不是只展示资料。

输入：

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

输出必须是可解释学习动作，并显示 reason/evidence。AI 不得无证据直接提高 Mastery 或修改考试事实。

## 18. Google Drive 与 GitHub 分工

GitHub：代码、schema、Course Package contract、processing rules、产品规范、Current State、Roadmap、测试/CI、小型 canonical 治理数据。

Drive：原始教材 PDF、课堂/Meeting 录音、用户附件、同步包、processing bundles、大型生成结果、exports/backups。

原始教材和原始录音不得因为已结构化/已精修而删除。

## 19. Android / Desktop / PWA

Book 最终支持桌面/PWA 与 Android App。

业务能力保持一致；设备差异只影响交互和底层实现。SQLite 路径、profile identity、sync boundary、课程资产和录音能力均不能绑定某一台 Windows 电脑。

教材、ASR 权重和本地模型长期按需安装/导入，避免把所有资产打入巨大 APK。

## 20. 开发与验收策略

详细见 `docs/DEVELOPMENT_STRATEGY.md`。

核心：

- ChatGPT 聊天模式 = 主开发
- Spec / Schema / Acceptance Contract
- Vertical Slice + TDD
- GitHub Actions 分层 CI
- Functional Analysis = Golden Course
- Architecture Fitness Functions
- exact final HEAD 才能宣称阶段完成
- 完整版本后 Codex 先做 read-only Full Repository Audit，再形成 Upgrade Spec 定向升级

## 21. 当前阶段边界

当前 Phase 1G 只做：

```text
StudyRecord
SQLite
hidden profile_id
recent learning
sync-ready metadata
```

多教材、Course Compiler、Unified Retrieval、Concept Graph、录音、Drive Sync、Meeting、ExamPoint、Mastery、Next Best Action 等均是已确认后续方向，不能在尚未实现时当成当前能力。