# Book 多教材、统一检索与学习智能架构

更新时间：2026-08-28

## 1. 文档定位

本文件固化 Book 已确认的跨阶段产品架构：多教材同课程、统一混合检索、Concept/Mastery Graph、考试数字模型、错题诊断、课程时间线、Next Best Action，以及桌面端与手机端的功能一致性。

它是后续 Phase 的产品与架构约束，不扩大当前 Phase 1G。Phase 1G 仍只实现：

```text
StudyRecord + SQLite + hidden profile_id + recent learning + sync-ready metadata
```

## 2. 跨设备产品原则：桌面端与手机端功能一致

Book 不再把桌面端定义为“只看资料的精简版”。桌面/PWA 与手机/Android 应共享同一业务能力集合，包括：

- 教材与辅助教材
- 预习 / 学习 / 复习 / 刷题
- 搜索与问答
- Chapter Hub / 思维导图
- ExamPoint / Exam Sprint
- StudyRecord / Mastery
- Learning 课堂录音
- 课堂初加工与 GPT 精加工结果
- Meeting 录音与会议整理
- 同步

允许因设备能力产生交互差异，例如麦克风权限、后台录音策略、屏幕布局和本地算力不同，但不人为把录音功能从桌面端删除。

同一 profile 的允许同步数据通过统一 Sync 边界交换；不同设备仍各自维护本地 SQLite，不共享数据库文件。

## 3. 多教材同 Course：Book 独立，Concept 对齐

如果同一门泛函分析课程上传两本或更多教材，不创建两个彼此孤立的 App，也不把多本教材原文粗暴合并成“一本书”。

长期结构：

```text
Course: Functional Analysis
├── Book A (primary)
│   └── 独立 Chapter / Section / objects / source anchors
├── Book B (supplementary)
│   └── 独立 Chapter / Section / objects / source anchors
├── Book C (reference / translation / supplementary)
│   └── 独立来源
└── Course Concept Graph
    ├── Banach Space
    ├── Hahn–Banach
    ├── Compact Operator
    └── ...
```

核心原则：

1. 每本书保持自己的 `book_id / book_version_id / page map / section_id / element_id / source_anchor`。
2. 不把不同教材的定义、定理编号、证明和符号体系强制融合成“唯一原文”。
3. 课程级统一发生在 Concept 层，而不是原文层。
4. 第一版仍由 `primary` 教材提供课程 Chapter/Section 主骨架，辅助教材作为 Concept/Section 的补充证据源。
5. 如果未来一门课确实存在两本同等权威教材，可再引入独立 `CourseSyllabus` / Concept-first 课程骨架，而不是强迫任选一本成为永久目录权威。

建议教材角色：

```text
primary
supplementary
reference
translation
```

## 4. ConceptAlignment

多本教材通过显式对齐记录连接：

```text
ConceptAlignment
concept_id
book_id
book_version_id
section_id
source_kind
source_id
source_anchor
relation
confidence
alignment_revision
```

`relation` 可表达：

```text
defines
explains
proves
examples
exercises
extends
contrasts
prerequisite
```

任何自动对齐都必须保留 confidence 和来源，不能因“语义相似”直接改写 canonical 事实。

例如：

```text
concept_compact_operator
├── Primary Book §4.2 -> defines / proves
├── Supplementary Book §6.1 -> explains / examples
└── Lecture 2026-10-17 -> teacher emphasis / no-proof-required
```

## 5. 同一本教材的不同版本

同一教材的新版/旧版不能当作普通两本辅助教材，也不能上传新版后覆盖旧版。

应采用：

```text
logical_book_id
├── book_version_id = edition_2011
└── book_version_id = edition_2025
```

版本间维护 source/anchor mapping：

```text
old source anchor
↕
Version Mapping
↕
new source anchor
```

历史课堂、笔记、StudyRecord、引用和 ExamPoint 必须继续能定位到当时使用的版本。

## 6. Course Compiler

教材导入最终应从“提取文件”升级为“编译课程数据”。

```text
主教材 + 辅助教材 / 参考教材
          ↓
      Course Compiler
          ↓
      Course Package
```

Course Compiler 负责：

- 身份与版本识别
- PageMap
- Chapter / Section
- Definition / Theorem / Formula / Proof / Example / Exercise 等结构化对象
- source anchors
- terminology
- search index
- Concept candidates / alignments
- prerequisite graph
- readiness / audit
- package hashes / schema version

失败项必须形成明确 `PASS / WARN / FAIL`，不能静默补造缺失来源。

