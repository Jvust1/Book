# Phase 1E 教材内搜索与来源跳转 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 local-first Book App 中加入 course-scoped、确定性、中英双语、来源可追溯的教材搜索，并完成 Search → Source → Return 闭环。

**Architecture:** 新增纯 Python `SearchRuntime`，只消费 `CourseRuntime.main_book().search_index_path` 指向的 canonical JSONL，并把可跳转结果映射为 `source_kind + source_id`。FastAPI/`BookAppService` 只投影稳定 DTO；React 通过 typed API 使用搜索，URL `q` 是查询真源，`sessionStorage` 仅保存来源往返所需的短期 route/scroll/active source 状态。现有 `SourceResolver` 不扩展新的 theorem/definition 路由类型。

**Tech Stack:** Python 3.11–3.13 standard library + unittest; FastAPI/Pydantic/Uvicorn; React 19 + TypeScript 5.9 + React Router 7 + Vite 7; Vitest/Testing Library; Playwright Chromium; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-search-phase-1e-design.md`

## Global Constraints

- 直接复用 Functional Analysis 已审计的 `search_index_v0_36.jsonl`，当前真实基线为 1493 条记录；不得重新生成搜索事实作为 Phase 1E 实现手段。
- 搜索仅限当前 course 的 enabled main book；不做跨课程全局搜索。
- 不引入 AI、embedding、向量数据库、reranker、外部搜索服务或模糊拼写纠正。
- Web 不直接读取 `books/`、`courses/`、`library/` 或 JSONL；FastAPI route 不直接解析教材文件。
- `source_kind` 只能使用现有 `SourceResolver` 可处理的 canonical kind；首版搜索结果为 `object` 或 `figure`。
- `object_type` 只用于展示 `theorem/definition/exercise/problem/...`，不得被当作 Source route kind。
- 索引缺失、损坏、book identity 不一致必须 fail closed；正常 0 hit 必须返回 HTTP 200。
- 搜索结果不得伪造 `source_anchor`、页码、中文内容或摘要。
- 查询规则完全确定：最高单项分数、无 bonus、同分按 JSONL 原行号排序。
- URL `q` 是 SearchPage 查询真源；`sessionStorage` 不保存完整 result DTO，不构成长期 StudyRecord。
- 保持 Phase 1D 的 Library/Course/Chapter/Section/Source 行为和 8 Chapter / 132 Section / 442 PageMap / 1493 search records 基线不回归。
- 所有用户可见新状态与错误使用中文。

---

## Planned File Structure

```text
runtime/
├── search_runtime.py                  # new: JSONL loader, integrity gate, deterministic ranking
└── __init__.py                        # export SearchRuntime contract

tests/
├── runtime_fixture_factory.py         # extend ready-book fixture to accept search records
└── test_search_runtime.py             # new Runtime RED/green tests

app/api/
├── errors.py                          # InvalidSearchQueryError
├── models.py                          # SearchResultItem/SearchResponse
├── service.py                         # BookAppService.search()
└── main.py                            # GET /api/courses/{course_id}/search

app_tests/
├── test_app_service.py                # service mapping/error contract
├── test_api.py                        # HTTP contract
└── test_api_live.py                   # real loopback search smoke

app/web/src/api/
├── types.ts                           # Search DTO types
├── client.ts                          # bookApi.searchCourse()
└── client.test.ts                     # encoded q/limit + error test

app/web/src/state/
├── searchViewState.ts                 # new: short-lived search return state
└── searchViewState.test.ts

app/web/src/pages/
├── SearchPage.tsx                     # new
├── SearchPage.test.tsx                # new
├── CoursePage.tsx                     # add 搜索教材 entry
├── CoursePage.test.tsx                # entry coverage
├── SourcePage.tsx                     # return-to-search before return-to-section
└── SourcePage.test.tsx                # search return precedence

app/web/src/routes/router.tsx           # course search route
app/web/src/styles.css                  # focused search form/result responsive styles
app/web/e2e/functional-analysis.spec.ts # real search acceptance

