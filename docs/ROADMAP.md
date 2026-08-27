# Book 开发路线图

> 状态同步：2026-08-28
>
> Stein & Shakarchi《Functional Analysis》已完成全书结构化并达到 `STRUCTURED_COMPLETE / RUNTIME_READY`。Phase 1F 教材内问答已通过最终 CI 并合并到 `main`。当前唯一工程主线是 Phase 1G 长期学习记录；Phase 1G 设计和详细实施计划均已完成，下一步直接按计划 TDD 实现。

详细跨阶段架构：

- `docs/DEVELOPMENT_STRATEGY.md`
- `docs/LEARNING_INTELLIGENCE_ARCHITECTURE.md`

## 产品基线

- [x] 一个 Book App 支持多门彼此独立的课程
- [x] 当前 App gate：一门 course 恰好对应一本 enabled 主教材
- [x] PDF 页 / 纸质页分离
- [x] 每节固定提供 `预习｜学习｜复习｜刷题` 四个并列入口
- [x] 四模式不强制顺序、不互相锁定
- [x] 教材来源必须可追溯；缺失内容与锚点不得静默编造
- [x] 第一本文档资产完成全书结构化、审计与完成标记
- [x] 教材搜索与教材问答已形成真实来源闭环
- [ ] 同一课程支持 `primary + supplementary + reference + translation` 多教材角色
- [ ] 同一教材多版本通过 `logical_book_id + book_version_id` 管理，不覆盖历史版本
- [ ] 桌面/PWA 与手机/Android 保持业务功能一致；允许设备交互差异，但不人为删除桌面录音能力

## Phase 1A–1F：Runtime、App MVP、搜索、教材问答 — 已完成

已完成：

- Runtime 导入契约与 readiness gate
- Book / Course / Library Runtime
- Functional Analysis：8 Chapters / 132 Sections / 1493 search records
- Local-first FastAPI + React/TypeScript/Vite PWA
- Library → Course → Chapter → Section
- 预习 / 学习 / 复习 / 刷题
- SourceResolver 与真实教材来源跳转
- deterministic canonical search
- source-grounded textbook QA
- server EvidenceGate / citation verification / fail closed
- Runtime / App / Web / Chromium gates
- Phase 1F PR #8 已合并

## Phase 1G：长期 StudyRecord — 设计与实施计划已完成，待实现

设计：`docs/superpowers/specs/2026-08-28-study-record-phase-1g-design.md`

实施计划：`docs/superpowers/plans/2026-08-28-study-record-phase-1g.md`

### 持久化

- [ ] 本机 SQLite 持久层
- [ ] FastAPI `StudyRecordService` / repository boundary
- [ ] 可移植数据库路径抽象

### 身份

- [ ] 首次初始化生成稳定隐藏 UUID `profile_id`
- [ ] 单用户 UI，不做账号选择
- [ ] 浏览器不能指定/伪造 profile identity

### 四模式进度

- [ ] `preview / learn / review / practice` 四模式独立
- [ ] 首次进入有效 mode：`in_progress`, `progress=0`
- [ ] 再次进入更新 `last_studied_at`
- [ ] 手动 `标记完成`：`completed`, `progress=100`
- [ ] completed 再进入不倒退
- [ ] 不用滚动距离/停留时间制造伪百分比

### 最近学习与 Sync-ready

- [ ] 最近学习按 `last_studied_at`
- [ ] 与 sessionStorage 短期返回状态严格分离
- [ ] 保留 `study_record_id / profile_id / revision / updated_at / deleted_at / sync_status`
- [ ] 1G 中 `sync_status=local`
- [ ] 不提前实现 Drive / SyncEvent / SyncEngine / 录音 / Meeting / ExamPoint

## Foundation A：Course Package / Course Compiler / 自动验收基础

Phase 1G 通过 exact-head gate 后优先冻结这一层，不要求作为大型 UI 版本发布。

### Course Package / Compiler

