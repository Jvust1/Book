# Phase 1F Textbook QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add course-scoped textbook QA whose generated answers are constrained to server-selected textbook evidence, carry verified canonical citations, fail closed on insufficient evidence, and round-trip from answer citations to the existing source page and back.

**Architecture:** Add a provider-agnostic QA trust layer above the completed Phase 1E `SearchRuntime`/`SourceResolver` stack. Deterministic Runtime code converts a natural-language question into a bounded set of lexical probes, retrieves and re-validates evidence, applies a sufficiency policy, passes only an immutable `EvidencePack` to an `AnswerProvider`, verifies cited evidence IDs after generation, and projects a stable `QAResult`. `BookAppService` and FastAPI expose that result to a Chinese-first React QA page. CI and browser acceptance use only `DeterministicFakeAnswerProvider`; the normal local app does not silently use the fake provider as if it were a real model.

**Tech Stack:** Python 3.11/3.12/3.13, dataclasses + typing `Protocol`, existing Book Runtime, FastAPI + Pydantic, React 19 + TypeScript 5.9 + React Router, Vitest, Playwright Chromium, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-textbook-qa-phase-1f-design.md`

## Global Constraints

- Phase 1F QA is scoped to exactly one `course_id` and that course's enabled main textbook.
- The evidence retriever must reuse the audited Phase 1E `SearchRuntime`; do not add embeddings, a vector database, or a second search index.
- Natural-language questions are converted only into bounded deterministic lexical probes; the provider never participates in retrieval.
- Every search hit used as QA evidence must be re-resolved through `SourceResolver` before model exposure.
- The provider receives only normalized `ProviderRequest` / `EvidencePack` content; never repository paths, raw files, browser state, credentials, unrelated courses, or arbitrary tool access.
- Provider citations are opaque server-issued evidence IDs (`E1`, `E2`, ...); the provider never owns canonical source identities, pages, anchors, or citation metadata.
- Final citations are projected only from server-owned evidence after verification.
- A successful provider-generated answer must contain at least one verified citation.
- `insufficient_evidence` is an HTTP 200 product result, must not call the provider, and uses `answer_kind="system_notice"`.
- Search/index/source trust-path failures are infrastructure errors (`qa_unavailable`), not evidence insufficiency.
- Provider unavailable is HTTP 503 `qa_provider_unavailable`; malformed/invalid provider output is HTTP 502 `qa_provider_invalid_response`.
- Generated prose must always be identified as generated and must never be written into textbook assets.
- CI and Playwright use `DeterministicFakeAnswerProvider`; no external provider/API key is required for repository acceptance.
- The normal local app defaults to an unavailable provider unless a real provider is explicitly configured; it must never present fake-provider text as production AI output.
- QA navigation state is short-lived `sessionStorage` only: `route`, `question`, `scrollY`, `activeCitationKey`; do not persist answer/citation payloads as StudyRecord/history.
- Existing Search → Source → Return and Section → Source → Return behavior must remain green.

---

## File Structure

### Runtime

- Create `runtime/qa_models.py` — immutable evidence/provider/result dataclasses and explicit constructors.
- Create `runtime/qa_provider.py` — `AnswerProvider` protocol, deterministic fake provider, unavailable provider, provider exceptions.
- Create `runtime/qa_evidence.py` — `QuestionProbeBuilder`, `EvidenceRetriever`, `EvidencePolicy`, `CitationVerifier`.
- Create `runtime/qa_runtime.py` — input validation and orchestration only.
- Modify `runtime/__init__.py` — export stable QA Runtime interfaces/errors.
- Create `tests/test_qa_provider.py`, `tests/test_qa_evidence.py`, `tests/test_qa_runtime.py`.
- Modify `tests/runtime_fixture_factory.py` only if a focused QA source/index fixture is required.

### App/API

- Create `app/api/qa_provider_factory.py` — server-side provider selection; `fake` is opt-in for tests/CI only.
- Modify `app/api/errors.py`, `models.py`, `service.py`, `main.py`.
- Create `app_tests/test_qa_provider_factory.py`.
- Modify `app_tests/test_app_service.py`, `test_api.py`, `test_api_live.py`.

### Web

- Modify `app/web/src/api/types.ts`, `client.ts`, `client.test.ts`.
- Create `app/web/src/pages/QAPage.tsx`, `QAPage.test.tsx`.
- Modify `CoursePage.tsx`, `CoursePage.test.tsx`, `routes/router.tsx`, `styles.css`.
- Create `app/web/src/state/qaViewState.ts`, `qaViewState.test.ts`.
- Modify `SourcePage.tsx`, `SourcePage.test.tsx`.

### Browser / CI / docs

- Modify `app/web/e2e/functional-analysis.spec.ts`.
- Modify `.github/workflows/runtime-reference-tests.yml`, `.github/workflows/app-ui-tests.yml`.
- Modify `README.md`, `docs/ROADMAP.md`, `docs/SEARCH_QA.md` only after implementation gates are green.

---

### Task 1: Immutable QA Contracts and Provider Boundary

**Files:**
- Create: `runtime/qa_models.py`
- Create: `runtime/qa_provider.py`
- Create: `tests/test_qa_provider.py`
- Modify: `runtime/__init__.py`

**Interfaces:**
- `EvidenceItem`, `EvidencePack`, `ProviderRequest`, `ProviderAnswer`, `QACitation`, `QAResult` are frozen dataclasses.
- `ProviderRequest.from_pack(pack: EvidencePack) -> ProviderRequest` is defined here and used later.
- `QAResult.generated(...)` and `QAResult.system_notice(...)` constructors are defined here and used by `QARuntime`.
- `AnswerProvider.answer(request: ProviderRequest) -> ProviderAnswer` is the only provider protocol method.
- `DeterministicFakeAnswerProvider` is test/CI-only.
- `UnavailableAnswerProvider` deterministically raises `AnswerProviderUnavailableError` and is the safe default when no real provider exists.

- [ ] **Step 1: Write RED provider-contract tests**

```python
from runtime.qa_models import EvidenceItem, EvidencePack, ProviderRequest
from runtime.qa_provider import (
    DeterministicFakeAnswerProvider,
    UnavailableAnswerProvider,
    AnswerProviderUnavailableError,
)