.github/workflows/runtime-reference-tests.yml
.github/workflows/app-ui-tests.yml
README.md
docs/ROADMAP.md
app/README.md
```

---

### Task 1: SearchRuntime deterministic retrieval contract

**Files:**
- Create: `runtime/search_runtime.py`
- Modify: `runtime/__init__.py`
- Modify: `tests/runtime_fixture_factory.py`
- Create: `tests/test_search_runtime.py`

**Interfaces:**
- Consumes: `CourseRuntime.main_book() -> BookRuntime`
- Consumes: `BookRuntime.search_index_path`, `BookRuntime.objects`, `BookRuntime.figures`, `BookRuntime.book_id`
- Produces: `SearchRuntime.from_course(course: CourseRuntime) -> SearchRuntime`
- Produces: `SearchRuntime.search(query: str, *, limit: int = 30) -> list[SearchHit]`
- Produces: `SearchHit`, `SearchRuntimeError`, `SearchIndexUnavailableError`, `SearchQueryError`
- Produces metrics: `index_record_count: int`, `searchable_candidate_count: int`

- [ ] **Step 1: Extend the fixture writer so tests can control JSONL content**

Change `write_ready_book()` to accept `search_records: list[dict[str, object]] | None = None`; write each record as one JSONL line. Preserve the current default section record when `search_records is None` so existing tests do not change behavior.

```python
records = search_records if search_records is not None else [
    {"id": "section_ch01_s01", "book_id": book_id, "type": "section"}
]
(root / "search_index_v1.jsonl").write_text(
    "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
    encoding="utf-8",
)
```

- [ ] **Step 2: Write RED tests for loading, identity and canonical source mapping**

Create `tests/test_search_runtime.py`. Include a fixture object with ID `def_banach`, a figure with ID `fig_fixture`, and search rows for both plus one unmappable section row. Assert:

```python
runtime = SearchRuntime.from_course(course)
self.assertEqual(runtime.index_record_count, 3)
self.assertEqual(runtime.searchable_candidate_count, 2)

