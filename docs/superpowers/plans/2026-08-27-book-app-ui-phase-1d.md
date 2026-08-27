# Book App Phase 1D Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first Chinese-first Book App MVP that exposes the existing runtime through FastAPI and a React/Vite PWA, supports Library → Course → Chapter → Section navigation, all four source-backed learning modes, structured source viewing, and lossless return-state restoration.

**Architecture:** Keep textbook parsing and truth in the Python runtime. Add one focused runtime source-resolution layer, a thin FastAPI application/service layer that converts runtime objects to stable JSON DTOs, and a React/TypeScript client that only consumes those DTOs. The browser stores route identity in the URL and ephemeral view state in `sessionStorage`; no account, cloud sync, AI generation, or PDF reader is introduced.

**Tech Stack:** Python 3.11–3.13 runtime compatibility; FastAPI + Uvicorn + HTTPX TestClient; React + TypeScript + Vite; React Router; Vitest + Testing Library; Vite PWA plugin; Playwright Chromium for one real app smoke flow; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-book-app-ui-phase-1d-design.md`

## Global Constraints

- First release is local-first: browser/PWA talks to a FastAPI process on the same machine.
- FastAPI must bind to localhost by default; do not expose a public network listener in the documented default command.
- All user-visible navigation, labels, statuses, empty states, and errors are Chinese.
- Chinese learning content is preferred; English is secondary source evidence only.
- First terminology occurrence may show `中文（English term）`; normal repeated UI uses Chinese.
- Current product profile remains one enabled main textbook per course at the App/Library layer.
- React must never read `books/`, `courses/`, `library/`, JSON, CSV, Markdown, or chunk files directly.
- FastAPI routes must never scatter direct file reads; they consume a Python service that consumes runtime APIs.
- Missing textbook content remains missing. Never invent anchors, answers, explanations, translations, or AI-generated textbook prose.
- `source_anchor` remains nullable. A missing real anchor is rendered as `教材锚点暂未提供`; the stable source ref remains `kind + source_id`.
- Section default mode is exactly `learn`.
- Valid modes are exactly `preview`, `learn`, `review`, `practice`.
- `review` and `practice` empty lists are valid HTTP 200 states.
- Source route includes course identity: `/courses/:courseId/sources/:kind/:sourceId`.
- `sessionStorage` restores state during the current browser session and across reloads; it is not a StudyRecord or permanent progress database.
- Phase 1A–1C readiness gates and existing runtime tests must remain green.
- Phase 1D does not implement AI Q&A, AI generation, accounts, cloud sync, PDF reading, lecture recording, Chapter Hub, mistake DB, full StudyRecord, Windows packaging, or native mobile apps.

---

## Planned File Structure

```text
runtime/
├── source_resolver.py                  # Stable source-ref → runtime evidence
└── __init__.py                         # Export resolver types

tests/
├── runtime_fixture_factory.py          # Existing fixture helper; enrich only where required
└── test_source_resolver.py             # Resolver TDD

app/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── main.py                         # FastAPI construction only
│   ├── models.py                       # Pydantic response DTOs
│   ├── service.py                      # Runtime → App DTO boundary
│   ├── errors.py                       # Stable app/API errors
│   └── requirements.txt                # FastAPI runtime/test deps
│
└── web/
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.json
    ├── tsconfig.app.json
    ├── tsconfig.node.json
    ├── vite.config.ts
    ├── index.html
    ├── playwright.config.ts
    ├── e2e/
    │   └── functional-analysis.spec.ts
    └── src/
        ├── main.tsx
        ├── app.tsx
        ├── styles.css
        ├── api/
        │   ├── client.ts
        │   └── types.ts
        ├── routes/
        │   └── router.tsx
        ├── state/
        │   ├── sectionViewState.ts
        │   └── sectionViewState.test.ts
        ├── components/
        │   ├── AppShell.tsx
        │   ├── ModeTabs.tsx
        │   ├── SourceLink.tsx
        │   ├── LearningObjectCard.tsx
        │   └── EmptyState.tsx
        └── pages/
            ├── LibraryPage.tsx
            ├── LibraryPage.test.tsx
            ├── CoursePage.tsx
            ├── CoursePage.test.tsx
            ├── ChapterPage.tsx
            ├── ChapterPage.test.tsx
            ├── SectionPage.tsx
            ├── SectionPage.test.tsx
            ├── SourcePage.tsx
            └── SourcePage.test.tsx

app_tests/
├── __init__.py
├── test_app_service.py                 # Real + fixture service tests
└── test_api.py                         # FastAPI contract tests

.github/workflows/
├── runtime-reference-tests.yml         # Existing workflow; only extend watch/test list when runtime changes
└── app-ui-tests.yml                    # API + web + build + real smoke

