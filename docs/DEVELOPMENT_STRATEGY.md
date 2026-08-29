# Book 开发系统策略

更新时间：2026-08-29

## 1. 目的

本文件定义 Book 在当前产品架构之上的长期开发方法。它不替代 `docs/MASTER_PLAN.md`、`docs/ROADMAP.md` 或各 Phase 已批准的 spec/implementation plan，而是规定如何把 Book 从“按功能逐步开发的单一 App”升级为“由标准 Course Package 驱动、可自动验收、可持续扩展到多教材/多课程的 Course OS”。

Phase 1G 和 Foundation A 已完成并合并。2026-08-29 批准的依赖顺序为 `H0 → H1 → H2 → H3a → H4a → Phase 1H`；H0–H3a 已完成并集成，当前下一阶段是 H4a。该顺序是面向当前实现周期的依赖例外，不追溯改写历史 Roadmap；H3b、B4b、B5 与 StudyRecord book-version migration 仍需以后分别批准。

## 2. 总体开发模型

```text
ChatGPT 聊天模式
= 主架构 / 主开发 / 状态维护 / 阶段验收
        ↓
Spec / Schema / Acceptance Contract
        ↓
feature branch / vertical slice
        ↓
GitHub Actions
= 自动测试 / 构建 / regression / architecture checks
        ↓
Functional Analysis Golden Course
= 真实教材基准样本
        ↓
PR / exact-head gate / freeze
        ↓
下一阶段

完整版本后：
Codex
= Full Repository Audit
        ↓
Upgrade Spec
        ↓
独立 upgrade branch
        ↓
定向升级 + 全量回归
```

原则：主开发不依赖 Codex 连续额度；Codex 主要用于完整版本后的独立审计和高价值升级。

## 3. Course Package：让“App 通用、教材是数据”真正落地

长期新增教材不应继续生成教材专用业务代码。每一本/每一组课程教材完成结构化后，应尽可能形成统一 Course Package。

建议逻辑结构：

```text
course-package/
├── course_manifest.json
├── books/
│   ├── main/
│   └── supplementary/
├── chapters.json
├── sections.json
├── objects.jsonl
├── search_index.jsonl
├── source_map.json
├── prerequisite_graph.json
├── terminology.json
├── exam_points.json        # ExamPoint 阶段后产生
└── readiness.json
```

Course Package Contract 需要定义：

- course / book / version 的稳定 identity
- 主教材与辅助教材角色
- Chapter / Section / object schema
- canonical source anchors
- PDF page / printed page mapping
- search records
- terminology
- prerequisite/dependency graph
- readiness / audit status
- package version / schema version / content hashes

最终导入流程应接近：

```text
上传教材
→ 结构化
→ package validation
→ readiness gate
→ 注册 Course / Library
→ App 自动获得可用学习能力
```

目标不是“一本教材做一个 App”，而是“一套 App + N 个可验证 Course Package”。

## 4. Golden Course：把 Functional Analysis 固化为参考实现

当前 Stein & Shakarchi《Functional Analysis》作为第一本完整结构化数学教材，应长期承担 Golden Course / Reference Course 角色。

当前基线至少包括：

```text
8 Chapters
132 Sections
1493 search records
STRUCTURED_COMPLETE / RUNTIME_READY
442 / 442 PDF coverage
final printed page 423
canonical source identities
```

任何涉及 Runtime、App、API、搜索、问答、StudyRecord、Chapter Hub、ExamPoint、Exam Sprint、Lecture linking 或 Course Package 的重要改动，都应使用 Golden Course 做自动回归。

Golden Course 的用途：

1. 检查旧功能是否回归。
2. 检查 canonical identity 是否漂移。
3. 检查新 Course Package Contract 是否仍能载入真实教材。
4. 作为第二、第三本教材接入时的行为参考，但不要求内容完全相同。
5. 作为大规模重构后的 Golden Master 验收样本。

禁止为了让测试变绿而修改 canonical 教材事实。

## 5. Contract-first：Schema 定义一次，前后端尽量自动生成

随着 StudyRecord、Lecture、ExamPoint、Meeting、SyncEvent 等对象增加，应降低 Python / Pydantic / TypeScript 多份手工 DTO 漂移风险。

长期方向：

```text
Canonical Schema / OpenAPI / JSON Schema
          ↓
Python contracts
TypeScript types
API client
validation
```

原则：

- 关键业务字段尽量只有一个权威 schema 来源。
- 前端不能自行扩大可写字段，例如不能选择 `profile_id`、`book_id` 或未来受保护的 sync identity。
- schema evolution 要有 version / migration policy。
- API contract 变化必须有兼容性测试。

Phase 1G 已完成；新的 contract-first 基础继续按后续批准阶段逐步引入，不反向重写现有稳定 API。

## 6. Architecture Fitness Functions：把架构规则变成 CI 可执行约束

长期不能只依靠文档提醒 AI/开发者“不要越界”，应把关键 Architecture Invariants 写成自动检查。

至少逐步覆盖：

