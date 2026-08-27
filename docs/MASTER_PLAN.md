# Book 总体产品计划

更新时间：2026-08-28

## 1. 产品目标

Book 的目标不是做“PDF + AI 聊天”，而是构建一个长期可更新、来源可追溯、可跨设备协作的学习 Course OS，并在同一个 App 中提供一个与教材体系独立的私有 Meeting 记录域。

Learning 系统持续接收：

- 多本教材 PDF 与教材版本更新
- 教材结构化数据
- 课堂录音与逐字稿
- 老师补充、强调、考试提示
- 作业、Deadline、考试范围与成绩规则
- 用户笔记、题目、错题与学习记录

最终统一到课程知识体系中，但必须始终保留“教材事实、老师事实、个人数据、AI 衍生内容”的来源边界。

Meeting 系统复用录音与处理基础设施，但业务数据默认私有，不并入 Course / Book / Section。

## 2. 顶层产品结构

```text
Book App
├── Learning / Course OS
│   ├── Courses
│   ├── Books / Versions
│   ├── Chapters / Sections
│   ├── StudyRecords
│   ├── Search / QA
│   ├── Lectures
│   ├── ExamPoints
│   ├── Exam Sprint
│   ├── Questions / Mistakes / Mastery
│   └── Exams
│
├── Meeting (private)
│   ├── Meetings
│   ├── Transcripts
│   ├── Decisions
│   ├── ActionItems
│   ├── Deadlines
│   └── FollowUps
│
└── Shared Infrastructure
    ├── local SQLite
    ├── hidden profile_id
    ├── Audio / VAD / ASR
    ├── local-first processing
    ├── sync transport
    └── AI refinement pipeline
```

Learning 与 Meeting 可以共享底层技术，但不得共享业务身份或事实语义。

## 3. Canonical 教材与来源原则

教材结构化数据是教材事实层的 canonical source。

任何教材对象至少应保留：

```text
course_id
book_id
book_version_id
chapter_id
section_id
pdf_page_index
printed_page
content_anchor_id
element_type
element_id
```

PDF 页与纸质页分离。版本更新不能让旧课堂、笔记、StudyRecord 或来源锚点静默失效；需要稳定 identity、hash、版本映射与锚点重定位。

缺失内容、页码、几何位置或来源不得由 AI 静默编造。

## 4. 多教材体系

一门课程可以长期支持主教材、辅助教材、英文教材和参考教材；不同教材可共同指向统一 Concept，但不能把不同教材观点强制融合为一个“唯一原文”。

当前 App 产品 gate 仍保持“一门 course 一本文启用主教材”；底层 Runtime 保持多书扩展能力。后续只有在真实需求出现时再放宽 App gate。

每一本达到 `STRUCTURED_COMPLETE / RUNTIME_READY` 的教材都应独立具备搜索、QA、ExamPoint 和 Exam Sprint 能力。

## 5. 四个学习模式

每一节固定提供：

```text
预习 / 学习 / 复习 / 刷题
```

规则：

- 用户自由进入
- 不强制固定顺序
- 不互相锁定
- 四模式分别记录进度

长期可发展为更丰富的百分比、次数或正确率，但 Phase 1G 第一版只使用：

```text
未开始：无记录
进行中：status=in_progress, progress=0
完成：status=completed, progress=100
```

第一版不使用滚动距离或停留时间伪造学习程度。

## 6. StudyRecord 与本地持久化

长期学习记录采用 local-first SQLite。

浏览器只通过 FastAPI 访问持久层；SQLite 路径通过可移植 helper 管理，不绑死 Windows 工作目录，为未来 Android App 数据目录预留。

UI 仍是单用户，但每个安装生成一个隐藏稳定 UUID `profile_id`。逻辑 StudyRecord 唯一键：

```text
profile_id + course_id + section_id + mode
```

需要保留 sync-ready metadata：

```text
study_record_id
profile_id
revision
updated_at
deleted_at
sync_status
```

Phase 1G 中 `sync_status=local`，只预留，不实现真正同步。