README.md
app/README.md
docs/ROADMAP.md
```

The `app/api` package owns HTTP concerns, `runtime/source_resolver.py` owns source truth resolution, and `app/web` owns presentation/state. Do not collapse these into a single large file.

---

### Task 1: Add a source-backed runtime resolver

**Files:**
- Create: `runtime/source_resolver.py`
- Modify: `runtime/__init__.py`
- Modify: `tests/runtime_fixture_factory.py`
- Create: `tests/test_source_resolver.py`
- Modify: `.github/workflows/runtime-reference-tests.yml`

**Interfaces:**
- Consumes: `CourseRuntime`, `BookRuntime.object()`, `BookRuntime.figures`, `BookRuntime.translation_text()`, `RuntimeObject.raw`, `RuntimeFigure.raw`.
- Produces:
  - `TYPE_LABELS_ZH: dict[str, str]`
  - `ResolvedSource` dataclass
  - `SourceResolver(course: CourseRuntime)`
  - `SourceResolver.resolve(kind: str, source_id: str) -> ResolvedSource`
  - `ResolvedSource.to_dict() -> dict[str, Any]`
- Supported `kind`: `object`, `figure`, `translation`.
- Unknown kind/source raises `SourceResolutionError`.

- [ ] **Step 1: Enrich the fixture with one real-looking source anchor and Chinese structured content**

Change `write_ready_book()` in `tests/runtime_fixture_factory.py` only enough for resolver tests to pass arbitrary `objects` through. Use the existing helper with this object in the test:

```python
{
    "type": "theorem",
    "id": "thm_fixture",
    "number": "1.1",
    "name_en": "Fixture theorem",
    "name_zh": "测试定理",
    "content_zh": "这是测试定理的中文内容。",
    "anchor": {
        "pdf_page": 1,
        "printed_page": 1,
        "source_anchor": "fixture:p1:thm_fixture",
    },
}
```

Do not change production Functional Analysis data to add anchors.

- [ ] **Step 2: Write failing resolver tests**

Create `tests/test_source_resolver.py` with fixture setup using `TemporaryDirectory`, `make_repo`, `write_ready_book`, `write_course`, `main_book_entry`, then assert:

```python
resolver = SourceResolver(CourseRuntime.open(course_dir))
source = resolver.resolve("object", "thm_fixture")
self.assertEqual(source.kind, "object")
self.assertEqual(source.source_id, "thm_fixture")
self.assertEqual(source.type, "theorem")
self.assertEqual(source.type_zh, "定理")
self.assertEqual(source.title_zh, "测试定理")
self.assertEqual(source.content_zh, "这是测试定理的中文内容。")
self.assertEqual(source.pdf_page, 1)
self.assertEqual(source.printed_page, 1)
self.assertEqual(source.source_anchor, "fixture:p1:thm_fixture")
```

Also test:

```python
with self.assertRaises(SourceResolutionError):
    resolver.resolve("object", "missing")
with self.assertRaises(SourceResolutionError):
    resolver.resolve("bogus", "thm_fixture")
```

Add a test proving missing `content_zh` and missing `source_anchor` remain `None`, not synthesized.

- [ ] **Step 3: Run the resolver test to verify RED**

Run:

```bash
python -m unittest tests.test_source_resolver -v
```

Expected: FAIL because `runtime.source_resolver` does not exist.

- [ ] **Step 4: Implement the minimal resolver**

Create `runtime/source_resolver.py` around this contract:

```python
from dataclasses import asdict, dataclass
from typing import Any

from .book_runtime import BookRuntimeError
from .course_runtime import CourseRuntime

TYPE_LABELS_ZH = {
    "definition": "定义",
    "theorem": "定理",
    "proposition": "命题",
    "lemma": "引理",
    "corollary": "推论",
    "formula": "公式",
    "example": "例题",
    "exercise": "练习",
    "problem": "习题",
    "figure": "图",
    "concept": "概念",
}

class SourceResolutionError(RuntimeError):
    pass

@dataclass(frozen=True)
class ResolvedSource:
    course_id: str
    book_id: str
    section_id: str | None
    kind: str
    source_id: str
    type: str | None
    type_zh: str
    number: str | None
    title_zh: str | None
    title_en: str | None
    content_zh: str | None
    formula: str | None
    printed_page: int | str | None
    pdf_page: int | None
    source_anchor: str | None
    source_batch: str | None
    translation_available: bool
    context_before: tuple[dict[str, Any], ...]
    context_after: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

For object `content_zh`, read only explicit structured keys in this order:

```python
("content_zh", "statement_zh", "description_zh", "summary_zh", "text_zh")
```

Do not heuristically slice batch Markdown into object prose in Phase 1D. If none exists, return `None` and `translation_available=True` when that object's source batch has a Chinese translation file.

For context, use the resolved object's owning Section and return at most two preceding and two following structural items, each as stable identity metadata only:

```python
{"kind": "object", "source_id": obj.id, "type": obj.type, "number": obj.number, "title_zh": obj.name_zh}
```

