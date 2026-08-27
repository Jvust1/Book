# Phase 1E 教材内搜索与来源跳转设计

> 日期：2026-08-27
> 状态：待实现
> 基线：Phase 1D local-first Book App MVP 已合并到 `main`

## 1. 目标

Phase 1E 在现有 Book App 上增加课程内教材搜索能力，直接复用已经审计完成的 Functional Analysis `search_index_v0_36.jsonl`（1493 条唯一记录），建立确定性、来源可追溯、可测试的中英文本地搜索闭环：

```text
Course Search
→ SearchRuntime
→ audited search_index JSONL
→ SearchResult
→ existing SourceResolver / SourcePage
→ return to preserved search context
```

本阶段不引入 AI、embedding、向量数据库、外部搜索服务或新的教材结构化资产。

## 2. 成功标准

Phase 1E 完成时必须满足：

1. 用户可在当前 course 内搜索中文与英文教材内容。
2. 术语、定义、定理、命题、引理、公式、例题、习题和 problem 可通过同一搜索接口命中。
3. 搜索只消费该 course 的 enabled 主教材现有 canonical search index。
4. 每个结果保留 canonical `course_id`、`book_id`、`source_id`、`source_anchor`、PDF 页和纸质页信息。
5. 点击结果复用 Phase 1D 的 `SourceResolver` 和 Source 页面，不实现第二套来源解析。
6. 从 Source 页面返回后恢复查询词、结果状态、选中结果和滚动位置。
7. 空结果与 search index 不可用必须区分。
8. 浏览器桌面与 390×844 窄屏验收通过。
9. 所有新增 API、Runtime 和 UI 行为进入 CI gate。

## 3. 非目标

Phase 1E 明确不做：

- AI 问答；该能力属于 Phase 1F。
- 语义向量检索、reranker 或 embedding。
- 全 App 跨 course 搜索。
- 搜课堂、考点、笔记、错题或学习记录。
- 修改 `books/functional-analysis/**` 中的教材结构化事实或重新生成 1493 条索引。
- 将搜索历史写入长期 `StudyRecord`。
- 原始 PDF Reader；点击结果仍进入现有结构化 Source 页面。

## 4. 架构选择

采用独立的 `SearchRuntime`，放在 Python Runtime 层，而不是让 `BookAppService` 或 React 前端直接解析 JSONL。

```text
React SearchPage
       ↓ typed HTTP API
FastAPI /api/courses/{course_id}/search?q=...
       ↓
BookAppService.search(...)
       ↓
SearchRuntime.from_course(course)
       ↓
CourseRuntime.main_book()
       ↓
BookRuntime.search_index_path
       ↓
search_index_v0_36.jsonl
```

### 4.1 选择原因

- 保持现有架构原则：Web 不直接读取 `books/`、`courses/`、`library/` 或 JSONL 资产。
- `BookAppService` 继续只做稳定 DTO 投影，不承担底层检索实现。
- 后续《实分析》等独立 course 可复用相同 Runtime。
- Phase 1F 教材问答可以复用搜索层作为可追溯检索入口，而无需反向依赖前端/API。
- 搜索算法保持确定性，便于用真实教材固定查询做 regression tests。

## 5. Runtime 设计

### 5.1 新文件

新增：

- `runtime/search_runtime.py`
- `tests/test_search_runtime.py`

并从 `runtime/__init__.py` 导出：

- `SearchRuntime`
- `SearchRuntimeError`
- `SearchIndexUnavailableError`
- `SearchQueryError`
- `SearchHit`

### 5.2 SearchRuntime 创建方式

公开入口：

```python
SearchRuntime.from_course(course: CourseRuntime) -> SearchRuntime
```

初始化规则：

1. 使用 `course.main_book()` 获取唯一 enabled 主教材。
2. 读取 `BookRuntime.search_index_path`。
3. 若 path 为 `None`、文件不存在、无法打开或 JSONL 行无法解析，则抛出 `SearchIndexUnavailableError`。
4. 不回退到扫描 structure JSON，不静默重建索引。