hits = runtime.search("巴拿赫空间")
self.assertEqual(hits[0].source_kind, "object")
self.assertEqual(hits[0].source_id, "def_banach")
self.assertEqual(hits[0].object_type, "definition")
```

Also write separate RED tests for: missing search path/file, malformed non-empty JSONL line, wrong `book_id`, blank query, limit 0 and 101, no hit returns `[]`.

- [ ] **Step 3: Run the new test module and confirm RED**

Run:

```bash
python -m unittest tests.test_search_runtime -v
```

Expected: import failure because `runtime.search_runtime` / exported symbols do not exist yet.

- [ ] **Step 4: Implement the minimal SearchRuntime loader and fail-closed integrity gate**

Implement immutable internal candidate rows retaining `line_number` and raw index data. On load: parse every non-empty line with `json.loads`, require dict rows, require every non-empty row's `book_id == book.book_id`, count all valid rows, then map only IDs present in `book.objects` or `book.figures` into searchable candidates. Never infer `source_kind` from index `type`.

- [ ] **Step 5: Add deterministic scoring tests before scoring implementation**

Test fixed scores and ordering using controlled rows:

```python
self.assertEqual(runtime.search("Banach")[0].score, 800)  # title prefix
self.assertEqual(runtime.search("巴拿赫空间")[0].score, 1000)
self.assertEqual(runtime.search("1/p + 1/q")[0].score, 600)
```

Create two same-score candidates and assert original JSONL order is preserved. Assert returned ranks are `1..len(hits)` after limit truncation.

- [ ] **Step 6: Implement exact scoring from the spec**

Use `query.strip().casefold()` and field-normalization helpers. Search only `title_zh/name_zh/title_en/name_en`, `number/id/unit_id`, `formula`, list-of-string `initial_concepts_zh`, and `type`. Score is exactly the maximum applicable value: 1000/900/800/700/600/500/400/350/300. Sort by `(-score, line_number)`, slice limit, then assign ranks.

- [ ] **Step 7: Add real Functional Analysis acceptance tests**

With repository root fixture:

```python
course = CourseRuntime.open(REPO_ROOT / "courses" / "functional-analysis")
runtime = SearchRuntime.from_course(course)
self.assertEqual(runtime.index_record_count, 1493)
self.assertGreater(runtime.searchable_candidate_count, 0)
```

Assert real queries include `Hölder` with `source_kind == "object"` and theorem `object_type`; add one Chinese query, one formula query, and at least one exercise/problem query chosen from actual index/runtime rows. Do not hard-code `searchable_candidate_count` until the first verified run reveals the real value.

- [ ] **Step 8: Run Runtime regression gate**

```bash
python -m unittest tests.test_search_runtime tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime tests.test_section_learning_runtime tests.test_source_resolver -v
```

Expected: all pass.

- [ ] **Step 9: Commit Task 1**

```bash
git add runtime/search_runtime.py runtime/__init__.py tests/runtime_fixture_factory.py tests/test_search_runtime.py
git commit -m "feat: add deterministic textbook search runtime"
```

---

### Task 2: Stable App service and HTTP search API

**Files:**
- Modify: `app/api/errors.py`
- Modify: `app/api/models.py`
- Modify: `app/api/service.py`
- Modify: `app/api/main.py`
- Modify: `app_tests/test_app_service.py`
- Modify: `app_tests/test_api.py`
- Modify: `app_tests/test_api_live.py`

**Interfaces:**
- Consumes: Task 1 `SearchRuntime`, `SearchHit`, `SearchQueryError`, `SearchIndexUnavailableError`, `SearchRuntimeError`
- Produces: `BookAppService.search(course_id: str, query: str, *, limit: int = 30) -> SearchResponse`
- Produces HTTP: `GET /api/courses/{course_id}/search?q=...&limit=30`
- Produces error: `InvalidSearchQueryError(code="invalid_search_query", user_message="搜索条件无效")`

- [ ] **Step 1: Write RED service tests**

Extend `BookAppServiceRealLibraryTests`:

```python
result = self.service.search("functional_analysis_course", "Hölder")
self.assertEqual(result.course_id, "functional_analysis_course")
self.assertEqual(result.book_id, "stein_shakarchi_functional_analysis_2011")
self.assertEqual(result.query, "Hölder")
self.assertGreater(result.result_count, 0)
self.assertEqual(result.results[0].source_kind, "object")
self.assertEqual(result.results[0].object_type, "theorem")
```

Add blank-query mapping to `InvalidSearchQueryError`, and a temporary fixture with a broken index that maps to `AppUnavailableError(code="search_unavailable")`.

- [ ] **Step 2: Run service tests and confirm RED**

```bash
python -m unittest app_tests.test_app_service -v
```

Expected: missing `BookAppService.search` / DTO/error symbols.

- [ ] **Step 3: Add DTO/error/service projection**

Add `SearchResultItem` and `SearchResponse` with exactly the spec fields. In `BookAppService.search`, preserve the stripped human query as response `query`, map Runtime input errors to `InvalidSearchQueryError`, and all search availability/integrity errors to `AppUnavailableError` without leaking internal details to the HTTP body.

- [ ] **Step 4: Write RED HTTP tests**

Add real endpoint cases to `app_tests/test_api.py`:

```python
response = self.client.get(
    "/api/courses/functional_analysis_course/search",
    params={"q": "Hölder", "limit": 10},
)
self.assertEqual(response.status_code, 200)
payload = response.json()
self.assertGreater(payload["result_count"], 0)
self.assertEqual(payload["results"][0]["source_kind"], "object")
```

Also test: nonsense query → 200 empty list; whitespace `q` → 400 `invalid_search_query`; missing course → 404; overridden service raising `search_unavailable` → 503. Ensure no traceback/detail appears.

- [ ] **Step 5: Add route and exception handler**

Update FastAPI app version from `1d` to `1e`. Add `InvalidSearchQueryError` handler returning 400, then:

```python
@app.get("/api/courses/{course_id}/search", response_model=SearchResponse)
def search(
    course_id: str,
    q: str,
    limit: int = 30,
    service: BookAppService = Depends(get_service),
) -> SearchResponse:
    return service.search(course_id, q, limit=limit)