For figures, use real figure metadata and no invented content. For translations, return the batch Markdown as `content_zh`, with `type="translation"`, and batch page ranges when available.

- [ ] **Step 5: Export resolver types and run GREEN**

Update `runtime/__init__.py` to export:

```python
ResolvedSource
SourceResolutionError
SourceResolver
TYPE_LABELS_ZH
```

Run:

```bash
python -m unittest tests.test_source_resolver tests.test_section_learning_runtime tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime -v
```

Expected: PASS.

- [ ] **Step 6: Extend runtime CI and commit**

Add `runtime/source_resolver.py` to compile checks and `tests.test_source_resolver` to the explicit unittest command in `.github/workflows/runtime-reference-tests.yml`.

Commit:

```bash
git add runtime/source_resolver.py runtime/__init__.py tests/runtime_fixture_factory.py tests/test_source_resolver.py .github/workflows/runtime-reference-tests.yml
git commit -m "feat: add source-backed textbook resolver"
```

---

### Task 2: Add the App service boundary and stable DTOs

**Files:**
- Create: `app/__init__.py`
- Create: `app/api/__init__.py`
- Create: `app/api/errors.py`
- Create: `app/api/models.py`
- Create: `app/api/service.py`
- Create: `app_tests/__init__.py`
- Create: `app_tests/test_app_service.py`

**Interfaces:**
- Consumes: `LibraryRuntime.open()`, `CourseRuntime`, `SectionLearningRuntime`, `SourceResolver`.
- Produces:
  - `BookAppService(repository_root: Path)`
  - `library() -> LibraryResponse`
  - `course(course_id: str) -> CourseResponse`
  - `chapter(course_id: str, chapter_id: str) -> ChapterResponse`
  - `section(course_id: str, section_id: str) -> SectionResponse`
  - `mode(course_id: str, section_id: str, mode: LearningMode) -> ModeResponse`
  - `source(course_id: str, kind: str, source_id: str) -> SourceResponse`
- App-specific exceptions: `AppNotFoundError`, `AppUnavailableError`, `InvalidModeError`.

- [ ] **Step 1: Write failing service tests against the real library**

Create `app_tests/test_app_service.py` and point `REPO_ROOT` to `Path(__file__).resolve().parents[1]`.

Required real assertions:

```python
service = BookAppService(REPO_ROOT)
library = service.library()
self.assertEqual(len(library.courses), 1)
course = library.courses[0]
self.assertEqual(course.course_id, "functional_analysis_course")
self.assertEqual(course.name_zh, "泛函分析：分析学进一步专题导论")
self.assertEqual(course.chapter_count, 8)
self.assertEqual(course.section_count, 132)
```

Also assert:

```python
section = service.section("functional_analysis_course", "ch01_s01")
self.assertEqual(section.section_id, "ch01_s01")
self.assertIsNotNone(section.pdf_page_start)
```

For default product naming, derive `name_zh` from `course.main_book().metadata["title_zh"]`; do not translate `course.name` on the fly.

- [ ] **Step 2: Run RED**

Run:

```bash
python -m unittest app_tests.test_app_service -v
```

Expected: FAIL because `app.api.service` and DTOs do not exist.

- [ ] **Step 3: Implement response models**

Use Pydantic models in `app/api/models.py`. Define exact top-level DTO names:

```python
class CourseCard(BaseModel): ...
class LibraryResponse(BaseModel): ...
class SectionCard(BaseModel): ...
class ChapterCard(BaseModel): ...
class CourseResponse(BaseModel): ...
class ChapterResponse(BaseModel): ...
class SectionResponse(BaseModel): ...
class ModeItem(BaseModel): ...
class SourceRef(BaseModel): ...
class ModeResponse(BaseModel): ...
class SourceContextItem(BaseModel): ...
class SourceResponse(BaseModel): ...
```

`CourseCard` fields are exactly:

```python
course_id: str
name_zh: str
name_en: str | None
authors: list[str]
book_id: str
chapter_count: int
section_count: int
runtime_status: str
```

`SectionCard` fields are exactly:

```python
section_id: str
number: str | None
title_zh: str | None
title_en: str | None
printed_page_start: int | str | None
printed_page_end: int | str | None
pdf_page_start: int | None
pdf_page_end: int | None
```

- [ ] **Step 4: Implement `BookAppService`**

`BookAppService.__init__` stores the repository root and eagerly opens exactly one `LibraryRuntime` from `<root>/library`; convert runtime load failures into `AppUnavailableError`.

Use helpers:

```python
def _course(self, course_id: str) -> CourseRuntime: ...
def _course_card(self, course: CourseRuntime) -> CourseCard: ...
def _section_card(self, section: RuntimeSection) -> SectionCard: ...
```

For chapter identity, consume `CourseRuntime.chapters()` in audited source order. Unknown course/chapter/section/source must raise `AppNotFoundError` with a Chinese user-safe message plus an internal `code`, for example:

