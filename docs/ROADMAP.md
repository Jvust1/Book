# Book 开发路线图

> 状态同步：2026-08-28
>
> Stein & Shakarchi《Functional Analysis》已完成全书结构化并达到 `STRUCTURED_COMPLETE / RUNTIME_READY`。Phase 1F 教材内问答已通过最终 CI 并合并到 `main`（merge commit `8d78b5beea8339f4326749ffebd123d1903f1a2b`）。当前唯一工程主线是 Phase 1G 长期学习记录；Phase 1G 设计已批准，实施尚未开始。

## 产品基线

- [x] 一个 Book App 支持多门彼此独立的教材课程
- [x] 当前 App 产品入口：一门 course 恰好对应一本 enabled 主教材
- [x] PDF 页 / 纸质页分离
- [x] 每节固定提供 `预习｜学习｜复习｜刷题` 四个并列入口
- [x] 四模式不强制顺序、不互相锁定
- [x] 教材来源必须可追溯；缺失内容与锚点不得静默编造
- [x] 第一本文档资产完成全书结构化、审计与完成标记
- [x] 教材搜索与教材问答已形成真实来源闭环
- [ ] 后续加入《实分析》等教材时，作为新的独立 course 注册到 Library

## Phase 1：教材运行时与本地学习 App

### 1A. Runtime 教材导入契约 — 已完成

- [x] `STRUCTURED_COMPLETE` / readiness gate
- [x] metadata / PageMap / structured chunks / 中文学习层 / search index
- [x] canonical identity 校验
- [x] `BookRuntime`
- [x] Functional Analysis 达到 `RUNTIME_READY`

当前真实基线：442 PageMap 行、1493 条唯一搜索记录。

### 1B. Course → Book → Chapter → Section — 已完成

- [x] `CourseRuntime`
- [x] `BookRuntime`
- [x] Chapter 树
- [x] Section 列表
- [x] PDF 页 / 纸质页同时暴露
- [x] Functional Analysis 稳定暴露 8 Chapter / 132 Section

### 1C. Library + Section Learning Runtime — 已完成

- [x] `LibraryRuntime`
- [x] App Library 注册真实课程
- [x] `SectionLearningRuntime`
- [x] Preview / Learn / Review / Practice 四个确定性来源投影
- [x] 四模式自由进入
- [x] review / practice 空结果作为正常状态
- [x] AI 生成内容与教材事实分离

### 1D. Local-first Book App MVP — 已完成

- [x] FastAPI 本地 API
- [x] React + TypeScript + Vite PWA
- [x] Library → Course → Chapter → Section
- [x] 四学习模式
- [x] `SourceResolver`
- [x] 结构化来源页
- [x] 纸质页 / PDF 页 / source anchor
- [x] Section → Source → Section 短期返回状态
- [x] 桌面与 390×844 浏览器验收

> `sessionStorage` 只承担短期导航恢复，不是长期学习记录。

### 1E. 教材内搜索与来源跳转 — 已完成

- [x] 中文 / 英文搜索
- [x] 术语 / 定理 / 公式 / 例题 / 习题统一搜索
- [x] canonical source identity
- [x] Search → Source → Search 恢复
- [x] 正常零结果与错误状态分离
- [x] Runtime / App / Web / 浏览器 gate

### 1F. 教材内问答 — 已完成并合并

- [x] Course 整本教材问答
- [x] Section-first → book fallback
- [x] bounded EvidencePack / history
- [x] server EvidenceGate
- [x] citation 服务端验证
- [x] 证据不足 fail closed
- [x] QA → Source → QA 恢复同一份已验证会话
- [x] OpenAI-compatible server provider；API Key 不进入浏览器
- [x] deterministic fake provider CI
- [x] Python 3.11 / 3.12 / 3.13 Runtime gate
- [x] App full discovery / Vitest / typecheck / build / Chromium acceptance
- [x] 未修改 `books/functional-analysis/**` canonical 教材资产
- [x] PR #8 合并到 `main`

## Phase 1G：长期 StudyRecord — 设计已批准，待实现

设计规范：`docs/superpowers/specs/2026-08-28-study-record-phase-1g-design.md`

### 持久化

- [ ] 本机 SQLite 持久层
- [ ] FastAPI `StudyRecordService` / repository boundary
- [ ] 数据库路径抽象，不绑死 Windows 当前工作目录

### 身份

- [ ] 首次初始化生成稳定隐藏 UUID `profile_id`
- [ ] 单用户 UI，不做账号/用户切换
- [ ] 浏览器不能指定或伪造 profile identity

### 四模式进度

- [ ] `preview / learn / review / practice` 四模式独立
- [ ] 首次进入有效 mode：`in_progress`, `progress=0`
- [ ] 再次进入更新 `last_studied_at`
- [ ] 用户手动 `标记完成`：`completed`, `progress=100`
- [ ] 已完成记录重新进入不退回进行中
- [ ] 不按滚动距离、停留时间制造中间百分比

