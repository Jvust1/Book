# Book

Book 是一个面向真实教材学习的 **Course OS / Book App**：在同一个 App 中管理多门彼此独立的教材课程，并把教材结构、来源锚点、学习入口以及后续的课堂、题目、错题和学习记录组织成可追溯、可扩展的学习系统。

## 核心原则

- **一个 Book App 支持多门彼此独立的教材课程；当前产品形态下每门课程对应一本教材。** 例如《泛函分析》《实分析》分别作为独立课程加入同一个 App，而不是把《实分析》挂到《泛函分析》下面。
- 新教材通过新增独立 course 加入 Library；不同课程不合并 Chapter / Section 树，也不共享 Section 级学习记录。
- 底层 `CourseRuntime` 保留通用多书能力作为兼容能力，但当前 Book App 产品入口只接纳恰好一本 enabled 主教材的课程。
- PDF 页码与纸质教材印刷页码必须分离，并通过稳定内容锚点连接。
- 每一节固定提供 **预习｜学习｜复习｜刷题** 四个并列入口，用户自由选择，不强制顺序。
- 教材内容与来源必须可追溯；缺失的中文内容、答案、解析或 anchor 保持缺失，不由 UI 静默编造。
- 每本教材结构化完成后必须执行全书通篇质量检查，存在 `FAIL` 时不得进入正式学习运行时。

## 当前软件架构

```text
React / TypeScript / Vite PWA
              ↓
        local FastAPI
              ↓
       BookAppService
              ↓
LibraryRuntime → CourseRuntime → BookRuntime
              ↓
 SectionLearningRuntime / SourceResolver
              ↓
     预习 / 学习 / 复习 / 刷题
```

前端只消费稳定 API DTO，不直接读取 `books/`、`courses/`、`library/` 或 chunk 文件。教材事实与解析规则继续由 Python Runtime 持有。

## 文档

- [本地 App 启动与验收](app/README.md)
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
- Runtime 目录树：**8 Chapter / 132 Section**
- 课程目录：`courses/functional-analysis`
- 教材目录：[books/functional-analysis](books/functional-analysis/README.md)
- 完成标记：[STRUCTURED_COMPLETE.json](books/functional-analysis/STRUCTURED_COMPLETE.json)
- 审计报告：[BOOK_AUDIT_REPORT.md](books/functional-analysis/BOOK_AUDIT_REPORT.md)

## 当前状态

Phase 1A 已完成第一本真实教材的全书结构化资产恢复与 `RUNTIME_READY` gate。

Phase 1B 已完成 `Course → Book → Chapter → Section` Runtime 层级，Functional Analysis 稳定暴露 **8 个 Chapter / 132 个 Section**。

Phase 1C 已完成 App Library 与 Section Learning Runtime：

```text
Library
→ functional_analysis_course
→ ch01_s01
→ SectionLearningSource
→ Preview / Learn / Review / Practice
```

Phase 1D 已完成第一个 **local-first Book App MVP**：

- React + TypeScript + Vite/PWA 前端。
- 本机 FastAPI 只读适配层。
- 教材库 → Course → Chapter → Section 真实导航。
- `预习｜学习｜复习｜刷题` 四模式中文优先 UI，默认 `学习`，互不锁定。
- 结构化教材来源页，展示真实教材页 / PDF 页 / anchor 状态 / 上下文。
- `sessionStorage` 支持来源往返时恢复 mode、展开项与滚动位置。
- `package-lock.json` 已固化，CI 使用 `npm ci`。
- GitHub Actions 同时运行 App API、17 个 Web 单元测试、TypeScript、PWA build 与 Chromium 真实浏览器验收。
- Functional Analysis 当前浏览器 acceptance 覆盖桌面真实来源往返和 390×844 窄屏。

Phase 1D 仍然是本地 Web/PWA，不是已封装的 Windows 桌面程序。PWA 可缓存前端静态资源，但教材动态数据仍需要本机 FastAPI 运行；仓库当前也不包含完整原始 PDF Reader。

## 后续顺序

1. 基于现有 1493 条真实索引接入教材内中文/英文搜索与来源跳转。
2. 接入教材内问答，强制答案携带真实来源；不把 AI 输出冒充教材正文。
3. 增加长期 `StudyRecord` / 最近学习位置 / 四模式独立进度；与当前 session 恢复机制分离。
4. 在现有四模式来源投影之上增加更丰富的预习、复习和刷题学习产品能力。
5. 保持一课程一本主教材的 App 入口规则，按同一导入契约逐本加入《实分析》等独立课程。
6. Web/PWA 稳定后再评估 Tauri Windows 打包与移动端复用。

原始产品/架构基线保留在 Issue #1；较早文档中的“单课程多教材”描述应视为底层兼容/未来架构，而非当前 Book App 的产品入口规则。