```python
AppNotFoundError(code="course_not_found", user_message="课程不存在")
```

For `mode()`, dispatch only:

```python
{"preview": learning.preview, "learn": learning.learn, "review": learning.review, "practice": learning.practice}
```

No generic `getattr()` on user input.

- [ ] **Step 5: Add service-level error/empty-state tests**

Test:

```python
with self.assertRaises(AppNotFoundError):
    service.course("missing")
with self.assertRaises(AppNotFoundError):
    service.chapter("functional_analysis_course", "missing")
with self.assertRaises(AppNotFoundError):
    service.section("functional_analysis_course", "missing")
with self.assertRaises(InvalidModeError):
    service.mode("functional_analysis_course", "ch01_s01", "bogus")
```

Also find or create a fixture Section with no review/practice objects and assert those modes return `items == []` rather than errors.

- [ ] **Step 6: Run GREEN and commit**

Run:

```bash
python -m unittest app_tests.test_app_service tests.test_source_resolver -v
```

Expected: PASS.

Commit:

```bash
git add app app_tests
git commit -m "feat: add Book App runtime service"
```

---

### Task 3: Expose the service through FastAPI

**Files:**
- Create: `app/api/main.py`
- Create: `app/api/requirements.txt`
- Create: `app_tests/test_api.py`

**Interfaces:**
- Consumes: every `BookAppService` method from Task 2.
- Produces FastAPI app `app.api.main:app` and these exact routes:
  - `GET /api/health`
  - `GET /api/library`
  - `GET /api/courses/{course_id}`
  - `GET /api/courses/{course_id}/chapters/{chapter_id}`
  - `GET /api/courses/{course_id}/sections/{section_id}`
  - `GET /api/courses/{course_id}/sections/{section_id}/preview`
  - `GET /api/courses/{course_id}/sections/{section_id}/learn`
  - `GET /api/courses/{course_id}/sections/{section_id}/review`
  - `GET /api/courses/{course_id}/sections/{section_id}/practice`
  - `GET /api/courses/{course_id}/sources/{kind}/{source_id}`

- [ ] **Step 1: Add app dependencies**

Create `app/api/requirements.txt`:

```text
fastapi>=0.115,<1
uvicorn>=0.30,<1
httpx>=0.27,<1
```

Do not add database, auth, ORM, AI SDK, or PDF packages.

- [ ] **Step 2: Write failing API contract tests**

Use `fastapi.testclient.TestClient` and set a test service before client creation. Assert:

```python
response = client.get("/api/library")
self.assertEqual(response.status_code, 200)
body = response.json()
self.assertEqual(body["courses"][0]["course_id"], "functional_analysis_course")
self.assertEqual(body["courses"][0]["name_zh"], "泛函分析：分析学进一步专题导论")
```

Assert Course counts 8/132, `ch01_s01` opens, and all four mode endpoints return matching:

```python
course_id == "functional_analysis_course"
book_id == "stein_shakarchi_functional_analysis_2011"
section_id == "ch01_s01"
```

Assert stable 404 bodies:

```json
{"error":{"code":"course_not_found","message":"课程不存在"}}
```

Assert no traceback string appears in user JSON.

- [ ] **Step 3: Run RED**

Run:

```bash
python -m unittest app_tests.test_api -v
```

Expected: FAIL because `app.api.main` does not exist.

- [ ] **Step 4: Implement FastAPI construction and exception mapping**

`app/api/main.py` must create the service from repository root, but expose an overridable dependency for tests:

```python
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_service = BookAppService(_REPOSITORY_ROOT)

def get_service() -> BookAppService:
    return _service
```

Route handlers use `Depends(get_service)` and response models from Task 2.

Map exceptions with explicit handlers:

```python
@app.exception_handler(AppNotFoundError)
async def app_not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": {"code": exc.code, "message": exc.user_message}})
```

Use 400 for invalid mode and 503 for App initialization/unavailable errors. Internal technical exceptions may be logged server-side but never sent as tracebacks.

- [ ] **Step 5: Add CORS only for local dev origins**

Allow only local Vite origins used by the documented dev setup:

```python
allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"]
```

Do not use `allow_origins=["*"]`.

- [ ] **Step 6: Run API + runtime tests and manual localhost smoke**

Run:

```bash
python -m unittest app_tests.test_api app_tests.test_app_service tests.test_source_resolver -v
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

From another shell:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/library
```

Expected: JSON success; service binds only localhost.

- [ ] **Step 7: Commit**

```bash
git add app/api app_tests/test_api.py
git commit -m "feat: expose Book App FastAPI"
```

---

### Task 4: Scaffold the React/TypeScript/Vite PWA and API client

**Files:**
- Create: `app/web/**` Vite React TypeScript base files
- Create: `app/web/src/api/types.ts`
- Create: `app/web/src/api/client.ts`
- Create: `app/web/src/routes/router.tsx`
- Create: `app/web/src/app.tsx`
- Create: `app/web/src/components/AppShell.tsx`
- Create: `app/web/src/styles.css`

