# Book App Phase 1D 设计规范

日期：2026-08-27  
状态：待实现  
分支：`feature/book-app-ui-phase-1d`

## 1. 目标

Phase 1D 将现有 Python runtime 与真实教材数据接入一个可直接使用的本地学习 App MVP。

这一阶段不把 Book 做成 PDF 阅读器，也不把 AI 聊天作为主入口。核心目标是让用户能够从书架进入课程、章节、小节，在同一小节内自由切换“预习 / 学习 / 复习 / 刷题”，并从任一教材对象跳到结构化来源后无损返回原学习位置。

最终用户路径：

```text
书架
→ 泛函分析
→ Chapter
→ Section
→ 预习 / 学习 / 复习 / 刷题
→ 定义 / 定理 / 公式 / 图 / 习题
→ 查看结构化教材来源
→ 返回并恢复原位置
```

## 2. 产品约束

### 2.1 第一版运行形态

第一版采用 local-first：

```text
React + TypeScript + Vite PWA
        ↓ HTTP
本机 FastAPI
        ↓
LibraryRuntime
CourseRuntime
BookRuntime
SectionLearningRuntime
        ↓
本机结构化教材数据
```

第一版不要求：

- 登录账号；
- 云服务器；
- 云同步；
- 教材上传第三方服务；
- Windows 原生安装包；
- 原生 iOS / Android App。

后续可以在同一前端基础上继续包装 PWA、Windows 桌面端和移动端。

Phase 1D 的 PWA 目标是“可安装的 Web App 外壳”，不要求教材离线缓存。FastAPI 与教材 runtime 仍在本机运行。

FastAPI 默认只绑定本机回环地址（`127.0.0.1`）；Phase 1D 不设计局域网或公网暴露。

### 2.2 中文优先

用户正常学习流程必须完全可用中文完成。

规则：

- 界面按钮、菜单、导航、状态、提示、错误信息全部中文；
- 教材对象类型中文显示：Definition→定义、Theorem→定理、Proposition→命题、Lemma→引理、Corollary→推论、Formula→公式、Example→例题、Exercise→练习、Problem→习题、Figure→图；
- 中文学习层优先；
- 数学术语第一次出现时允许显示“中文（English term）”，后续默认只显示中文；
- 英文原教材保留为来源证据，但不是主学习入口；
- 若某段中文内容缺失，明确显示“本段中文学习内容暂未提供”，不得把英文原文直接作为默认正文；
- 可提供次级“查看英文原文”按钮，但不能阻塞主要学习流程。

中文课程/教材名称不能由 UI 或运行时临时生成。Functional Analysis 第一版的中文名称直接使用现有 `books/functional-analysis/book_metadata.json` 中的 `title_zh`：`泛函分析：分析学进一步专题导论`。后续如果 course 需要与书名不同的独立中文产品名，应通过明确的产品元数据字段加入，而不是运行时猜测或 AI 翻译。

### 2.3 当前课程产品规则

一个 Book App 可以有多门彼此独立的教材课程，但当前产品入口下“一门课程 = 一本 enabled 主教材”。

第一门真实课程：

- Course：`functional_analysis_course`
- Book：`stein_shakarchi_functional_analysis_2011`
- 真实结构：8 Chapters / 132 Sections

不同课程不合并 Chapter / Section 树。

## 3. Phase 1D 范围

### 3.1 必须完成

1. React + TypeScript + Vite PWA 前端骨架；
2. 本地 FastAPI 服务层；
3. Library → Course → Chapter → Section 主导航；
4. Section 页四个并列模式：预习 / 学习 / 复习 / 刷题；
5. 中文优先教材对象展示；
6. 结构化来源查看；
7. 从来源返回后恢复原 Section 状态；
8. Functional Analysis `ch01_s01` 真实端到端验收；
9. API 与 UI 的自动化测试；
10. CI 增加 Phase 1D 基础门。

### 3.2 明确不做

本阶段不实现：

- AI 教材问答；
- AI 自动摘要；
- AI 自动出题；
- 账号系统；
- 云同步；
- 原始 PDF 阅读器；
- 课堂录音；
- 错题数据库；
- 完整 StudyRecord；
- Chapter Hub；
- Windows 安装包；
- 原生手机 App；
- 教材数据离线缓存；
- 跨设备状态恢复。

这些能力必须保持未来可扩展，但不能扩大 Phase 1D 实现范围。

## 4. 原始 PDF 定位

Phase 1D 不要求原始 PDF 二进制存在，也不要求用户打开 PDF。

结构化教材视图是主界面。来源卡至少显示：

- 教材名称；
- Chapter；
- Section；
- printed page；
- PDF page；
- source anchor；
- source batch（调试/详情层）；
- 结构化上下文。

