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
→ SearchHit
→ existing SourceResolver / SourcePage
→ return to preserved search context
```

本阶段不引入 AI、embedding、向量数据库、外部搜索服务或新的教材结构化资产。

## 2. 成功标准

Phase 1E 完成时必须满足：

1. 用户可在当前 course 内搜索中文与英文教材内容。
2. 术语、定义、定理、命题、引理、公式、例题、习题和 problem 可通过同一搜索接口命中。
3. 搜索只消费该 course 的 enabled 主教材现有 canonical search index。
4. 每个可展示结果保留 canonical `course_id`、`book_id`、`source_kind`、`source_id`、`source_anchor`、PDF 页和纸质页信息。
5. `source_kind` 与教材对象类型严格分离：`source_kind` 用于 SourceResolver 跳转，`object_type` 用于展示 theorem / definition / exercise 等教材类型。
6. 点击结果复用 Phase 1D 的 `SourceResolver` 和 Source 页面，不实现第二套来源解析。
7. 从 Source 页面返回后恢复查询词、结果状态、选中结果和滚动位置。
8. 空结果与 search index 不可用必须区分。
9. 浏览器桌面与 390×844 窄屏验收通过。
10. 所有新增 API、Runtime 和 UI 行为进入 CI gate。

## 3. 非目标

Phase 1E 明确不做：

- AI 问答；该能力属于 Phase 1F。
- 语义向量检索、reranker 或 embedding。
- 全 App 跨 course 搜索。
- 搜课堂、考点、笔记、错题或学习记录。
- 修改 `books/functional-analysis/**` 中的教材结构化事实或重新生成 1493 条索引。
- 将搜索历史写入长期 `StudyRecord`。
- 原始 PDF Reader；点击结果仍进入现有结构化 Source 页面。
- 为了覆盖无法跳转的索引条目而扩展新的 Section SourceResolver 类型；该能力可后续单独设计。

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

### 5.1 新文件与导出

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
3. 若 path 为 `None`、文件不存在、无法打开或 JSONL 任一非空行无法解析，则抛出 `SearchIndexUnavailableError`。
4. 不回退到扫描 structure JSON，不静默重建索引，不跳过损坏行。
5. 完整读取现有 1493 条索引记录并保留原 JSONL 行号，用于稳定排序与完整性测试。

### 5.3 SearchHit 数据模型

`SearchHit` 为只读 dataclass：

```python
@dataclass(frozen=True)
class SearchHit:
    rank: int
    score: int
    course_id: str
    book_id: str
    source_kind: str
    source_id: str
    object_type: str | None
    number: str | None
    title_zh: str | None
    title_en: str | None
    formula: str | None
    pdf_page: int | None
    printed_page: int | str | None
    source_anchor: str | None
    snippet: str | None
```

字段规则：

- `source_kind` 只能使用现有 `SourceResolver` 支持的 canonical kind：首版搜索结果仅为 `object` 或 `figure`；translation 不从当前 search index 推断。
- `object_type` 保存索引/Runtime 中的教材类型，例如 `theorem`、`definition`、`exercise`、`problem`、`concept`、`figure`。
- `source_id` 使用 canonical Runtime ID。
- `book_id` 必须与 `course.main_book().book_id` 一致，否则整个索引视为完整性失败并抛出 `SearchIndexUnavailableError`。
- `source_anchor` 直接使用索引事实，不生成伪 anchor。
- `pdf_page` / `printed_page` 使用索引顶层字段，缺失时只允许回退到索引自身 `jump_target` 的对应字段，不扫描其他教材文件猜测。
- `snippet` 只从索引已有的人类可读短文本字段投影，不生成 AI 摘要。

### 5.4 source_kind 解析

为了保证点击结果必定使用现有 SourceResolver contract，索引记录按以下固定顺序映射：

1. `source_id` 在 `book.objects` 中：`source_kind="object"`，`object_type=book.objects[source_id].type`。
2. 否则 `source_id` 在 `book.figures` 中：`source_kind="figure"`，`object_type="figure"`。
3. 否则该记录保留在原始索引统计中，但不进入可跳转的 searchable candidate 集合。

不通过索引 `type="theorem"` 直接生成 `source_kind="theorem"`，因为现有 `SourceResolver.resolve()` 不接受这种 kind。

因此，`index_record_count` 与 `searchable_candidate_count` 是两个不同指标；前者对 Functional Analysis 必须继续为 1493，后者由 Runtime 可跳转身份决定并由测试记录实际值，不硬编码猜测。

## 6. 查询规范化与匹配

### 6.1 Query contract

公开接口：

```python
SearchRuntime.search(query: str, *, limit: int = 30) -> list[SearchHit]
```

规则：

- `normalized_query = query.strip().casefold()`。
- `normalized_query` 不能为空；否则抛出 `SearchQueryError`。
- `limit` 必须为整数且处于 `1..100`；否则抛出 `SearchQueryError`。
- 不对数学表达式做会改变语义的 aggressive normalization。
- 首版不做拼写纠正、分词器、编辑距离或模糊搜索。

### 6.2 可搜索字段

仅搜索以下明确字段，不序列化整个 JSON：

- 标题/名称：`title_zh`、`name_zh`、`title_en`、`name_en`
- 身份/编号：`number`、`id`、`unit_id`
- 数学：`formula`
- 概念列表：`initial_concepts_zh`（仅 list[str]）
- 类型：`type`

不存在或不是预期类型的字段按空值处理。

### 6.3 完全确定的打分

每个 candidate 计算所有适用规则，**最终 score 取最高单项分值，不叠加 bonus**。结果按 `(score DESC, original_line_number ASC)` 排序。

固定权重：

- 1000：任一标题/名称字段规范化后完全等于 query。
- 900：`number`、`id` 或 `unit_id` 完全等于 query。
- 800：任一标题/名称字段以 query 开头。
- 700：任一标题/名称字段包含 query。
- 600：formula 完全等于 query。
- 500：formula 包含 query。
- 400：`initial_concepts_zh` 任一元素完全等于 query。
- 350：`initial_concepts_zh` 任一元素包含 query。
- 300：type 完全等于 query。
- 0：不命中，不进入结果集。

`rank` 在截取 limit 后从 1 开始连续编号。

## 7. App API 设计

### 7.1 DTO

在 `app/api/models.py` 新增：

- `SearchResultItem`
- `SearchResponse`

```python
class SearchResultItem(BaseModel):
    rank: int
    score: int
    source_kind: str
    source_id: str
    object_type: str | None
    number: str | None
    title_zh: str | None
    title_en: str | None
    formula: str | None
    pdf_page: int | None
    printed_page: int | str | None
    source_anchor: str | None
    snippet: str | None

class SearchResponse(BaseModel):
    course_id: str
    book_id: str
    query: str
    result_count: int
    results: list[SearchResultItem]
```

### 7.2 App error

在 `app/api/errors.py` 新增 `InvalidSearchQueryError(BookAppError)`，用于把 Runtime 的 `SearchQueryError` 映射到 HTTP 400。不得复用 `InvalidModeError`。

### 7.3 Service

在 `BookAppService` 增加：

```python
def search(self, course_id: str, query: str, *, limit: int = 30) -> SearchResponse
```

职责：

1. 通过现有 `_course(course_id)` 校验课程。
2. 创建 `SearchRuntime.from_course(course)`。
3. 调用 `search(query, limit=limit)`。
4. 投影成 API DTO。
5. 将 `SearchQueryError` 转换为 `InvalidSearchQueryError(code="invalid_search_query", user_message="搜索条件无效", ...)`。
6. 将 `SearchIndexUnavailableError` / 其他 SearchRuntime 完整性错误转换为 `AppUnavailableError(code="search_unavailable", user_message="教材搜索暂不可用", ...)`。

### 7.4 HTTP endpoint

FastAPI 新增：

```text
GET /api/courses/{course_id}/search?q={query}&limit=30
```

行为：

- 正常有结果：HTTP 200。
- 正常无结果：HTTP 200，`result_count=0`，`results=[]`。
- `q` 为空/全空格或 limit 越界：HTTP 400，`error.code="invalid_search_query"`。
- course 不存在：沿用现有 HTTP 404。
- 索引不存在、损坏或 identity 不一致：HTTP 503，`error.code="search_unavailable"`。

FastAPI app version 从 `1d` 更新到 `1e`。

## 8. Web 设计

### 8.1 Route

新增 course-scoped route：

```text
/courses/:courseId/search?q=Banach
```

首版不增加跨 course `/search`。

### 8.2 入口

Course 页面增加“搜索教材”入口。搜索页始终显示当前课程名称和返回课程入口，使用户不会混淆检索范围。

### 8.3 SearchPage 状态

搜索词以 URL `q` 为 canonical 状态，便于刷新和浏览器后退恢复。

页面严格区分：

1. 初始空 query：显示输入与提示，不调用 API。
2. loading。
3. results。
4. no-results：显示“未找到匹配教材内容”，不是错误。
5. unavailable：显示“教材搜索暂不可用”，与 no-results 分开。
6. generic error：沿用 App 现有错误模式。

### 8.4 Result card

每条结果显示：

- 中文标题/名称；无中文时明确显示“中文内容暂未提供”，不把英文正文伪装成中文。
- 英文标题作为辅助（存在时）。
- `object_type` 与编号。
- 公式（存在时）。
- 纸质页 / PDF 页。
- snippet（存在时）。

卡片跳转必须使用 `source_kind + source_id` 构造现有 Source route；`object_type` 只用于显示，不用于 SourceResolver 路由。

## 9. 搜索 → Source → 返回状态

继续复用 Phase 1D 的 session-level state 原则，不引入长期记录。

搜索页在跳转 Source 前保存：

```ts
{
  route: currentSearchUrl,
  query: q,
  scrollY: window.scrollY,
  activeSourceKey: `${sourceKind}:${sourceId}`
}
```

返回时：

1. URL 恢复 `q`。
2. React 根据 `q` 重新请求确定性搜索结果。
3. 恢复 `scrollY`。
4. 对 `activeSourceKey` 对应结果恢复选中/焦点提示。

不把完整搜索结果数组写入 `sessionStorage`，避免 stale DTO；结果必须由相同 deterministic query 重新获取。

## 10. 错误与完整性策略

必须区分：

- `SearchQueryError`：Runtime 用户查询输入无效。
- `SearchIndexUnavailableError`：索引文件、JSONL、book identity 或索引加载不可用。
- `SearchRuntimeError`：搜索层其他内部错误；App 层对用户统一为 `search_unavailable`。
- 正常 0 命中：不是异常。

JSONL 采用 fail-closed：任一非空行无法解析时，整个搜索 Runtime 不可用。

无法映射到现有 `book.objects` / `book.figures` 的合法索引记录不是“损坏行”；它们计入 `index_record_count`，但不进入可跳转 candidate 集合。

## 11. 测试设计

### 11.1 Runtime tests

`tests/test_search_runtime.py` 至少覆盖：

- Functional Analysis 真实索引成功读取且 `index_record_count == 1493`。
- `searchable_candidate_count > 0`，并由测试输出/fixture 锁定实际可跳转基线。
- 中文 `巴拿赫空间` 可命中相关 object。
- 英文大小写不敏感搜索。
- `Hölder` 可命中真实 theorem object，且 `source_kind == "object"`、`object_type == "theorem"`。
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
- 索引中不可映射到 object/figure 的记录不会产生不可跳转 SearchHit。

### 11.2 App service/API tests

扩展 `app_tests`：

- service 返回 stable DTO。
- HTTP 中文查询 200。
- HTTP 英文查询 200。
- 0 结果为 200 + empty results。
- 空 q 为 400 + `invalid_search_query`。
- index unavailable 为 503 + `search_unavailable`。
- unknown course 为 404。
- result 同时包含 `source_kind` 与 `object_type`。

### 11.3 Web unit tests

至少覆盖：

- URL query 驱动搜索。
- loading/results/no-results/unavailable 状态。
- 结果卡片显示 canonical 页码、`object_type`。
- 点击结果使用 `source_kind` 构造现有 Source route。
- Source 返回后恢复 q。
- session state 只保存 route/scroll/active source，不保存结果数组或长期学习状态。

### 11.4 Browser acceptance

Playwright 增加：

1. 桌面：Course → 搜索 `Hölder` → theorem object result → Source → 返回 → q 与位置恢复。
2. 桌面：中文搜索真实结果。
3. 桌面：无结果查询显示 no-results 而不是 error。
4. 390×844：搜索、结果卡片和来源往返无横向溢出。

## 12. CI 变更

Runtime reference workflow 增加：

- `python -m py_compile runtime/search_runtime.py`
- `tests.test_search_runtime`
- Functional Analysis rebuild 后验证 `SearchRuntime.from_course(...)`：`index_record_count == 1493`，并执行至少一个固定真实查询。

App UI workflow 增加：

- Search service/API tests。
- Web search unit tests。
- Search Playwright acceptance。

不得降低现有 Phase 1D gate。

## 13. 文件边界

### Runtime
- Create `runtime/search_runtime.py`
- Modify `runtime/__init__.py`
- Create `tests/test_search_runtime.py`

### API
- Modify `app/api/errors.py`
- Modify `app/api/models.py`
- Modify `app/api/service.py`
- Modify `app/api/main.py`
- Modify/extend `app_tests/test_app_service.py`
- Modify/extend `app_tests/test_api.py`
- Modify/extend `app_tests/test_api_live.py`

### Web
- Modify typed API client under `app/web/src/api/`
- Create a focused Search page following the repository's existing page naming convention
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

## 14. 实施顺序

实施使用 TDD，并按可独立审查的边界提交：

1. SearchRuntime RED tests → deterministic Runtime 实现。
2. API DTO/service RED tests → API 实现。
3. Web typed client + SearchPage RED tests → UI 实现。
4. Search → Source → return RED tests → session restore 实现。
5. Playwright acceptance。
6. CI gate 与文档更新。
7. 全量验证后创建 PR。

## 15. Phase 1F 接口预留

Phase 1E 不实现 QA。`SearchRuntime.search()` 保持纯检索接口，不返回 UI-specific 状态或模型回答。Phase 1F 可在其上建立独立 QA retrieval orchestration，同时继续要求每个证据指向 canonical `SearchHit` / Source identity。

## 16. 验收结论规则

Phase 1E 只有在以下全部成立时才能标记完成：

- Runtime tests 全绿。
- App API tests 全绿。
- Web unit/typecheck/build 全绿。
- Playwright 搜索闭环全绿。
- Functional Analysis `RUNTIME_READY` 未回归。
- 8 Chapter / 132 Section、442 PageMap、1493 search records 等既有基线未发生非预期变化。
- 搜索结果未引入 AI 生成教材事实。
- `source_kind` 与 `object_type` 没有混用。
- search index unavailable 与 0 hit 的用户语义明确区分。