def evidence(evidence_id: str = "E1") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_kind="object",
        source_id="obj_holder",
        object_type="theorem",
        title_zh="Hölder 不等式",
        title_en="Holder inequality",
        number="1.4",
        formula="|∫fg| ≤ ||f||p ||g||q",
        content_zh="教材中的确定性内容",
        source_anchor="anchor_holder",
        pdf_page=42,
        printed_page=23,
        search_score=1000,
    )


def test_provider_request_is_built_only_from_evidence_pack():
    pack = EvidencePack(
        course_id="functional_analysis_course",
        book_id="stein_shakarchi_functional_analysis_2011",
        question="Hölder 不等式是什么？",
        evidence=(evidence(),),
    )
    request = ProviderRequest.from_pack(pack)
    assert request.question == pack.question
    assert request.evidence == pack.evidence
    assert not hasattr(request, "repository_root")
    assert not hasattr(request, "browser_state")


def test_fake_provider_cites_only_supplied_ids():
    pack = EvidencePack(
        course_id="functional_analysis_course",
        book_id="stein_shakarchi_functional_analysis_2011",
        question="Hölder 不等式是什么？",
        evidence=(evidence(),),
    )
    result = DeterministicFakeAnswerProvider().answer(ProviderRequest.from_pack(pack))
    assert result.cited_evidence_ids == ("E1",)
    assert "Hölder" in result.answer_text


def test_unavailable_provider_fails_explicitly():
    with pytest.raises(AnswerProviderUnavailableError):
        UnavailableAnswerProvider().answer(ProviderRequest.from_pack(pack))
```

Use the repository's current unittest style if tests do not use pytest assertions; the behavioral contract above is authoritative.

- [ ] **Step 2: Run RED test**

```bash
python -m unittest tests.test_qa_provider -v
```

Expected: import failure because QA modules do not exist.

- [ ] **Step 3: Implement minimal frozen contracts**

Required core shapes:

```python
@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_kind: str
    source_id: str
    object_type: str | None
    title_zh: str | None
    title_en: str | None
    number: str | None
    formula: str | None
    content_zh: str | None
    source_anchor: str | None
    pdf_page: int | None
    printed_page: int | str | None
    search_score: int

@dataclass(frozen=True)
class EvidencePack:
    course_id: str
    book_id: str
    question: str
    evidence: tuple[EvidenceItem, ...]

