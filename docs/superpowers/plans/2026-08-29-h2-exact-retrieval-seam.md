# H2 Exact-only Shared Retrieval Seam Implementation Plan

> **For implementers:** Use Superpowers TDD. H0 and H1 must be available. This stage must not activate FTS, semantic retrieval, multi-book public APIs, or persistent retrieval caches.

**Goal:** Route App Search and QA candidate selection through one internal Retrieval seam while preserving the existing `SearchRuntime` algorithm and every public Search/QA behavior.

**Architecture:** `runtime.retrieval` owns internal request/hit/retriever/engine types. `CanonicalExactRetriever` wraps `SearchRuntime` and adds H1 `SourceIdentity`. App Search and `EvidenceBuilder` consume `RetrievalEngine`, but canonical re-resolution and citation verification remain independent.

**Tech stack:** Python 3.11–3.13 stdlib typing/dataclasses, existing Runtime/App `unittest` suite.

---

## Task 1: Lock SearchRuntime equivalence with characterization tests

**Files:**
- Modify: `tests/test_search_runtime.py`
- Reference: `runtime/search_runtime.py`

**Step 1: Add/confirm exact score ordering tests**

Ensure tests cover all frozen score classes:

```text
title exact       1000
ID exact           900
title prefix       800
title substring    700
formula exact      600
formula substring  500
concept exact      400
concept substring  350
object type        300
```

Also assert:

- rank tie breaks by original search-index line order;
- `section_id` filtering occurs before `limit`;
- blank query fails;
- blank section fails;
- limit outside 1..100 fails;
- no match returns `[]`;
- malformed/missing/mismatched canonical index fails closed.

**Step 2: Run characterization**

```bash
python -m unittest tests.test_search_runtime -v
```

Expected: PASS. Any current missing characterization should be added without changing production code.

**Step 3: Commit characterization only**

```bash
git add tests/test_search_runtime.py
git commit -m "test: freeze exact search ranking contract"
```

---

## Task 2: Define Retrieval types and error boundary with RED tests

**Files:**
- Create: `runtime/retrieval.py`
- Create: `tests/test_retrieval.py`

**Step 1: Write failing interface tests**

Tests should import:

```python
from runtime.retrieval import (
    CanonicalExactRetriever,
    RetrievalEngine,
    RetrievalHit,
    RetrievalInvariantError,
    RetrievalQueryError,
    RetrievalRequest,
    RetrievalUnavailableError,
)
```

Test the request contract:

```python
request = RetrievalRequest(query="Hölder", limit=10, section_id=None)
self.assertEqual(request.query, "Hölder")
self.assertEqual(request.limit, 10)
```

Using a fixture course, test `CanonicalExactRetriever` equivalence:

```python
search_hits = SearchRuntime.from_course(course).search("fixture", limit=10)
retrieval_hits = CanonicalExactRetriever.from_course(course).search(
    RetrievalRequest("fixture", limit=10)
)
self.assertEqual(
    [(h.rank, h.score, h.source_kind, h.source_id) for h in retrieval_hits],
    [(h.rank, h.score, h.source_kind, h.source_id) for h in search_hits],
)
```

Assert every Retrieval hit has:

```python
hit.identity.course_id == course.course_id
hit.identity.book == course.main_book_identity()
hit.identity.source_kind == hit.source_kind
hit.identity.source_id == hit.source_id
```

Write error translation tests:

```text
SearchQueryError          -> RetrievalQueryError
SearchIndexUnavailable    -> RetrievalUnavailableError
source identity mismatch  -> RetrievalInvariantError
```

**Step 2: Verify RED**

```bash
python -m unittest tests.test_retrieval -v
```

Expected: FAIL because `runtime.retrieval` does not exist.

**Step 3: Commit RED tests**

```bash
git add tests/test_retrieval.py
git commit -m "test: define exact retrieval seam"
```

---

## Task 3: Implement `runtime.retrieval` as an Exact wrapper only

**Files:**
- Create: `runtime/retrieval.py`
- Test: `tests/test_retrieval.py`

**Step 1: Implement the internal public shape**

