# Book

Book 是一个面向真实教材学习的 **Course OS / Book App**：在同一个 App 中管理多门彼此独立的教材课程，并把教材结构、来源锚点、学习入口以及后续的课堂、题目、错题和学习记录组织成可追溯、可扩展的学习系统。

## 核心原则

- **一个 Book App 支持多门彼此独立的教材课程；当前产品形态下每门课程对应一本教材。** 例如《泛函分析》《实分析》分别作为独立课程加入同一个 App，而不是把《实分析》挂到《泛函分析》下面。
- 新教材通过新增独立 course 加入 Library；不同课程不合并 Chapter / Section 树，也不共享 Section 级学习记录。
- 底层 `CourseRuntime` 保留通用多书能力作为兼容能力，但当前 Book App 产品入口只接纳恰好一本 enabled 主教材的课程。
- PDF 页码与纸质教材印刷页码必须分离，并通过稳定内容锚点连接。
- 每一节固定提供 **预习｜学习｜复习｜刷题** 四个并列入口，用户自由选择，不强制顺序。
- 教材内容与来源必须可追溯；缺失的中文内容、答案、解析或 anchor 保持缺失，不由 UI 静默编造。
- 教材问答只能依据当前课程允许的真实教材证据；模型生成回答必须与教材正文明确区分，并携带可验证来源。
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
SectionLearningRuntime / SourceResolver / SearchRuntime / QARuntime
              ↓
预习 / 学习 / 复习 / 刷题 / 教材搜索 / 教材问答 → 来源
```

前端只消费稳定 API DTO，不直接读取 `books/`、`courses/`、`library/` 或 chunk 文件。教材事实、来源解析、确定性搜索与问答证据选择规则继续由 Python Runtime 持有。

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

Phase 1E 已完成 **教材内搜索与来源跳转**：

- 直接复用 Functional Analysis 的 1493 条 canonical 搜索记录，不建立第二套索引。
- `SearchRuntime` 提供确定性 course-scoped 中英文搜索，并保留 canonical course / book / source identity。
- 支持术语、定理、公式、例题、习题等结构化对象命中；不可映射为真实来源的记录不会生成伪跳转结果。
- FastAPI 明确区分正常 0 hit、无效查询、课程不存在与搜索索引不可用。
- Course 页面提供“搜索教材”入口，SearchPage 通过 URL `q` 驱动查询并跳转到真实 Source 页面。
- Search → Source → Search 使用独立短期 `sessionStorage` 状态恢复 query、scroll 与 active source；不保存结果数组，也不冒充长期 `StudyRecord`。

Phase 1F 已完成 **教材内问答**：

- `QARuntime` 只从当前课程的 canonical SearchRuntime / SourceResolver 构造有界教材证据，不把模型知识当作教材事实来源。
- Course 入口直接按整本教材问答；Section 入口优先当前小节，证据不足时才显式扩展到整本教材。
- 服务端先执行证据充分性 gate；模型还可以做第二次“证据不足”判断。资料不足时返回稳定 system notice，而不是猜测答案。
- 生成回答必须引用服务端已验证的真实 citation；citation 可进入现有教材来源页。
- QA → Source → QA 使用课程级短期 session 恢复已验证回答、引用、滚动位置与 active citation，返回时不会重新调用模型生成同一回答。
- 连续追问只携带受限的最近对话 history；history 是上下文，不会被当成新的教材证据。
- 支持服务器侧 OpenAI-compatible provider；API Key 不下发到浏览器。CI 使用 deterministic fake provider，不依赖外部模型密钥。
- Runtime CI 在 Python 3.11 / 3.12 / 3.13 上执行 Phase 1F gate、全量 Runtime discovery 与 3.13 canonical rebuild/smoke；App CI 执行全量 App discovery；Web CI 执行 Vitest、TypeScript、PWA build 与真实 Chromium acceptance，包括 390×844 问答/来源往返。

## 教材问答 Provider 配置

真实在线模型由本机 FastAPI 进程通过服务器侧环境变量配置：

```text
BOOK_QA_BASE_URL=https://your-openai-compatible-provider.example/v1
BOOK_QA_API_KEY=<your-key>
BOOK_QA_MODEL=<model-name>
BOOK_QA_TIMEOUT_SECONDS=60
```

`BOOK_QA_BASE_URL`、`BOOK_QA_API_KEY`、`BOOK_QA_MODEL` 必须同时配置；三者都未配置时，教材浏览与搜索仍可使用，但在线问答 provider 处于未配置状态。`BOOK_QA_PROVIDER=fake` 只用于确定性测试/CI，不是实际模型配置。

完整教材资产继续保留在本机。执行真实在线问答时，只会把当前问题、受限的最近对话，以及 Runtime 为本次问题选择出的有界 EvidencePack 片段发送给所配置的在线模型 provider；不会把整本教材目录自动上传给 provider。详见 [app/README.md](app/README.md)。

当前仍然是本地 Web/PWA，不是已封装的 Windows 桌面程序。PWA 可缓存前端静态资源，但教材动态数据仍需要本机 FastAPI 运行；仓库当前也不包含完整原始 PDF Reader。

## 后续顺序

1. 增加长期 `StudyRecord` / 最近学习位置 / 四模式独立进度；与当前 session 恢复机制分离。
2. 在现有四模式来源投影之上增加更丰富的预习、复习和刷题学习产品能力。
3. 增加 Chapter Hub、ExamPoint 与教材来源往返。
4. 接入按 canonical `book_id` 注册的本地 PDF Reader，在真实 geometry 存在时才做精确高亮。
5. 保持一课程一本主教材的 App 入口规则，按同一导入契约逐本加入《实分析》等独立课程。
6. Web/PWA 稳定后再评估 Tauri Windows 打包与移动端复用。

原始产品/架构基线保留在 Issue #1；较早文档中的“单课程多教材”描述应视为底层兼容/未来架构，而非当前 Book App 的产品入口规则。
### 可选符号比较的安全边界

已有 SymPy 比较器现使用受限数学语法与有时限的本地工作进程；未支持的表达式、未知定义域、超时或不确定结果均返回 unknown，不自动判错。
可通过 `requirements-extras/symbolic.txt` 安装固定版本，并向 `tools/check_symbolic_answer.py` 的标准输入提供 student / expected JSON 做本机诊断。
这不生成教材标准答案、不核验答案来源，也不自动批改证明。详见 [安全 SymPy 适配记录](docs/upstream/safe-sympy-input-2026-09-30.md)。
