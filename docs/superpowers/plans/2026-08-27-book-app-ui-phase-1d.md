# Book App Phase 1D Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first Chinese-first Book App MVP that exposes the existing runtime through FastAPI and a React/Vite PWA, supports Library → Course → Chapter → Section navigation, all four source-backed learning modes, structured source viewing, and lossless return-state restoration.

**Architecture:** Keep textbook parsing and truth in the Python runtime. Add one focused source-resolution layer, a thin FastAPI application/service layer that converts runtime objects to stable DTOs, and a React/TypeScript client that only consumes those DTOs. Route identity lives in the URL; ephemeral Section view state lives in `sessionStorage`. No account, cloud sync, AI generation, or PDF reader is introduced.

**Tech Stack:** Python 3.11–3.13; FastAPI + Uvicorn + HTTPX TestClient; React + TypeScript + Vite; React Router; Vitest + Testing Library; Vite PWA plugin; Playwright Chromium; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-book-app-ui-phase-1d-design.md`

## Global Constraints

- First release is local-first; browser/PWA talks to FastAPI on the same machine.
- Documented FastAPI startup binds exactly to `127.0.0.1` by default.
- All user-visible navigation, labels, statuses, empty states, and errors are Chinese.
- Chinese learning content is preferred; English is secondary evidence only.
- First terminology occurrence may show `中文（English term）`; normal repeated UI uses Chinese.
- Current App/Library product profile remains one enabled main textbook per course.
- React never reads `books/`, `courses/`, `library/`, JSON, CSV, Markdown, or chunk files directly.
- FastAPI routes never read textbook files directly; they call a Python service, which calls runtime APIs.
- Missing textbook content stays missing. Never invent anchors, translations, answers, explanations, or AI-generated textbook prose.
- `source_anchor` is nullable. Missing anchor renders `教材锚点暂未提供`; stable source identity remains `kind + source_id`.
- Section default mode is exactly `learn`.
- Valid modes are exactly `preview`, `learn`, `review`, `practice`.
- Empty `review` and `practice` payloads are valid HTTP 200 states.
- Source route is course-scoped: `/courses/:courseId/sources/:kind/:sourceId`.
- `sessionStorage` restores current-session/reload UI state only; it is not permanent StudyRecord storage.
- Phase 1A–1C runtime readiness gates remain green.
- Phase 1D does not implement AI Q&A/generation, account/cloud sync, PDF reader, lecture recording, Chapter Hub, mistake DB, full StudyRecord, Windows packaging, or native mobile apps.

---

## Planned File Structure

```text
runtime/
├── source_resolver.py
└── __init__.py

tests/
├── runtime_fixture_factory.py
└── test_source_resolver.py

app/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── service.py
│   ├── errors.py
│   └── requirements.txt
└── web/
    ├── package.json
    ├── package-lock.json
    ├── vite.config.ts
    ├── playwright.config.ts
    ├── e2e/
    │   └── functional-analysis.spec.ts
    └── src/
        ├── main.tsx
        ├── app.tsx
        ├── styles.css
        ├── api/
        │   ├── client.ts
        │   ├── client.test.ts
        │   └── types.ts
        ├── routes/router.tsx
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
├── test_app_service.py
└── test_api.py

.github/workflows/
├── runtime-reference-tests.yml
└── app-ui-tests.yml

README.md
app/README.md
docs/ROADMAP.md
```

`runtime/source_resolver.py` owns source truth resolution. `app/api/service.py` owns runtime→DTO projection. FastAPI owns HTTP only. React owns presentation and ephemeral browser state.

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

```python
TYPE_LABELS_ZH: dict[str, str]
class SourceResolutionError(RuntimeError): ...
@dataclass(frozen=True)
class ResolvedSource: ...
class SourceResolver:
    def __init__(self, course: CourseRuntime): ...
    def resolve(self, kind: str, source_id: str) -> ResolvedSource: ...
```

Supported kinds: `object`, `figure`, `translation`.

- [ ] **Step 1: Write failing resolver tests**

Use existing fixture helpers with this object:

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

Assert:

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

Also assert unknown kind/source raises `SourceResolutionError`, and missing `content_zh`/`source_anchor` remain `None`.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_source_resolver -v
```