### 最近学习与返回

- [ ] 最近学习 Course / Section / mode
- [ ] 最近学习按 `last_studied_at` 排序
- [ ] 与 Section / Search / QA 的 `sessionStorage` 短期返回状态严格分离

### Sync-ready

- [ ] 记录保留 `study_record_id / profile_id / revision / updated_at / deleted_at / sync_status`
- [ ] Phase 1G `sync_status` 固定为 `local`
- [ ] 不实现 Drive、SyncEvent、SyncEngine、云账号、远程冲突解决

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
- [ ] 老师课堂补充入口预留

### 复习

- [x] Runtime 核心对象过滤
- [x] 内容按需展开
- [ ] 1 分钟 / 5 分钟 / 完整复习
- [ ] 闪卡
- [ ] 填空 / 判断 / 简答
- [ ] 公式回忆
- [ ] 错题重做入口

### 刷题

- [x] Runtime 教材 exercise / problem 投影
- [ ] 题目筛选
- [ ] 作答与答案记录
- [ ] 教材变式题接口
- [ ] AI 生成题接口
- [ ] 错题筛选

> 所有非教材原生内容必须与教材原文/结构化事实在数据与 UI 上明确区分。

## Phase 1I：Chapter Hub

- [ ] 章节总结
- [ ] 核心知识点
- [ ] 章节公式
- [ ] 初始考点
- [ ] 可点击思维导图
- [ ] 章节测试

## Phase 1J：ExamPoint Engine 与教材锚点

第一版基础重要度只使用教材真实结构化证据，不让 AI 凭感觉决定“重点”。

- [ ] `ExamPoint`
- [ ] `ExamPointAnchor`
- [ ] S / A / B / C 或等价优先级
- [ ] 可解释 `priority_score / reasons`
- [ ] 定义 / 定理 / 公式 / 证明 / 例题 / 习题证据
- [ ] 教材内部重复引用信号
- [ ] 前置 / 后续知识依赖信号
- [ ] 教材显式强调信号
- [ ] 每个考点绑定真实 canonical source anchors
- [ ] 点击跳具体来源 / 锚点
- [ ] 返回时恢复考点上下文、滚动、展开与筛选
- [ ] 上一个 / 下一个考点

后续课堂、考试范围、作业、错题和 Mastery 只能在教材基础重要度上追加独立可解释信号，不能覆盖教材原始证据。

## Phase 1K：Exam Sprint / 期末速通

每一本已完成结构化的教材都生成独立的期末速通路线。它不是四学习模式中的第五个 mode。

- [ ] 30 分钟保命版
- [ ] 2 小时核心版
- [ ] 6 小时考试版
- [ ] 完整速通
- [ ] 按 ExamPoint 优先级裁剪内容
- [ ] 保留最小必要前置依赖
- [ ] 必须掌握的定义 / 定理 / 公式 / 条件
- [ ] 证明主线与“是否需要完整证明”层级
- [ ] 典型例题 / 习题
- [ ] 易混淆点
- [ ] 每项显示“为什么重要”和真实教材来源
- [ ] AI 只负责基于已选真实材料组织速通讲义，不负责无证据发明重点

长期可叠加：老师强调、明确考试提示、考试范围、作业频率、个人错题、Mastery。

## Phase 1L：本地 PDF Reader 接入

- [ ] canonical `book_id` → 本机 PDF 路径
- [ ] 不把大 PDF 提交 GitHub
- [ ] PDF.js 或等价查看器
- [ ] PageMap 驱动 PDF 页 / 纸质页跳转
- [ ] 有真实 geometry 时精确高亮
- [ ] geometry 缺失时仅真实页级定位，不伪造高亮
- [ ] 与现有结构化来源页并存

## Phase 2：Learning 录音与本地初加工

- [ ] 开始 / 暂停 / 结束录音
- [ ] `Lecture` 对象
- [ ] 原始音频本地持久化
- [ ] 原始音频永久保留
- [ ] VAD
- [ ] 本地 ASR
- [ ] 时间戳字幕
- [ ] 基础断句 / 标点 / 中英文混排
- [ ] 数字 / 百分比
- [ ] 从当前教材生成专业术语词典
- [ ] 教材术语辅助 ASR 二次纠错
- [ ] 本地初步知识点 / Section 匹配
- [ ] `raw_transcript` 与 `local_refined` 分开

### 快捷标记

- [ ] ⭐ 重点
- [ ] 🎓 考试
- [ ] 📝 作业
- [ ] ❓ 没听懂
- [ ] 💡 拓展

## Phase 3：Drive-backed 多设备协作同步

目标：朋友只使用 App，不需要 GitHub / Drive 操作权限，也不持有 owner Drive 长期凭证。