最终目标：通用 App 稳定后，新课程主要走“上传资料 -> 编译/结构化 -> readiness -> 注册”，而不是为每本教材重新开发程序。

## 7. Unified Retrieval Engine

现有 Phase 1E deterministic canonical search 保留，作为未来统一检索的高可信 Exact 层，不被向量搜索取代。

长期统一检索：

```text
Query
  ↓
Query Normalizer
  ├── 中英文归一
  ├── 数学术语别名
  ├── Unicode / LaTeX / 数学符号归一
  └── scope / source intent
  ↓
Parallel Retrievers
  ├── CanonicalExactRetriever
  ├── TextFTSRetriever (SQLite FTS5 / BM25)
  ├── FormulaRetriever
  ├── ConceptRetriever
  ├── SemanticRetriever
  ├── LectureEventRetriever
  ├── ExamPointRetriever
  ├── PersonalRetriever
  └── MeetingRetriever (privacy-isolated)
  ↓
RRF / equivalent rank fusion
  ↓
Source-aware reranking
  ↓
Provenance-preserving SearchHit
```

### 7.1 为什么不是纯向量搜索

数学课程同时需要：

- 定理编号/对象 ID 的精确匹配
- 公式和符号匹配
- 全文 BM25
- Concept 关系
- 模糊语义回忆
- 老师结构化事件查询

因此 embedding 只是一种召回器，不能成为唯一真相源。

### 7.2 数学查询归一

应逐步支持类似：

```text
Hahn Banach / Hahn–Banach / 哈恩-巴拿赫
||T|| / ‖T‖ / \|T\|
L^p / Lp
ε / epsilon / \epsilon
```

公式检索后续可进一步做变量无关的结构相似检索，但不是早期必需项。

### 7.3 搜索结果来源必须显式

统一结果至少区分：

```text
[主教材]
[辅助教材]
[课堂]
[老师重点]
[考试]
[个人笔记]
[题目/错题]
[GPT Derived]
[Meeting]
```

默认 source-aware 排序不能把 AI Derived 排在明确 canonical 精确命中之前。查询意图可以动态改变优先级，例如“老师说哪些证明不考”应优先 LectureEvent；“正式定义是什么”应优先 canonical 教材。

### 7.4 Search 与 QA 共用 Retrieval

长期架构：

```text
Unified Retrieval Engine
├── Search UI -> 返回证据与来源
└── QA -> Evidence Pack -> EvidenceGate -> LLM
```

新增辅助教材、课堂、ExamPoint 或个人资料时，只新增/扩展 Retriever，不为 Search 和 QA 各维护一套独立找资料逻辑。

### 7.5 Meeting 检索隔离

Meeting 与 Learning 使用不同逻辑索引/授权域。只有用户明确进入 Meeting 搜索范围或允许的全局搜索范围时，才查询 Meeting，避免私人会议资料意外混入普通教材搜索。

## 8. Concept Graph：课程知识的第二骨架

`Course -> Book -> Chapter -> Section` 是阅读骨架；Concept Graph 是学习与依赖骨架。

```text
Concept
├── prerequisite concepts
├── dependent concepts
├── primary textbook evidence
├── supplementary textbook evidence
├── lecture evidence
├── exam signals
├── questions / mistakes
├── mastery
└── ExamPoint
```

Chapter/Section 与 Concept 并存，不能互相替代。

Concept Graph 用于：

- 多教材对齐
- Chapter Hub 思维导图
- ExamPoint 依赖
- Exam Sprint 最小必要知识闭包
- 课堂关联
- 错题根因诊断
- Mastery
- Next Best Action

第一版可使用确定性 graph records，不要求一开始引入专门图数据库。

## 9. Mastery Graph

StudyRecord 只回答“是否开始/完成某个 Section mode”。长期掌握度必须成为独立模型，不能把 `completed=100` 等同于真正掌握。

概念掌握状态可逐步表达：

```text
unseen
seen
understood
recallable
basic_problem_ready
transfer_problem_ready
stable
```

Mastery 的证据来自：

- 复习测试
- 刷题结果
- 错题与重复错误
- 回忆题
- 最近学习/复习时间
- 用户明确自评

AI 可以解释和推荐，但不能无证据直接把掌握度改高。

## 10. 一个知识点的一生 / Concept 360 View

Concept 页面最终应成为资料融合入口，例如：

```text
Compact Operator
├── 主教材正式定义 / 定理 / 证明 / 例题
├── 辅助教材直观解释 / 其他证明 / 补充题
├── 课堂第一次讲解 / 再次强调 / 时间戳
├── 老师要求：定义必会、证明不要求
├── ExamPoint / Exam scope
├── 我的学习记录
├── 错题
└── Mastery
```

