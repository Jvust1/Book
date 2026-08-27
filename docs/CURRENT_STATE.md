# Book 当前状态

更新时间：2026-08-28

> 本文件记录当前有效成果、已确认产品决策和唯一下一步。若与旧聊天、旧 Drive CURRENT 文档或更早规划冲突，以 GitHub 当前分支中的本文件、`docs/ROADMAP.md`、`docs/MASTER_PLAN.md` 和已批准设计规范为准。历史 Git 提交继续保留事实，不把已废弃方案写入当前计划。

## 1. 当前工程状态

- Repository：`Jvust1/Book`
- `main` 当前 HEAD：`2fe6758d65a3317691922964e644f3a681571d24`
- Phase 1F 教材内问答已通过最终 CI 并由 PR #8 合并；Phase 1F merge commit：`8d78b5beea8339f4326749ffebd123d1903f1a2b`。
- 最新治理/安全基线已经同步到 Phase 1G 分支；PR #9 merge commit：`8b184ba459b64a6928b1fc66b419f8cb3d9c8884`。
- 当前开发分支：`feature/study-record-phase-1g`
- Phase 1G 设计规范：`docs/superpowers/specs/2026-08-28-study-record-phase-1g-design.md`
- Phase 1G 实施计划：`docs/superpowers/plans/2026-08-28-study-record-phase-1g.md`
- Phase 1G 实施计划提交：`229e5369c80412a66d1e37bba252d9bb817d3991`
- Phase 1G 当前状态：设计和详细实施计划均已完成；业务代码实现尚未开始。

## 2. 当前教材与 Runtime 基线

当前 canonical course：

- `course_id = functional_analysis_course`
- `book_id = stein_shakarchi_functional_analysis_2011`
- Stein & Shakarchi《Functional Analysis》
- 8 Chapters / 132 Sections
- 1493 条唯一搜索记录
- `STRUCTURED_COMPLETE / RUNTIME_READY`
- PDF 442 / 442 页覆盖，最终印刷页 423
- 全书审计：PASS 20 / WARN 1 / FAIL 0

Phase 1F 分支和合并未修改 `books/functional-analysis/**` canonical 教材资产。

这本教材是当前第一本完整结构化的数学教材，也是通用 Book App 的首个真实验证载体。长期目标不是为每本书单独写 App，而是让新教材通过统一导入/结构化/注册流程进入同一个系统。

## 3. 已完成产品能力

### Phase 1A–1C

已完成 Runtime 导入契约、Book / Course / Library Runtime、Chapter / Section 树、四学习模式确定性教材投影和真实来源解析基础。

### Phase 1D

已完成 Local-first FastAPI + React/TypeScript/Vite PWA MVP，包括：

- Library → Course → Chapter → Section
- `预习 / 学习 / 复习 / 刷题` 四个并列入口
- 结构化教材来源页
- 纸质页 / PDF 页身份
- Section → Source → Section 返回状态恢复
- 桌面和 390×844 浏览器验收

### Phase 1E

已完成教材 canonical 搜索：

- 中英文搜索
- 术语 / 定理 / 公式 / 例题 / 习题统一命中
- Search → Source → Search 返回状态恢复
- 无结果、查询错误、course 不存在、search unavailable 明确区分

### Phase 1F

已完成 source-grounded conversational textbook QA：

- Course 整本教材问答
- Section 优先、证据不足时显式 fallback 到整本
- server-owned EvidenceGate
- citation 服务端验证
- 证据不足 fail closed，不猜测答案
- QA → Source → QA 恢复已验证会话，不重新生成旧回答
- OpenAI-compatible provider 仅存在于服务端，浏览器不接触 API Key
- deterministic fake provider 支持 CI

## 4. Phase 1G：已批准且已完成实施计划

Phase 1G 只实现长期学习记录和 sync-ready 本地持久化，不提前实现录音、Drive 同步或 Meeting。

### 持久化与身份

- 本机 SQLite 是长期学习记录的权威运行存储。
- 浏览器通过 FastAPI 访问持久层，不直接操作 SQLite。
- UI 仍为单用户，不做登录或多用户选择。
- 每个安装/设备自动生成一个稳定隐藏 UUID `profile_id`。
- 不使用跨设备共享的 `local-default` 作为持久身份。

### StudyRecord

逻辑唯一键：

```text
profile_id + course_id + section_id + mode
```

四种 mode：

```text
preview / learn / review / practice
```

四模式互相独立，不锁定、不自动联动完成状态。

进度规则：

- 没有记录 = 从未开始
- 首次进入有效 Section / mode = 创建 `in_progress`，`progress=0`
- 再次进入 = 更新 `last_studied_at`，不破坏已完成状态
- 用户手动点击“标记完成” = `completed`，`progress=100`
- 第一版不根据滚动距离、停留时间或 AI 判断制造中间百分比

最近学习位置以 `last_studied_at` 为准。

### Sync-ready 但不做同步

Phase 1G 预留：