Use this interface:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from book_core.provenance import SourceIdentity
from .course_runtime import CourseRuntime
from .provenance import RuntimeProvenanceError, source_identity_for
from .search_runtime import SearchQueryError, SearchRuntime, SearchRuntimeError


class RetrievalError(RuntimeError):
    pass


class RetrievalQueryError(RetrievalError):
    pass


class RetrievalUnavailableError(RetrievalError):
    pass


class RetrievalInvariantError(RetrievalError):
    pass


@dataclass(frozen=True)
class RetrievalRequest:
    query: str
    limit: int = 30
    section_id: str | None = None


@dataclass(frozen=True)
class RetrievalHit:
    rank: int
    score: int
    identity: SourceIdentity
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


class Retriever(Protocol):
    def search(self, request: RetrievalRequest) -> list[RetrievalHit]: ...
```

Implement `CanonicalExactRetriever` to own a `SearchRuntime` and convert each `SearchHit` field-by-field. It must call `source_identity_for(course, hit.source_kind, hit.source_id)` for provenance; do not construct provenance from unverified row text.

Translate errors exactly:

```python
except SearchQueryError as exc:
    raise RetrievalQueryError(str(exc)) from exc
except SearchRuntimeError as exc:
    raise RetrievalUnavailableError(str(exc)) from exc
except RuntimeProvenanceError as exc:
    raise RetrievalInvariantError(str(exc)) from exc
```

Implement `RetrievalEngine`:

```python
class RetrievalEngine:
    def __init__(self, retriever: Retriever):
        self._retriever = retriever

    @classmethod
    def exact(cls, course: CourseRuntime) -> "RetrievalEngine":
        return cls(CanonicalExactRetriever.from_course(course))

    def search(
        self,
        query: str,
        *,
        limit: int = 30,
        section_id: str | None = None,
    ) -> list[RetrievalHit]:
        return self._retriever.search(
            RetrievalRequest(query=query, limit=limit, section_id=section_id)
        )
```

Do not export these names from `runtime/__init__.py` in H2.

**Step 2: Run Retrieval + Search tests**

```bash
python -m unittest tests.test_retrieval tests.test_search_runtime tests.test_runtime_provenance -v
```

Expected: PASS.

**Step 3: Compile**

```bash
python -m py_compile runtime/retrieval.py
```

Expected: PASS.

**Step 4: Commit**

```bash
git add runtime/retrieval.py tests/test_retrieval.py
git commit -m "feat: add exact-only retrieval engine"
```

---

## Task 4: Route App Search through Retrieval without changing HTTP output

**Files:**
- Modify: `app/api/service.py`
- Modify: `app_tests/test_app_service.py`
- Modify: `app_tests/test_api.py`
- Modify: `app_tests/test_serialization_contracts.py`

**Step 1: Write RED injection/equivalence tests**

Add a spy factory:

```python
class SpyRetrievalFactory:
    def __init__(self):
        self.calls = []

    def __call__(self, course):
        self.calls.append(course.course_id)
        return RetrievalEngine.exact(course)
```

Add test:

```python
service = BookAppService(repo, retrieval_factory=spy)
response = service.search("functional_analysis_course", "Hölder")
self.assertEqual(spy.calls, ["functional_analysis_course"])
```

Add an exact JSON equality test comparing the current expected SearchResponse payload before/after seam. The payload must not include `identity`, `book_version_id`, or `retriever_id`.

Add fake-engine error tests that assert HTTP/App mappings remain:

```text
RetrievalQueryError       -> 400 invalid_search_query / 搜索条件无效
RetrievalUnavailableError -> 503 search_unavailable / 教材搜索暂不可用
RetrievalInvariantError   -> 503 search_unavailable / 教材搜索暂不可用
```

**Step 2: Verify RED**

```bash
python -m unittest app_tests.test_app_service app_tests.test_api app_tests.test_serialization_contracts -v
```

Expected: injection tests fail because `BookAppService` has no `retrieval_factory`; existing Search tests remain GREEN.

**Step 3: Implement keyword-only factory seam**

In `app/api/service.py` import directly from internal module:

```python
from collections.abc import Callable
from runtime.retrieval import (
    RetrievalEngine,
    RetrievalInvariantError,
    RetrievalQueryError,
    RetrievalUnavailableError,
)
```

Extend constructor without breaking old calls:

```python
def __init__(
    self,
    repository_root: Path,
    *,
    qa_provider: ModelProvider | None = None,
    retrieval_factory: Callable[[CourseRuntime], RetrievalEngine] | None = None,
):
    ...
    self._retrieval_factory = retrieval_factory or RetrievalEngine.exact