- [ ] 冻结 Course Package schema/version
- [ ] 支持教材角色：`primary / supplementary / reference / translation`
- [ ] `course_manifest`
- [ ] book/version identity + hashes
- [ ] chapters / sections / objects / source map
- [ ] terminology / search index
- [ ] readiness `PASS / WARN / FAIL`
- [ ] Course Compiler：上传资料 → 结构化 → validation → readiness → 注册

### Golden Course

- [ ] Functional Analysis 固化为 Golden Course
- [ ] 8 Chapters / 132 Sections / 1493 search records 自动基线
- [ ] canonical identity / source integrity 回归
- [ ] Course Package compatibility 回归

### Architecture Fitness Functions / Contract-first

- [ ] browser 不直接访问 SQLite
- [ ] raw audio 不进入 GitHub
- [ ] raw transcript 不被 refined 覆盖
- [ ] Meeting private data 不进入 shared Learning
- [ ] ExamPoint 必须有 evidence
- [ ] canonical assets 不被产品状态反向修改
- [ ] OpenAPI/JSON Schema 逐步作为前后端契约权威来源

### CI 分层

- [ ] FAST GATE：targeted tests / Vitest / typecheck / architecture checks
- [ ] PR FULL GATE：Python matrix / API / SQLite / build / Chromium / Golden Course
- [ ] HEAVY/RELEASE GATE：canonical rebuild / readiness / release artifacts
- [ ] 重型教材重建、ASR、本地模型、Android/Windows 特殊验证后续可走 self-hosted runner

## Phase 1H：丰富四模式学习体验

### 预习

- [ ] 学习目标
- [ ] 前置知识
- [ ] 核心概念
- [ ] 核心公式预览
- [ ] 关键教材图
- [ ] 易卡点
- [ ] 快速检测

### 学习

- [x] 教材真实对象与来源
- [x] 公式 / 结构化对象基础展示
- [ ] 更完整图表 / 例题交互
- [ ] 个人笔记入口
- [ ] 辅助教材补充入口
- [ ] 老师课堂补充入口预留

### 复习

- [x] Runtime 核心对象过滤
- [ ] 1 分钟 / 5 分钟 / 完整复习
- [ ] 闪卡 / 填空 / 判断 / 简答
- [ ] 公式回忆
- [ ] 错题重做入口

### 刷题

- [x] 教材 exercise / problem 投影
- [ ] 题目筛选
- [ ] 作答与答案记录
- [ ] 教材变式题接口
- [ ] AI 生成题接口
- [ ] 错题筛选

## Foundation B：Minimal Concept Graph + ConceptAlignment + Unified Retrieval v1

### Concept Graph

- [ ] `Concept`
- [ ] prerequisite / dependent relations
- [ ] Chapter/Section ↔ Concept
- [ ] 教材对象 ↔ Concept
- [ ] 第一版使用确定性 graph records，不要求图数据库

### 多教材 ConceptAlignment

- [ ] 同一 Course 下多本 Book 保持原文/页码/编号独立
- [ ] `ConceptAlignment`
- [ ] `defines / explains / proves / examples / exercises / extends / contrasts`
- [ ] 自动对齐保留 confidence / revision
- [ ] primary book 第一版继续提供课程 Section 主骨架
- [ ] 同一本书不同 edition 使用 version mapping，不覆盖旧 anchor

### Unified Retrieval v1

- [ ] 保留现有 deterministic Exact Search
- [ ] SQLite FTS5 / BM25 全文检索
- [ ] Query normalization：中英文、术语别名、Unicode/LaTeX/符号
- [ ] Exact + FTS 结果做 provenance-aware fusion
- [ ] Search 与 QA 共用 Retrieval boundary
- [ ] 结果显式显示主教材/辅助教材/课堂/个人/AI Derived 来源

后续逐步加入：FormulaRetriever、SemanticRetriever、LectureEventRetriever、ExamPointRetriever、PersonalRetriever、MeetingRetriever 和 RRF/等价 rank fusion。

## Phase 1I：Chapter Hub / 思维导图

- [ ] 章节总结
- [ ] 核心知识点
- [ ] 章节公式
- [ ] 初始考点
- [ ] 基于 Concept Graph 的可点击思维导图
- [ ] 章节测试

## Phase 1J：ExamPoint Engine