```text
browser 不能直接访问 SQLite
browser / APK 不能嵌入 owner Drive token
StudyRecord 不能退回 localStorage 作为 durable authority
raw_audio 不能提交 GitHub
raw_transcript 不能被 refined transcript 覆盖
教材补充不能写成 teacher quote
Meeting private data 不能进入 shared Learning feed
ExamPoint 必须有 canonical evidence
Sync 不能通过整库 SQLite 覆盖完成
canonical textbook assets 不能被产品状态反向修改
```

实现形式可以包括：

- dependency / import boundary tests
- forbidden path / secret scanning
- schema assertions
- API permission tests
- provenance invariant tests
- canonical asset hash/diff checks
- CI workflow gates

这些检查应逐步成为 PR 必须通过的 Architecture Fitness Functions。

## 7. GitHub Actions 作为持续自动验收执行层

聊天模式负责设计和提交代码，GitHub Actions 负责尽可能机器化地证明结果。

目标 gate：

```text
Python 3.11 / 3.12 / 3.13
Runtime tests
FastAPI / SQLite tests
Vitest
TypeScript typecheck
Vite build
Playwright Chromium
Golden Course regression
canonical integrity
Architecture Fitness Functions
Course Package validation
```

后续 Android 阶段再加入 Gradle/APK/Android 相关构建和验收。

任何阶段只能基于 exact final HEAD 的 gate 宣称完成，不能拿旧 commit 的绿色 CI 给新 HEAD 背书。

## 8. Vertical Slice：每次开发一条完整可运行链路

后续实现优先采用 Vertical Slice / Walking Skeleton，而不是先把某一层全部写完再一次性联调。

以 StudyRecord 为例，推荐思路是：

```text
Slice 1
Section learn → SQLite → API → UI in_progress → browser test

Slice 2
manual complete → durable completed → browser test

Slice 3
四模式独立

Slice 4
recent learning

Slice 5
full regression
```

每个 slice 结束时仓库都应保持可运行、可测试、可恢复。

好处：

- 适合聊天模式跨会话开发。
- 更容易定位失败。
- 减少大批代码写完后才发现架构错误。
- 每个 checkpoint 都能形成真实进展，而不是半完成模块。

Phase 1G 与 H0–H3a 的纵向切片已经完成并合并；H4a 与后续 Phase 1H 继续沿用同样的独立 reviewable slice 原则。

## 9. Concept Graph：从“目录结构”升级到“学习依赖结构”

`Course → Book → Chapter → Section` 是阅读结构，不应成为最终唯一知识结构。

后续逐步建立 Concept Graph：

```text
Concept
├── prerequisite concepts
├── dependent concepts
├── textbook definitions/theorems/formulas
├── supplementary textbook explanations
├── lecture explanations
├── teacher emphasis
├── exam signals
├── questions / mistakes
├── mastery
└── ExamPoint
```

Concept Graph 的价值：

- Chapter Hub 思维导图不再只是静态章节树。
- ExamPoint 可以计算知识依赖。
- Exam Sprint 可以求“最小必要知识闭包”，而不是简单从前往后裁章节。
- 课堂内容可以稳定关联到 Concept，而不是只依赖时间戳文本。
- 辅助教材可以对齐同一 Concept，同时保留各自原始来源。

Concept Graph 建议在 Chapter Hub / ExamPoint 之前建立最小基础，不要求一开始实现复杂知识图数据库；可先使用确定性结构化 graph records。

### 当前批准的 Concept / Retrieval 分段

当前实现周期明确把长期方向拆成互不偷跑的阶段：

```text
H3a = Concept/ConceptAlignment contract + repository reference validation only [COMPLETE_MERGED]
H3b = real production Concept authority/lifecycle; later approval required
H4a = shadow FTS5/BM25 evidence only; public ranking unchanged [NEXT]
B4b = public FTS/fusion/ranking activation; later approval required
```

因此 H3a 没有创建 production Concept authority，H4a 也不能改变真实 Search/QA 返回；这些边界是为了让未来能力建立在可验证证据上，而不是把长期路线一次性塞入当前产品。

## 10. LectureEvent：录音保留事件流，不只保留最终总结

课堂录音初加工应逐步从“逐字稿 + 摘要”升级成可追溯事件流。

建议事件类型包括：

```text
IMPORTANT
EXAM_POINT
EXAM_SCOPE
GRADE_WEIGHT
GRADE_RULE
HOMEWORK
DEADLINE
NO_PROOF_REQUIRED
NOT_EXAMINED
TEACHER_EXTENSION
TEXTBOOK_REFERENCE
QUESTION
```

每个 LectureEvent 至少尽量保留：

```text
event_id
lecture_id
start_ms / end_ms
raw_text
normalized_text
type
confidence
concept_id / section_id if matched
source_audio_id
processing_revision
```

最终的“老师重点”“考试范围”“期末建议”都是这些真实事件的派生视图，而不是覆盖事件本身。

## 11. GPT 精加工改为 versioned Processing Job

每天手动触发 GPT 时，不应只生成一份不可追踪的最终笔记，而应把每次精加工视为可重跑的 Processing Job。

概念结构：