```

Change only `search()` candidate retrieval:

```python
engine = self._retrieval_factory(course)
hits = engine.search(query, limit=limit)
```

Keep explicit mapping to `SearchResultItem` exactly field-for-field.

Map the Retrieval errors to the existing App errors/messages. Do not leak internal details in HTTP response.

**Step 4: Run App Search tests**

```bash
python -m unittest \
  tests.test_retrieval \
  tests.test_search_runtime \
  app_tests.test_app_service \
  app_tests.test_api \
  app_tests.test_api_live \
  app_tests.test_serialization_contracts -v
```

Expected: PASS and exact response keys remain frozen.

**Step 5: Commit**

```bash
git add app/api/service.py app_tests/test_app_service.py app_tests/test_api.py app_tests/test_serialization_contracts.py
git commit -m "refactor: route app search through exact retrieval"
```

---

## Task 5: Route `EvidenceBuilder` through Retrieval while preserving SourceResolver trust

**Files:**
- Modify: `runtime/qa_evidence.py`
- Modify: `tests/test_qa_evidence.py`
- Modify: `tests/test_retrieval.py`

**Step 1: Write RED EvidenceBuilder injection tests**

Define a fake engine in tests that records:

```text
query
limit
section_id
```

Return controlled `RetrievalHit` values pointing to canonical fixture sources.

Add tests proving:

- `EvidenceBuilder.from_course(course)` still works unchanged;
- optional retrieval factory is called;
- every RetrievalHit is independently re-resolved by `SourceResolver` before an `EvidenceItem` exists;
- a fake RetrievalHit that claims a canonical-looking ID but cannot resolve causes `QAEvidenceUnavailableError` instead of being passed to the model;
- Section scope cannot be escaped;
- item/text budgets remain 8 / 12000.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_qa_evidence -v
```

Expected: new factory tests fail before refactor.

**Step 3: Replace SearchRuntime dependency with RetrievalEngine**

In `runtime/qa_evidence.py`:

- change `_EvidenceCandidate.hit` from `SearchHit` to `RetrievalHit`;
- import Retrieval types from `.retrieval`;
- constructor becomes:

```python
def __init__(
    self,
    course: CourseRuntime,
    *,
    retrieval_factory: Callable[[CourseRuntime], RetrievalEngine] | None = None,
):
    self.course = course
    self._retrieval_factory = retrieval_factory or RetrievalEngine.exact
```

- `from_course(course, *, retrieval_factory=None)` remains backward compatible;
- inside `build()`, construct one engine and call:

```python
engine.search(probe, limit=search_limit, section_id=section_id)
```

- catch Retrieval errors and map to `QAEvidenceUnavailableError`.

Keep the existing `SourceResolver` loop, resolved identity checks, text budgets, dedupe, ordering, and `EvidenceItem` construction.

Dedupe can remain `(source_kind, source_id)` while public product is single-primary; do not introduce B5 semantics here. Internal `RetrievalHit.identity` still provides collision-safe future provenance.

**Step 4: Run QA evidence tests**

```bash
python -m unittest tests.test_retrieval tests.test_qa_evidence tests.test_source_resolver -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add runtime/qa_evidence.py tests/test_qa_evidence.py tests/test_retrieval.py
git commit -m "refactor: share exact retrieval with qa evidence"
```

---

## Task 6: Thread Retrieval DI through `QARuntime`

**Files:**
- Modify: `runtime/qa_runtime.py`
- Modify: `tests/test_qa_runtime.py`
- Modify: `app/api/service.py`
- Modify: `app_tests/test_qa_service.py`

**Step 1: Write RED constructor compatibility tests**

Assert old calls remain legal:

```python
QARuntime.from_course(course, provider=provider)
QARuntime(course, provider=provider)
```