`sessionStorage` 继续只负责页面返回状态，与 SQLite 长期记录严格分离。

## 7. 搜索与教材问答

搜索与问答必须建立在真实 canonical 资料源上。

当前已完成：

- 教材中英文搜索
- 真实来源往返
- Course / Section 教材内问答
- Section-first → book fallback
- server EvidenceGate
- 服务端 citation verification
- 证据不足 fail closed

长期如果问答加入课堂、笔记、错题等资料源，必须显式配置证据源和优先级，并在 UI 中区分教材依据、课堂依据、个人依据和 AI 衍生。

## 8. ExamPoint Engine

ExamPoint 是“什么重要”的可解释层，不等同于 AI 摘要。

第一版只根据教材真实结构化信息形成教材基础重要度，例如：

- Definition / core concept
- Theorem / proposition
- Formula + assumptions / conditions
- Proof / proof skeleton
- Example
- Exercise / problem
- 教材内部重复引用
- 前置与后续知识依赖
- 教材显式强调

每个 ExamPoint 必须保留：

```text
priority_level
priority_score
reasons
prerequisite_ids
canonical source anchors
```

以后可追加老师强调、明确考试提示、考试范围、作业频率、个人错题和 Mastery，但这些附加信号不能覆盖教材基础证据。

## 9. Exam Sprint / 期末速通

Exam Sprint 是每本结构化教材的独立考试学习路径，不作为第五个学习 mode。

第一版提供：

```text
30 分钟：保命版
2 小时：核心版
6 小时：考试版
完整速通：全部核心考点
```

路线由 ExamPoint priority 和最小必要前置依赖决定，而不是简单按章节截断。

速通内容重点组织：

- 必须会的定义
- 必须记的定理和使用条件
- 核心公式
- 需要掌握的证明主线
- 典型例题 / 习题
- 易混淆点
- 高频结构关系

每一项必须能解释“为什么重要”和“教材来源在哪里”。AI 只负责将已选真实证据组织为高效讲义，不负责凭空决定考点。

## 10. Learning 课堂录音

课堂录音用于捕获教材之外的真实教学信息。

建议记录：

```text
Lecture
lecture_id
course_id
profile_id
date
started_at
ended_at
raw_audio_id
processing_status
```

录音优先 local-first：

```text
Audio
→ VAD
→ local ASR
→ timestamped raw transcript
→ 术语纠错 / 断句
→ 初步 Section / Concept 匹配
→ pending_ai
```

教材结构化后可生成课程专属术语词典，并优先匹配教材已存在的数学术语、公式和对象，减少通用 ASR 在数学课堂中的误识别。

## 11. 老师事实、教材事实与 AI 融合永久分层

课堂与教材不能互相覆盖。

```text
① Textbook fact layer
② Lecture fact layer
③ Derived / AI fusion layer
```

例如老师只说“完备性自己回去看”，系统可以判断课堂没有完整展开，然后从教材中检索定义、定理、证明或例题进行补充，但必须显示：

- 哪句话来自老师及其录音时间戳
- 哪个补充来自教材及其 canonical source
- 哪部分是 AI 的组织、摘要或学习建议

教材补充不能改写 `raw_transcript`，也不能被显示成“老师原话”。

## 12. 录音数据版本与永久保留

录音相关内容至少保留四层：

```text
raw_audio
raw_transcript
local_refined
ai_refined
```

当前产品决策：

- `raw_audio` 永久保留
- 派生内容不得覆盖 raw source
- 处理需要 `processing_version / processed_at / source_links`
- 需要重跑时生成新 processing revision
- 当前不要求 App 在上传 Drive 前自行加密原始录音

原始音频不提交 GitHub。

## 13. 多设备协作与 Drive 同步

长期目标是让朋友只使用 App 联网同步，不需要操作 GitHub 或 owner 的 Drive 账号。

推荐边界：

```text
你的 App ─┐
          ├─ Book Sync API ─→ owner-controlled Google Drive
朋友 App ─┘
```

约束：

