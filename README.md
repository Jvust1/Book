# Book

Book 是一个面向真实教材学习的 **Course OS / Book App**：在同一个 App 中管理多门彼此独立的教材课程，并把教材结构、来源锚点、学习入口以及后续的课堂、题目、错题和学习记录组织成可追溯、可扩展的学习系统。

## 核心原则

- **一个 Book App 支持多门彼此独立的教材课程；当前产品形态下每门课程对应一本教材。** 例如《泛函分析》《实分析》分别作为独立课程加入同一个 App，而不是把《实分析》挂到《泛函分析》下面。
- 新教材通过新增独立 course 加入 Library；不同课程不合并 Chapter / Section 树，也不共享 Section 级学习记录。
- 底层 `CourseRuntime` 保留通用多书能力作为兼容能力，但当前 Book App 产品入口只接纳恰好一本 enabled 主教材的课程。
- PDF 页码与纸质教材印刷页码必须分离，并通过稳定内容锚点连接。
- 每一节固定提供 **预习｜学习｜复习｜刷题** 四个并列入口，用户自由选择，不强制顺序。
- 每章未来生成：章节总结、核心知识点、考点、公式、思维导图和章节测试。
- 教材图片尽量保留；公式、表格、例题、习题同时结构化。
- 课堂录音未来支持实时字幕、专业术语纠错、标点/断句修正和课后精修稿。
- 后续自动提取老师拓展、重点、作业、期中/期末范围、成绩占比等关键事件，并保留录音时间戳证据。
- 每个考点最终必须能快速跳转到教材对应段落/公式/图表/例题，并能一键返回原考点且恢复页面状态。
- 每本教材支持中英双语搜索与教材内提问，回答必须返回教材来源锚点。
- 每本教材结构化完成后必须执行全书通篇质量检查，存在 `FAIL` 时不得进入正式学习运行时。

## 当前运行时架构

```text
Book App
   ↓
LibraryRuntime
   ↓
CourseRuntime        # 当前产品：一个 course 对应一本教材
   ↓
BookRuntime
   ↓
SectionLearningRuntime
   ↓
预习 / 学习 / 复习 / 刷题
```

后续新增《实分析》等教材时，新增独立 `courses/<slug>/course.json` 并注册进 `library/library.json`，复用同一套运行时代码，教材数据彼此隔离。

## 文档

- [总体计划](docs/MASTER_PLAN.md)
- [数据模型](docs/DATA_MODEL.md)
- [交互与导航](docs/UX_NAVIGATION.md)
- [开发路线图](docs/ROADMAP.md)
- [教材搜索与提问](docs/SEARCH_QA.md)
- [全书结构化完成质量门](docs/BOOK_COMPLETION_AUDIT.md)
- [Drive 目录约定](docs/DRIVE_LAYOUT.md)
- [Runtime 参考层](runtime/README.md)

## 已导入教材课程

### Functional Analysis: Introduction to Further Topics in Analysis

- App 课程 ID：`functional_analysis_course`
- 教材 ID：`stein_shakarchi_functional_analysis_2011`
- 中文工作名：《泛函分析：分析学进一步专题导论》
- 作者：Elias M. Stein、Rami Shakarchi
- 状态：**STRUCTURED_COMPLETE / RUNTIME_READY**
- 最终版本：**v0.36 FINAL**
- 源 PDF：**442 / 442 页全部完成结构化覆盖**
- 最终纸质页：**423**
- 全书审计：**PASS 20 / WARN 1 / FAIL 0**
- 最终搜索索引：`search_index_v0_36.jsonl`，1493 条唯一记录
- 课程目录：`courses/functional-analysis`
- 教材目录：[books/functional-analysis](books/functional-analysis/README.md)
- 完成标记：[STRUCTURED_COMPLETE.json](books/functional-analysis/STRUCTURED_COMPLETE.json)
- 审计报告：[BOOK_AUDIT_REPORT.md](books/functional-analysis/BOOK_AUDIT_REPORT.md)

## 当前状态

Phase 1A 已完成第一本真实教材的全书结构化资产恢复与 `RUNTIME_READY` gate。

Phase 1B 已完成并合并：`Course → Book → Chapter → Section`，Functional Analysis 可稳定暴露 **8 个 Chapter / 132 个 Section**。

当前主线 **Phase 1C** 已打通运行时软件链路：

```text
Library
→ functional_analysis_course
→ ch01_s01
→ SectionLearningSource
→ Preview / Learn / Review / Practice
```

Phase 1C 的四个模式当前是**确定性、来源可追溯的教材投影**，不会把 AI 生成内容冒充成教材内容。

后续顺序：

1. 在真实 App UI 中实现 Library → Course → Chapter → Section 页面。
2. 将 `预习｜学习｜复习｜刷题` 四个运行时 payload 接到 Section 页面。
3. 打通教材内容锚点定位、考点往返与页面状态恢复。
4. 接入教材内搜索/问答与学习进度记录。
5. 选择一章完成端到端真实验收，再按同一结构逐本加入《实分析》等课程。

原始产品/架构基线保留在 Issue #1；较早文档中的“单课程多教材”描述应视为底层兼容/未来架构，而非当前 Book App 的产品入口规则。