### 5.3 SearchHit 数据模型

`SearchHit` 为只读 dataclass，至少包含：

```python
@dataclass(frozen=True)
class SearchHit:
    rank: int
    score: int
    course_id: str
    book_id: str
    kind: str
    source_id: str
    number: str | None
    title_zh: str | None
    title_en: str | None
    formula: str | None
    pdf_page: int | None
    printed_page: int | str | None
    source_anchor: str | None
    snippet: str | None
```

其中：

- `kind` 优先来自索引 `type`。
- `source_id` 使用 `id`，若缺失则使用 `unit_id`；两者都不存在的记录不作为可跳转搜索结果。
- `book_id` 必须与 `course.main_book().book_id` 一致；不一致记录视为索引完整性错误，不静默返回。
- `source_anchor` 直接使用索引事实，不生成伪 anchor。
- `pdf_page` / `printed_page` 直接使用索引或 `jump_target` 中的 canonical 页码。
- `snippet` 只从索引已有可显示字段投影，不生成 AI 摘要。

## 6. 查询规范化与匹配

### 6.1 Query contract

公开接口：

```python
SearchRuntime.search(query: str, *, limit: int = 30) -> list[SearchHit]
```

规则：

- `query.strip()` 后不能为空。
- 空 query 抛出 `SearchQueryError`。
- `limit` 必须在 `1..100`；超出范围抛出 `SearchQueryError`。
- Unicode 文本使用 `casefold()` 做不区分大小写比较。
- 不对数学表达式做会改变语义的 aggressive normalization。
- 首版不做拼写纠正和模糊编辑距离。

### 6.2 可搜索字段

按索引实际存在值构建搜索文本：

高优先级：

- `title_zh`
- `name_zh`
- `title_en`
- `name_en`
- `number`
- `id`
- `unit_id`

中优先级：

- `formula`
- `initial_concepts_zh`
- 类型字段 `type`

低优先级：

- 其他明确为人类可读的短文本标题/标签字段；不得把整个嵌套 JSON 序列化后搜索，以免产生不可解释命中。

### 6.3 确定性打分

首版使用整数打分，结果按 `score DESC`，然后按原 JSONL 行号 ASC 稳定排序。

推荐权重：

- 1000：标题/名称字段规范化后完全等于 query。
- 900：`number` / `id` / `unit_id` 完全等于 query。
- 800：标题/名称以 query 开头。
- 700：标题/名称包含 query。
- 600：formula 完全等于 query。
- 500：formula 包含 query。
- 400：`initial_concepts_zh` 某项完全等于 query。
- 350：`initial_concepts_zh` 某项包含 query。
- 300：type 完全等于 query。
- 0：不命中。

一个记录可以命中多个字段，但使用最高等级作为主分数；可以加入有限 secondary bonus，但总分规则必须固定并由测试锁定，不能依赖字典遍历顺序。

## 7. App API 设计

### 7.1 DTO

在 `app/api/models.py` 新增：

- `SearchResultItem`
- `SearchResponse`

`SearchResponse`：

```python
class SearchResponse(BaseModel):
    course_id: str
    book_id: str
    query: str
    result_count: int
    results: list[SearchResultItem]
```

`SearchResultItem` 至少投影 `SearchHit` 的可显示/可跳转字段。

### 7.2 Service

在 `BookAppService` 增加：

```python
def search(self, course_id: str, query: str, *, limit: int = 30) -> SearchResponse
```

职责：

1. 通过现有 `_course(course_id)` 校验课程。
2. 创建 `SearchRuntime.from_course(course)`。
3. 调用 `search(query, limit=limit)`。
4. 投影成 API DTO。
5. 将 `SearchQueryError` 转换为 400 类用户错误。
6. 将 `SearchIndexUnavailableError` 转换为 `AppUnavailableError(code="search_unavailable", user_message="教材搜索暂不可用", ...)`。

### 7.3 HTTP endpoint

FastAPI 新增：

```text
GET /api/courses/{course_id}/search?q={query}&limit=30
```

行为：