Expected: import failure for `runtime.source_resolver`.

- [ ] **Step 3: Implement resolver contract**

Use:

```python
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
    "translation": "中文学习层",
}
```

`ResolvedSource` fields:

```python
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
```

For object `content_zh`, read only explicit raw keys in order:

```python
("content_zh", "statement_zh", "description_zh", "summary_zh", "text_zh")
```

Do not heuristically slice batch Markdown into object prose. If object prose is absent but its batch has Chinese translation, set `translation_available=True` and keep `content_zh=None`.

Context contains at most two preceding/two following structural items from the same owning Section, preserving runtime order:

```python
{"kind": "object", "source_id": obj.id, "type": obj.type, "number": obj.number, "title_zh": obj.name_zh}
```

For figure `section_id`, deterministically choose the narrowest RuntimeSection covering its real PDF page; if none, keep `None`.

For translation kind, resolve exact `RuntimeBatch.id`, return its full translation Markdown as `content_zh`, and pass through real batch page ranges. Never use translation text as if it were exact prose for a different object.

- [ ] **Step 4: Export resolver and run GREEN**

Export `ResolvedSource`, `SourceResolutionError`, `SourceResolver`, `TYPE_LABELS_ZH` from `runtime/__init__.py`.

Run:

```bash
python -m unittest tests.test_source_resolver tests.test_section_learning_runtime tests.test_book_runtime tests.test_course_runtime tests.test_library_runtime -v
```

Expected: PASS.

- [ ] **Step 5: Extend runtime CI and commit**

Compile `runtime/source_resolver.py` and add `tests.test_source_resolver` to the explicit unittest list.

```bash
git add runtime/source_resolver.py runtime/__init__.py tests/runtime_fixture_factory.py tests/test_source_resolver.py .github/workflows/runtime-reference-tests.yml
git commit -m "feat: add source-backed textbook resolver"
```

---

### Task 2: Add stable App DTOs and `BookAppService`

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

```python
LearningMode = Literal["preview", "learn", "review", "practice"]
class BookAppService:
    def __init__(self, repository_root: Path): ...
    def library(self) -> LibraryResponse: ...
    def course(self, course_id: str) -> CourseResponse: ...
    def chapter(self, course_id: str, chapter_id: str) -> ChapterResponse: ...
    def section(self, course_id: str, section_id: str) -> SectionResponse: ...
    def mode(self, course_id: str, section_id: str, mode: LearningMode) -> ModeResponse: ...
    def source(self, course_id: str, kind: str, source_id: str) -> SourceResponse: ...
```

- [ ] **Step 1: Write failing real-library service tests**

Use repository root `Path(__file__).resolve().parents[1]` and assert:

```python
service = BookAppService(REPO_ROOT)
library = service.library()
self.assertEqual(len(library.courses), 1)
card = library.courses[0]
self.assertEqual(card.course_id, "functional_analysis_course")
self.assertEqual(card.name_zh, "泛函分析：分析学进一步专题导论")
self.assertEqual(card.chapter_count, 8)
self.assertEqual(card.section_count, 132)
```

Assert `ch01_s01` opens and its page bounds are real.

- [ ] **Step 2: Run RED**

```bash
python -m unittest app_tests.test_app_service -v
```

Expected: missing `app.api.service`/models.

- [ ] **Step 3: Implement Pydantic DTOs**

Define exact names:

```python
CourseCard
LibraryResponse
SectionCard
ChapterCard
CourseResponse
ChapterResponse
SectionResponse
ModeItem
SourceRef
ModeResponse
SourceContextItem
SourceResponse
```

`CourseCard` fields:

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

`SectionCard` fields:

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

`ModeItem` is an enriched source summary, not only a raw ref:

```python
kind: str
source_id: str
object_type: str | None
type_zh: str | None
number: str | None
title_zh: str | None
title_en: str | None
formula: str | None
printed_page: int | str | None
pdf_page: int | None
content_zh: str | None
translation_available: bool
```

`ModeResponse` preserves `source_refs` exactly as runtime emits them and keeps item order identical to `SectionLearningRuntime`.

- [ ] **Step 4: Implement service projection**

`BookAppService.__init__` opens `<root>/library` and converts runtime load failures into `AppUnavailableError`.