未来可增加“查看原教材页”作为辅助证据入口，但不能改变当前结构化来源契约。

## 5. 页面信息架构

### 5.1 书架页 `/`

显示当前 Library 中所有 enabled course。

每张课程卡至少包括：

- 中文课程/教材名；
- 英文书名或课程英文名（次级）；
- 作者；
- Chapter 数量；
- Section 数量；
- Runtime readiness；
- 进入课程按钮。

如果本次浏览器会话中存在该课程的 Section return snapshot，可以额外显示“继续学习”；否则不得伪造历史学习位置。

第一版不在首页中心放 AI 聊天框，不做复杂统计仪表盘。

### 5.2 课程页 `/courses/:courseId`

主要职责是教材目录导航。

显示：

- 中文课程/教材名；
- 英文名（次级）；
- 作者；
- Chapter 列表；
- 每章可折叠 Section 列表；
- 点击 Chapter 进入 Chapter 页；
- 点击 Section 可直接进入 Section 页。

Phase 1D 不要求真正接通本书搜索，只允许预留搜索入口而不伪造功能。

### 5.3 Chapter 页 `/courses/:courseId/chapters/:chapterId`

显示：

- Chapter 编号；
- 中文标题优先；
- 英文标题次级；
- Section 数量；
- Section 卡片列表；
- Section 页码范围；
- 进入 Section。

Chapter Hub（章节总结、公式、测试等）不在本阶段实现。

### 5.4 Section 页 `/courses/:courseId/sections/:sectionId?mode=<mode>`

顶部固定显示：

- 返回 Chapter；
- Section 编号；
- 中文标题；
- 英文标题可作为次级信息；
- printed page 范围；
- PDF page 范围；
- 四个并列模式 Tab。

合法 mode：

- `preview`
- `learn`
- `review`
- `practice`

默认 mode 固定为 `learn`。未提供 mode 或 mode 非法时，前端必须规范化到 `learn`；API 不根据隐式 UI 状态决定默认模式。

四个模式：

- 可自由进入；
- 不强制先后顺序；
- 不互相锁定；
- 切换后应保持各自页面位置状态。

### 5.5 来源页 `/courses/:courseId/sources/:kind/:sourceId`

来源页用于查看结构化教材证据，不是 PDF 阅读器。

来源 URL 必须包含 `courseId`，避免未来多个课程存在相同 source ID 时深链接歧义。

显示：

- 中文对象类型；
- 中文标题；
- 英文术语或标题（可选、次级）；
- 中文内容；
- 公式；
- printed page；
- PDF page；
- source anchor；
- source batch；
- 上下文前后对象；
- 当前目标对象高亮；
- “返回学习”操作。

若来源不可解析，必须显示明确的中文错误状态，并允许返回原学习页。

## 6. Section 四模式设计

### 6.1 预习 Preview

Phase 1D 的预习只使用已经存在的真实结构化证据，不自动生成学习目标或易卡点。

显示：

- 本节对象统计；
- 定义数量；
- 定理/命题/引理/推论数量；
- 公式数量；
- 图数量；
- 练习/习题数量；
- 核心对象快速预览；
- 中文学习层是否可用。

目标是让用户 1–3 分钟了解本节结构。

### 6.2 学习 Learn

这是 Phase 1D 核心视图。

按真实教材对象连续阅读，不模拟 PDF 页面。

每个对象卡可显示：

- 中文对象类型；
- 编号；
- 中文标题；
- 首次出现时的英文术语；
- 中文正文；
- 公式；
- 图片；
- printed page；
- “查看来源”。

正常阅读时 source ID、batch ID 等低级字段不应抢占视觉注意力，只在来源详情层展示。

### 6.3 复习 Review

仅基于当前 runtime 定义的核心对象类型：

- definition
- theorem
- proposition
- lemma
- corollary
- formula

第一版采用回忆式卡片：

```text
定理 1.3
[先自己回忆]
[显示内容]
```

显示内容后提供教材页码与“查看来源”。

无 review 对象时必须是合法空状态，不应报错。

### 6.4 刷题 Practice

第一版只展示真实教材中的：

- exercise
- problem

不自动生成新题。

若结构化数据没有答案或解析，显示明确状态：

> 教材数据中暂未提供解析

禁止现场生成内容并伪装成教材答案。

无 practice 对象时必须是合法空状态。

## 7. 前端与 runtime 边界

React 不直接读取教材 JSON、chunk 文件、CSV 或 Markdown。

所有教材数据必须通过 FastAPI → Python runtime 获取。

前端只理解稳定 API DTO，不理解底层目录结构。

结构：

```text
React
  ↓ API DTO
FastAPI
  ↓
LibraryRuntime / CourseRuntime / BookRuntime / SectionLearningRuntime
  ↓
books/ courses/ library/
```