@dataclass(frozen=True)
class ProviderRequest:
    question: str
    course_id: str
    book_id: str
    evidence: tuple[EvidenceItem, ...]

    @classmethod
    def from_pack(cls, pack: EvidencePack) -> "ProviderRequest":
        return cls(pack.question, pack.course_id, pack.book_id, pack.evidence)

@dataclass(frozen=True)
class ProviderAnswer:
    answer_text: str
    cited_evidence_ids: tuple[str, ...]
```

`QACitation` contains presentation ID plus canonical source/page/anchor fields. `QAResult` contains `course_id`, `book_id`, `question`, `answer_kind`, `evidence_status`, `answer`, `citations`, with explicit `generated()` and `system_notice()` classmethods.

- [ ] **Step 4: Implement provider protocol/fake/unavailable provider**

`DeterministicFakeAnswerProvider` may compose a stable answer from the first evidence item's title/content/formula and cite its evidence ID. It must not inspect Runtime/filesystem/environment. `UnavailableAnswerProvider` always raises `AnswerProviderUnavailableError`.

- [ ] **Step 5: Run GREEN tests and compile**

```bash
python -m unittest tests.test_qa_provider -v
python -m compileall -q runtime/qa_models.py runtime/qa_provider.py
```

- [ ] **Step 6: Commit Task 1**

```bash
git add runtime/qa_models.py runtime/qa_provider.py runtime/__init__.py tests/test_qa_provider.py
git commit -m "feat: add textbook QA provider contracts"
```

---

### Task 2: Deterministic Question Probes and Source-Verified Evidence

**Files:**
- Create: `runtime/qa_evidence.py`
- Create: `tests/test_qa_evidence.py`
- Modify: `tests/runtime_fixture_factory.py` only if necessary

**Interfaces:**
- `QuestionProbeBuilder.build(question: str) -> tuple[str, ...]`.
- `EvidenceRetriever.from_course(course)` and `.retrieve(question, *, limit: int) -> EvidencePack`.
- `EvidencePolicy.status(pack) -> Literal["sufficient", "insufficient_evidence"]`.
- `CitationVerifier.verify(pack, provider_answer) -> tuple[QACitation, ...]`.

- [ ] **Step 1: Write RED probe-builder tests**

Required deterministic behavior:

```python
assert QuestionProbeBuilder.build("Hölder 不等式的作用是什么？")[0] == "Hölder 不等式的作用是什么？"
assert "Hölder" in QuestionProbeBuilder.build("Hölder 不等式的作用是什么？")
assert "巴拿赫空间" in QuestionProbeBuilder.build("什么是巴拿赫空间？")
assert len(QuestionProbeBuilder.build("什么是巴拿赫空间？")) <= 24
```

Exact algorithm:
1. preserve the trimmed original question as probe 1;
2. add unique Latin/alphanumeric tokens of length >= 3 in appearance order;
3. for each contiguous CJK run, add unique n-grams length 8 down to 2, appearance order within each length;
4. stop after 24 unique probes;
5. no model, dictionary, external NLP library, or network call.

This bounded probe set is the only Phase 1F refinement over Phase 1E lexical search.

- [ ] **Step 2: Run RED probe test**

```bash
python -m unittest tests.test_qa_evidence -v
```

Expected: import failure for `runtime.qa_evidence`.

- [ ] **Step 3: Implement `QuestionProbeBuilder`**

Use Python stdlib only (`re`, Unicode string handling). Preserve deterministic ordering exactly as tested.

- [ ] **Step 4: Add RED real-evidence tests**

Use the real Functional Analysis course:

```python
pack = EvidenceRetriever.from_course(course).retrieve("什么是巴拿赫空间？", limit=8)
assert pack.course_id == "functional_analysis_course"
assert pack.book_id == "stein_shakarchi_functional_analysis_2011"
assert pack.evidence
assert pack.evidence[0].evidence_id == "E1"
```

Also verify `Hölder 不等式的作用是什么？` produces source-verified evidence.

- [ ] **Step 5: Implement evidence merge/revalidation**

For each probe in order:

```python
hits = SearchRuntime.from_course(course).search(probe, limit=limit)
```

Merge candidates by `(source_kind, source_id)`. For duplicates retain the candidate with highest `hit.score`; ties prefer earlier probe index then earlier hit rank. Final sort is `score desc`, `probe_index asc`, `hit_rank asc`, then canonical source key. Re-resolve every retained candidate through `SourceResolver` before creating evidence. Issue `E1`, `E2`, ... only after final validation/sort.

Search/index/source trust-path exceptions must raise a QA unavailable/runtime exception, never an empty evidence pack.

- [ ] **Step 6: Add RED sufficiency and citation tests**

Cover:
- no validated evidence -> `insufficient_evidence`;
- highest retained score `<= 300` -> `insufficient_evidence`;
- title/formula/concept match above that threshold -> `sufficient`;
- duplicate cited IDs dedupe preserving first occurrence;
- unknown `E99` -> `AnswerProviderInvalidResponseError`;
- non-empty generated answer with zero citations -> invalid response;
- every final citation is copied from server-owned evidence and remains resolvable through `SourceResolver`.

- [ ] **Step 7: Implement `EvidencePolicy` and `CitationVerifier`**

Provider output supplies only answer text and evidence IDs. Never accept provider-supplied pages/anchors/source IDs.

- [ ] **Step 8: Run Task 2 GREEN gates**

```bash
python -m unittest tests.test_qa_evidence tests.test_search_runtime tests.test_source_resolver -v
python -m compileall -q runtime/qa_evidence.py
```

- [ ] **Step 9: Commit Task 2**

```bash
git add runtime/qa_evidence.py tests/test_qa_evidence.py tests/runtime_fixture_factory.py
git commit -m "feat: add deterministic textbook QA evidence retrieval"
```

---

### Task 3: QARuntime Orchestration

**Files:**
- Create: `runtime/qa_runtime.py`
- Create: `tests/test_qa_runtime.py`
- Modify: `runtime/__init__.py`

**Interfaces:**
- Consumes `EvidenceRetriever`, `EvidencePolicy`, `CitationVerifier`, `AnswerProvider`.
- Produces `QARuntime.from_course(course, provider=provider)`.
- Produces `QARuntime.answer(question, *, evidence_limit=8) -> QAResult`.

- [ ] **Step 1: Write RED orchestration tests**

Cover:
- blank question rejected;
- >1000 Unicode code points rejected;
- `evidence_limit` outside integer 1..12 rejected;
- insufficient evidence does not call provider;
- insufficient result is `answer_kind="system_notice"`, `evidence_status="insufficient_evidence"`, stable Chinese non-assertive message;
- sufficient fake-provider answer is `answer_kind="generated"`, has verified citation(s), canonical course/book identity;
- provider unavailable and provider invalid response remain distinct exceptions.

Spy provider:

```python
class FailIfCalledProvider:
    def answer(self, request):
        raise AssertionError("provider must not be called")