Derive the Chinese product name from `course.main_book().metadata["title_zh"]`; never machine-translate `course.name`.

For `mode()`, dispatch using an explicit map only:

```python
mode_fn = {
    "preview": learning.preview,
    "learn": learning.learn,
    "review": learning.review,
    "practice": learning.practice,
}[mode]
```

Enrich each mode item with `SourceResolver.resolve(kind, source_id)` while preserving original order. If a source ref cannot resolve, treat it as an App/runtime integrity error; do not silently drop it.

Unknown course/chapter/section/source raises `AppNotFoundError(code=..., user_message=...)`. Invalid mode raises `InvalidModeError`.

- [ ] **Step 5: Add empty/error tests**

Assert stable errors for missing course/chapter/section/source and valid empty `review`/`practice` payloads on a fixture Section with no matching objects.

- [ ] **Step 6: Run GREEN and commit**

```bash
python -m unittest app_tests.test_app_service tests.test_source_resolver -v
git add app app_tests
git commit -m "feat: add Book App runtime service"
```

---

### Task 3: Expose `BookAppService` through FastAPI

**Files:**
- Create: `app/api/main.py`
- Create: `app/api/requirements.txt`
- Create: `app_tests/test_api.py`

**Interfaces:**
- Routes:

```text
GET /api/health
GET /api/library
GET /api/courses/{course_id}
GET /api/courses/{course_id}/chapters/{chapter_id}
GET /api/courses/{course_id}/sections/{section_id}
GET /api/courses/{course_id}/sections/{section_id}/preview
GET /api/courses/{course_id}/sections/{section_id}/learn
GET /api/courses/{course_id}/sections/{section_id}/review
GET /api/courses/{course_id}/sections/{section_id}/practice
GET /api/courses/{course_id}/sources/{kind}/{source_id}
```

- [ ] **Step 1: Add minimal dependencies**

`app/api/requirements.txt`:

```text
fastapi>=0.115,<1
uvicorn>=0.30,<1
httpx>=0.27,<1
```

No database/auth/AI/PDF packages.

- [ ] **Step 2: Write failing API tests**

Use `TestClient` and FastAPI dependency override. Assert `/api/library` returns the real Chinese name; Course returns 8 Chapters/132 Sections; `ch01_s01` opens; four mode identities match:

```python
course_id == "functional_analysis_course"
book_id == "stein_shakarchi_functional_analysis_2011"
section_id == "ch01_s01"
```

Assert stable error JSON:

```json
{"error":{"code":"course_not_found","message":"课程不存在"}}
```

No traceback text appears in client JSON.

- [ ] **Step 3: Run RED**

```bash
python -m unittest app_tests.test_api -v
```

Expected: missing FastAPI app.

- [ ] **Step 4: Implement lazy service dependency so import cannot crash**

Do **not** instantiate `BookAppService` at module import. Use cached lazy construction:

```python
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

@lru_cache(maxsize=1)
def default_service() -> BookAppService:
    return BookAppService(REPOSITORY_ROOT)

def get_service() -> BookAppService:
    return default_service()
```

If runtime/library initialization fails, `AppUnavailableError` propagates through the dependency and is mapped to HTTP 503 JSON. The module itself remains importable so `/api/health` can report unavailable state rather than terminating Python import.

For tests, override `get_service` with a fixture/real service as needed.

- [ ] **Step 5: Add explicit exception handlers and local CORS**

Map:

```text
AppNotFoundError → 404
InvalidModeError → 400
AppUnavailableError → 503
```

User body is always:

```json
{"error":{"code":"...","message":"中文消息"}}
```

Allow only:

```python
["http://127.0.0.1:5173", "http://localhost:5173"]
```

Never use wildcard CORS.

- [ ] **Step 6: Run GREEN and localhost smoke**

```bash
python -m unittest app_tests.test_api app_tests.test_app_service tests.test_source_resolver -v
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Then:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/library
```

Expected: valid JSON.

- [ ] **Step 7: Commit**

```bash
git add app/api app_tests/test_api.py
git commit -m "feat: expose Book App FastAPI"
```

---

### Task 4: Scaffold React/TypeScript/Vite PWA and typed API client