```text
profile_id
study_record_id
revision
updated_at
deleted_at
sync_status
```

Phase 1G 中 `sync_status` 固定为 `local`。不实现 Drive、SyncEvent、SyncEngine、云账号或冲突合并。

当前 `sectionViewState / searchViewState / qaSessionState` 的 `sessionStorage` 继续只负责短期返回状态，不能作为长期 StudyRecord。

## 5. 当前确认的课程产品模型

Book 的核心单位是“课程”，每门课程可以使用课堂主教材和辅助教材。教材先进入统一结构化流程，再由同一个 App 自动提供学习功能。

目标工作流：

```text
上传课堂主教材 / 辅助教材
→ 统一结构化
→ canonical identity / source anchors / Runtime readiness
→ 注册到 Course / Library
→ 自动获得学习能力
```

每门课程按三个层级组织：

```text
按节 Section
├── 预习
├── 学习
├── 复习
└── 刷题

按章 Chapter
├── 核心考点
├── 章节总结
└── 可点击思维导图

按整本 Book
└── Exam Sprint / 期末速通资料
```

最终产品原则是“App 通用、教材是数据”。在通用 App 和教材导入契约稳定后，新增课程应主要是上传教材、完成结构化并注册，而不是为每本教材重新开发一套程序。

当前 App gate 仍以每门 course 的 enabled 主教材作为教材事实主源；辅助教材的多书证据融合属于后续扩展，不能在尚未实现时当作已完成能力。

## 6. 已确认的 Learning 课堂录音架构

课堂录音属于 Learning 域，并与 canonical 教材建立关联，但两者不是同一事实源。

永远分离：

```text
Textbook fact layer
Lecture fact layer
Derived / AI fusion layer
```

教材负责稳定、结构化、可引用的知识基线；课堂录音负责老师真实讲授方式、强调、考试信号和教材之外的补充；AI 负责匹配、整理和补充，但不能混淆来源。

录音处理采用 local-first：

```text
课堂录音
→ 本地 VAD / ASR
→ raw_transcript
→ 本地术语纠错 / 断句
→ 初步 Section / Concept 匹配
→ 即时课堂初加工
→ pending_ai
```

即时初加工除逐字记录外，应尽可能结构化提取并标注置信度：

- 老师强调 / 重点
- 初步考点
- 考试范围
- 分值 / 占比 / 成绩规则
- 作业
- Deadline
- 老师额外知识
- 明确“不考 / 不要求证明 / 了解即可”等教学要求

老师原话不会被教材补充改写。系统可以识别课堂知识缺口，再从真实教材结构化数据中补充定义、定理、公式、证明、例题和相关考点，并明确标注教材来源。

教材结构化数据还可用于生成课程术语词典，帮助数学术语、公式和已有对象的 ASR 二次纠错。

录音派生层永久分开：

```text
raw_audio
raw_transcript
local_refined
ai_refined
```

`raw_audio` 按当前产品决策永久保留，不由精修稿覆盖。当前不要求 App 在上传 Drive 前自行加密原始录音。

## 7. 每日 GPT 精加工与“老师课堂独立知识体系”

第一版不做自动定时 AI，由用户每天手动触发 GPT 精加工当天新增录音。

目标不是只生成课堂摘要，而是逐步构建每门课独立的“老师课堂知识体系”，保留老师自己的讲法、强调、考试要求和课程组织方式，再用教材结构化数据补足老师没有完整展开的正式知识。

处理链：

```text
App 本地初加工
→ processing_status=pending_ai
→ 允许同步的数据进入 Drive
+
GitHub 当前 schema / rules / project state / canonical structures
→ GPT 每日精加工
→ 老师课堂知识体系 + 教材补充 + 来源关联
→ 新 processing revision 写回 Drive
→ App 反向同步 processed 结果
```

Learning 精加工至少包括：

- 术语与数学表达校正
- 老师讲课内容重组，但保留原始时间戳与来源
- 老师独立知识点 / Concept 体系
- 老师强调与考试信号归档
- 考点、考试范围、占比/成绩规则、作业、Deadline 抽取
- 与 Section / Concept / ExamPoint 建立关系
- 识别老师未完整展开的知识缺口
- 从主教材/辅助教材结构化数据补充定义、定理、公式、证明、例题和习题
- 明确区分“老师说的”“教材补的”“GPT 组织/建议的”

同一录音不因每天运行而重复精加工；需要重跑时生成新的 processing revision，而不是覆盖 raw source。

## 8. 多设备 / App ↔ Drive/GitHub ↔ GPT ↔ App 方向

用户与朋友最终都只使用联网 App。每台设备保持自己的 SQLite 和稳定 `profile_id`，不共享同一个 SQLite 文件。

长期数据流：

```text
你的 App ─┐
          ├─ Book Sync API ─→ owner-controlled Drive ─→ pending_ai
朋友 App ─┘                                      │
                                                │
GitHub：代码 / schema / rules / current state ───┤
                                                ↓
                                               GPT
                                                ↓
                                     processed revisions
                                                ↓
                                       Drive / Sync API
                                                ↓
                                           双方 App
```