- 正常有结果：HTTP 200。
- 正常无结果：HTTP 200，`result_count=0`，`results=[]`。
- `q` 为空/全空格或 limit 越界：HTTP 400，稳定中文错误 JSON。
- course 不存在：沿用现有 HTTP 404。
- 索引不存在/损坏：HTTP 503，`error.code = "search_unavailable"`。

## 8. Web 设计

### 8.1 Route

新增 course-scoped route：

```text
/courses/:courseId/search?q=Banach
```

首版不增加跨 course `/search`。

### 8.2 入口

Course 页面增加明显但不抢占主导航的“搜索教材”入口。搜索页始终显示当前课程名称/返回课程入口，使用户不会混淆检索范围。

### 8.3 SearchPage 状态

搜索词以 URL `q` 为 canonical 状态，便于刷新和后退恢复。

页面状态区分：

1. 初始空 query：显示搜索输入与提示，不发起 API 请求。
2. loading。
3. results。
4. no-results：明确显示“未找到匹配教材内容”，不描述为系统故障。
5. unavailable：显示“教材搜索暂不可用”，与 no-results 分开。
6. generic error：沿用 App 现有错误展示模式。

### 8.4 Result card

每条结果优先显示：

- 中文标题/名称；无中文时明确显示中文内容未提供，不把英文伪装成中文。
- 英文标题作为辅助。
- 类型与编号。
- 公式（存在时）。
- 纸质页 / PDF 页。
- 可选 snippet。

卡片点击时根据 `kind + source_id` 进入现有 Source route；不得通过搜索记录直接复制 Source 页正文。

## 9. 搜索 → Source → 返回状态

继续复用 Phase 1D 的 session-level state 原则，不引入长期记录。

搜索页在跳转 Source 前保存：

```ts
{
  route: current search URL,
  query: q,
  scrollY: window.scrollY,
  activeSourceKey: `${kind}:${sourceId}`
}
```

返回时：

1. URL 恢复 `q`。
2. React 根据 `q` 重新请求确定性搜索结果。
3. 恢复 `scrollY`。
4. 对 `activeSourceKey` 对应结果恢复选中/焦点提示。

不把完整搜索结果数组塞入 `sessionStorage`，避免 stale DTO；结果应从相同 deterministic query 重新获取。

## 10. Source identity 与跳转约束

SearchRuntime 返回结果前必须保证：

- result `book_id` == 当前 course 主教材 canonical `book_id`。
- `source_id` 存在。
- `kind` 存在。

实际 Source 是否可解析仍由现有 `SourceResolver` 负责。搜索层不复制 object / figure / translation 的解析逻辑。

如果某搜索结果来自索引但 `SourceResolver` 无法解析：

- Runtime 搜索本身可以返回该 canonical 索引记录；
- 点击来源时沿用现有 Source integrity/error 行为；
- acceptance fixtures 应选择可解析的真实记录；
- 若大量不可解析记录出现，应视为数据完整性回归而不是由 UI 猜测映射。

## 11. 错误与完整性策略

必须明确区分：

- `SearchQueryError`：用户输入无效。
- `SearchIndexUnavailableError`：索引文件不可使用。
- `SearchRuntimeError`：其他搜索层完整性错误。
- 正常 0 命中：不是异常。

JSONL 加载采用 fail-closed：任何非空行无法解析时，整个索引标记 unavailable，不跳过坏行继续给用户不完整结果。

## 12. 测试设计

### 12.1 Runtime tests

`tests/test_search_runtime.py` 至少覆盖：

- Functional Analysis 真实索引可打开。
- 中文 `巴拿赫空间` 可命中相关 definition/concept。
- 英文大小写不敏感搜索。
- `Hölder` 可命中真实 theorem。
- 数学 formula 查询可命中。
- exercise/problem 类型可命中。
- 精确标题排名高于包含命中。
- 同分结果保持 JSONL 原顺序。
- 无结果返回空 list。
- 空 query 拒绝。
- 非法 limit 拒绝。
- 缺索引拒绝。
- 损坏 JSONL fail-closed。
- book identity mismatch 拒绝。