**Interfaces:**
- Consumes the exact API routes/DTO fields from Task 3.
- Produces typed `bookApi` methods:
  - `getLibrary()`
  - `getCourse(courseId)`
  - `getChapter(courseId, chapterId)`
  - `getSection(courseId, sectionId)`
  - `getMode(courseId, sectionId, mode)`
  - `getSource(courseId, kind, sourceId)`
- Produces route tree for `/`, course, chapter, section, and course-scoped source routes.

- [ ] **Step 1: Create the Vite React TypeScript app and lock dependencies**

From repository root:

```bash
npm create vite@latest app/web -- --template react-ts
cd app/web
npm install
npm install react-router-dom
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event vite-plugin-pwa @playwright/test
```

Commit `package-lock.json`. Do not use an uncommitted globally installed package.

- [ ] **Step 2: Configure scripts and test environment**

Ensure `package.json` includes:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "typecheck": "tsc -b --pretty false",
    "test": "vitest run",
    "test:watch": "vitest",
    "e2e": "playwright test"
  }
}
```

Configure Vitest with `environment: "jsdom"` and a setup file importing `@testing-library/jest-dom/vitest`.

- [ ] **Step 3: Configure local API proxy and PWA metadata**

In `vite.config.ts`, proxy only `/api` to `http://127.0.0.1:8000` in dev. Configure `VitePWA` with a Chinese app name such as `Book 学习` and `registerType: "autoUpdate"`.

Do not cache `/api` responses as permanent textbook state in Phase 1D.

- [ ] **Step 4: Define API types exactly once**

`src/api/types.ts` mirrors Task 2 DTOs. Define:

```ts
export type LearningMode = 'preview' | 'learn' | 'review' | 'practice'
```

`SourceResponse.source_anchor` and `content_zh` are nullable.

- [ ] **Step 5: Write API client unit tests before implementation**

Mock `global.fetch` and assert a call like:

```ts
await bookApi.getMode('functional_analysis_course', 'ch01_s01', 'learn')
expect(fetch).toHaveBeenCalledWith('/api/courses/functional_analysis_course/sections/ch01_s01/learn', expect.anything())
```

Also verify a non-2xx response throws `ApiError` whose user message comes from `error.message`, falling back to `请求失败，请稍后重试`.

- [ ] **Step 6: Run RED, implement client, run GREEN**

Run:

```bash
cd app/web
npm test -- src/api/client.test.ts
```

Expected RED: client missing.

Implement one generic `request<T>()` and the six typed `bookApi` methods; then rerun and expect PASS.

- [ ] **Step 7: Add route skeleton and build**

Create routes exactly:

```text
/
/courses/:courseId
/courses/:courseId/chapters/:chapterId
/courses/:courseId/sections/:sectionId
/courses/:courseId/sources/:kind/:sourceId
```

Section mode stays in query string, not path.

Run:

```bash
npm run typecheck
npm run build
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add app/web
git commit -m "feat: scaffold Book React PWA"
```

---

### Task 5: Implement Library, Course, and Chapter navigation pages

**Files:**
- Create: `app/web/src/pages/LibraryPage.tsx`
- Create: `app/web/src/pages/LibraryPage.test.tsx`
- Create: `app/web/src/pages/CoursePage.tsx`
- Create: `app/web/src/pages/CoursePage.test.tsx`
- Create: `app/web/src/pages/ChapterPage.tsx`
- Create: `app/web/src/pages/ChapterPage.test.tsx`
- Modify: `app/web/src/routes/router.tsx`
- Modify: `app/web/src/styles.css`

**Interfaces:**
- Consumes: `bookApi.getLibrary/getCourse/getChapter`.
- Produces visible navigation links to exact route identities.

- [ ] **Step 1: Write failing Library page test**

Mock API response with the real course identity and assert visible Chinese text:

```ts
expect(await screen.findByText('泛函分析：分析学进一步专题导论')).toBeInTheDocument()
expect(screen.getByText('8 章 · 132 节')).toBeInTheDocument()
expect(screen.getByRole('link', { name: '进入课程' })).toHaveAttribute(
  'href',
  '/courses/functional_analysis_course',
)
```

- [ ] **Step 2: Write failing Course and Chapter page tests**

Course page must render chapter list in API order and links to Sections. Chapter page must show Chinese title first, English second, Section count, page range, and `进入本节` links.

No search box may pretend to work; if a visual placeholder is retained, mark it disabled with Chinese copy `搜索将在后续阶段开放`.

- [ ] **Step 3: Run RED**

```bash
cd app/web
npm test -- src/pages/LibraryPage.test.tsx src/pages/CoursePage.test.tsx src/pages/ChapterPage.test.tsx
```