**Files:**
- Create: `app/web/**` base Vite React TypeScript files
- Create: `app/web/src/api/types.ts`
- Create: `app/web/src/api/client.ts`
- Create: `app/web/src/api/client.test.ts`
- Create: `app/web/src/routes/router.tsx`
- Create: `app/web/src/app.tsx`
- Create: `app/web/src/components/AppShell.tsx`
- Create: `app/web/src/styles.css`

**Interfaces:**

```ts
export type LearningMode = 'preview' | 'learn' | 'review' | 'practice'

bookApi.getLibrary()
bookApi.getCourse(courseId)
bookApi.getChapter(courseId, chapterId)
bookApi.getSection(courseId, sectionId)
bookApi.getMode(courseId, sectionId, mode)
bookApi.getSource(courseId, kind, sourceId)
```

- [ ] **Step 1: Scaffold and lock dependencies**

```bash
npm create vite@latest app/web -- --template react-ts
cd app/web
npm install
npm install react-router-dom
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event vite-plugin-pwa @playwright/test
```

Commit `package-lock.json`.

- [ ] **Step 2: Configure scripts and test environment**

Ensure scripts:

```json
{
  "dev": "vite",
  "build": "tsc -b && vite build",
  "typecheck": "tsc -b --pretty false",
  "test": "vitest run",
  "test:watch": "vitest",
  "e2e": "playwright test"
}
```

Vitest uses jsdom and imports `@testing-library/jest-dom/vitest` in setup.

- [ ] **Step 3: Configure local API proxy and PWA**

Proxy `/api` to `http://127.0.0.1:8000`. Configure PWA metadata with Chinese app name `Book 学习` and `registerType: "autoUpdate"`.

Do not persistently cache `/api` responses in Phase 1D.

- [ ] **Step 4: Define API types once**

Mirror Task 2 DTOs exactly. `SourceResponse.source_anchor` and `content_zh` are nullable.

- [ ] **Step 5: Write failing API-client tests**

Example:

```ts
await bookApi.getMode('functional_analysis_course', 'ch01_s01', 'learn')
expect(fetch).toHaveBeenCalledWith(
  '/api/courses/functional_analysis_course/sections/ch01_s01/learn',
  expect.anything(),
)
```

Non-2xx throws `ApiError`; use server `error.message`, otherwise `请求失败，请稍后重试`.

- [ ] **Step 6: Run RED, implement client, run GREEN**

```bash
npm test -- src/api/client.test.ts
```

Implement one generic `request<T>()` plus six typed methods; rerun to PASS.

- [ ] **Step 7: Add route skeleton and build**

Routes exactly:

```text
/
/courses/:courseId
/courses/:courseId/chapters/:chapterId
/courses/:courseId/sections/:sectionId
/courses/:courseId/sources/:kind/:sourceId
```

Section mode is query string.

```bash
npm run typecheck
npm run build
```

- [ ] **Step 8: Commit**

```bash
git add app/web
git commit -m "feat: scaffold Book React PWA"
```

---

### Task 5: Implement Library → Course → Chapter navigation

**Files:**
- Create: `app/web/src/pages/LibraryPage.tsx`
- Create: `app/web/src/pages/LibraryPage.test.tsx`
- Create: `app/web/src/pages/CoursePage.tsx`
- Create: `app/web/src/pages/CoursePage.test.tsx`
- Create: `app/web/src/pages/ChapterPage.tsx`
- Create: `app/web/src/pages/ChapterPage.test.tsx`
- Modify: `app/web/src/routes/router.tsx`
- Modify: `app/web/src/styles.css`

- [ ] **Step 1: Write failing Library test**

Assert:

```ts
expect(await screen.findByText('泛函分析：分析学进一步专题导论')).toBeInTheDocument()
expect(screen.getByText('8 章 · 132 节')).toBeInTheDocument()
expect(screen.getByRole('link', { name: '进入课程' })).toHaveAttribute(
  'href',
  '/courses/functional_analysis_course',
)
```

- [ ] **Step 2: Write failing Course/Chapter tests**

Course renders audited Chapter order and direct Section links. Chapter renders Chinese title first, English secondary, Section count, page ranges, and `进入本节` links.