每一项必须保留来源，不生成不可追踪的“融合原文”。

## 11. Exam Digital Twin

考试中心长期不仅保存日期，而是建立一个可追踪 `Exam` 模型：

```text
Exam
├── date
├── scope
├── total_score
├── section/topic weights
├── question types
├── teacher explicit signals
├── confirmed / probable / unknown
├── ExamPoints
├── current coverage
└── risk areas
```

老师录音中的 `EXAM_SCOPE / GRADE_WEIGHT / GRADE_RULE / NOT_EXAMINED / NO_PROOF_REQUIRED` 等事件是考试模型的证据之一，但必须保留原始时间戳与 confidence。

Exam Digital Twin 为 Exam Sprint 和 Next Best Action 提供目标函数。

## 12. 错题知识诊断

错题系统不能只保存题目与答案，还应把错误映射回 Concept Graph。

建议错误类型：

```text
definition_gap
theorem_condition_missed
formula_misuse
prerequisite_gap
reasoning_break
calculation_error
careless_error
unknown
```

流程：

```text
Mistake
-> error classification + evidence
-> linked concepts
-> prerequisite inspection
-> shortest repair path
```

系统应能判断“这道 Fredholm 题错了，但根因可能是 Compact Operator 前置未掌握”，而不是机械推荐重做同题。

## 13. Course Timeline

课堂录音、教材进度和考试信息应共同形成课程时间线：

```text
Week / Lecture
├── 讲到哪些 Section / Concept
├── 老师重点
├── 新考点
├── 作业
├── Deadline
├── 考试范围变化
└── 对应教材来源
```

从 Lecture 可以跳教材/Concept；从 Section/Concept 也可以反查老师在哪些课堂讲过。

## 14. What Changed 增量摘要

每日 GPT Processing Job 除完整 processed revision 外，应生成结构化变化摘要，例如：

```text
今日新增知识点
老师新增重点
考试范围变化
新作业 / Deadline
新增教材补充
Mastery / 风险变化
待处理问题
```

用户第二天打开 App 时优先看到“课程发生了什么变化”，而不是重新翻全部历史资料。

## 15. Next Best Action 学习决策引擎

Book 的长期目标不是只提供资料，而是根据当前证据给出“现在最值得做什么”。

输入可包括：

```text
ExamPoint 基础重要度
+ teacher emphasis
+ Exam Digital Twin
+ StudyRecord
+ Mastery
+ mistakes
+ remaining time
+ prerequisite graph
```

输出必须是可解释的学习动作，例如：

```text
1. 先完成 Compact Operator 定义回忆
2. 做 Example X
3. 修复 prerequisite Y
4. 暂时跳过完整证明，因为老师明确标记 NO_PROOF_REQUIRED
```

每项建议都应能说明原因与证据，避免黑箱“AI 觉得你应该学这个”。

## 16. Learning Intelligence 的证据分层

任何学习决策都必须保持信号来源分离：

```text
Textbook base evidence
Lecture / teacher evidence
Exam evidence
Personal performance evidence
Derived AI recommendation
```

这些层可以在排序和决策时组合，但不能相互覆盖。

## 17. 分阶段落地顺序

推荐逐步吸收到现有 Roadmap：

```text
Phase 1G
StudyRecord / SQLite
        ↓
Foundation A
Course Package + Course Compiler contract
Golden Course
Architecture Fitness Functions
多教材 role + version identity
        ↓
Phase 1H
四模式增强
        ↓
Foundation B
Minimal Concept Graph + ConceptAlignment
Unified Retrieval v1 (Exact + FTS/BM25 + provenance fusion)
        ↓
Phase 1I
Chapter Hub / 思维导图
        ↓
Phase 1J
ExamPoint
        ↓
Phase 1K
Exam Sprint
        ↓
后续
Semantic / Formula / LectureEvent retrieval
Exam Digital Twin
Mastery + Mistake Diagnosis
Next Best Action
Course Timeline / What Changed
```

实现顺序可以根据实际价值重新评估，但不能打乱来源边界和 canonical 约束。

## 18. 当前状态

本文件中的能力除已明确标记为现有 Phase 1E/1F 基础外，均属于已批准的后续架构方向，不应在尚未实现时宣称为当前功能。

当前唯一工程下一步仍是按 `docs/superpowers/plans/2026-08-28-study-record-phase-1g.md` 实现 Phase 1G。