# Phase 1G StudyRecord Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add durable local-first StudyRecord persistence with a hidden stable profile UUID, independent preview/learn/review/practice progress, recent-learning lookup, explicit completion, and sync-ready metadata while preserving the existing textbook/source/search/QA behavior.

**Architecture:** Keep the existing React → FastAPI → BookAppService → canonical runtime path unchanged for textbook reads. Add a separate `app.study` layer: a portable path helper selects the local app-data directory, `StudyRecordRepository` owns SQLite schema/transactions/profile identity, and `StudyRecordService` validates course/section/mode against the existing BookAppService before writing. The browser talks only to explicit StudyRecord API routes; `sessionStorage` remains navigation-only state.

**Tech Stack:** Python 3.11–3.13 standard library (`sqlite3`, `uuid`, `pathlib`, `datetime`), FastAPI/Pydantic, React 19 + TypeScript + Vite, Vitest/Testing Library, Playwright Chromium, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-28-study-record-phase-1g-design.md`

## Global Constraints

- Implementation branch is `feature/study-record-phase-1g`; current reviewed baseline after governance sync is `8b184ba459b64a6928b1fc66b419f8cb3d9c8884` or a later explicitly reviewed descendant.
- Do not modify `books/functional-analysis/**` canonical textbook assets, PageMap, search indexes, source anchors, translations, or QA evidence merely to satisfy StudyRecord tests.
- SQLite is the durable local authority for Phase 1G StudyRecord data.
- UI remains single-user; there is no login, account picker, or user-facing profile management.
- Each installation creates one hidden stable UUID `profile_id`; never use a shared constant such as `local-default` as durable identity.
- Logical StudyRecord uniqueness is `(profile_id, course_id, section_id, mode)`.
- Supported modes are exactly `preview`, `learn`, `review`, `practice`; they are independent and do not unlock or complete each other.
- Missing row = never started. First touch = `status=in_progress`, `progress=0`. Explicit completion = `status=completed`, `progress=100`.
- Do not infer progress from scroll distance, dwell time, AI output, question count, or navigation behavior.
- Re-entering a completed mode updates activity timestamps/revision but keeps it completed.
- Phase 1G `sync_status` is always `local`; reserve `study_record_id`, `profile_id`, `revision`, `updated_at`, `deleted_at`, `sync_status`, but do not implement upload/download, SyncEvent, SyncEngine, Drive auth, cloud API, or conflict resolution.
- The browser never supplies or selects `profile_id` or `book_id`; the backend obtains both from trusted local state/runtime.
- A StudyRecord write failure must not make textbook content unavailable; SectionPage keeps rendering and surfaces a non-blocking retryable persistence error.
- Existing `sectionViewState`, `searchViewState`, and `qaSessionState` remain short-lived navigation/session state and must not become StudyRecord storage.
- No new third-party database dependency is required; use Python standard-library SQLite.
- Use parameterized SQL and explicit transactions for every mutation.
- Use UTC ISO-8601 timestamps consistently.
- All new Python tests use `unittest` to match the repository.
- Do not mark Phase 1G complete until full Runtime/App/Web/Chromium regression gates are green.

---

## File structure after Phase 1G

### Durable study layer

- Create `app/study/__init__.py` — export the small public StudyRecord surface.
- Create `app/study/paths.py` — portable app-data directory / SQLite path resolution with deterministic override.
- Create `app/study/repository.py` — schema initialization, hidden profile identity, SQLite CRUD, transactions, row mapping.
- Create `app/study/service.py` — canonical course/section/mode validation and repository error mapping.

### API boundary

- Modify `app/api/models.py` — stable StudyRecord response DTOs only; no browser-writable profile/book fields.
- Modify `app/api/main.py` — cached repository dependency plus touch/complete/list/recent routes.
- Keep `app/api/service.py` textbook behavior unchanged except additive helpers only if a test proves they are needed.

### Web boundary

- Modify `app/web/src/api/types.ts` — StudyRecord response types.
- Modify `app/web/src/api/client.ts` — typed touch/complete/list/recent calls.
- Modify `app/web/src/api/client.test.ts` — exact route/method tests.
- Modify `app/web/src/pages/SectionPage.tsx` — touch after successful mode load, completion control, non-blocking persistence failure/retry.
- Modify `app/web/src/pages/SectionPage.test.tsx` — interaction and failure-mode tests.
- Modify `app/web/src/styles.css` only for the small progress controls/error presentation.

### Tests / acceptance / docs

- Create `app_tests/test_study_repository.py`.
- Create `app_tests/test_study_service.py`.
- Create `app_tests/test_study_api.py`.
- Modify `app/web/e2e/functional-analysis.spec.ts`.
- Modify `.github/workflows/app-ui-tests.yml` to include deterministic StudyRecord API/browser execution.
- At completion, update `docs/DATA_MODEL.md`, `docs/ROADMAP.md`, `docs/CURRENT_STATE.md`, and `app/README.md`.

---

### Task 1: Add portable StudyRecord path resolution and deterministic schema initialization

**Files:**
- Create: `app/study/__init__.py`
- Create: `app/study/paths.py`
- Create: `app/study/repository.py`
- Create: `app_tests/test_study_repository.py`

**Interfaces:**
- Produces: `resolve_study_db_path(environ: Mapping[str, str] | None = None, home: Path | None = None) -> Path`
- Produces: `StudyRecordRepository(db_path: Path, *, now=None, uuid_factory=None)`
- Produces: `StudyRecordRepository.get_profile_id() -> str`
- Produces: immutable `StudyRecord` dataclass used by later service/API tasks.

- [ ] **Step 1: Write failing path/profile/schema tests**

Add tests equivalent to:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from uuid import UUID

from app.study.paths import resolve_study_db_path
from app.study.repository import StudyRecordRepository


class StudyRecordRepositoryTests(TestCase):
    def test_data_dir_override_is_deterministic(self) -> None:
        path = resolve_study_db_path(
            environ={"BOOK_APP_DATA_DIR": "/tmp/book-data"},
            home=Path("/ignored"),
        )
        self.assertEqual(path, Path("/tmp/book-data") / "book-app.sqlite3")

    def test_first_open_creates_one_stable_profile_uuid(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "study.sqlite3"
            first = StudyRecordRepository(db_path).get_profile_id()
            second = StudyRecordRepository(db_path).get_profile_id()
            self.assertEqual(first, second)
            self.assertEqual(str(UUID(first)), first)
```

Also assert the schema rejects invalid `mode`, invalid `status`, invalid `progress`, `revision < 1`, and duplicate `(profile_id, course_id, section_id, mode)` rows using direct fixture SQL.

- [ ] **Step 2: Run the repository test and verify it fails before implementation**

Run:

```bash
python -m unittest app_tests.test_study_repository -v
```

Expected: import/module failures because `app.study` does not exist yet.

- [ ] **Step 3: Implement `paths.py` using only standard library paths**

Use this precedence:

```python
def resolve_study_db_path(*, environ=None, home=None) -> Path:
    env = os.environ if environ is None else environ
    base_home = Path.home() if home is None else Path(home)
    override = str(env.get("BOOK_APP_DATA_DIR") or "").strip()
    if override:
        data_dir = Path(override).expanduser()
    elif os.name == "nt":
        data_dir = Path(env.get("LOCALAPPDATA") or (base_home / "AppData" / "Local")) / "BookApp"
    elif sys.platform == "darwin":
        data_dir = base_home / "Library" / "Application Support" / "BookApp"
    else:
        xdg = str(env.get("XDG_DATA_HOME") or "").strip()
        data_dir = (Path(xdg).expanduser() if xdg else base_home / ".local" / "share") / "BookApp"
    return data_dir / "book-app.sqlite3"
```

Do not create directories in `paths.py`; repository initialization owns filesystem mutation.

- [ ] **Step 4: Implement the minimal schema and stable profile identity**

`repository.py` must create parent directories and initialize tables in one explicit transaction. Use a singleton profile row and a StudyRecord table whose SQL constraints encode Phase 1G invariants:

```sql
CREATE TABLE IF NOT EXISTS app_profile (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    profile_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS study_records (
    study_record_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    book_id TEXT NOT NULL,
    section_id TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('preview','learn','review','practice')),
    status TEXT NOT NULL CHECK (status IN ('in_progress','completed')),
    progress INTEGER NOT NULL CHECK (progress IN (0,100)),
    started_at TEXT NOT NULL,
    last_studied_at TEXT NOT NULL,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    deleted_at TEXT,
    sync_status TEXT NOT NULL CHECK (sync_status = 'local'),
    UNIQUE (profile_id, course_id, section_id, mode)
);
```

On first initialization insert one UUID into `app_profile`; on later initialization validate the stored value with `UUID(profile_id)` and fail clearly if it is malformed rather than silently generating a second identity.

- [ ] **Step 5: Run the focused repository tests**

```bash
python -m unittest app_tests.test_study_repository -v
```

Expected: PASS for path override, schema creation, UUID stability, and SQL constraints.

- [ ] **Step 6: Commit the schema foundation**

```bash
git add app/study app_tests/test_study_repository.py
git commit -m "feat: add StudyRecord SQLite foundation"
```

---

### Task 2: Implement StudyRecord mutation/query semantics

**Files:**
- Modify: `app/study/repository.py`
- Modify: `app_tests/test_study_repository.py`

**Interfaces:**
- Produces: `get_record(course_id, section_id, mode) -> StudyRecord | None`
- Produces: `touch_record(course_id, book_id, section_id, mode) -> StudyRecord`
- Produces: `complete_record(course_id, book_id, section_id, mode) -> StudyRecord`
- Produces: `list_course_records(course_id) -> tuple[StudyRecord, ...]`
- Produces: `get_recent_record() -> StudyRecord | None`

- [ ] **Step 1: Add failing behavior tests**

Cover all of these as separate test methods:

```text
first touch -> one in_progress row, progress 0, revision 1
second touch -> same study_record_id, revision +1, started_at unchanged
complete after touch -> completed, progress 100, completed_at set
complete when already completed -> same logical row and no duplicate
re-enter completed via touch -> remains completed/100, activity timestamp advances
preview/learn/review/practice -> four independent rows
same mode in two sections -> two independent rows
recent -> highest last_studied_at wins
list_course_records -> only that course and deleted_at IS NULL
logical duplicate -> impossible for same profile
same course/section/mode with a different profile_id -> schema permits coexistence
```

Use an injected deterministic clock rather than `sleep()`:

```python
moments = iter([
    datetime(2026, 8, 28, 1, 0, tzinfo=timezone.utc),
    datetime(2026, 8, 28, 1, 1, tzinfo=timezone.utc),
])
repo = StudyRecordRepository(db_path, now=lambda: next(moments))
```

- [ ] **Step 2: Run tests and confirm the new behavior tests fail**

```bash
python -m unittest app_tests.test_study_repository -v
```

Expected: failures for missing CRUD methods.

- [ ] **Step 3: Implement row mapping and parameterized query helpers**

Define one immutable dataclass with all durable columns:

```python
@dataclass(frozen=True)
class StudyRecord:
    study_record_id: str
    profile_id: str
    course_id: str
    book_id: str
    section_id: str
    mode: str
    status: str
    progress: int
    started_at: str
    last_studied_at: str
    completed_at: str | None
    created_at: str
    updated_at: str
    revision: int
    deleted_at: str | None
    sync_status: str
```

Set `connection.row_factory = sqlite3.Row` and map columns explicitly; do not return raw SQLite rows beyond the repository.

- [ ] **Step 4: Implement `touch_record` as one transaction**

Use the current local profile. If absent, insert:

```text
status=in_progress
progress=0
revision=1
completed_at=NULL
sync_status=local
```

If present, update only activity fields and revision:

```sql
UPDATE study_records
SET last_studied_at = ?, updated_at = ?, revision = revision + 1
WHERE study_record_id = ?;
```

Do not reset `status`, `progress`, `completed_at`, or `started_at` when reopening a completed record.

- [ ] **Step 5: Implement `complete_record` idempotently**

The normal UI sequence touches before completion. For an existing in-progress row, update `status`, `progress`, `completed_at`, `last_studied_at`, `updated_at`, and increment revision. If the row is already completed, return it unchanged rather than generating revision churn from duplicate POST retries.

If a valid direct complete request reaches the repository before a touch, create one completed row in the same transaction with `started_at=completed_at=now`, `progress=100`, `revision=1`. This keeps the endpoint total/idempotent without creating a fake intermediate row.

- [ ] **Step 6: Implement course list and recent lookup**

Use non-deleted rows only:

```sql
SELECT * FROM study_records
WHERE profile_id = ? AND course_id = ? AND deleted_at IS NULL
ORDER BY last_studied_at DESC, updated_at DESC;
```

and:

```sql
SELECT * FROM study_records
WHERE profile_id = ? AND deleted_at IS NULL
ORDER BY last_studied_at DESC, updated_at DESC
LIMIT 1;
```

- [ ] **Step 7: Run focused tests**

```bash
python -m unittest app_tests.test_study_repository -v
```

Expected: all repository semantics PASS.

- [ ] **Step 8: Commit repository behavior**

```bash
git add app/study/repository.py app_tests/test_study_repository.py
git commit -m "feat: persist StudyRecord progress semantics"
```

---

### Task 3: Add canonical-validation StudyRecordService

**Files:**
- Create: `app/study/service.py`
- Modify: `app/study/__init__.py`
- Create: `app_tests/test_study_service.py`

**Interfaces:**
- Consumes: `BookAppService.section(course_id, section_id) -> SectionResponse`
- Consumes: repository CRUD from Task 2.
- Produces: `StudyRecordService.touch(course_id, section_id, mode)`
- Produces: `StudyRecordService.complete(course_id, section_id, mode)`
- Produces: `StudyRecordService.list_course(course_id)`
- Produces: `StudyRecordService.recent()`

- [ ] **Step 1: Write failing service tests with a temporary SQLite database**

Use the real Functional Analysis BookAppService for canonical validation and a temp repository. Verify:

```text
valid ch01_s01 + learn -> stored canonical book_id stein_shakarchi_functional_analysis_2011
unknown course -> AppNotFoundError(course_not_found), no row
unknown section -> AppNotFoundError(section_not_found), no row
invalid mode -> InvalidModeError(invalid_mode), no row
browser-equivalent caller never supplies book_id/profile_id
list_course validates the course before querying
repository failure maps to AppUnavailableError with stable study persistence code
```

- [ ] **Step 2: Run the service test and verify it fails**

```bash
python -m unittest app_tests.test_study_service -v
```

- [ ] **Step 3: Implement mode validation and canonical book derivation**

Keep the service small:

```python
VALID_STUDY_MODES = frozenset({"preview", "learn", "review", "practice"})

class StudyRecordService:
    def __init__(self, book_service: BookAppService, repository: StudyRecordRepository):
        self._book_service = book_service
        self._repository = repository

    def _canonical_context(self, course_id: str, section_id: str, mode: str):
        normalized = str(mode).strip().casefold()
        if normalized not in VALID_STUDY_MODES:
            raise InvalidModeError(
                code="invalid_mode",
                user_message="学习模式无效",
                detail=f"Unsupported learning mode: {mode!r}",
            )
        section = self._book_service.section(course_id, section_id)
        return section.book_id, normalized
```

`touch` and `complete` call `_canonical_context` and pass the trusted `book_id` into the repository. `list_course` calls `book_service.course(course_id)` first, then queries the repository. `recent` needs no textbook mutation and returns the durable recent row.

- [ ] **Step 4: Map repository exceptions to stable App errors**

Repository/storage/corrupt-profile errors must surface as `AppUnavailableError`, for example:

```python
raise AppUnavailableError(
    code="study_store_unavailable",
    user_message="学习进度暂无法保存",
    detail=str(exc),
) from exc
```

Do not expose filesystem paths or SQLite internals in the JSON response.

- [ ] **Step 5: Run service + existing App service tests**

```bash
python -m unittest app_tests.test_study_service app_tests.test_app_service -v
```

Expected: PASS with no change to textbook projections.

- [ ] **Step 6: Commit the application service boundary**

```bash
git add app/study app_tests/test_study_service.py
git commit -m "feat: add canonical StudyRecord service"
```

---

### Task 4: Expose minimal StudyRecord FastAPI contracts

**Files:**
- Modify: `app/api/models.py`
- Modify: `app/api/main.py`
- Create: `app_tests/test_study_api.py`

**Interfaces:**
- Produces routes:
  - `POST /api/courses/{course_id}/sections/{section_id}/study/{mode}/touch`
  - `POST /api/courses/{course_id}/sections/{section_id}/study/{mode}/complete`
  - `GET /api/courses/{course_id}/study-records`
  - `GET /api/study/recent`
- Browser request has no StudyRecord request body.

- [ ] **Step 1: Write failing API tests using dependency overrides**

Create a temp repository per test case and override both textbook and study dependencies. Verify exact JSON and status behavior:

```python
response = client.post(
    "/api/courses/functional_analysis_course/sections/ch01_s01/study/learn/touch"
)
self.assertEqual(response.status_code, 200)
self.assertEqual(response.json()["mode"], "learn")
self.assertEqual(response.json()["status"], "in_progress")
self.assertEqual(response.json()["progress"], 0)
self.assertNotIn("profile_id", response.json())
self.assertNotIn("sync_status", response.json())
```

Also cover complete, list, recent-null on fresh store, recent-after-touch, invalid mode 400, unknown course/section 404, and storage failure 503. Assert the API never accepts browser-provided `book_id` or `profile_id` because these POST routes have no body contract.

- [ ] **Step 2: Run and verify red**

```bash
python -m unittest app_tests.test_study_api -v
```

- [ ] **Step 3: Add response DTOs to `app/api/models.py`**

Use product-facing fields only:

```python
class StudyRecordResponse(BaseModel):
    course_id: str
    book_id: str
    section_id: str
    mode: LearningMode
    status: Literal["in_progress", "completed"]
    progress: Literal[0, 100]
    started_at: str
    last_studied_at: str
    completed_at: str | None
    updated_at: str

class StudyRecordListResponse(BaseModel):
    course_id: str
    records: list[StudyRecordResponse]
```

Do not expose `profile_id`, `sync_status`, `deleted_at`, or local DB path. Keep `study_record_id` and `revision` server-internal in Phase 1G unless a concrete client test later proves they are required.

- [ ] **Step 4: Add FastAPI dependencies without changing textbook dependencies**

In `app/api/main.py`:

```python
@lru_cache(maxsize=1)
def default_study_repository() -> StudyRecordRepository:
    return StudyRecordRepository(resolve_study_db_path())


def get_study_repository() -> StudyRecordRepository:
    return default_study_repository()


def get_study_service(
    book_service: BookAppService = Depends(get_service),
    repository: StudyRecordRepository = Depends(get_study_repository),
) -> StudyRecordService:
    return StudyRecordService(book_service, repository)
```

This keeps tests able to override a temp repository and ensures the same BookAppService canonical runtime validates identities.

- [ ] **Step 5: Add the four endpoints and DTO conversion helper**

Use a helper that constructs `StudyRecordResponse` from the internal dataclass. Do not let Pydantic accept arbitrary input into repository methods.

- [ ] **Step 6: Run focused and full App API tests**

```bash
python -m unittest app_tests.test_study_api app_tests.test_api app_tests.test_api_live -v
python -m unittest discover -s app_tests -p "test_*.py" -v
```

Expected: all PASS.

- [ ] **Step 7: Commit the API contract**

```bash
git add app/api app_tests/test_study_api.py
git commit -m "feat: expose StudyRecord API"
```

---

### Task 5: Add typed StudyRecord browser client methods

**Files:**
- Modify: `app/web/src/api/types.ts`
- Modify: `app/web/src/api/client.ts`
- Modify: `app/web/src/api/client.test.ts`

**Interfaces:**
- Produces TypeScript `StudyRecord` and `StudyRecordListResponse`.
- Produces `bookApi.touchStudy(...)`, `completeStudy(...)`, `getCourseStudyRecords(...)`, `getRecentStudy()`.

- [ ] **Step 1: Write failing client route tests**

Mock `fetch` and assert exact methods/paths:

```typescript
await bookApi.touchStudy('functional_analysis_course', 'ch01_s01', 'learn')
expect(fetch).toHaveBeenCalledWith(
  '/api/courses/functional_analysis_course/sections/ch01_s01/study/learn/touch',
  expect.objectContaining({ method: 'POST' }),
)
```

Repeat for complete/list/recent and verify API error parsing remains unchanged.

- [ ] **Step 2: Run the focused Vitest file and verify red**

```bash
cd app/web
npm test -- src/api/client.test.ts
```

- [ ] **Step 3: Add exact response types**

```typescript
export type StudyStatus = 'in_progress' | 'completed'

export interface StudyRecord {
  course_id: string
  book_id: string
  section_id: string
  mode: LearningMode
  status: StudyStatus
  progress: 0 | 100
  started_at: string
  last_studied_at: string
  completed_at: string | null
  updated_at: string
}

export interface StudyRecordListResponse {
  course_id: string
  records: StudyRecord[]
}
```

- [ ] **Step 4: Add client methods using the existing `request<T>` helper**

```typescript
touchStudy(courseId, sectionId, mode) {
  return request<StudyRecord>(
    `/api/courses/${segment(courseId)}/sections/${segment(sectionId)}/study/${mode}/touch`,
    { method: 'POST' },
  )
}
```

Add equivalent complete/list/recent methods; recent returns `Promise<StudyRecord | null>`.

- [ ] **Step 5: Run API client tests and typecheck**

```bash
npm test -- src/api/client.test.ts
npm run typecheck
```

- [ ] **Step 6: Commit the web API client**

```bash
git add app/web/src/api
git commit -m "feat: add StudyRecord web client"
```

---

### Task 6: Integrate durable progress into SectionPage without blocking textbook reading

**Files:**
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/styles.css`

**Interfaces:**
- Consumes: `bookApi.touchStudy` after a valid mode payload has resolved.
- Consumes: `bookApi.completeStudy` only from explicit user action.
- Produces: current-mode `StudyRecord | null`, non-blocking persistence error, retry control, and explicit `标记完成` / `已完成` UI.

- [ ] **Step 1: Add failing page tests for touch timing and completion**

Test these separately:

```text
mode payload resolves -> exactly one touch for current mode
mode payload fails -> no touch
preview -> learn switch -> independent touch for each mode
successful touch shows in-progress control
click 标记完成 -> complete API called once and UI becomes 已完成
completed state disables/replaces repeat completion action
```

Mock the existing textbook calls plus new StudyRecord calls; do not rewrite source navigation fixtures.

- [ ] **Step 2: Add failing non-blocking error tests**

Make `touchStudy` reject while `getMode` succeeds. Assert:

```text
教材 heading is still present
learning objects are still present
progress error is visible
retry button is visible
```

Then make retry succeed and assert the error clears.

- [ ] **Step 3: Run SectionPage tests and verify red**

```bash
cd app/web
npm test -- src/pages/SectionPage.test.tsx
```

- [ ] **Step 4: Add progress state without touching sessionStorage modules**

Add component state such as:

```typescript
const [studyRecord, setStudyRecord] = useState<StudyRecord | null>(null)
const [studyError, setStudyError] = useState<string | null>(null)
const [studyBusy, setStudyBusy] = useState(false)
const touchedKeyRef = useRef<string | null>(null)
```

Only touch after `payload` is non-null. Key by `${courseId}:${sectionId}:${mode}` so switching away and back counts as a new re-entry, while React effect re-runs for the same resolved payload do not issue accidental duplicate POSTs. If a touch fails, clear the successful-touch key so explicit retry can run.

- [ ] **Step 5: Implement retry and completion handlers**

Use the existing `errorMessage()` helper for stable Chinese text. Completion must update only StudyRecord UI state; it must not mutate `payload`, source cards, expanded IDs, or navigation state.

Render a small panel after `ModeTabs`:

```text
学习进度：进行中    [标记完成]
```

or:

```text
学习进度：已完成
```

On persistence failure:

```text
学习内容仍可正常查看。学习进度暂未保存。 [重试]
```

- [ ] **Step 6: Keep narrow-screen CSS additive**

Use existing spacing/button conventions. The progress row must wrap at 390px width and must not set fixed widths that create body overflow.

- [ ] **Step 7: Run focused page tests plus existing navigation/session tests**

```bash
npm test -- src/pages/SectionPage.test.tsx src/state/sectionViewState.test.ts src/state/searchViewState.test.ts src/state/qaSessionState.test.ts
npm run typecheck
```

Expected: all PASS; no StudyRecord data appears in sessionStorage tests.

- [ ] **Step 8: Commit SectionPage integration**

```bash
git add app/web/src/pages/SectionPage.tsx \
        app/web/src/pages/SectionPage.test.tsx \
        app/web/src/styles.css
git commit -m "feat: persist Section learning progress"
```

---

### Task 7: Add real-browser persistence acceptance and deterministic CI storage

**Files:**
- Modify: `app/web/e2e/functional-analysis.spec.ts`
- Modify: `.github/workflows/app-ui-tests.yml`

**Interfaces:**
- Consumes: real Functional Analysis canonical course and real StudyRecord FastAPI routes.
- Produces: browser proof that durable progress survives web reload and remains independent across modes.

- [ ] **Step 1: Add a failing Playwright acceptance case**

The test must use the real course and API, not route-stub StudyRecord responses. Sequence:

```text
open /courses/functional_analysis_course/sections/ch01_s01?mode=preview
wait for textbook content and progress=进行中
switch to learn
confirm learn has its own in-progress state
click 标记完成
confirm 已完成
reload the page
confirm learn remains 已完成
switch to preview and confirm preview was not auto-completed
fetch /api/study/recent in page context and confirm its course/section/mode match the latest touch
open a source and return; confirm existing Section return state still works
set viewport 390×844 and assert document.scrollWidth <= document.documentElement.clientWidth
```

Use a unique test section/mode ordering so retries do not depend on another test's previous completion state.

- [ ] **Step 2: Make browser CI storage deterministic**

In the API start step add:

```yaml
env:
  BOOK_QA_PROVIDER: fake
  BOOK_APP_DATA_DIR: /tmp/book-app-data
```

Before starting the API, ensure the directory is fresh inside the ephemeral CI runner:

```bash
rm -rf /tmp/book-app-data
mkdir -p /tmp/book-app-data
```

This is CI-local scratch cleanup only; do not add application code that deletes user data.

- [ ] **Step 3: Add new Python test modules to the explicit App test command**

Extend the existing workflow command with:

```text
app_tests.test_study_repository
app_tests.test_study_service
app_tests.test_study_api
```

The existing full discovery step remains as the broader guard.

- [ ] **Step 4: Run browser acceptance locally against a temp data directory**

Terminal 1:

```bash
export BOOK_QA_PROVIDER=fake
export BOOK_APP_DATA_DIR="$(mktemp -d)"
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd app/web
npm run dev -- --host 127.0.0.1 --port 5173
```

Terminal 3:

```bash
cd app/web
npm run e2e
```

Expected: all Chromium acceptance tests PASS.

- [ ] **Step 5: Commit acceptance/CI changes**

```bash
git add app/web/e2e/functional-analysis.spec.ts .github/workflows/app-ui-tests.yml
git commit -m "test: gate durable StudyRecord behavior"
```

---

### Task 8: Update durable-data documentation only after all gates pass

**Files:**
- Modify: `docs/DATA_MODEL.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/CURRENT_STATE.md`
- Modify: `app/README.md`

**Interfaces:**
- Produces: handoff documentation that distinguishes completed Phase 1G behavior from future sync/recording/Meeting/Exam Sprint work.

- [ ] **Step 1: Run the complete Python regression gates before editing completion docs**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s app_tests -p "test_*.py" -v
```

Expected: 0 failures/errors.

- [ ] **Step 2: Run canonical readiness without changing canonical assets**

```bash
python tools/check_runtime_readiness.py books/functional-analysis
```

If this tool's current CLI differs, read its argparse/help first and use the repository-supported read-only readiness invocation. Do not run normalization/recovery tools as part of Phase 1G.

- [ ] **Step 3: Run complete web gates**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
npm run e2e
```

Expected: Vitest 0 failures, TypeScript 0 errors, Vite build exit 0, Playwright 0 failures.

- [ ] **Step 4: Verify canonical textbook assets are unchanged**

```bash
git diff --name-only main...HEAD -- books/functional-analysis
```

Expected: no output.

- [ ] **Step 5: Update `docs/DATA_MODEL.md` with the concrete schema**

Record:

```text
stable hidden profile UUID
StudyRecord primary/logical keys
0/100 progress semantics
started_at / last_studied_at / completed_at
revision / deleted_at / sync_status=local
SQLite is local authority
no SyncEvent/Drive implementation yet
```

- [ ] **Step 6: Update `app/README.md` with storage behavior**

Document:

```text
default OS app-data location
BOOK_APP_DATA_DIR override
SQLite filename book-app.sqlite3
browser never writes SQLite directly
sessionStorage is navigation-only
how to use a temporary data directory for tests/development
```

Do not document any Drive token or future cloud secret.

- [ ] **Step 7: Mark only Phase 1G complete in ROADMAP/CURRENT_STATE**

`docs/ROADMAP.md` should mark the StudyRecord/SQLite/recent-learning/sync-ready bullets complete. Keep recording, Drive sync, SyncEvent, Meeting, ExamPoint, Exam Sprint, and PDF Reader explicitly unimplemented.

`docs/CURRENT_STATE.md` should set the next mainline phase to Phase 1H only after the full gates above are green.

- [ ] **Step 8: Commit final Phase 1G documentation**

```bash
git add docs/DATA_MODEL.md docs/ROADMAP.md docs/CURRENT_STATE.md app/README.md
git commit -m "docs: mark Phase 1G StudyRecord complete"
```

- [ ] **Step 9: Re-run the final completion gate on the exact documentation head**

Because documentation changes can affect workflow path logic or handoff claims, rerun at minimum:

```bash
python -m unittest discover -s app_tests -p "test_*.py" -v
cd app/web
npm test
npm run typecheck
npm run build
```

Then use GitHub Actions on the exact final branch head to confirm the Runtime/App/Web/Chromium workflow gates required by repository policy. Do not merge based on an older green commit.

---

## Self-review checklist

Before implementation begins, verify this plan still satisfies the approved spec:

- [ ] Stable hidden profile identity is generated once and validated on reopen.
- [ ] SQLite schema encodes 4-mode/status/progress/revision/sync-status constraints.
- [ ] Browser cannot choose `profile_id` or `book_id`.
- [ ] Touch occurs only after valid textbook mode content resolves.
- [ ] Write failures are non-blocking for textbook reading.
- [ ] Manual completion is explicit and durable.
- [ ] Reopening completed content preserves completion.
- [ ] Four modes and different sections are independent.
- [ ] Recent learning is durable and ordered by `last_studied_at`.
- [ ] Existing sessionStorage modules remain navigation-only.
- [ ] No Drive/SyncEvent/recording/Meeting/mastery implementation sneaks into Phase 1G.
- [ ] Canonical Functional Analysis assets remain unchanged.
- [ ] Full Runtime/App/Web/Chromium regression gates run on the final head.