Add a spy retrieval factory test:

```python
qa = QARuntime.from_course(
    course,
    provider=provider,
    retrieval_factory=spy_factory,
)
qa.answer("fixture question")
self.assertTrue(spy_factory.called)
```

For App service, assert the same configured retrieval factory is used by both `search()` and `ask()` while existing `qa_provider` behavior stays unchanged.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_qa_runtime app_tests.test_qa_service -v
```

Expected: new retrieval-factory tests fail.

**Step 3: Add optional keyword-only threading**

In `runtime/qa_runtime.py`:

```python
def __init__(
    self,
    course: CourseRuntime,
    *,
    provider: ModelProvider,
    retrieval_factory: Callable[[CourseRuntime], RetrievalEngine] | None = None,
):
    ...
    self._builder = EvidenceBuilder.from_course(
        course,
        retrieval_factory=retrieval_factory,
    )
```

Apply the same optional keyword-only argument to `from_course()`.

In `BookAppService.ask()`, pass `self._retrieval_factory` to `QARuntime.from_course()`.

Do not change `CitationVerifier` construction.

**Step 4: Run QA suite**

```bash
python -m unittest \
  tests.test_qa_evidence \
  tests.test_qa_provider \
  tests.test_qa_runtime \
  app_tests.test_qa_service \
  app_tests.test_qa_api \
  app_tests.test_openai_compatible_provider -v
```

Expected: PASS. Section-first → book fallback, insufficient evidence, provider mappings, and citation verification remain unchanged.

**Step 5: Commit**

```bash
git add runtime/qa_runtime.py app/api/service.py tests/test_qa_runtime.py app_tests/test_qa_service.py
git commit -m "refactor: inject shared retrieval into qa runtime"
```

---

## Task 7: Add explicit rollback/equivalence tests

**Files:**
- Modify: `tests/test_retrieval.py`
- Modify: `tests/test_qa_evidence.py`
- Modify: `app_tests/test_app_service.py`

**Step 1: Add adapter-equivalence tests on real Golden course when fixture exists**

Compare:

```python
queries = ["Hölder", "巴拿赫空间", "1/p + 1/q = 1", "definitely-no-such-text-92831"]
for query in queries:
    exact = SearchRuntime.from_course(course).search(query)
    seam = RetrievalEngine.exact(course).search(query)
    self.assertEqual(
        [(h.rank, h.score, h.source_kind, h.source_id) for h in seam],
        [(h.rank, h.score, h.source_kind, h.source_id) for h in exact],
    )
```

Add one section-scoped query equivalence.

**Step 2: Run targeted suite**

```bash
python -m unittest tests.test_search_runtime tests.test_retrieval tests.test_qa_evidence tests.test_qa_runtime app_tests.test_app_service -v
```

Expected: PASS.

**Step 3: Commit**

```bash
git add tests/test_retrieval.py tests/test_qa_evidence.py app_tests/test_app_service.py
git commit -m "test: prove exact retrieval behavior equivalence"
```

---

## Task 8: CI wiring and exact-HEAD H2 verification

**Files:**
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Modify if needed: `.github/workflows/app-ui-tests.yml`

**Step 1: Compile the new module in Runtime CI**

Add:

```bash
python -m py_compile runtime/retrieval.py
```

Add `tests.test_retrieval` to the Phase 1F/Runtime test step. `runtime/**` already triggers Runtime and App workflows; do not add unrelated paths.

**Step 2: Run Python regressions**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s app_tests -p "test_*.py" -v
```

Expected: PASS.

**Step 3: Run web regression**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
```

Expected: PASS; no browser state/type changes are required for H2.

**Step 4: Verify no forbidden scope**

```bash
git diff --name-only <H2_BASE_SHA>...HEAD
```

Expected:

```text
no books/**
no courses/**
no StudyRecord schema/storage change
no FTS implementation
no public multi-book DTO change
```

Replace `<H2_BASE_SHA>` with the real branch base SHA.

**Step 5: Record exact HEAD and prepare reviewable PR**

```bash
git rev-parse HEAD
```

Record test evidence against that exact SHA. Do not merge automatically. Public product remains Exact-only after H2.