- [ ] Book Sync API 边界
- [ ] App 本地 SQLite 保持设备内权威运行库
- [ ] Drive 作为用户数据 / 大文件 / 同步包存储后端
- [ ] `profile_id` 区分不同设备/参与者
- [ ] 增量同步，不共享整个 SQLite 文件
- [ ] `SyncEvent` 全局唯一 `event_id`
- [ ] unseen event 幂等应用
- [ ] per-record `revision`
- [ ] 删除 tombstone 语义
- [ ] 大文件通过 hash + Drive reference 关联，不嵌进事件
- [ ] shared Learning 与 private 数据通道隔离
- [ ] 个人 StudyRecord 是否共享作为独立配置策略

## Phase 4：Learning 课堂智能结构化与教材融合

事实层永久分开：

```text
Textbook fact layer
Lecture fact layer
Derived / AI fusion layer
```

- [ ] `raw_transcript`
- [ ] `local_refined`
- [ ] `ai_refined`
- [ ] LectureEvent：IMPORTANT / EXAM / HOMEWORK / DEADLINE / SCOPE / GRADE_RULE / TEACHER_EXTENSION / TEXTBOOK_REFERENCE / QUESTION
- [ ] 老师原话保留原始时间戳
- [ ] 老师未完整展开的定义 / 定理 / 公式 / 证明 / 例题可从 canonical 教材补充
- [ ] 教材补充必须标明教材来源，不伪装成老师原话
- [ ] 课堂知识点与 Concept / Section 对齐
- [ ] 老师强调可作为后续 ExamPoint 附加证据

### 人工触发的每日精加工

第一版不自动定时。

- [ ] App / Drive 标记当天新增录音为 `pending_ai`
- [ ] 用户每天晚上手动触发 ChatGPT 处理当天全部新增录音
- [ ] ChatGPT 读取 Drive pending 数据 + GitHub schema / 规则 + canonical 教材
- [ ] 生成新 processing revision
- [ ] 写回 `processed` 结果
- [ ] 双端 App 后续同步
- [ ] 默认不重复处理已经 `processed` 的同一 revision

## Phase 5：Private Meeting 分支

Meeting 是与 Course / Book / Section 独立的业务域，默认私有。

- [ ] Meeting 首页/入口
- [ ] `Meeting`
- [ ] `MeetingTranscriptSegment`
- [ ] `MeetingEvent`
- [ ] Decision
- [ ] ActionItem
- [ ] Deadline
- [ ] FollowUp
- [ ] 复用 Audio / VAD / ASR / SQLite / profile_id / sync transport / refinement pipeline
- [ ] Meeting 不进入朋友 shared Learning 数据流
- [ ] Meeting 不参与教材知识融合
- [ ] 每天新增 Meeting 录音同样进入 `pending_ai`
- [ ] 精加工结果只回到 owner 自己的 App

## Phase 6：考试中心

- [ ] 成绩构成
- [ ] 作业 / 期中 / 期末比例
- [ ] 考试日期与范围
- [ ] 不考 / 必考内容
- [ ] 题型 / 分值
- [ ] 开卷 / 闭卷 / 允许资料
- [ ] 是否提供公式
- [ ] 已确认 / 高概率 / 待确认状态
- [ ] 用户确认 / 修正流程
- [ ] 真实考试信息作为 ExamPoint / Exam Sprint 独立证据层

## Phase 7：更多独立课程与教材版本更新

- [ ] 新教材作为独立 course 注册到 Library
- [ ] 复用 Runtime / API / Web，不复制 App
- [ ] 教材版本差异分析
- [ ] 旧锚点 → 新锚点重映射
- [ ] 历史课堂 / 笔记 / StudyRecord 不失效
- [ ] 每一本 `STRUCTURED_COMPLETE / RUNTIME_READY` 教材可生成自己的 ExamPoint / Exam Sprint

## Phase 8：掌握度与自适应复习

- [ ] AnswerRecord
- [ ] Mistake
- [ ] Mastery
- [ ] 错误类型分析
- [ ] 正确率 / 复习次数 / 最近复习
- [ ] 遗忘管理
- [ ] 间隔复习
- [ ] 个人错题 / Mastery 作为个性化 Exam Sprint 追加证据

## Phase 9：全课程搜索与 AI

- [ ] 搜教材
- [ ] 搜课堂
- [ ] 搜考点
- [ ] 搜题目
- [ ] 搜笔记
- [ ] 搜错题
- [ ] 明确配置不同资料源的证据优先级
- [ ] 教材、老师、个人资料、AI 衍生内容在 UI 和数据层保持可区分

## 当前唯一下一步

**保持 `feature/study-record-phase-1g`，为已批准的 Phase 1G 设计编写详细实施计划，然后按 TDD 实现 `StudyRecord + SQLite + hidden profile_id + recent learning + sync-ready metadata`。**

当前不要提前实现录音、Drive Sync、Meeting、ExamPoint 或 Exam Sprint；这些能力的边界已经固定到路线图，等对应阶段再实现。
