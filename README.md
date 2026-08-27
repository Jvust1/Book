# Book

Book 是一个面向真实课程学习的 **Course OS**：把持续上传的多本教材 PDF、课堂录音、老师补充、考试规则、题目、错题和学习记录组织成一个可追溯、可更新的课程知识系统。

## 核心原则

- 一门课程支持多本教材：主教材、辅助教材、英文教材、参考教材。
- 教材可持续新增与换版，旧的课堂关联、笔记、错题和学习记录不能被破坏。
- PDF 页码与纸质教材印刷页码必须分离，并通过稳定内容锚点连接。
- 每一节固定提供 **预习｜学习｜复习｜刷题** 四个并列按钮，用户自由选择，不强制顺序。
- 每章生成：章节总结、核心知识点、考点、公式、思维导图和章节测试。
- 教材图片尽量保留；公式、表格、例题、习题同时结构化。
- 课堂录音支持实时字幕、专业术语纠错、标点/断句修正和课后精修稿。
- 自动提取老师拓展、重点、作业、期中/期末范围、成绩占比等关键事件，并保留录音时间戳证据。
- 每个考点必须能快速跳转到教材对应段落/公式/图表/例题，并能一键返回原考点且恢复页面状态。
- 每本教材支持中英双语搜索与教材内提问，回答必须返回教材来源锚点。
- 每本教材结构化完成后必须执行全书通篇质量检查，存在 `FAIL` 时不得标记完成。

## 文档

- [总体计划](docs/MASTER_PLAN.md)
- [数据模型](docs/DATA_MODEL.md)
- [交互与导航](docs/UX_NAVIGATION.md)
- [开发路线图](docs/ROADMAP.md)
- [教材搜索与提问](docs/SEARCH_QA.md)
- [全书结构化完成质量门](docs/BOOK_COMPLETION_AUDIT.md)
- [Drive 目录约定](docs/DRIVE_LAYOUT.md)

## 已导入教材

### Functional Analysis: Introduction to Further Topics in Analysis

- 中文工作名：《泛函分析：分析学进一步专题导论》
- 作者：Elias M. Stein、Rami Shakarchi
- 状态：**STRUCTURED_COMPLETE**
- 最终版本：**v0.36 FINAL**
- 源 PDF：**442 / 442 页全部完成结构化覆盖**
- 最终纸质页：**423**
- 全书审计：**PASS 20 / WARN 1 / FAIL 0**
- 最终搜索索引：`search_index_v0_36.jsonl`，1493 条唯一记录
- 项目目录：[books/functional-analysis](books/functional-analysis/README.md)
- 完成标记：[STRUCTURED_COMPLETE.json](books/functional-analysis/STRUCTURED_COMPLETE.json)
- 审计报告：[BOOK_AUDIT_REPORT.md](books/functional-analysis/BOOK_AUDIT_REPORT.md)

## 当前状态

第一本真实教材的全书结构化阶段已经完成，**不再继续执行 PDF 51–60 等旧批次任务**。

当前主线已经切换到 **Course OS 软件 MVP**：

1. 建立结构化教材运行时导入/读取契约。
2. 用 Functional Analysis v0.36 作为第一本真实 fixture。
3. 打通 `Course → Book → Chapter → Section`。
4. 打通每节 `预习｜学习｜复习｜刷题` 四个独立入口。
5. 打通教材内容锚点定位、考点往返与页面状态恢复。
6. 接入教材搜索/问答与学习进度记录。
7. 选择一章完成端到端真实验收。

原始产品/架构基线保留在 Issue #1：`Book Course OS 总体计划与架构基线`，已同步更新到上述里程碑。