Expected: FAIL because pages are placeholders/missing.

- [ ] **Step 4: Implement pages with loading/error states**

Every page handles:

```text
正在加载…
加载失败
返回书架 / 返回课程
```

Do not render raw exception stacks.

Course page may use collapsible Chapter groups, but Chapter title and direct Section links must remain keyboard-accessible buttons/links.

- [ ] **Step 5: Add basic responsive CSS and run GREEN**

Use a readable centered content column, course cards, and a drawer-ready shell. Do not keep a permanent wide sidebar.

Run:

```bash
npm test -- src/pages/LibraryPage.test.tsx src/pages/CoursePage.test.tsx src/pages/ChapterPage.test.tsx
npm run typecheck
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/web/src/pages app/web/src/routes/router.tsx app/web/src/styles.css
git commit -m "feat: add textbook navigation pages"
```

---

### Task 6: Implement the Chinese-first Section four-mode UI

**Files:**
- Create: `app/web/src/components/ModeTabs.tsx`
- Create: `app/web/src/components/LearningObjectCard.tsx`
- Create: `app/web/src/components/EmptyState.tsx`
- Create: `app/web/src/components/SourceLink.tsx`
- Create: `app/web/src/pages/SectionPage.tsx`
- Create: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/styles.css`

**Interfaces:**
- Consumes: `bookApi.getSection()`, `bookApi.getMode()`, `bookApi.getSource()` only when a rendered item needs detail.
- Produces query-normalized Section route where missing/invalid `mode` becomes exactly `?mode=learn`.

- [ ] **Step 1: Write failing default-mode and free-switching tests**

Starting route:

```text
/courses/functional_analysis_course/sections/ch01_s01
```

must normalize to:

```text
/courses/functional_analysis_course/sections/ch01_s01?mode=learn
```

Test all four tabs remain enabled and clicking them changes only `mode`, never blocks on completion state.

- [ ] **Step 2: Write failing Chinese rendering tests**

For a source-backed item, assert:

```ts
expect(screen.getByText('定义')).toBeInTheDocument()
expect(screen.getByText('L^p 空间')).toBeInTheDocument()
```

When `content_zh === null`, assert exact fallback:

```text
本段中文学习内容暂未提供
```

If formula exists, it must still render. Do not replace missing content with English body.

- [ ] **Step 3: Write failing review/practice empty-state tests**

Review empty state:

```text
本节暂无可复习的教材核心对象
```

Practice empty state:

```text
本节暂无教材练习或习题
```

Both are normal successful states.

- [ ] **Step 4: Run RED**

```bash
cd app/web
npm test -- src/pages/SectionPage.test.tsx
```

Expected: FAIL.

- [ ] **Step 5: Implement mode rendering**

Rules:

- Preview: show real object-type counts and source-backed compact entries; no generated objectives.
- Learn: render source-backed objects/figures/translation availability in runtime order; resolve visible object detail through API.
- Review: only runtime-provided review items; content initially hidden behind `显示内容`.
- Practice: only runtime-provided exercise/problem items; when no explanation exists show `教材数据中暂未提供解析`.

`SourceLink` builds exactly:

```ts
`/courses/${courseId}/sources/${kind}/${sourceId}`
```

- [ ] **Step 6: Add responsive four-tab behavior**

On narrow screens, keep all four tabs accessible in one horizontally scrollable/tab row. Ensure keyboard focus style is visible and text does not overlap.

- [ ] **Step 7: Run GREEN and commit**

```bash
npm test -- src/pages/SectionPage.test.tsx
npm run typecheck
npm run build
```

Expected: PASS.

Commit:

```bash
git add app/web/src/components app/web/src/pages/SectionPage.tsx app/web/src/pages/SectionPage.test.tsx app/web/src/styles.css
git commit -m "feat: add four-mode Section learning UI"
```

---

### Task 7: Implement structured source page and return-state restoration

**Files:**
- Create: `app/web/src/state/sectionViewState.ts`
- Create: `app/web/src/state/sectionViewState.test.ts`
- Create: `app/web/src/pages/SourcePage.tsx`
- Create: `app/web/src/pages/SourcePage.test.tsx`
- Modify: `app/web/src/components/SourceLink.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/routes/router.tsx`

**Interfaces:**
- Produces:

```ts
export interface SectionViewState {
  route: string
  scrollY: number
  expandedSourceIds: string[]
  activeSourceId: string | null
}