```text
ProcessingJob
├── job_id
├── input_revision
├── processor_version
├── rule/schema version
├── textbook/package version
├── started_at
├── processed_at
└── outputs
```

输出可包括：

```text
ai_refined transcript
lecture_events
concept_links
exam_signals
textbook_supplements
derived_notes
```

以后 GPT、规则或教材版本升级时，可以生成新的 processing revision，不覆盖 raw_audio / raw_transcript，也不伪装成老师原话。

## 12. 开发自举与跨聊天恢复

Book 最终应逐步具备“新的聊天/模型无需旧上下文也能安全继续”的自举开发结构。

建议长期补齐：

```text
development/
├── PRODUCT_CONTRACT.md
├── course_package_schema/
├── architecture_checks/
├── acceptance/
├── task_manifests/
└── upgrade_reports/
```

每个活跃阶段至少应有：

- approved spec
- implementation plan
- exact active branch/head
- test commands / acceptance gate
- current blockers
- unique next action

GitHub 继续是项目状态权威；聊天只负责执行，不成为唯一持久记忆。

## 13. Codex 的最终角色

主线开发默认由 ChatGPT 聊天模式完成。

完整可用版本达到阶段 gate 后，再使用 Codex：

### 第一次：Full Repository Audit

默认只读，重点检查：

- architecture
- data model / migrations
- Python / FastAPI
- React / TypeScript
- tests / CI
- security
- sync readiness
- Android readiness
- performance
- maintainability
- canonical data integrity
- duplicated / dead abstractions

### 第二次：Targeted Upgrade

审计结果先按 P0 / P1 / P2 / P3 分类，再由主线决策形成 Upgrade Spec。

随后：

```text
Upgrade Spec
→ independent upgrade branch
→ targeted changes
→ exact-head full regression
→ PR
```

Codex 不应在没有 Upgrade Spec 的情况下自由“大扫除式重构”稳定仓库。

## 14. 与当前 Roadmap 的推荐插入位置

历史 Phase 名称继续以 `docs/ROADMAP.md` 为准。原长期顺序仍保留，但 2026-08-29 已批准一个当前周期依赖例外：

```text
Phase 1G
StudyRecord / SQLite
        ↓
Cross-cutting Foundation A
Course Package Contract
Golden Course automation
Architecture Fitness Functions foundation
Contract-first foundation
        ↓
[Approved dependency exception]
H0 neutral Book identity                     [COMPLETE_MERGED]
        ↓
H1 internal source provenance                [COMPLETE_MERGED]
        ↓
H2 Exact-only shared Retrieval seam          [COMPLETE_MERGED]
        ↓
H3a Concept/ConceptAlignment contract        [COMPLETE_MERGED]
        ↓
H4a shadow FTS5/BM25 evaluation              [NEXT]
        ↓
Phase 1H
四模式增强（按 Vertical Slice 实现）
        ↓
Cross-cutting Foundation B / later separately approved work
Minimal Concept Graph production lifecycle / public retrieval activation / multi-book migration
        ↓
Phase 1I
Chapter Hub / 思维导图
        ↓
Phase 1J
ExamPoint Engine + dependency graph
        ↓
Phase 1K
Exam Sprint / 期末速通
        ↓
Phase 1L
PDF Reader（除非后续价值排序重新调整）
        ↓
Phase 2
Lecture recording / local ASR / LectureEvent
        ↓
Phase 3
Incremental Sync / SyncEvent
        ↓
Phase 4
Lecture ↔ textbook fusion + versioned Processing Jobs
        ↓
Meeting
        ↓
Android / APK productization
        ↓
Full usable version
        ↓
Codex Full Repository Audit
        ↓
Book v2 Targeted Upgrade
```

其中 Cross-cutting Foundation 不要求变成面向用户的“大版本”，可以作为紧邻相关 Phase 的小型基础阶段。

## 15. 当前执行优先级

当前唯一工程优先级是 **H4a shadow FTS5/BM25 evaluation**。

```text
H0 neutral Book identity                         COMPLETE_MERGED
→ H1 internal source provenance                  COMPLETE_MERGED
→ H2 Exact-only shared Retrieval seam            COMPLETE_MERGED
→ H3a Concept/ConceptAlignment contract          COMPLETE_MERGED
→ H4a shadow FTS5/BM25 evaluation                NEXT
→ Phase 1H user-visible slices                   AFTER_H4A
```

H4a 只允许通过 H2 shared Retrieval boundary 做 shadow evaluation，定义确定性 query/dataset、coverage/ranking metrics、provenance checks 与 failure semantics；public Search/QA 排名、分数、顺序和返回行为必须保持 Exact-only，不得在 H4a 内静默激活 FTS/BM25。

每一阶段继续采用非默认分支、TDD、exact-final-HEAD gate 和 reviewable PR。设计批准不等于 merge 授权；每个具体 PR 仍需要单独的人类明确合并授权。

Foundation A 的 App Runtime consumer migration 仍保持 out of scope。`H3b`、`B4b`、`B5` 与 StudyRecord book-version migration 不属于当前批准序列，不得因为长期策略文档已经描述相关方向就提前实现。