```

- [ ] **Step 2: Run RED runtime test**

```bash
python -m unittest tests.test_qa_runtime -v
```

- [ ] **Step 3: Implement minimal orchestration**

```python
question = validate_question(question)
pack = self._retriever.retrieve(question, limit=evidence_limit)
status = self._policy.status(pack)
if status == "insufficient_evidence":
    return QAResult.system_notice(
        course_id=pack.course_id,
        book_id=pack.book_id,
        question=pack.question,
        answer="现有教材证据不足，暂不能给出可靠回答。",
        citations=(),
    )
provider_answer = self._provider.answer(ProviderRequest.from_pack(pack))
citations = self._verifier.verify(pack, provider_answer)
return QAResult.generated(...)
```

Do not catch and collapse provider/retrieval exceptions here unless mapping to a more specific QA Runtime exception.

- [ ] **Step 4: Run Task 3 GREEN gates**

```bash
python -m unittest tests.test_qa_provider tests.test_qa_evidence tests.test_qa_runtime -v
python -m compileall -q runtime/qa_models.py runtime/qa_provider.py runtime/qa_evidence.py runtime/qa_runtime.py
```

- [ ] **Step 5: Commit Task 3**

```bash
git add runtime/qa_runtime.py runtime/__init__.py tests/test_qa_runtime.py
git commit -m "feat: add source-verified textbook QA runtime"
```

---

### Task 4: Safe Provider Selection, Stable App Service, and POST API

**Files:**
- Create: `app/api/qa_provider_factory.py`
- Create: `app_tests/test_qa_provider_factory.py`
- Modify: `app/api/errors.py`
- Modify: `app/api/models.py`
- Modify: `app/api/service.py`
- Modify: `app/api/main.py`
- Modify: `app_tests/test_app_service.py`
- Modify: `app_tests/test_api.py`
- Modify: `app_tests/test_api_live.py`

**Interfaces:**
- `provider_from_environment() -> AnswerProvider`.
- `BookAppService(repository_root, *, qa_provider: AnswerProvider | None = None)`; if omitted, service uses `UnavailableAnswerProvider` rather than fake.
- `BookAppService.ask(course_id: str, question: str) -> QAResponse`.
- `POST /api/courses/{course_id}/qa` body `{"question":"..."}`.

- [ ] **Step 1: Write RED provider-factory tests**

Contract:

```python
monkeypatch.delenv("BOOK_QA_PROVIDER", raising=False)
assert isinstance(provider_from_environment(), UnavailableAnswerProvider)