If a search control is shown, it is disabled and labeled `搜索将在后续阶段开放`; no fake search behavior.

- [ ] **Step 3: Run RED**

```bash
npm test -- src/pages/LibraryPage.test.tsx src/pages/CoursePage.test.tsx src/pages/ChapterPage.test.tsx
```

- [ ] **Step 4: Implement loading/error/navigation UI**

All pages use Chinese loading/error states and never show raw stack traces. Keep main content wide; no permanent wide sidebar.

- [ ] **Step 5: Run GREEN and commit**

```bash
npm test -- src/pages/LibraryPage.test.tsx src/pages/CoursePage.test.tsx src/pages/ChapterPage.test.tsx
npm run typecheck
git add app/web/src/pages app/web/src/routes/router.tsx app/web/src/styles.css
git commit -m "feat: add textbook navigation pages"
```

---

### Task 6: Implement Chinese-first Section four-mode UI

**Files:**
- Create: `app/web/src/components/ModeTabs.tsx`
- Create: `app/web/src/components/LearningObjectCard.tsx`
- Create: `app/web/src/components/EmptyState.tsx`
- Create: `app/web/src/components/SourceLink.tsx`
- Create: `app/web/src/pages/SectionPage.tsx`
- Create: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/styles.css`

- [ ] **Step 1: Write failing default-mode/free-switching tests**

Starting at:

```text
/courses/functional_analysis_course/sections/ch01_s01
```

must normalize with router replace to:

```text
/courses/functional_analysis_course/sections/ch01_s01?mode=learn
```

All four tabs stay enabled; switching changes only `mode`.

- [ ] **Step 2: Write failing Chinese/fallback tests**

Assert `定义`, Chinese title, and formula render from `ModeItem`.

If `content_zh === null`, exact fallback is:

```text
本段中文学习内容暂未提供
```

Do not render English prose as default body.

- [ ] **Step 3: Write failing empty-state tests**

Review:

```text
本节暂无可复习的教材核心对象
```

Practice:

```text
本节暂无教材练习或习题
```

Both are normal success states.

- [ ] **Step 4: Run RED**

```bash
npm test -- src/pages/SectionPage.test.tsx
```

- [ ] **Step 5: Implement each mode from runtime payload only**

- Preview: real object-type counts + source-backed compact items; no generated objectives.
- Learn: render enriched `ModeItem`s in runtime order.
- Review: runtime review items only; body hidden until `显示内容`.
- Practice: runtime exercise/problem only; absent explanation shows `教材数据中暂未提供解析`.

`SourceLink` route:

```ts
`/courses/${courseId}/sources/${kind}/${sourceId}`
```

- [ ] **Step 6: Add responsive tab behavior**

At narrow widths, four tabs remain keyboard-accessible in a horizontally scrollable row. Content stays single-column.

- [ ] **Step 7: Run GREEN and commit**

```bash
npm test -- src/pages/SectionPage.test.tsx
npm run typecheck
npm run build
git add app/web/src/components app/web/src/pages/SectionPage* app/web/src/styles.css
git commit -m "feat: add four-mode Section learning UI"
```

---

### Task 7: Implement structured source page and session return-state restoration

**Files:**
- Create: `app/web/src/state/sectionViewState.ts`
- Create: `app/web/src/state/sectionViewState.test.ts`
- Create: `app/web/src/pages/SourcePage.tsx`
- Create: `app/web/src/pages/SourcePage.test.tsx`
- Modify: `app/web/src/components/SourceLink.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/routes/router.tsx`

**Interfaces:**

```ts
export interface SectionViewState {
  route: string
  scrollY: number
  expandedSourceIds: string[]
  activeSourceId: string | null
}