### 12.2 App service/API tests

扩展 `app_tests`：

- service 返回 stable DTO。
- HTTP 中文查询 200。
- HTTP 英文查询 200。
- 0 结果为 200 + empty results。
- 空 q 为 400。
- index unavailable 为 503 + `search_unavailable`。
- unknown course 为 404。

### 12.3 Web unit tests

至少覆盖：

- URL query 驱动搜索。
- loading/results/no-results/unavailable 四类页面状态。
- 结果卡片显示 canonical 页码和类型。
- 点击结果构造现有 Source route。
- Source 返回后恢复 q。
- session state 只保存 route/scroll/active source，不保存长期学习状态。

### 12.4 Browser acceptance

Playwright 增加至少：

1. 桌面：Course → 搜索 `Hölder` → theorem result → Source → 返回 → q 与位置恢复。
2. 桌面：中文搜索真实结果。
3. 桌面：无结果查询显示 no-results 而不是 error。
4. 390×844：搜索、结果卡片和来源往返无横向溢出。

## 13. CI 变更

现有 App UI workflow 应纳入新增 Runtime/API/Web tests。

Runtime reference workflow 增加：

- `python -m py_compile runtime/search_runtime.py`
- `tests.test_search_runtime`
- Functional Analysis rebuild 后验证 `SearchRuntime.from_course(...)` 能打开 1493 条真实索引并执行至少一个固定查询。

App UI workflow 增加：

- Search service/API tests。
- Web search unit tests。
- Search Playwright acceptance。

不降低现有 Phase 1D gate。

## 14. 文件边界

预计主要变更：

### Runtime
- Create `runtime/search_runtime.py`
- Modify `runtime/__init__.py`
- Create `tests/test_search_runtime.py`

### API
- Modify `app/api/models.py`
- Modify `app/api/service.py`
- Modify `app/api/main.py`
- Modify/extend `app_tests/test_app_service.py`
- Modify/extend `app_tests/test_api.py`
- Modify/extend `app_tests/test_api_live.py`

### Web
- Modify typed API client under `app/web/src/api/`
- Create `app/web/src/pages/search_page.tsx` or follow the repository's existing page naming convention exactly
- Modify route configuration under `app/web/src/routes/`
- Modify Course page to add search entry
- Reuse/extend state helpers under `app/web/src/state/`
- Add focused search tests under the existing Vitest test structure
- Extend Playwright specs

### CI/docs
- Modify `.github/workflows/runtime-reference-tests.yml`
- Modify `.github/workflows/app-ui-tests.yml`
- Modify `README.md`
- Modify `docs/ROADMAP.md`
- Modify `app/README.md`

不得为了 Phase 1E 进行无关目录重构。

## 15. 实施顺序

实施使用 TDD，并按可独立审查的边界提交：

1. SearchRuntime RED tests → deterministic Runtime 实现。
2. API DTO/service RED tests → API 实现。
3. Web typed client + SearchPage RED tests → UI 实现。
4. Search → Source → return RED tests → session restore 实现。
5. Playwright acceptance。
6. CI gate 与文档更新。
7. 全量验证后创建 PR。

## 16. Phase 1F 接口预留

Phase 1E 不实现 QA，但 `SearchRuntime.search()` 必须保持纯检索接口，不返回 UI-specific 字段或模型回答。Phase 1F 可以在其上增加独立 QA retrieval orchestration，同时继续要求每个证据指向 canonical `SearchHit` / Source identity。

## 17. 验收结论规则

Phase 1E 只有在以下全部成立时才能标记完成：

- Runtime tests 全绿。
- App API tests 全绿。
- Web unit/typecheck/build 全绿。
- Playwright 搜索闭环全绿。
- Functional Analysis `RUNTIME_READY` 未回归。
- 8 Chapter / 132 Section、442 PageMap、1493 search records 等既有基线未发生非预期变化。
- 搜索结果未引入 AI 生成教材事实。
- search index unavailable 与 0 hit 的用户语义明确区分。