职责边界：

- Drive 保存用户数据、录音、大文件、同步包和 processed 结果。
- GitHub 保存代码、schema、处理规则、产品治理和适合版本管理的 canonical 结构/规范。
- 原始录音和私有 Meeting 数据不提交 GitHub。
- 朋友端 APK 不内置 owner Drive Token、Google 账号凭证或长期秘密。
- 未来同步采用增量 event/record，不整库覆盖；同一 `event_id` 只应用一次。
- StudyRecord 是否共享作为独立策略处理，不与课堂共享强绑定。

## 9. 独立 Private Meeting 域

Meeting 独立于 Course / Book / Section 教材体系之外。

它可以复用：

- Audio capture
- VAD / ASR
- 本地 SQLite
- `profile_id`
- Drive transport
- processing queue
- AI refinement pipeline

但业务数据独立，例如：

```text
Meeting
MeetingTranscriptSegment
MeetingEvent
Decision
ActionItem
Deadline
FollowUp
```

Meeting 默认私有：

- 不进入朋友共享 Learning 数据流
- 不参与教材知识融合
- 精加工结果只回到 owner App
- 每天新增 Meeting 录音同样进入夜间 `pending_ai` 处理

## 10. 每本结构化教材的 ExamPoint / 思维导图 / Exam Sprint

### 按章：ExamPoint + Chapter Hub

章节层应形成：

- 核心考点
- 章节总结
- 核心知识点 / 公式
- 可点击思维导图
- 章节测试

第一版 ExamPoint 只根据教材真实结构化证据确定基础重要度，不让 AI 凭感觉决定重点。

基础信号包括：

- 定义 / 核心概念
- 定理 / 命题
- 公式及使用条件
- 证明及证明主线
- 典型例题
- 教材习题
- 教材内部重复引用
- 前置 / 后续知识依赖
- 教材显式强调

每个考点保存可解释 priority、reasons 和 canonical source anchors。以后可叠加老师强调、考试范围、作业、错题和 Mastery，但课堂/个人信号必须与教材基础证据分开保存。

### 按整本：Exam Sprint / 期末速通

每本 `STRUCTURED_COMPLETE / RUNTIME_READY` 教材都应具备独立 Exam Sprint：

```text
30 分钟：保命版
2 小时：核心版
6 小时：考试版
完整速通：覆盖全部核心考点
```

路线必须考虑 ExamPoint priority 和最小必要前置依赖，不只是按章节截断。每一项显示“为什么重要”和真实教材来源；AI 只负责组织已经有证据的材料。

## 11. 主开发与 Codex 的协作策略

当前正式开发策略：

```text
ChatGPT 聊天模式 = 项目主开发
Codex = 完整版本后的独立审计 + 定向升级
```

聊天模式负责从当前 Phase 1G 开始继续推进整个项目：设计、Spec、Plan、代码实现、测试、CI、GitHub/Drive 状态维护和阶段 PR 审查。

Codex 不作为主线连续开发依赖。等项目达到一个完整可用版本后，再让 Codex：

1. 先做全仓独立审计，重点检查 Architecture / Data Model / SQLite / FastAPI / React / TypeScript / CI / Security / Sync readiness / Android readiness / Performance / Maintainability / canonical data integrity。
2. 审计结果按严重度形成 Upgrade Spec，不直接无边界大改仓库。
3. 需要升级时在独立 upgrade branch 上做 targeted upgrade，再重新跑完整回归。

这样主线不会受 Codex 额度/会话连续性影响，同时保留第二视角审计和后期重构价值。

## 12. 当前明确未实现的能力

以下均为已确认的后续方向，但当前不能当成已完成成果：

- Phase 1G SQLite / StudyRecord 代码实现
- 丰富四模式体验
- Chapter Hub / 可点击思维导图
- ExamPoint Engine
- Exam Sprint / 期末速通
- Android APK 封装
- Google Drive 登录/同步
- Book Sync API
- SyncEvent / SyncEngine
- 多设备冲突解决
- 录音 UI、VAD、ASR
- 即时课堂结构化提取
- Learning 课堂知识体系与教材融合
- 每日 GPT processing pipeline 的真实写回/反向同步
- Meeting UI / Meeting storage
- 原始 PDF Reader

## 13. 当前唯一下一步

保持当前分支 `feature/study-record-phase-1g`，直接按已经完成的实施计划进行测试驱动实现：

```text
StudyRecord + SQLite + hidden profile_id + recent learning + sync-ready metadata
```

实施计划：`docs/superpowers/plans/2026-08-28-study-record-phase-1g.md`

不要在 Phase 1G 顺手实现录音、Meeting、Drive Sync、SyncEvent、ExamPoint 或 Exam Sprint。完成 Phase 1G 后继续沿 `docs/ROADMAP.md` 推进，主线开发默认由聊天模式完成；Codex 留到完整版本后的独立审计与定向升级阶段。