第一版基础重要度只使用真实教材结构化证据。

- [ ] `ExamPoint`
- [ ] `ExamPointAnchor`
- [ ] S / A / B / C 或等价 priority
- [ ] `priority_score / reasons`
- [ ] 定义 / 定理 / 公式 / 证明 / 例题 / 习题证据
- [ ] 重复引用 / 显式强调 / dependency signals
- [ ] 每个考点绑定 canonical source anchors
- [ ] 点击跳真实来源并恢复上下文

课堂、考试、作业、错题和 Mastery 只能作为独立追加证据，不能覆盖教材基础证据。

## Phase 1K：Exam Sprint / 期末速通

- [ ] 30 分钟保命版
- [ ] 2 小时核心版
- [ ] 6 小时考试版
- [ ] 完整速通
- [ ] ExamPoint priority 裁剪
- [ ] 最小必要 prerequisite closure
- [ ] 定义 / 定理 / 公式 / 条件
- [ ] 证明主线与是否要求完整证明
- [ ] 典型例题 / 习题 / 易混淆点
- [ ] 每项显示“为什么重要”与真实来源

## Phase 1L：本地 PDF Reader

- [ ] canonical `book_id` → 本机 PDF
- [ ] PDF.js 或等价查看器
- [ ] PageMap 驱动 PDF / printed page 跳转
- [ ] 有真实 geometry 才精确高亮
- [ ] geometry 缺失时只做真实页级定位
- [ ] 与结构化来源页并存

## Phase 2：Learning 录音与本地初加工

桌面/PWA 与手机/Android 都提供录音业务能力；可因平台权限和后台策略采用不同实现。

- [ ] 开始 / 暂停 / 结束录音
- [ ] `Lecture`
- [ ] raw audio 本地持久化并永久保留
- [ ] VAD / local ASR / 时间戳字幕
- [ ] 断句 / 标点 / 中英文 / 数字百分比
- [ ] 教材术语词典辅助 ASR 二次纠错
- [ ] 初步 Section / Concept 匹配
- [ ] `raw_transcript` 与 `local_refined` 分开
- [ ] 快捷标记：重点 / 考试 / 作业 / 没听懂 / 拓展

## Phase 3：Drive-backed 多设备协作同步

- [ ] Book Sync API
- [ ] 每台设备自己的 SQLite
- [ ] Drive 保存用户数据、大文件、同步包
- [ ] `profile_id` 区分参与者
- [ ] 增量同步，不共享整个 SQLite
- [ ] `SyncEvent` 全局唯一 `event_id`
- [ ] unseen event 幂等应用
- [ ] per-record revision / tombstone
- [ ] 大文件 hash + Drive reference
- [ ] shared Learning 与 private Meeting 隔离
- [ ] 允许同步的数据在桌面和手机保持一致业务语义

## Phase 4：课堂智能结构化、LectureEvent 与 GPT Processing Jobs

事实层永久分开：

```text
Textbook fact
Lecture fact
Derived / AI fusion
```

- [ ] `raw_transcript / local_refined / ai_refined`
- [ ] LectureEvent：IMPORTANT / EXAM_POINT / EXAM_SCOPE / GRADE_WEIGHT / GRADE_RULE / HOMEWORK / DEADLINE / NO_PROOF_REQUIRED / NOT_EXAMINED / TEACHER_EXTENSION / TEXTBOOK_REFERENCE / QUESTION
- [ ] 老师原话保留时间戳
- [ ] Concept / Section 对齐
- [ ] 教材补充显示 canonical source，不伪装老师原话
- [ ] versioned `ProcessingJob`
- [ ] `input_revision / processor_version / schema_version / textbook_version / processed_at`
- [ ] 每日人工触发 GPT，处理 `pending_ai`
- [ ] 生成新 processing revision，不覆盖 raw source
- [ ] Course Timeline
- [ ] What Changed 增量摘要

## Phase 5：Private Meeting