monkeypatch.setenv("BOOK_QA_PROVIDER", "fake")
assert isinstance(provider_from_environment(), DeterministicFakeAnswerProvider)
```

Unknown values must resolve to unavailable or raise a stable startup/config error; never silently choose fake. If unittest style is used, patch `os.environ` with `unittest.mock.patch.dict`.

- [ ] **Step 2: Implement provider factory**

Only `BOOK_QA_PROVIDER=fake` activates fake. No external vendor adapter is added in Phase 1F. `default_service()` in `main.py` obtains its provider from this server-side factory.

- [ ] **Step 3: Write RED service tests**

With injected fake provider:

```python
response = service.ask("functional_analysis_course", "什么是巴拿赫空间？")
assert response.answer_kind == "generated"
assert response.evidence_status == "sufficient"
assert response.citations
```

With default/unavailable provider and sufficient evidence, assert stable provider-unavailable App error. With insufficient evidence, assert HTTP/product path remains 200 and does not touch provider.

- [ ] **Step 4: Implement DTOs and service projection**

Pydantic DTOs:

```python
class QARequest(BaseModel):
    question: str

class QACitationItem(BaseModel):
    citation_id: str
    evidence_id: str
    source_kind: str
    source_id: str
    object_type: str | None
    number: str | None
    title_zh: str | None
    title_en: str | None
    source_anchor: str | None
    pdf_page: int | None
    printed_page: int | str | None

class QAResponse(BaseModel):
    course_id: str
    book_id: str
    question: str
    answer_kind: Literal["generated", "system_notice"]
    evidence_status: Literal["sufficient", "insufficient_evidence"]
    answer: str
    citations: list[QACitationItem]
```

Map Runtime/provider exceptions to stable App errors without leaking detail to the client.

- [ ] **Step 5: Write RED HTTP tests**

Required semantics:

```text
valid + fake provider                    -> 200 sufficient/generated
insufficient question                    -> 200 insufficient_evidence/system_notice
blank or >1000 chars                     -> 400 invalid_qa_question
unknown course                            -> 404 course_not_found
search/index/source trust failure         -> 503 qa_unavailable
provider unavailable                      -> 503 qa_provider_unavailable
invalid provider response/citation        -> 502 qa_provider_invalid_response
```

Malformed/missing request bodies must follow a stable user-facing 400 contract rather than exposing raw Pydantic details.

- [ ] **Step 6: Implement POST route and CORS**

Change local CORS from GET-only to exactly `['GET', 'POST']`; keep localhost/127.0.0.1 origins unchanged.

```python
@app.post("/api/courses/{course_id}/qa", response_model=QAResponse)
def qa(course_id: str, payload: QARequest, service: BookAppService = Depends(get_service)) -> QAResponse:
    return service.ask(course_id, payload.question)