- owner Drive Token / Google 账号凭据不进入朋友 APK
- 每台设备保留自己的 SQLite
- 不允许两台设备直接编辑同一个 SQLite 文件
- `profile_id` 区分不同参与者
- Drive 保存用户数据、录音、大文件、同步包和 processed 结果
- GitHub 保存代码、schema、处理规则、治理和可版本控制的项目规范

未来同步采用增量事件，而不是整库上传：

```text
local mutation
→ unique SyncEvent
→ incremental bundle
→ Sync API / Drive
→ remote device applies unseen event_id once
```

每个事件应具备全局唯一 `event_id`，以实现幂等。大文件通过 `audio_id / hash / path-or-reference` 关联，不把音频 bytes 嵌入事件。

StudyRecord 数据模型允许未来共享/合并；第一版同步是否共享个人进度作为独立策略配置，不与课堂共享强绑定。

## 14. 每日晚间人工 AI 精加工

第一版明确采用人工触发，不做后台定时任务。

你和朋友的 App 在本地完成初加工后，将允许共享的 Learning 数据同步到 owner-controlled Drive；你的私有 Meeting 数据进入独立私有区域。

每天新增录音标记：

```text
processing_status = pending_ai
```

你晚上手动让 ChatGPT 处理当天新增录音：

```text
Drive pending_ai
+ GitHub 当前 schema / rules / project state
+ canonical textbook data
→ ChatGPT refinement
→ processed result
→ Drive
→ apps sync
```

Learning 处理包括术语修正、教材匹配、知识缺口识别、考点/作业/考试信息抽取和教材补充。

Meeting 处理包括摘要、决策、Action Items、Deadline、风险、未决问题和 Follow-up，但只回到 owner 私有空间。

## 15. Private Meeting 域

Meeting 业务独立于教材系统。

建议实体：

```text
Meeting
MeetingTranscriptSegment
MeetingEvent
Decision
ActionItem
Deadline
FollowUp
```

Meeting 可复用录音、VAD、ASR、SQLite、profile_id、Drive transport 和 AI refinement pipeline，但：

- 不要求 `course_id / book_id / section_id`
- 默认私有
- 不进入朋友 shared Learning 数据流
- 不参与教材知识融合
- 当天新增录音仍进入夜间 `pending_ai` 精加工

## 16. Google Drive 与 GitHub 分工

### GitHub

作为项目状态与软件治理权威，主要保存：

- 源代码
- Schema / API contract
- Runtime / processing rules
- 产品规范
- Current State / Roadmap
- 测试与 CI
- 小型结构化治理数据

### Google Drive

作为项目文件与用户数据保险库，主要保存：

- 原始教材 PDF
- 原始课堂录音
- 私有 Meeting 录音
- 用户附件
- 同步包 / processing bundles
- 大型生成结果
- 导出包 / snapshots / backups

原始教材和原始录音不得为了“已结构化/已精修”而删除。

## 17. Android / APK 兼容目标

Book 最终可封装为 Android App 并分享给朋友。

本地 SQLite、路径 abstraction、profile identity 和 sync boundary 从现在开始必须避免绑定某一台 Windows 电脑。

同一个 APK 在不同设备安装后拥有各自 `profile_id` 和 SQLite；未来通过 Sync API 交换允许共享的增量数据，而不是把设备数据库文件互相覆盖。

模型和课程资产长期应支持按需安装/导入，避免把所有教材、ASR 权重和本地 LLM 一次性打进巨大 APK。

## 18. 阶段原则

当前开发顺序以 `docs/ROADMAP.md` 为准。

重要边界：

- 当前 Phase 1G 只做 StudyRecord / SQLite / profile_id / recent learning / sync-ready metadata
- 录音、Drive Sync、Meeting、ExamPoint、Exam Sprint 均不提前塞进 Phase 1G
- 功能实现前先完成设计、测试边界和真实来源约束
- 所有阶段完成时运行对应 Runtime / App / Web / browser regression gate
- canonical 教材资产不得被产品状态或 AI 衍生内容反向污染