export function stateKey(courseId: string, sectionId: string, mode: LearningMode): string
export function saveSectionViewState(...): void
export function loadSectionViewState(...): SectionViewState | null
export function clearSectionViewState(...): void
```

- `SourceLink` saves current state before navigation.
- `SourcePage` explicit `返回学习` uses saved `route` when present; otherwise falls back to the source's Section learn route.

- [ ] **Step 1: Write failing storage tests**

Use jsdom `sessionStorage` and assert round-trip:

```ts
saveSectionViewState('functional_analysis_course', 'ch01_s01', 'learn', {
  route: '/courses/functional_analysis_course/sections/ch01_s01?mode=learn',
  scrollY: 2460,
  expandedSourceIds: ['def_lp'],
  activeSourceId: 'def_lp',
})
expect(loadSectionViewState(...)).toEqual(...)
```

Corrupt JSON must return `null` and remove the corrupt entry rather than crash the App.

- [ ] **Step 2: Write failing source-page tests**

Assert page shows:

```text
教材来源
教材页：2
PDF 页：21
教材锚点暂未提供   # when source_anchor is null
结构化来源：object:def_lp
返回学习
```

For a fixture API response with a real non-null anchor, assert that exact anchor text is displayed unchanged.

Also render context-before/current/context-after and visually/semantically mark current target with `aria-current="true"` or an equivalent accessible current marker.

- [ ] **Step 3: Write failing return-state tests**

Test that clicking source from Section saves mode/expanded state, and clicking explicit `返回学习` navigates back to the exact saved route.

Mock `window.scrollTo` and assert the Section page restores stored `scrollY` after content load.

- [ ] **Step 4: Run RED**

```bash
cd app/web
npm test -- src/state/sectionViewState.test.ts src/pages/SourcePage.test.tsx src/pages/SectionPage.test.tsx
```

Expected: FAIL.

- [ ] **Step 5: Implement storage helpers and source page**

Use a namespaced storage key:

```ts
book:section-view:${courseId}:${sectionId}:${mode}
```

Do not use localStorage for Phase 1D progress. Do not store textbook content blobs in browser storage.

- [ ] **Step 6: Restore scroll/expanded state only after Section data renders**

Implement a single restore effect keyed by `courseId`, `sectionId`, `mode`, and successful content load. Call `window.scrollTo({ top: saved.scrollY, behavior: 'auto' })` once per restoration.

Browser Back remains functional through React Router history; explicit `返回学习` is the primary tested path.

- [ ] **Step 7: Run GREEN and commit**

```bash
npm test -- src/state/sectionViewState.test.ts src/pages/SourcePage.test.tsx src/pages/SectionPage.test.tsx
npm run typecheck
```

Expected: PASS.

Commit:

```bash
git add app/web/src/state app/web/src/pages/SourcePage* app/web/src/pages/SectionPage* app/web/src/components/SourceLink.tsx app/web/src/routes/router.tsx
git commit -m "feat: add source navigation state restoration"
```

---

### Task 8: Add real Functional Analysis app acceptance and CI

**Files:**
- Create: `app/web/playwright.config.ts`
- Create: `app/web/e2e/functional-analysis.spec.ts`
- Create: `.github/workflows/app-ui-tests.yml`
- Modify: `.github/workflows/runtime-reference-tests.yml` only if path filters need app-runtime coupling coverage

**Interfaces:**
- Consumes the real repository `library/library.json`, real Functional Analysis runtime, FastAPI, and built React UI.
- Produces a repeatable CI smoke proving the user-visible path.

- [ ] **Step 1: Write the failing Playwright smoke before CI wiring**

The test must use the real application, not mocked API responses. Required flow:

```ts
await page.goto('/')
await page.getByText('泛函分析：分析学进一步专题导论').click()
// enter Chapter 1
// enter ch01_s01
await expect(page).toHaveURL(/ch01_s01\?mode=learn/)
// open a real source-backed object, e.g. def_lp if exposed by the API
// verify source URL contains /courses/functional_analysis_course/sources/object/
// verify real printed/PDF page values are shown
// click 返回学习 and verify learn route restored
// switch 复习 and 刷题 without lock errors
```

If `ch01_s01` has no non-null `source_anchor`, assert `教材锚点暂未提供` rather than modifying textbook data. This smoke proves source truth, not anchor fabrication.

- [ ] **Step 2: Configure Playwright**

Use Chromium only. Base URL is `http://127.0.0.1:5173`. Capture screenshot/trace only on failure.

Install browser locally for test:

```bash
cd app/web
npx playwright install chromium
```

- [ ] **Step 3: Run local real smoke**

Shell A:

```bash
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Shell B:

```bash
cd app/web
npm run dev -- --host 127.0.0.1 --port 5173
```

Shell C:

```bash
cd app/web
npm run e2e
```

Expected: PASS using real `functional_analysis_course` and `ch01_s01`.

- [ ] **Step 4: Add `app-ui-tests.yml`**

Workflow triggers on:

```text
app/**
runtime/source_resolver.py
runtime/__init__.py
library/**
courses/**
books/functional-analysis/**
app_tests/**
tests/test_source_resolver.py
.github/workflows/app-ui-tests.yml
```

Use Python 3.13 + Node 22. Steps:

```bash
python -m pip install -r app/api/requirements.txt
python -m unittest app_tests.test_app_service app_tests.test_api tests.test_source_resolver -v
cd app/web && npm ci
npm run typecheck
npm test
npm run build
npx playwright install --with-deps chromium
```

Then start API and Vite on localhost, wait for `/api/health` and `/`, and run `npm run e2e`.

Do not replace the existing runtime-reference workflow; both gates must pass.

- [ ] **Step 5: Verify both workflows locally as far as possible**

Run Python suites:

```bash
python -m unittest tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime tests.test_section_learning_runtime tests.test_source_resolver app_tests.test_app_service app_tests.test_api -v
```

Run web suites:

```bash
cd app/web
npm run typecheck
npm test
npm run build
```

Then run the Playwright smoke with real local servers.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/app-ui-tests.yml app/web/playwright.config.ts app/web/e2e
git commit -m "ci: gate Book App Phase 1D"
```

---

### Task 9: Update product docs and developer startup instructions

**Files:**
- Create: `app/README.md`
- Modify: `README.md`
- Modify: `docs/ROADMAP.md`

**Interfaces:**
- Documents the final supported startup/verification path only; no new runtime behavior.

- [ ] **Step 1: Write `app/README.md` with exact local commands**

Document Python environment setup:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pip install -r app/api/requirements.txt
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Document web setup:

```bash
cd app/web
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

State clearly that the first release is personal/local, has no login/cloud sync, and the structured textbook view is primary; PDF is not required.

- [ ] **Step 2: Update root README current-state diagram**

Extend current architecture to:

```text
React / PWA
    ↓
FastAPI BookAppService
    ↓
LibraryRuntime → CourseRuntime → BookRuntime → SectionLearningRuntime / SourceResolver
```

Mark Phase 1D as UI foundation only; do not claim AI Q&A, full StudyRecord, Chapter Hub, or PDF viewer are complete.

- [ ] **Step 3: Clarify ROADMAP naming**

Add a current-status note near Phase 1 explaining that the implementation branch's “Phase 1D UI foundation” is the software-shell milestone described by the new spec, while older 1D–1K feature labels remain future functional work. Mark only capabilities actually passing acceptance as done.

- [ ] **Step 4: Run final doc/startup sanity commands**

```bash
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
cd app/web && npm run build
```

Open the documented URLs and verify commands are copy-paste correct.

- [ ] **Step 5: Commit**

```bash
git add README.md app/README.md docs/ROADMAP.md
git commit -m "docs: document local Book App MVP"
```

---

### Task 10: Final Phase 1D verification and integration readiness

**Files:**
- No feature code unless verification exposes a defect.
- Potentially modify tests/code only to fix failures found here; each fix gets its own focused commit.

**Interfaces:**
- Produces final evidence for PR review.

- [ ] **Step 1: Run the complete existing runtime reference suite**

Run the exact explicit modules currently gated by CI, plus `tests.test_source_resolver`.

Expected: PASS on supported Python versions in GitHub Actions; no Phase 1A–1C regression.

- [ ] **Step 2: Run all Phase 1D API tests**

```bash
python -m unittest app_tests.test_app_service app_tests.test_api tests.test_source_resolver -v
```

Expected: PASS.

- [ ] **Step 3: Run all frontend checks**

```bash
cd app/web
npm ci
npm run typecheck
npm test
npm run build
```

Expected: PASS.

- [ ] **Step 4: Run the real Functional Analysis Playwright smoke**

Use the real API and UI servers. Expected user path:

```text
书架
→ 泛函分析
→ Chapter 1
→ ch01_s01
→ 学习
→ 真实教材对象
→ 结构化来源
→ 返回并恢复学习模式/位置
→ 复习
→ 刷题
```

Confirm the source ref returned by API matches the runtime source ID displayed/opened by the UI.

- [ ] **Step 5: Verify no out-of-scope behavior slipped in**

Review changed files and confirm there is no:

```text
AI-generated textbook prose
fake source anchors
fake answer/explanation generation
account/auth layer
cloud persistence
PDF reader
lecture recording
Chapter Hub implementation
permanent StudyRecord DB
```

- [ ] **Step 6: Verify branch diff and CI**

Compare `feature/book-app-ui-phase-1d` against `main` and verify only expected runtime resolver, App/API/web/tests/docs/CI files changed. Confirm both:

```text
Runtime reference tests = success
App UI tests = success
```

- [ ] **Step 7: Prepare PR but do not merge without explicit approval**

Suggested title:

```text
Add local Chinese-first Book App UI foundation
```

Suggested PR summary must report:

- local React/Vite PWA + FastAPI shell;
- Chinese-first Library/Course/Chapter/Section navigation;
- source-backed Preview/Learn/Review/Practice;
- structured source navigation + session return restoration;
- real Functional Analysis `ch01_s01` smoke;
- existing runtime readiness remains green;
- no PDF reader/AI/cloud/account functionality added.

Do not merge the PR until the user explicitly approves integration.
