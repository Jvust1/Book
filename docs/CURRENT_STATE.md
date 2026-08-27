# Book 当前状态

更新时间：2026-08-28

> 本文件记录当前有效成果、已确认产品决策和唯一下一步。若与旧聊天、旧 Drive CURRENT 文档或更早规划冲突，以 GitHub 当前分支中的本文件、`docs/ROADMAP.md` 和已批准设计规范为准。历史 Git 提交继续保留事实，不把已废弃方案写入当前计划。

## 1. 当前工程状态

- Repository：`Jvust1/Book`
- `main` 当前已包含 Phase 1F 教材内问答，合并提交：`8d78b5beea8339f4326749ffebd123d1903f1a2b`
- Phase 1F PR #8 已合并；合并前 Runtime / App / Web / Chromium 最终 HEAD gate 全部通过。
- 当前开发分支：`feature/study-record-phase-1g`
- Phase 1G 设计规范：`docs/superpowers/specs/2026-08-28-study-record-phase-1g-design.md`
- Phase 1G 当前状态：设计已确认，尚未进入实现；下一步是实施计划，然后按 TDD 实现。
- Phase 1G 设计检查点：`728bc17dc1a6547f042f43164742e2542b4f23d6`

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

## 4. Phase 1G：已批准设计

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

## 5. 已确认的长期 Learning 录音架构

课堂录音属于 Learning 域，并与 canonical 教材建立关联，但两者不是同一事实源。

永远分离：

```text
Textbook fact layer
Lecture fact layer
Derived / AI fusion layer
```

老师原话不会被教材补充改写。系统可以识别课堂知识缺口，再从真实教材结构化数据中补充定义、定理、公式、证明、例题和考点，并明确标注教材来源。

录音处理采用 local-first：

```text
录音
→ 本地 VAD / ASR
→ 原始逐字稿
→ 本地术语纠错 / 断句 / 初步知识匹配
→ pending_ai
→ 晚间人工触发 ChatGPT 精加工
```

教材结构化数据可用于生成课程术语词典，并帮助数学术语和已有公式匹配。

录音派生层永久分开：

```text
raw_audio
raw_transcript
local_refined
ai_refined
```

`raw_audio` 按当前产品决策永久保留，不由精修稿覆盖。当前不要求 App 在上传 Drive 前自行加密原始录音。

## 6. 已确认的多设备 / 朋友同步方向

目标：朋友只使用联网 App，不需要直接操作 GitHub 或 Google Drive；你可以汇聚双方允许共享的 Learning 数据，再手动交给 ChatGPT 精加工，处理结果再同步回双方 App。

长期拓扑：

```text
你的 App ─┐
          ├─ Book Sync API ─→ owner-controlled Drive
朋友 App ─┘                    ↓
                         pending_ai 数据
                              ↓
                    你手动触发 ChatGPT
                              ↓
                   GitHub 规则 + 教材数据
                              ↓
                       processed 结果
                              ↓
                         双方 App 同步
```

约束：

- 朋友端 APK 不内置你的 Drive Token、Google 账号凭证或长期秘密。
- Drive 负责用户数据、大文件、录音、同步包和处理结果。
- GitHub 负责代码、schema、处理规则、产品治理和适合版本管理的小型结构化规范；原始录音不进入 GitHub。
- SQLite 仍是每台设备本地运行数据库，不共享同一个 SQLite 文件。
- 未来同步采用增量事件 / 增量记录，不整库覆盖。
- 每个 SyncEvent 使用全局唯一 `event_id`，远端只应用未见过的事件，保证幂等。
- 音频等大文件作为 Drive 文件保存；事件只携带 ID、revision、hash、路径/引用等元数据。
- `profile_id` 允许两个人学习同一本教材时仍安全合并。
- StudyRecord 模型允许未来共享/合并；第一版实际同步是否下发个人进度作为独立共享策略，不是 Phase 1G 目标。

## 7. 每日晚间人工精加工

第一版不做自动定时 AI。

每天新增录音均进入待处理范围：

```text
status = pending_ai
```

你晚上手动要求 ChatGPT“处理今天的新录音”后：

1. 读取 Drive 当天新增 `pending_ai` 数据。
2. 读取 GitHub 中当前 schema、处理规则和项目状态。
3. 对 Learning 录音结合 canonical 教材进行精加工。
4. 对 Meeting 录音按私有会议规则精加工。
5. 生成带来源、版本和处理状态的结果。
6. 写回 Drive；对应任务标记 `processed`。
7. App 后续同步处理结果。

同一录音不因每天运行而重复精加工；需要重跑时必须生成新的 processing revision，而不是覆盖 raw source。

## 8. 独立 Meeting 域

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
- 精加工结果只回到你的 App
- 每天新增 Meeting 录音同样进入夜间 `pending_ai` 处理

## 9. 每本结构化教材的“期末速通”

每本完成结构化的教材都应具备独立的 Exam Sprint / 期末速通能力。它不是四学习模式中的第五个 tab，而是建立在教材考点层上的独立考试路径。

第一版只根据教材真实结构化证据确定基础优先级，不让 AI 凭感觉决定重点。

基础 ExamPoint 信号包括：

- 定义 / 核心概念
- 定理 / 命题
- 公式及使用条件
- 证明及证明主线
- 典型例题
- 教材习题
- 教材内部重复引用
- 前置 / 后续知识依赖
- 教材显式强调

每个考点保存 S / A / B / C 或等价优先级、可解释 reasons 和 canonical source anchors。

Exam Sprint 提供：

```text
30 分钟：保命版
2 小时：核心版
6 小时：考试版
完整速通：覆盖全部核心考点
```

路线必须考虑最小必要前置依赖，不只是按章节截断。

以后存在课堂、考试范围、作业、错题和 Mastery 后，可以在“教材基础重要度”上叠加个性化证据；教材基础分和课堂/个人信号必须可区分、可解释、可追溯。

## 10. 当前明确未实现的能力

以下均为已确认的后续方向，但当前不能当成已完成成果：

- Phase 1G SQLite / StudyRecord 代码实现
- Android APK 封装
- Google Drive 登录/同步
- Book Sync API
- SyncEvent / SyncEngine
- 多设备冲突解决
- 录音 UI、VAD、ASR
- Learning 课堂结构化与教材融合
- Meeting UI / Meeting storage
- 晚间自动化调度
- ExamPoint Engine
- Exam Sprint / 期末速通
- 原始 PDF Reader

## 11. 当前唯一下一步

保持当前分支 `feature/study-record-phase-1g`，基于已批准设计编写 Phase 1G 详细实施计划，然后按测试驱动方式实现：

```text
StudyRecord + SQLite + hidden profile_id + recent learning + sync-ready metadata
```

不要在 Phase 1G 顺手实现录音、Meeting、Drive Sync、SyncEvent 或 Exam Sprint。