这保证未来教材目录、chunk 格式或 runtime 内部实现变化时，不需要同步重写前端。

FastAPI route 层不得为了方便直接散落读取 `books/**` 文件；教材文件解析必须集中在 runtime/service 边界。

## 8. FastAPI 接口契约

### 8.1 Library

`GET /api/library`

返回 enabled courses，用于书架。

每个 course 至少包含：

- `course_id`
- `name_zh`
- `name_en`
- `book_id`
- `authors`
- `chapter_count`
- `section_count`
- `runtime_status`

对于当前 Functional Analysis，`name_zh` 必须由 main book 的 `book_metadata.title_zh` 提供；`authors` 必须由 `book_metadata.authors` 提供。

### 8.2 Course

`GET /api/courses/{course_id}`

返回：

- course 基本信息；
- main book 基本信息；
- Chapter 摘要列表；
- Section 总数。

### 8.3 Chapter

`GET /api/courses/{course_id}/chapters/{chapter_id}`

返回：

- Chapter identity；
- 中文/英文标题；
- Section 列表；
- Section 页码范围。

### 8.4 Section source summary

`GET /api/courses/{course_id}/sections/{section_id}`

返回：

- identity；
- Chapter identity；
- 中文/英文标题；
- printed/PDF 页范围；
- object summary；
- figures summary；
- translation availability。

### 8.5 四模式

- `GET /api/courses/{course_id}/sections/{section_id}/preview`
- `GET /api/courses/{course_id}/sections/{section_id}/learn`
- `GET /api/courses/{course_id}/sections/{section_id}/review`
- `GET /api/courses/{course_id}/sections/{section_id}/practice`

mode payload 必须保持与 `SectionLearningRuntime` identity 一致，并保留 source refs。

### 8.6 Source resolver

`GET /api/courses/{course_id}/sources/{kind}/{source_id}`

职责：

- 根据 source ref 解析真实教材对象；
- 返回中文优先内容；
- 返回对象元数据；
- 返回页码与 anchor；
- 返回有限上下文；
- 不让 React 自己定位 chunk 文件。

建议响应字段：

- `course_id`
- `book_id`
- `section_id`
- `kind`
- `source_id`
- `type`
- `type_zh`
- `number`
- `title_zh`
- `title_en`
- `content_zh`
- `formula`
- `printed_page`
- `pdf_page`
- `source_anchor`
- `source_batch`
- `context_before`
- `context_after`

不同 `kind` 可以让不适用字段为 `null`，但 identity、source ref 与页码/anchor 真实性约束不变。

如果当前 runtime 还没有足够信息直接返回 `content_zh`，实现计划必须新增一个明确、可测试的 Python source resolver；禁止 FastAPI 直接散落读取底层 chunk 文件来绕过 runtime 边界。

## 9. 状态恢复设计

### 9.1 URL 保存“在哪里”

URL 至少保存：

- course_id；
- chapter_id（Chapter 页）；
- section_id；
- mode。

示例：

```text
/courses/functional_analysis_course/sections/ch01_s01?mode=learn
```

浏览器刷新或直接打开该深链接时，必须回到同一个 Section + mode。

Phase 1D 不承诺关闭浏览器/PWA 后自动恢复“上一次打开页面”；这属于后续 StudyRecord / 持久化能力。

### 9.2 sessionStorage 保存“页面里具体在哪里”

Phase 1D 不引入数据库。

客户端用 `sessionStorage` 保存本次浏览器会话的局部 UI 状态：

- 每个 mode 的 scrollY；
- 当前高亮对象；
- 展开卡片；
- 复习卡翻开状态；
- 刷题当前题号；
- 目录抽屉状态。

建议按 `course_id + section_id + mode` 分 key，避免不同 Section 状态串扰。

这些状态必须支持同一标签页内的路由往返与页面刷新；不要求跨浏览器会话永久保留。

### 9.3 来源往返

点击“查看来源”前保存 return snapshot：

- return route；
- mode；
- scrollY；
- expanded objects；
- active object。

进入来源页后高亮目标对象。

点击“返回学习”时恢复：

- 原 Section；
- 原 mode；
- 原滚动位置；
- 原展开状态；
- 原当前对象。

浏览器后退与显式“返回学习”都必须可用；显式返回是产品主路径。

## 10. 错误与空状态

所有用户可见错误必须中文显示。

至少覆盖：

- Library 不可用；
- course 不存在；
- Chapter 不存在；
- Section 不存在；
- source ref 不存在；
- 中文正文缺失；
- mode 没有对象；
- FastAPI 与 runtime 初始化失败。

错误不能把 Python traceback 暴露为主界面内容。

开发模式可以在控制台保留技术细节。

## 11. 可访问性与响应式

### 11.1 桌面端