export function stateKey(courseId: string, sectionId: string, mode: LearningMode): string
export function saveSectionViewState(courseId: string, sectionId: string, mode: LearningMode, state: SectionViewState): void
export function loadSectionViewState(courseId: string, sectionId: string, mode: LearningMode): SectionViewState | null
export function clearSectionViewState(courseId: string, sectionId: string, mode: LearningMode): void
```

- [ ] **Step 1: Write failing storage tests**

Round-trip exact state through `sessionStorage`; corrupt JSON returns `null` and removes corrupt entry.

Namespace:

```text
book:section-view:${courseId}:${sectionId}:${mode}
```

- [ ] **Step 2: Write failing SourcePage tests**

Null anchor case must show:

```text
教材来源
教材页：2
PDF 页：21
教材锚点暂未提供
结构化来源：object:def_lp
返回学习
```

A fixture response with non-null `source_anchor` must display the exact anchor unchanged.

Render `context_before`, current source, `context_after`; mark current target accessibly with `aria-current="true"` or equivalent.

- [ ] **Step 3: Write failing return-state tests**

Clicking source from Section saves exact route, mode, scrollY, expanded IDs, and active source. Explicit `返回学习` navigates to saved route.

Mock `window.scrollTo` and assert saved scroll restores after Section content is loaded.

- [ ] **Step 4: Run RED**

```bash
npm test -- src/state/sectionViewState.test.ts src/pages/SourcePage.test.tsx src/pages/SectionPage.test.tsx
```

- [ ] **Step 5: Implement state helpers and source page**

Do not use `localStorage`. Do not store textbook content blobs. Browser Back remains functional; explicit `返回学习` is primary path.

If no saved route exists, SourcePage falls back to:

```text
/courses/{course_id}/sections/{section_id}?mode=learn
```

If `section_id` is absent, fallback is course page, not a fabricated Section route.

- [ ] **Step 6: Restore state after data render**

Use one restore effect keyed by `courseId`, `sectionId`, `mode`, and successful mode load. Restore scroll once with:

```ts
window.scrollTo({ top: saved.scrollY, behavior: 'auto' })
```

- [ ] **Step 7: Run GREEN and commit**

```bash
npm test -- src/state/sectionViewState.test.ts src/pages/SourcePage.test.tsx src/pages/SectionPage.test.tsx
npm run typecheck
git add app/web/src/state app/web/src/pages/SourcePage* app/web/src/pages/SectionPage* app/web/src/components/SourceLink.tsx app/web/src/routes/router.tsx
git commit -m "feat: restore Section state across source navigation"
```

---

### Task 8: Add real Functional Analysis browser acceptance and CI

**Files:**
- Create: `app/web/playwright.config.ts`
- Create: `app/web/e2e/functional-analysis.spec.ts`
- Create: `.github/workflows/app-ui-tests.yml`

- [ ] **Step 1: Write failing real desktop smoke**

Use real API/runtime, not mocks:

```text
书架
→ 泛函分析
→ Chapter 1
→ ch01_s01
→ 默认学习
→ 打开真实 source-backed object（优先 def_lp，如 API identity 不同则按真实 payload 选择第一个 object）
→ source URL 包含 /courses/functional_analysis_course/sources/object/
→ 显示真实教材页/PDF页
→ source_anchor 缺失则明确显示“教材锚点暂未提供”，不得改教材数据
→ 返回学习
→ mode=learn 恢复
→ 切换复习
→ 切换刷题
```

The test must assert the source ID in the URL equals the mode payload's real source ref.

- [ ] **Step 2: Add a real narrow-screen smoke**

Use Playwright viewport:

```ts
{ width: 390, height: 844 }
```

Open real `ch01_s01?mode=learn` and assert all four mode tabs are visible/reachable and the page has no horizontal body overflow caused by content cards. This is the required responsive browser check; do not rely on jsdom layout assertions.

- [ ] **Step 3: Configure Playwright**

Chromium only, base URL `http://127.0.0.1:5173`, screenshot/trace on failure.

```bash
cd app/web
npx playwright install chromium
```

- [ ] **Step 4: Run local real smoke**

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

Expected: desktop + narrow-screen tests PASS.

- [ ] **Step 5: Add `app-ui-tests.yml`**

Trigger on `app/**`, `runtime/source_resolver.py`, `runtime/__init__.py`, `library/**`, `courses/**`, Functional Analysis assets, `app_tests/**`, resolver tests, and workflow file.

Use Python 3.13 + Node 22. Run:

```bash
python -m pip install -r app/api/requirements.txt
python -m unittest app_tests.test_app_service app_tests.test_api tests.test_source_resolver -v
cd app/web
npm ci
npm run typecheck
npm test
npm run build
npx playwright install --with-deps chromium
```

