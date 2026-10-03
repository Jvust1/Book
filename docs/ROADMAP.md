# Book 开发路线图

## 2026-10-01 01:56 UTC 阅读器候选检查点（尚未合并）

- 实时核对 `main`：`805510f86546709b6f67c9e9079943f205c2c245`，仍为 PR #57 合并结果；下列新增能力目前只在 Draft 分支。
- 已验证代码基线：PR [#75](https://github.com/Jvust1/Book/pull/75)，`5616246fbf88c8a3a0a8732d0e36c5a11c6c6f3b`。整合交接分支 `docs/coherent-reader-candidate-20261001` 以此为父提交，目标为 `main`，自身 exact-head gates 必须另行通过。
- 七个新接入项目为 KaTeX、PDF.js、react-markdown、math.js、Fuse.js、Zod、TanStack Query，均实际进入阅读器运行路径；既有 SymPy 做安全加固，既有 Playwright 用于验收，不重复计入新项目数。
- 原创单章贯通预习/学习/复习/刷题、来源 PDF 本地检索、引用问答、数值计算与显式进度回执恢复。#75 exact head 已通过 Linux/Windows 干净源码提取、403 个 Web 测试、类型/构建、40 个提取后 Python 测试及五条原创浏览器旅程；完整 UI gate 为 38 条常规 + 5 条原创旅程，平台重跑不累计为新用例。
- #71 目录验证/导航恢复分支六条新浏览器用例失败，未纳入该候选；旧 PR 与其他教材审校分支均保留。不得以候选通过推断 #71 已修复。
- 外部[六书审计报告](https://github.com/Jvust1/Book/blob/6d7ecf5969ed1feffc1061dc6bdb68aff77fd708/audits/2026-10-01/six-books_0800_acceptance.md)报告 24 PDF / 3477 页，其中五书 2733 页非 A4、当代中国经济文本层 578 个 NUL、逐书审校/同步证据仍有缺口；这是另一分支的报告，非本次重跑。原创代码验收不替代教材、排版、字体或来源重排验收。
- 交付为 code-only 源码，包含原创合成章节，不含用户教材全文、扫描 PDF、私有资产或原生安装器。详细复现、上游出处和边界见 [阅读器交接](upstream/reader-integration-handoff-2026-10-01.md)。

以下旧阶段和导出记录按当时证据保留。出现“当前 main / 唯一下一步 / H4a 下一步”等旧表述时，按其历史日期理解；实时分支状态以上方检查点和最新 GitHub 记录为准，不将旧记录重新解释为本次授权。

### 本候选后的有界下一步

1. 对 main-targeted Draft 的最终提交重新跑完整 Linux/Windows gates，保留旧 PR 的独立历史。
2. 评审整合差异和许可证/包清单；合并、部署、原生安装器及用户设备验收各自另行处理。
3. 教材审校负责人推进外部报告中的 A4 源重排、隐藏文本层和逐书证据问题；不将这些教材任务纳入本原创代码包。
4. #71 的目录响应/恢复工作仍独立未通过，不能按后面的历史路线图勾选为完成。

## 历史路线与产品基线（保留原复选框）

> 状态同步：2026-08-29
>
> Stein & Shakarchi《Functional Analysis》已完成全书结构化并达到 `STRUCTURED_COMPLETE / RUNTIME_READY`。Phase 1F 教材内问答已合并到 `main`。Phase 1G 长期 StudyRecord 已通过 PR #11 合并到 `main`，merge commit `4b111e4b1ffde86a365aaad2a3164f8aedccc819` 的合并后 Book App UI tests run #194 全绿。Foundation A Tasks 1–10 已完成并通过 PR #13 合并；H0/H1/H2/H3a 也已分别通过 PR #18/#19/#20/#21 集成到 `main`。H3a merge commit 为 `f69166568839b7038b0f0472baefcee34299fa17`；post-H3a governance PR #17 合并后当前 `main` 为 `3c5585b0c5c27d336473a4dfa59ca675097216fd`，下一批准阶段为 H4a shadow FTS5/BM25 evaluation。

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
- [x] 本机 SQLite 持久化四模式 StudyRecord，隐藏本机 `profile_id`
- [ ] 同一课程支持 `primary + supplementary + reference + translation` 多教材角色（Course Package contract 已支持角色；Runtime consumer 尚未迁移）
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

## Phase 1G：长期 StudyRecord — 已完成并合并到 `main`

设计：`docs/superpowers/specs/2026-08-28-study-record-phase-1g-design.md`

实施计划：`docs/superpowers/plans/2026-08-28-study-record-phase-1g.md`

### 持久化

- [x] 本机 SQLite 持久层
- [x] FastAPI `StudyRecordService` / repository boundary
- [x] 可移植数据库路径抽象与 `BOOK_APP_DATA_DIR` 覆盖
- [x] repository 初始化失败与运行期 storage failure 都稳定映射为用户可见 503，不泄露 SQLite 路径/内部细节

### 身份

- [x] 首次初始化生成稳定隐藏 UUID `profile_id`
- [x] 单用户 UI，不做账号选择
- [x] 浏览器不能指定/伪造 profile identity
- [x] `book_id` 由服务器从 canonical Runtime 解析，浏览器不能提交身份字段

### 四模式进度

- [x] `preview / learn / review / practice` 四模式独立
- [x] 首次进入有效 mode：`in_progress`, `progress=0`
- [x] 再次进入更新 `last_studied_at`
- [x] 手动 `标记完成`：`completed`, `progress=100`
- [x] completed 再进入不倒退
- [x] 重复完成幂等，不制造 revision churn
- [x] 不用滚动距离/停留时间制造伪百分比
- [x] StudyRecord 保存失败不阻断教材内容阅读，并提供可重试状态

### 最近学习与 Sync-ready

- [x] 最近学习按 `last_studied_at`
- [x] 与 sessionStorage 短期返回状态严格分离
- [x] 保留 `study_record_id / profile_id / revision / updated_at / deleted_at / sync_status`
- [x] 1G 中 `sync_status=local`
- [x] 浏览器 DTO 不暴露内部 `profile_id / revision / sync_status`
- [x] 不提前实现 Drive / SyncEvent / SyncEngine / 录音 / Meeting / ExamPoint

### Phase 1G 验证基线

PR #11 合并后，`main` merge commit `4b111e4b1ffde86a365aaad2a3164f8aedccc819` 的 Book App UI tests run #194 已通过：

- Runtime discovery：146 / 146
- Functional Analysis readiness：`READY`
- App discovery：87 / 87
- Web tests / typecheck / production build：PASS
- real Chromium acceptance：PASS
- StudyRecord completion 跨 reload 持久化：PASS
- 四模式独立：PASS
- Source → Section 往返：PASS
- 390×844 窄屏无 body 横向溢出：PASS
- StudyRecord SQLite read connection lifecycle regression：PASS
- StudyRecord repository 初始化失败稳定 503 / no-detail-leak regression：PASS
- `books/functional-analysis/**` 在 Phase 1G 产品改动中保持 canonical 零修改

Phase 1G 已完成并集成；后续不再把它作为待合并工作项。

## Foundation A：Course Package / Course Compiler / 自动验收基础 — 已完成并合并

Foundation A Tasks 1–10 已完成，并通过 PR #13 合并到 `main`。Foundation A 不要求作为大型 UI 版本发布，也没有迁移现有 Runtime/App consumer。

- reviewed head：`f1eb4ebd144ccb233e5b8b74e97001af214c60bb`
- merge commit：`82f0cbbcfe5078d304ca7c163b81d4eb01b515f4`

### Course Package / Compiler

- [x] 冻结 Course Package schema/version：`course_package_v1` / `1.0.0`
- [x] Course Package contract 支持教材角色：`primary / supplementary / reference / translation`
- [x] legacy `course_manifest` normalization
- [x] book/version identity + hashes
- [x] chapters / sections / objects / source map 等当前 package artifacts 的确定性编译边界
- [x] terminology / search index 等当前 canonical artifacts 纳入 package inventory / identity
- [x] readiness `PASS / WARN / FAIL`
- [ ] 通用 Course Compiler 产品主链路：上传任意资料 → 自动结构化 → validation → readiness → Runtime/Library 注册

### Golden Course

- [x] Functional Analysis 固化为 Golden Course
- [x] 8 Chapters / 132 Sections / 1493 search records / 442 PDF pages / printed 423 自动基线
- [x] canonical identity / source integrity 回归
- [x] Course Package compatibility / deterministic compile / independent validation 回归

### Architecture Fitness Functions / Contract-first

- [x] browser source 不允许 durable SQLite 依赖/路径模式
- [ ] raw audio 不进入 GitHub（对应模块尚未实现，未来阶段加入 gate）
- [ ] raw transcript 不被 refined 覆盖（对应模块尚未实现）
- [ ] Meeting private data 不进入 shared Learning（对应模块尚未实现）
- [ ] ExamPoint 必须有 evidence（对应模块尚未实现）
- [x] canonical assets 不被 Course Package / Golden / fitness 产品状态反向修改
- [x] Course Package JSON Schema 作为 Foundation A contract 权威来源；其他前后端 OpenAPI/Schema 继续分阶段推进

### CI 分层

- [x] FAST GATE：Python 3.13 syntax / Foundation focused tests / architecture fitness
- [x] PR FULL GATE：Python 3.11/3.12/3.13 / Golden compile+validate / App API / Web / build / Chromium
- [x] HEAVY GATE：manual `workflow_dispatch`，隔离副本 rebuild/recovery + canonical readiness / Golden / fitness；不写回 canonical
- [ ] 重型教材重建、ASR、本地模型、Android/Windows 特殊验证后续可走 self-hosted runner

### Foundation A 历史验证证据

Task 9 workflow implementation HEAD `94fee411b5f8d67a5db2ef5779657f39c226c220`：

- Course Package FAST #1：PASS，Foundation focused 46 / 46，Architecture Fitness PASS
- Runtime reference #157：Python 3.11 / 3.12 / 3.13 PASS；3.13 Golden compile/validate + fitness PASS
- Book App UI #213：app-api / web-client / browser-acceptance PASS
- real Chromium：11 / 11 PASS
- Foundation A 起点到 Task 9 HEAD：`books/functional-analysis/**` canonical diff = 0，App source diff = 0

manual HEAVY workflow 已定义，但没有实际手工运行记录时不得声称 HEAVY 已通过。

### Approved dependency exception — 2026-08-29

历史 Roadmap 顺序继续保留。当前实现周期批准按以下依赖顺序执行：

```text
H0 → H1 → H2 → H3a → H4a → Phase 1H
```

这是明确的依赖例外，不是对历史路线图的追溯式重写。当前进度：

- [x] H0：neutral Book identity — PR #18 merged
- [x] H1：internal source provenance — PR #19 merged
- [x] H2：Exact-only shared Retrieval seam — PR #20 merged
- [x] H3a：Concept/ConceptAlignment contract + reference validation — PR #21 merged
- [ ] H4a：shadow FTS5/BM25 evaluation — NEXT
- [ ] Phase 1H：user-visible slices — AFTER H4a

`H3b`、`B4b`、`B5` 与 StudyRecord book-version migration 仍是以后分别批准的独立决策。H4a 本身不改变 public Search 的 Exact-only 行为。

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

- [ ] `Concept` production authority/data
- [ ] prerequisite / dependent relations production data
- [ ] Chapter/Section ↔ Concept production alignment
- [ ] 教材对象 ↔ Concept production alignment
- [x] H3a inert `Concept / ConceptAlignment / ConceptGraph` v1 contract + repository reference validation
- [ ] 第一版 production graph 使用确定性 graph records，不要求图数据库

### 多教材 ConceptAlignment

- [ ] 同一 Course 下多本 Book 保持原文/页码/编号独立
- [x] H3a `ConceptAlignment` contract / schema
- [x] H3a `defines / explains / proves / examples / exercises / extends / contrasts` relation contract
- [ ] 自动对齐保留 confidence / revision 的 production lifecycle
- [ ] primary book 第一版继续提供课程 Section 主骨架的 multi-book Runtime consumer
- [ ] 同一本书不同 edition 使用 version mapping，不覆盖旧 anchor

### Unified Retrieval v1

- [x] 保留现有 deterministic Exact Search
- [ ] SQLite FTS5 / BM25 全文检索公开激活（H4a 仅 shadow evaluation）
- [ ] Query normalization：中英文、术语别名、Unicode/LaTeX/符号
- [ ] Exact + FTS 结果做 provenance-aware fusion
- [x] Search 与 QA 共用 H2 internal Exact-only Retrieval boundary
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

**H4a shadow FTS5/BM25 evaluation** 是当前唯一下一实现阶段。它必须通过 H2 shared Retrieval boundary 做 shadow 候选/排名/覆盖率评估，并保持 public Search/QA 的 Exact-only 排名、分数、顺序与返回行为不变。

H4a 需要先定义确定性 query/dataset、coverage/ranking metrics、provenance checks、failure semantics 与 exact-HEAD evidence，再进入实现。当前不要提前实现 `H3b`、`B4b`、`B5`、StudyRecord book-version migration，也不要提前实现录音、Drive Sync、Meeting、ExamPoint、Mastery 或 Next Best Action。