- [ ] Meeting 首页/入口
- [ ] 录音 / VAD / ASR
- [ ] `Meeting / MeetingTranscriptSegment / MeetingEvent`
- [ ] Decision / ActionItem / Deadline / FollowUp
- [ ] 复用 SQLite / profile_id / sync / ProcessingJob
- [ ] 默认私有
- [ ] 不参与教材知识融合
- [ ] Meeting Search 与 Learning Search 授权/索引隔离

## Phase 6：Exam Digital Twin / 考试中心

- [ ] `Exam`
- [ ] 日期 / 范围 / 总分
- [ ] 章节/主题占比
- [ ] 题型 / 分值
- [ ] 开卷/闭卷/允许资料/公式表
- [ ] 老师明确考试信号
- [ ] confirmed / probable / unknown
- [ ] 当前知识覆盖率 / 风险区域
- [ ] ExamPoint / Exam Sprint 使用该模型作为独立证据层

## Phase 7：更多课程、同课程多教材与版本更新

- [ ] 不同学科/不同课程注册为独立 Course
- [ ] 同一门课的第二本泛函分析教材优先作为同 Course 的 supplementary/reference，而不是复制 App/创建孤立课程
- [ ] primary / supplementary / reference / translation role
- [ ] 多教材 ConceptAlignment
- [ ] 同一本 logical book 多 edition version mapping
- [ ] 旧 anchor → 新 anchor 重映射
- [ ] 历史课堂 / 笔记 / StudyRecord 不失效
- [ ] 各 Book 保持独立 canonical provenance

## Phase 8：Mistake / Mastery Graph / 自适应复习

- [ ] AnswerRecord
- [ ] Mistake
- [ ] Mastery 独立于 StudyRecord
- [ ] `unseen / seen / understood / recallable / basic_problem_ready / transfer_problem_ready / stable`
- [ ] 错误类型：definition gap / theorem condition / formula misuse / prerequisite gap / reasoning / calculation / careless
- [ ] 错题映射 Concept 与 prerequisite
- [ ] shortest repair path
- [ ] 遗忘管理 / 间隔复习

## Phase 9：Unified Retrieval 扩展

- [ ] FormulaRetriever
- [ ] SemanticRetriever
- [ ] ConceptRetriever
- [ ] LectureEventRetriever
- [ ] ExamPointRetriever
- [ ] PersonalRetriever
- [ ] MeetingRetriever（隔离）
- [ ] RRF / equivalent fusion
- [ ] source-aware reranking
- [ ] 搜教材 / 辅助教材 / 课堂 / 考点 / 题目 / 笔记 / 错题
- [ ] Search / QA 共享统一 Retrieval Engine

## Phase 10：Next Best Action 学习决策引擎

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

- [ ] 生成可解释的下一最佳学习动作
- [ ] 说明每个推荐的 evidence / reason
- [ ] 支持考试倒计时下的最短有效学习路径
- [ ] 不允许 AI 无证据直接修改 Mastery 或考试事实

## Android / APK 产品化

- [ ] Android App / APK
- [ ] 与桌面/PWA 共享业务 contract
- [ ] 本地 SQLite / profile identity / sync boundary 跨平台
- [ ] 录音在手机与桌面均可用，平台差异只存在于实现/交互层
- [ ] 教材、模型、ASR 权重按需安装/导入，避免巨大 APK

## 完整版本后的 Codex 阶段

```text
Full usable version
→ Codex Full Repository Audit (read-only first)
→ P0 / P1 / P2 / P3 findings
→ ChatGPT review
→ Upgrade Spec
→ independent upgrade branch
→ targeted upgrade
→ exact-head full regression
```

Codex 不作为主线开发依赖，也不在没有 Upgrade Spec 时自由大扫除式重构稳定仓库。

## 当前唯一下一步

**保持 `feature/study-record-phase-1g`，直接按已完成的实施计划 `docs/superpowers/plans/2026-08-28-study-record-phase-1g.md` 进行 TDD，实现 `StudyRecord + SQLite + hidden profile_id + recent learning + sync-ready metadata`。**

当前不要提前实现录音、Drive Sync、Meeting、ExamPoint、Unified Retrieval、Mastery 或 Next Best Action；这些能力已经进入正式路线图，等对应阶段再实现。