```

- [ ] **Step 7: Add real loopback deterministic QA smoke**

Launch with `BOOK_QA_PROVIDER=fake` and assert a real Functional Analysis natural-language question returns canonical citation data.

- [ ] **Step 8: Run Task 4 GREEN gates**

```bash
python -m unittest app_tests.test_qa_provider_factory app_tests.test_app_service app_tests.test_api app_tests.test_api_live -v
python -m unittest tests.test_qa_provider tests.test_qa_evidence tests.test_qa_runtime -v
```

- [ ] **Step 9: Commit Task 4**

```bash
git add app/api app_tests/test_qa_provider_factory.py app_tests/test_app_service.py app_tests/test_api.py app_tests/test_api_live.py
git commit -m "feat: expose trusted textbook QA api"
```

---

### Task 5: Typed Web Client and Chinese-first QA Page

**Files:**
- Modify: `app/web/src/api/types.ts`
- Modify: `app/web/src/api/client.ts`
- Modify: `app/web/src/api/client.test.ts`
- Create: `app/web/src/pages/QAPage.tsx`
- Create: `app/web/src/pages/QAPage.test.tsx`
- Modify: `app/web/src/pages/CoursePage.tsx`
- Modify: `app/web/src/pages/CoursePage.test.tsx`
- Modify: `app/web/src/routes/router.tsx`
- Modify: `app/web/src/styles.css`

**Interfaces:**
- `bookApi.askCourse(courseId: string, question: string): Promise<QAResponse>`.
- Route `/courses/:courseId/qa`.
- Citation links reuse `/courses/:courseId/sources/:sourceKind/:sourceId`.

- [ ] **Step 1: Write RED client test**

```ts
await bookApi.askCourse('functional_analysis_course', '什么是巴拿赫空间？')
expect(fetch).toHaveBeenCalledWith(
  '/api/courses/functional_analysis_course/qa',
  expect.objectContaining({
    method: 'POST',
    headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ question: '什么是巴拿赫空间？' }),
  }),
)
```

- [ ] **Step 2: Extend request helper without regressing GET**

Change `request<T>(path)` to accept a narrow optional `RequestInit`; merge `Accept: application/json` with POST content-type. Existing GET calls keep identical URLs/error parsing.

- [ ] **Step 3: Write RED QAPage tests**

Cover:
- empty initial state does not request;
- submit -> loading;
- generated result shows persistent `AI 生成回答，依据下方教材来源`;
- `system_notice`/insufficient result does not show generated label;
- citations show source/page metadata and use `source_kind + source_id` link;
- `qa_unavailable`, `qa_provider_unavailable`, `qa_provider_invalid_response` render stable error state;
- Course page has `教材问答` link;
- router resolves QAPage.

- [ ] **Step 4: Implement typed QA DTOs and page**

State machine:

```text
empty -> loading -> sufficient | insufficient_evidence | error
```

Submit only on form submit, not on keystroke. Disable duplicate submit while loading. Never label generated prose as textbook original text.

- [ ] **Step 5: Run Web GREEN gates**

```bash
cd app/web
npm test
npm run typecheck
npm run build
```

- [ ] **Step 6: Commit Task 5**

```bash
git add app/web/src/api app/web/src/pages/QAPage.tsx app/web/src/pages/QAPage.test.tsx app/web/src/pages/CoursePage.tsx app/web/src/pages/CoursePage.test.tsx app/web/src/routes/router.tsx app/web/src/styles.css
git commit -m "feat: add textbook QA page"
```

---

### Task 6: QA → Source → Return Context

**Files:**
- Create: `app/web/src/state/qaViewState.ts`
- Create: `app/web/src/state/qaViewState.test.ts`
- Modify: `app/web/src/pages/QAPage.tsx`
- Modify: `app/web/src/pages/QAPage.test.tsx`
- Modify: `app/web/src/pages/SourcePage.tsx`
- Modify: `app/web/src/pages/SourcePage.test.tsx`

**Interfaces:**
- `saveQAViewState`, `loadQAViewState`, `clearQAViewState`.
- Stored shape only `{ route, question, scrollY, activeCitationKey }`.
- `activeCitationKey = `${source_kind}:${source_id}``.

- [ ] **Step 1: Write RED state-helper tests**

Assert key `book:qa-view:${courseId}`, corrupt/invalid JSON -> `null`, and no full answer/citation arrays are accepted or persisted.

- [ ] **Step 2: Implement helper matching `searchViewState` validation style**

Do not refactor unrelated state modules.

- [ ] **Step 3: Write RED return-flow tests**

Required behavior:
1. citation click saves QA route/question/scroll/source key before navigation;
2. matching SourcePage shows `返回问答`;
3. matching QA state takes precedence over stale matching Search state;
4. click returns to saved QA route;
5. QAPage re-runs `askCourse` from saved question, restores scroll, and marks the originating citation `aria-current="true"`;
6. answer/citation payloads are not stored in sessionStorage;
7. without QA match, existing Search return still works;
8. without QA/Search match, existing Section return still works.

- [ ] **Step 4: Implement SourcePage priority**

```text
matching QA -> 返回问答
matching Search -> 返回搜索
matching Section -> 返回学习
existing fallback otherwise
```

- [ ] **Step 5: Run Task 6 GREEN gates**

```bash
cd app/web
npm test
npm run typecheck
npm run build
```

- [ ] **Step 6: Commit Task 6**

```bash
git add app/web/src/state/qaViewState.ts app/web/src/state/qaViewState.test.ts app/web/src/pages/QAPage.tsx app/web/src/pages/QAPage.test.tsx app/web/src/pages/SourcePage.tsx app/web/src/pages/SourcePage.test.tsx
git commit -m "feat: restore textbook QA source context"
```

---

### Task 7: Real Browser Acceptance and CI Hardening

**Files:**
- Modify: `app/web/e2e/functional-analysis.spec.ts`
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Modify: `.github/workflows/app-ui-tests.yml`

**Interfaces:**
- Browser/API acceptance explicitly sets `BOOK_QA_PROVIDER=fake` for the local test API process.
- Normal runtime without that opt-in remains provider-unavailable.

- [ ] **Step 1: Add Playwright cases**

Use real Functional Analysis assets:
- English natural-language theorem question containing `Hölder`;
- Chinese natural-language question containing `巴拿赫空间`;
- clearly nonexistent question -> normal `insufficient_evidence`, not alert/error;
- QA citation -> existing SourcePage -> `返回问答` -> context restored;
- 390×844 QA/source round trip has `scrollWidth <= clientWidth`.

Assert the generated-label/canonical route, not free-form wording beyond deterministic fake-provider guarantees.

- [ ] **Step 2: Run local E2E with fake provider explicitly enabled**

API process:

```bash
BOOK_QA_PROVIDER=fake python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Then:

```bash
cd app/web && npm run e2e
```

- [ ] **Step 3: Harden Runtime workflow**

Compile QA modules and run QA unit tests on Python 3.11/3.12/3.13. Add canonical smoke for one sufficient natural-language question and one insufficient question. Trigger on QA files plus canonical search/source assets.

- [ ] **Step 4: Harden App UI workflow**

App/API job includes provider-factory/service/API QA tests. Browser job sets `BOOK_QA_PROVIDER=fake` only for the local API process; no secrets are required.

- [ ] **Step 5: Commit Task 7**

```bash
git add app/web/e2e/functional-analysis.spec.ts .github/workflows/runtime-reference-tests.yml .github/workflows/app-ui-tests.yml
git commit -m "ci: gate source-verified textbook QA"
```

---

### Task 8: Documentation, Full Regression, and PR Readiness

**Files:**
- Modify: `README.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/SEARCH_QA.md`

- [ ] **Step 1: Update docs only for verified behavior**

Document trusted evidence flow, deterministic lexical probes, generated/system-notice distinction, provider-agnostic boundary, fake-provider CI behavior, default provider-unavailable behavior, QA → Source → Return, and explicit non-goals. Do not claim a real external model adapter exists.

- [ ] **Step 2: Run full Python QA/App verification**

```bash
python -m unittest \
  tests.test_qa_provider \
  tests.test_qa_evidence \
  tests.test_qa_runtime \
  tests.test_search_runtime \
  tests.test_source_resolver \
  app_tests.test_qa_provider_factory \
  app_tests.test_app_service \
  app_tests.test_api \
  app_tests.test_api_live -v
```

Then require the repository Runtime workflow green on Python 3.11/3.12/3.13.

- [ ] **Step 3: Run full Web verification**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
npm run e2e
```

- [ ] **Step 4: Verify canonical Functional Analysis invariants**

Require:

```text
STRUCTURED_COMPLETE / RUNTIME_READY
8 chapters / 132 sections
442 PageMap rows
1493 unique search records
```

`books/functional-analysis/**` must have zero changes.

- [ ] **Step 5: Compare branch to `main` and inspect scope**

Allowed scope: QA Runtime/API/Web/tests/CI/docs only. Reject unrelated refactors or canonical textbook-asset modifications.

- [ ] **Step 6: Commit docs**

```bash
git add README.md docs/ROADMAP.md docs/SEARCH_QA.md
git commit -m "docs: document Phase 1F textbook QA"
```

- [ ] **Step 7: Fresh final verification before PR**

On the final head, require fresh Runtime reference success, App API success, Web unit/typecheck/build success, Chromium acceptance success, unchanged validated head SHA, and zero textbook asset changes. Only then open a PR from `feature/textbook-qa-phase-1f` to `main`.