Start localhost API + Vite, wait for `/api/health` and `/`, then `npm run e2e`.

Do not replace `runtime-reference-tests.yml`; both workflows are required.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/app-ui-tests.yml app/web/playwright.config.ts app/web/e2e
git commit -m "ci: gate Book App Phase 1D"
```

---

### Task 9: Update docs and exact local startup instructions

**Files:**
- Create: `app/README.md`
- Modify: `README.md`
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Document exact local API startup**

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pip install -r app/api/requirements.txt
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: Document web startup**

```bash
cd app/web
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

State: personal/local first release; no login/cloud sync; structured textbook view is primary; original PDF is not required.

- [ ] **Step 3: Update root README architecture**

```text
React / PWA
    ↓
FastAPI BookAppService
    ↓
LibraryRuntime → CourseRuntime → BookRuntime → SectionLearningRuntime / SourceResolver
```

Do not claim AI Q&A, full StudyRecord, Chapter Hub, or PDF viewer are complete.

- [ ] **Step 4: Clarify ROADMAP naming**

Add current-status note explaining that this Phase 1D is the UI-foundation milestone and does not mean all older 1D–1K feature rows are complete. Mark only passing capabilities as done.

- [ ] **Step 5: Run startup/build sanity and commit**

```bash
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
cd app/web && npm run build
```

Then:

```bash
git add README.md app/README.md docs/ROADMAP.md
git commit -m "docs: document local Book App MVP"
```

---

### Task 10: Final verification and PR readiness

**Files:**
- No planned feature files. Any defect found here gets its own focused fix + test commit.

- [ ] **Step 1: Run complete runtime gates**

Run the explicit runtime modules currently in `.github/workflows/runtime-reference-tests.yml`, including new `tests.test_source_resolver`.

Expected: PASS; no Phase 1A–1C regression.

- [ ] **Step 2: Run Phase 1D API tests**

```bash
python -m unittest app_tests.test_app_service app_tests.test_api tests.test_source_resolver -v
```

Expected: PASS.

- [ ] **Step 3: Run frontend checks**

```bash
cd app/web
npm ci
npm run typecheck
npm test
npm run build
```

Expected: PASS.

- [ ] **Step 4: Run desktop + narrow real Playwright smoke**

Expected real path:

```text
书架
→ 泛函分析
→ Chapter 1
→ ch01_s01
→ 学习
→ 真实教材对象
→ 结构化来源
→ 返回并恢复
→ 复习
→ 刷题
```

Confirm URL source ID matches runtime source ref.

- [ ] **Step 5: Check scope/authenticity**

Confirm diff contains no AI-generated textbook prose, fake anchor, fake answer/explanation, auth, cloud persistence, PDF reader, lecture recording, Chapter Hub, or permanent StudyRecord DB.

- [ ] **Step 6: Check branch diff and GitHub CI**

Compare feature branch against `main`. Required:

```text
Runtime reference tests = success
App UI tests = success
```

- [ ] **Step 7: Prepare PR, do not merge automatically**

Suggested title:

```text
Add local Chinese-first Book App UI foundation
```

PR summary reports local React/Vite PWA + FastAPI, Chinese-first textbook navigation, source-backed four modes, structured source navigation + session restoration, real `ch01_s01` smoke, and unchanged runtime readiness guarantees.

Do not merge until explicit user approval.

---

## Self-Review Result

- Spec coverage: Library/Course/Chapter/Section, Chinese-first four modes, source page, null-anchor truthfulness, return-state restoration, local FastAPI, PWA, API/UI tests, responsive check, real `ch01_s01` smoke, docs, and CI all map to explicit tasks.
- Placeholder scan: no `TBD`, no `TODO`, no “add appropriate handling”, and every test/implementation task has concrete commands and expected behavior.
- Type consistency: Python `LearningMode` and TypeScript `LearningMode` use the same four exact strings; course-scoped source route is identical in API/client/router/tests; nullable `source_anchor`/`content_zh` remain nullable through runtime→DTO→TypeScript.
- Initialization correction: FastAPI service construction is lazy, so runtime failure becomes HTTP 503 instead of import-time process failure.
- Responsive correction: real 390×844 Playwright coverage is required in addition to component tests.