- 正文优先宽度；
- 不长期占用宽左侧目录；
- 目录通过抽屉打开；
- 四模式 Tab 固定且明显。

### 11.2 手机/PWA

- 同一页面单列适配；
- 四模式 Tab 可横向容纳或滚动；
- 来源详情保持单列；
- 不要求独立移动端代码库。

## 12. 数据真实性原则

Phase 1D 必须继续遵守现有 runtime 的来源真实性约束：

- 不把 AI 生成文本冒充教材文本；
- 不伪造教材 anchor；
- 不伪造答案或解析；
- 不因 UI 需要而自动填充缺失教材内容；
- 缺失即显示缺失状态；
- 所有 mode item 必须可追溯到真实 source ref。

## 13. 测试策略

### 13.1 Python API 测试

至少测试：

- Library API 返回 Functional Analysis；
- Functional Analysis 中文名称来自现有 `book_metadata.title_zh`；
- Course API 返回 8 Chapters / 132 Sections；
- Chapter API 可解析真实 Chapter；
- Section `ch01_s01` 可打开；
- preview / learn / review / practice 四接口 identity 一致；
- source resolver 对真实 object 可解析；
- unknown course/chapter/section/source 为稳定 4xx；
- review/practice 空列表为 200 合法空状态。

### 13.2 前端测试

至少测试：

- 书架渲染；
- 课程目录渲染；
- Chapter → Section 导航；
- Section 缺省 mode 规范化为 `learn`；
- 四 mode 可自由切换；
- 中文对象类型映射；
- 中文优先缺失 fallback；
- 查看来源；
- 来源 route 包含 course ID；
- 返回后恢复 mode；
- 返回后恢复 scroll/展开状态；
- 手机宽度基础响应式不破版。

### 13.3 真实端到端验收

使用真实：

- `functional_analysis_course`
- `ch01_s01`

验收链：

```text
书架
→ 泛函分析
→ Chapter 1
→ ch01_s01
→ 学习
→ 选一个真实教材对象
→ 查看来源
→ 返回
→ 原学习状态恢复
→ 切复习
→ 切刷题
```

必须证明 payload 与真实 runtime source ref 一致。

## 14. CI 门

Phase 1D 完成后 CI 至少包含：

- 现有 Python runtime reference tests 保持通过；
- FastAPI API tests；
- React TypeScript typecheck；
- 前端 unit/component tests；
- production build；
- 至少一个真实 Functional Analysis app-smoke 测试。

任何新增 UI/API 不能降低 Phase 1A–1C 的真实教材 readiness gate。

## 15. 目录建议

实现阶段建议新增：

```text
app/
├── api/
│   ├── main.py
│   ├── routes/
│   ├── schemas/
│   └── services/
└── web/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── api/
        ├── components/
        ├── pages/
        ├── state/
        └── routes/
```

具体文件拆分由 implementation plan 决定，但必须维持：

- FastAPI routes 不直接散落读取教材文件；
- Python service 层封装 runtime；
- React API client 独立；
- 页面组件与状态恢复逻辑分离。

## 16. 与旧 ROADMAP 的关系

`docs/ROADMAP.md` 当前将 Phase 1 的“预习 / 学习 / 复习 / 刷题 / Chapter Hub / 锚点 / 搜索 / StudyRecord”拆成 1D–1K 多个子阶段。

本规范中的“Phase 1D”是当前软件主线使用的 UI foundation 阶段名称：它只实现四模式的现有确定性 source-backed shell，不宣称完成旧 ROADMAP 中后续的 AI、完整复习策略、题库、StudyRecord、Chapter Hub 等内容。

实现计划应在不扩大范围的前提下更新 ROADMAP 状态说明，使阶段命名不再产生歧义。

## 17. 完成定义

Phase 1D 只有同时满足以下条件才算完成：

1. 本机能启动 FastAPI，默认只绑定本机；
2. 本机能启动/构建 React PWA；
3. 书架真实显示 Functional Analysis 的中文教材名；
4. 真实显示 8 Chapters / 132 Sections；
5. `ch01_s01` 可进入；
6. Section 缺省 mode 固定进入学习模式；
7. 四模式均可打开且可自由切换；
8. 学习页中文优先；
9. 至少一个真实教材对象可打开结构化来源；
10. 来源 URL 包含 course ID；
11. 来源页显示真实 printed/PDF page 和 source anchor；
12. 返回后恢复原 Section mode 与页面位置；
13. 无中文内容时明确显示缺失状态，不伪造内容；
14. 原有 runtime CI 不回退；
15. 新 API、前端测试和 production build 全部通过。

达到以上条件后，才能进入后续搜索/问答、持久化 StudyRecord、Chapter Hub 或原始 PDF 辅助查看器等阶段。