```

Do not rely on FastAPI's default 422 for domain limit/query validation; `BookAppService/SearchRuntime` must own the stable 400 contract.

- [ ] **Step 6: Extend real live loopback smoke**

In `test_api_live.py`, URL-encode a real query and verify a live Uvicorn request to `/api/courses/functional_analysis_course/search?q=H%C3%B6lder` returns 200 and at least one canonical result.

- [ ] **Step 7: Run App API gate**

```bash
python -m unittest app_tests.test_api app_tests.test_api_live app_tests.test_app_service tests.test_search_runtime tests.test_source_resolver -v
```

Expected: all pass.

- [ ] **Step 8: Commit Task 2**

```bash
git add app/api app_tests
git commit -m "feat: expose course textbook search API"
```

---

### Task 3: Typed web search client and SearchPage states

**Files:**
- Modify: `app/web/src/api/types.ts`
- Modify: `app/web/src/api/client.ts`
- Modify: `app/web/src/api/client.test.ts`
- Create: `app/web/src/pages/SearchPage.tsx`
- Create: `app/web/src/pages/SearchPage.test.tsx`
- Modify: `app/web/src/pages/CoursePage.tsx`
- Modify: `app/web/src/pages/CoursePage.test.tsx`
- Modify: `app/web/src/routes/router.tsx`
- Modify: `app/web/src/styles.css`

**Interfaces:**
- Consumes HTTP Task 2 search endpoint
- Produces `SearchResultItem`, `SearchResponse` TypeScript interfaces
- Produces `bookApi.searchCourse(courseId: string, query: string, limit?: number): Promise<SearchResponse>`
- Produces route `/courses/:courseId/search?q=...`

- [ ] **Step 1: Write RED typed-client test**

Add:

```ts
await bookApi.searchCourse('functional_analysis_course', 'Hölder & Banach', 12)
expect(fetchMock).toHaveBeenCalledWith(
  '/api/courses/functional_analysis_course/search?q=H%C3%B6lder%20%26%20Banach&limit=12',
  expect.any(Object),
)
```

- [ ] **Step 2: Implement TS DTOs and client method**

Mirror the Python DTO exactly; build query params with `URLSearchParams`, not manual string concatenation. Default limit is 30.

- [ ] **Step 3: Write SearchPage RED tests for all UI states**

Use `MemoryRouter` with `/courses/functional_analysis_course/search`, mock `bookApi.searchCourse`, and cover:

1. empty `q`: input + “输入关键词搜索当前教材” and no API call;
2. `?q=H%C3%B6lder`: loading then result;
3. zero results: “未找到匹配教材内容”;
4. `ApiError(code="search_unavailable")`: “教材搜索暂不可用”;
5. generic error uses existing Chinese error message;
6. result renders Chinese fallback, English auxiliary title, object type/number, formula and paper/PDF pages;
7. result link path uses `source_kind`, never `object_type`.

- [ ] **Step 4: Implement SearchPage with URL q as canonical state**

Use `useSearchParams()`. Local input may mirror `q`, but submit must update URL, after which effect calls `bookApi.searchCourse(courseId, q)`. Empty q must not call API. Keep separate `loading`, `response`, `error` states so 0-hit is not rendered as an error.

- [ ] **Step 5: Add course route and entry**

Import `SearchPage` in router and add before/alongside other course children:

```tsx
{
  path: 'courses/:courseId/search',
  element: <SearchPage />,
}
```

On CoursePage add a visible `搜索教材` link to `/courses/${courseId}/search`. Extend CoursePage test to assert this exact href.

- [ ] **Step 6: Add focused responsive styles**

Add `search-form`, `search-input`, `search-results`, `search-result-card`, metadata/focus styles. Inputs/buttons must fit the existing `.app-main`; formula/snippet must wrap or scroll locally so body does not overflow at 390px.

- [ ] **Step 7: Run web unit/type gates**

```bash
cd app/web
npm test
npm run typecheck
npm run build
```

Expected: all pass.

- [ ] **Step 8: Commit Task 3**

```bash
git add app/web/src
git commit -m "feat: add course textbook search page"
```

---

### Task 4: Search → Source → Return session state

**Files:**
- Create: `app/web/src/state/searchViewState.ts`
- Create: `app/web/src/state/searchViewState.test.ts`
- Modify: `app/web/src/pages/SearchPage.tsx`
- Modify: `app/web/src/pages/SearchPage.test.tsx`
- Modify: `app/web/src/pages/SourcePage.tsx`
- Modify: `app/web/src/pages/SourcePage.test.tsx`

**Interfaces:**
- Produces state key: `book:search-view:{courseId}`
- Produces `SearchViewState { route: string; query: string; scrollY: number; activeSourceKey: string | null }`
- Produces helpers `saveSearchViewState`, `loadSearchViewState`, `clearSearchViewState`
- SourcePage return precedence: matching saved Search state → matching Section state → section learn fallback → course fallback

- [ ] **Step 1: Write state-helper RED tests**

Copy the defensive validation style of `sectionViewState.ts`. Test round-trip, wrong shape removal, malformed JSON removal, and course-scoped key isolation. Assert no `results` field exists in the persisted object.

- [ ] **Step 2: Implement searchViewState helper**

Validation requires finite `scrollY`, strings for route/query, and nullable string `activeSourceKey`. Do not store result arrays.

- [ ] **Step 3: Write SearchPage RED test for save/restore behavior**

Before clicking a source result, set `window.scrollY` via a test-safe property, click the source link, then assert saved state equals:

```ts
{
  route: '/courses/functional_analysis_course/search?q=H%C3%B6lder',
  query: 'Hölder',
  scrollY: 420,
  activeSourceKey: 'object:thm_1_1_holder',
}
```

On remount with the same q and saved state, mock deterministic results and assert `window.scrollTo(0, 420)` is called after results load and the matching result receives an active/focus marker.

- [ ] **Step 4: Save state on source navigation and restore after deterministic refetch**

Use an `onClick` handler on result source links to save state before navigation. Restore only when saved `route/query` match current route/q. Clear or retain the state consistently after restoration according to the spec; prefer retaining within session so browser back/forward remains stable, but never apply it to another query.

- [ ] **Step 5: Write SourcePage RED test for return-to-search precedence**

Save both a search state for `object:def_lp` and an existing Section state for `def_lp`; after clicking the return button, assert navigation chooses the saved search route. Keep the existing Section-only test green when no matching search state exists.

- [ ] **Step 6: Update SourcePage return behavior and label**

Load course-level Search state and compare `activeSourceKey === `${source.kind}:${source.source_id}``. If matched, navigate to saved search route before scanning `RETURN_MODES`. A neutral button label such as `返回上一位置` is acceptable only if all existing tests/copy are updated consistently; otherwise retain current label while behavior becomes context-aware.

- [ ] **Step 7: Run focused and full web tests**

```bash
cd app/web
npx vitest run src/state/searchViewState.test.ts src/pages/SearchPage.test.tsx src/pages/SourcePage.test.tsx
npm test
npm run typecheck
npm run build
```

Expected: all pass.

- [ ] **Step 8: Commit Task 4**

```bash
git add app/web/src/state app/web/src/pages/SearchPage.tsx app/web/src/pages/SearchPage.test.tsx app/web/src/pages/SourcePage.tsx app/web/src/pages/SourcePage.test.tsx
git commit -m "feat: restore search context after source navigation"
```

---

### Task 5: Real browser acceptance for search semantics and narrow layout

**Files:**
- Modify: `app/web/e2e/functional-analysis.spec.ts`

**Interfaces:**
- Consumes real FastAPI + Vite services
- Verifies canonical real search endpoint and browser round trip

- [ ] **Step 1: Add desktop RED acceptance for real English theorem search**

Extend Playwright with:

```ts
await page.goto(`/courses/${COURSE_ID}`)
await page.getByRole('link', { name: '搜索教材' }).click()
await page.getByRole('searchbox').fill('Hölder')
await page.getByRole('button', { name: '搜索' }).click()
await expect(page).toHaveURL(/search\?q=H%C3%B6lder/)
await expect(page.getByText(/Hölder/).first()).toBeVisible()
```

Use the real API response to select a canonical hit, verify its `source_kind/source_id`, click the corresponding result, assert Source page identity/page/anchor, click return, and assert q remains `Hölder`.

- [ ] **Step 2: Add Chinese and no-result browser cases**

Search a verified real Chinese term (from Task 1 acceptance), then search a deterministic nonsense token such as `__book_no_result_1e__` and assert “未找到匹配教材内容” while no error alert is present.

- [ ] **Step 3: Add 390×844 search overflow acceptance**

Set viewport 390×844, search a real query with a formula/result card, assert controls and at least one result are visible, and evaluate:

```ts
document.documentElement.scrollWidth <= document.documentElement.clientWidth
```

- [ ] **Step 4: Run E2E against local services**

With API on 127.0.0.1:8000 and Vite on 127.0.0.1:5173:

```bash
cd app/web
npm run e2e
```

Expected: old Phase 1D tests plus all new search acceptance pass.

- [ ] **Step 5: Commit Task 5**

```bash
git add app/web/e2e/functional-analysis.spec.ts
git commit -m "test: add real textbook search browser acceptance"
```

---

### Task 6: CI gates, documentation, and final verification

**Files:**
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Modify: `.github/workflows/app-ui-tests.yml`
- Modify: `README.md`
- Modify: `docs/ROADMAP.md`
- Modify: `app/README.md`

**Interfaces:**
- CI must compile/test SearchRuntime on Python 3.11/3.12/3.13
- CI must retain all Phase 1D App API/Web/Playwright gates

- [ ] **Step 1: Extend Runtime CI**

Add `python -m py_compile runtime/search_runtime.py`; add `tests.test_search_runtime` to the unittest command. In the Python 3.13 real validation block, instantiate `SearchRuntime.from_course(course)`, assert `index_record_count == 1493`, and assert a fixed verified real query returns a canonical object hit. Keep existing readiness/page/search reconstruction assertions unchanged.

- [ ] **Step 2: Extend App UI CI test command**

Ensure App job explicitly includes `tests.test_search_runtime` in addition to existing App/API/Source tests. Existing `npm test`, typecheck, build and Playwright already discover the new Web tests/spec and must remain unchanged unless a concrete discovery issue is observed.

- [ ] **Step 3: Update README and App docs**

Document Phase 1E architecture and endpoint:

```text
GET /api/courses/{course_id}/search?q={query}&limit=30
```

Update current capabilities to include course-scoped Chinese/English deterministic search, canonical Source jump, return-context recovery, and explicit no-result vs unavailable semantics. Do not describe it as semantic/AI search.

- [ ] **Step 4: Update ROADMAP checkboxes only after verified implementation**

Mark the Phase 1E checklist complete only for capabilities proven by tests: Chinese, English, unified object types, canonical identity, source jump, return context, no-result/unavailable distinction, browser acceptance.

- [ ] **Step 5: Run the full Python verification**

```bash
python -m unittest \
  tests.test_book_runtime \
  tests.test_course_runtime \
  tests.test_library_runtime \
  tests.test_section_learning_runtime \
  tests.test_source_resolver \
  tests.test_search_runtime \
  tests.test_functional_analysis_page_map \
  tests.test_continuation_integrity \
  tests.test_runtime_object_merge \
  tests.test_functional_analysis_identity_normalizer \
  tests.test_functional_analysis_figure_normalizer \
  app_tests.test_api \
  app_tests.test_api_live \
  app_tests.test_app_service -v
```

Expected: zero failures/errors.

- [ ] **Step 6: Run full web verification**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
npm run e2e
```

Expected: zero failures and successful build.

- [ ] **Step 7: Verify repository baselines with existing runtime tooling**

From repository root run the same readiness/rebuild validation commands used by `.github/workflows/runtime-reference-tests.yml`. Confirm Functional Analysis remains `READY`, 8 chapters / 132 sections, 442 PageMap rows, and 1493 unique search records.

- [ ] **Step 8: Commit CI/docs**

```bash
git add .github/workflows README.md docs/ROADMAP.md app/README.md
git commit -m "ci: gate Phase 1E textbook search"
```

- [ ] **Step 9: Final diff review before PR**

```bash
git diff main...HEAD --stat
git status --short --branch
```

Confirm no `books/functional-analysis/**` source assets changed, no generated node/build artifacts are committed, and changes remain Phase 1E-scoped.
