# Phase 1F Textbook QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add course-scoped textbook QA whose generated answers are constrained to server-selected textbook evidence, carry verified canonical citations, fail closed on insufficient evidence, and round-trip from answer citations to the existing source page and back.

**Architecture:** Add a provider-agnostic QA trust layer above the completed Phase 1E `SearchRuntime`/`SourceResolver` stack. Deterministic Runtime code retrieves and validates evidence, applies sufficiency policy, passes only an immutable `EvidencePack` to an `AnswerProvider`, verifies cited evidence IDs after generation, and projects a stable `QAResult`; `BookAppService` and FastAPI expose that result to a Chinese-first React QA page. CI and browser acceptance use only `DeterministicFakeAnswerProvider`, so repository verification never depends on an external model, API key, quota, or network call.

**Tech Stack:** Python 3.11/3.12/3.13, dataclasses + typing `Protocol`, existing Book Runtime, FastAPI + Pydantic, React 19 + TypeScript 5.9 + React Router, Vitest, Playwright Chromium, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-textbook-qa-phase-1f-design.md`

## Global Constraints

- Phase 1F QA is scoped to exactly one `course_id` and that course's enabled main textbook.
- The initial evidence retriever must reuse the audited Phase 1E `SearchRuntime`; do not add embeddings, vector databases, or a second search index.
- Every search hit used as QA evidence must be re-resolved through `SourceResolver` before model exposure.
- The provider receives only normalized `ProviderRequest` / `EvidencePack` content; never repository paths, raw files, browser state, credentials, unrelated courses, or arbitrary tool access.
- Provider citations are opaque server-issued evidence IDs (`E1`, `E2`, ...); the provider never owns canonical source identities, pages, anchors, or citation metadata.
- Final citations are projected only from server-owned evidence after verification.
- A successful provider-generated answer must contain at least one verified citation.
- `insufficient_evidence` is an HTTP 200 product result, must not call the provider, and uses `answer_kind="system_notice"`.
- Search/index/source trust-path failures are infrastructure errors (`qa_unavailable`), not evidence insufficiency.
- Provider unavailable is HTTP 503 `qa_provider_unavailable`; malformed/invalid provider output is HTTP 502 `qa_provider_invalid_response`.
- Generated prose must always be identified as generated and must never be written into textbook assets.
- CI and Playwright must use `DeterministicFakeAnswerProvider`; no external provider is required for Phase 1F acceptance.
- QA navigation state is short-lived `sessionStorage` only: `route`, `question`, `scrollY`, `activeCitationKey`; do not persist answer/citation payloads as StudyRecord/history.
- Existing Search → Source → Return and Section → Source → Return behavior must remain green.

---

## File Structure

### Runtime

- Create `runtime/qa_models.py` — immutable internal QA/evidence/provider dataclasses.
- Create `runtime/qa_provider.py` — `AnswerProvider` protocol, provider exceptions, deterministic fake provider.
- Create `runtime/qa_evidence.py` — `EvidenceRetriever`, `EvidencePolicy`, `CitationVerifier`.
- Create `runtime/qa_runtime.py` — question validation and orchestration only.
- Modify `runtime/__init__.py` — export stable QA Runtime interfaces/errors.
- Create `tests/test_qa_provider.py` — provider contract/fake-provider tests.
- Create `tests/test_qa_evidence.py` — real and fixture evidence/policy/verifier tests.
- Create `tests/test_qa_runtime.py` — QARuntime contract and orchestration tests.
- Modify `tests/runtime_fixture_factory.py` only when a QA-specific source/index fixture is required; preserve existing fixture behavior.

### App/API

- Modify `app/api/errors.py` — stable QA input/provider errors.
- Modify `app/api/models.py` — `QARequest`, `QACitationItem`, `QAResponse`.
- Modify `app/api/service.py` — inject/create QA provider and add `ask(course_id, question)` projection.
- Modify `app/api/main.py` — POST QA route, POST CORS allowance, 400/502/503 handlers.
- Modify `app_tests/test_app_service.py` — service QA projection/error mapping.
- Modify `app_tests/test_api.py` — POST contract/status semantics.
- Modify `app_tests/test_api_live.py` — real loopback deterministic QA smoke.

### Web

- Modify `app/web/src/api/types.ts` — typed QA DTOs.
- Modify `app/web/src/api/client.ts` — request method/body support + `askCourse`.
- Modify `app/web/src/api/client.test.ts` — POST request contract.
- Create `app/web/src/pages/QAPage.tsx` — Chinese-first QA UI.
- Create `app/web/src/pages/QAPage.test.tsx` — QA UI states/citations.
- Modify `app/web/src/pages/CoursePage.tsx` and `CoursePage.test.tsx` — add “教材问答” entry.
- Modify `app/web/src/routes/router.tsx` — `/courses/:courseId/qa`.
- Create `app/web/src/state/qaViewState.ts` and `.test.ts` — short-term return state.
- Modify `app/web/src/pages/SourcePage.tsx` and `.test.tsx` — QA citation return path without breaking Search/Section return paths.
- Modify `app/web/src/styles.css` — QA layout and narrow-screen rules only.

### Browser / CI / docs

- Modify `app/web/e2e/functional-analysis.spec.ts` — real textbook QA browser flows using deterministic provider.
- Modify `.github/workflows/runtime-reference-tests.yml` — compile/run QA Runtime tests and canonical QA smoke.
- Modify `.github/workflows/app-ui-tests.yml` — include QA service/API tests; browser job remains local-only.
- Modify `README.md`, `docs/ROADMAP.md`, and `docs/SEARCH_QA.md` after implementation gates are green.

---

### Task 1: Immutable QA Contracts and Deterministic Provider

**Files:**
- Create: `runtime/qa_models.py`
- Create: `runtime/qa_provider.py`
- Create: `tests/test_qa_provider.py`
- Modify: `runtime/__init__.py`

**Interfaces:**
- Produces `EvidenceItem`, `EvidencePack`, `ProviderRequest`, `ProviderAnswer`, `QACitation`, `QAResult` dataclasses.
- Produces `AnswerProvider.answer(request: ProviderRequest) -> ProviderAnswer`.
- Produces `DeterministicFakeAnswerProvider` for all repository tests/CI/browser acceptance.
- Produces provider errors `AnswerProviderError`, `AnswerProviderUnavailableError`, `AnswerProviderInvalidResponseError`.

- [ ] **Step 1: Write RED provider-contract tests**

Add tests equivalent to:

```python
from runtime.qa_models import EvidenceItem, EvidencePack, ProviderRequest
from runtime.qa_provider import DeterministicFakeAnswerProvider


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


def test_fake_provider_uses_only_supplied_evidence_ids():
    pack = EvidencePack(
        course_id="functional_analysis_course",
        book_id="stein_shakarchi_functional_analysis_2011",
        question="Hölder 不等式是什么？",
        evidence=(evidence(),),
    )
    result = DeterministicFakeAnswerProvider().answer(ProviderRequest.from_pack(pack))
    assert result.cited_evidence_ids == ("E1",)
    assert "Hölder" in result.answer_text
```

Also assert all dataclasses are frozen and provider request exposes no path/repository/browser fields.

- [ ] **Step 2: Run RED test**

Run:

```bash
python -m unittest tests.test_qa_provider -v
```

Expected: import failure because QA contract/provider modules do not exist.

- [ ] **Step 3: Implement minimal immutable contracts and fake provider**

Use frozen dataclasses. Required shapes:

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

@dataclass(frozen=True)
class ProviderAnswer:
    answer_text: str
    cited_evidence_ids: tuple[str, ...]
```

`DeterministicFakeAnswerProvider.answer()` must synthesize only from supplied evidence fields and cite deterministic IDs. It must not inspect Runtime, filesystem, environment, or global state.

- [ ] **Step 4: Run GREEN tests and compile**

```bash
python -m unittest tests.test_qa_provider -v
python -m compileall -q runtime/qa_models.py runtime/qa_provider.py
```

Expected: all provider tests pass; compile exits 0.

- [ ] **Step 5: Commit Task 1**

```bash
git add runtime/qa_models.py runtime/qa_provider.py runtime/__init__.py tests/test_qa_provider.py
git commit -m "feat: add textbook QA provider contracts"
```

---

### Task 2: Evidence Retrieval, Sufficiency Policy, Citation Verification, QARuntime

**Files:**
- Create: `runtime/qa_evidence.py`
- Create: `runtime/qa_runtime.py`
- Create: `tests/test_qa_evidence.py`
- Create: `tests/test_qa_runtime.py`
- Modify: `runtime/__init__.py`
- Modify: `tests/runtime_fixture_factory.py` only if a focused fixture is needed

**Interfaces:**
- Consumes `CourseRuntime`, `SearchRuntime.from_course(course).search(question, limit=N)`, `SourceResolver(course).resolve(kind, source_id)`.
- Produces `EvidenceRetriever.retrieve(question, *, limit) -> EvidencePack`.
- Produces `EvidencePolicy.status(pack) -> Literal["sufficient", "insufficient_evidence"]`.
- Produces `CitationVerifier.verify(pack, provider_answer) -> tuple[QACitation, ...]`.
- Produces `QARuntime.from_course(course, provider=...)` and `.answer(question, *, evidence_limit=8) -> QAResult`.

- [ ] **Step 1: Write RED evidence tests**

Test fixture and real Functional Analysis paths:

```python
runtime = EvidenceRetriever.from_course(course)
pack = runtime.retrieve("Hölder", limit=8)
assert pack.course_id == "functional_analysis_course"
assert pack.book_id == "stein_shakarchi_functional_analysis_2011"
assert pack.evidence
assert pack.evidence[0].evidence_id == "E1"
assert pack.evidence[0].source_kind == "object"
```

Add tests proving:
- duplicate `(source_kind, source_id)` rows collapse deterministically;
- each evidence identity resolves through `SourceResolver`;
- evidence IDs follow final deterministic rank (`E1`, `E2`, ...);
- unavailable/corrupt search index raises a QA retrieval/unavailable error, not an empty pack;
- no validated hits or top score `<= 300` yields `insufficient_evidence`;
- sufficient lexical/title/formula evidence yields `sufficient`.

- [ ] **Step 2: Run RED evidence tests**

```bash
python -m unittest tests.test_qa_evidence -v
```

Expected: import failure for `runtime.qa_evidence`.

- [ ] **Step 3: Implement `EvidenceRetriever` and `EvidencePolicy`**

Implementation rules:

```python
hits = SearchRuntime.from_course(course).search(question, limit=limit)
resolver = SourceResolver(course)
```

For each hit in order:
1. skip duplicates by `(hit.source_kind, hit.source_id)`;
2. resolve again with `resolver.resolve(...)`;
3. build `EvidenceItem` from resolved server-owned fields plus `hit.score`;
4. issue evidence IDs after validation/deduplication.

Map `SearchRuntimeError` and source integrity failures to a QA runtime unavailable exception; never convert them to insufficiency.

- [ ] **Step 4: Write RED citation-verifier tests**

Required cases:

```python
answer = ProviderAnswer(answer_text="supported", cited_evidence_ids=("E1", "E1"))
citations = verifier.verify(pack, answer)
assert [c.evidence_id for c in citations] == ["E1"]
```

Also assert:
- unknown `E99` => `AnswerProviderInvalidResponseError`;
- non-empty provider answer with zero citations => invalid response;
- final citation source metadata exactly equals server-owned evidence metadata;
- final citation is re-resolvable via `SourceResolver`.

- [ ] **Step 5: Implement `CitationVerifier` minimally**

Provider output contributes only `answer_text` and evidence IDs. All `QACitation` fields are copied from the matching `EvidenceItem`; dedupe by evidence ID preserving first occurrence.

- [ ] **Step 6: Write RED QARuntime orchestration tests**

Required cases:
- blank question rejected;
- >1000 Unicode code points rejected;
- `evidence_limit` outside 1..12 rejected;
- insufficient evidence does **not** call provider;
- insufficient result has `answer_kind="system_notice"` and stable Chinese non-assertive message;
- sufficient fake-provider result has `answer_kind="generated"`, verified citations, canonical course/book identity;
- provider unavailable and invalid provider response stay distinguishable.

Use a spy provider to assert no call on insufficient evidence:

```python
class FailIfCalledProvider:
    def answer(self, request):
        raise AssertionError("provider must not be called")
```

- [ ] **Step 7: Implement `QARuntime` orchestration**

Keep orchestration small:

```python
question = validate_question(...)
pack = self._retriever.retrieve(question, limit=evidence_limit)
status = self._policy.status(pack)
if status == "insufficient_evidence":
    return QAResult.system_notice(...)
provider_answer = self._provider.answer(ProviderRequest.from_pack(pack))
citations = self._verifier.verify(pack, provider_answer)
return QAResult.generated(...)
```

- [ ] **Step 8: Run Task 2 GREEN gates**

```bash
python -m unittest tests.test_qa_evidence tests.test_qa_runtime tests.test_qa_provider -v
python -m unittest tests.test_search_runtime tests.test_source_resolver -v
python -m compileall -q runtime/qa_models.py runtime/qa_provider.py runtime/qa_evidence.py runtime/qa_runtime.py
```

Expected: zero failures.

- [ ] **Step 9: Commit Task 2**

```bash
git add runtime/qa_evidence.py runtime/qa_runtime.py runtime/__init__.py tests/test_qa_evidence.py tests/test_qa_runtime.py tests/runtime_fixture_factory.py
git commit -m "feat: add source-verified textbook QA runtime"
```

---

### Task 3: Stable App Service and POST QA API

**Files:**
- Modify: `app/api/errors.py`
- Modify: `app/api/models.py`
- Modify: `app/api/service.py`
- Modify: `app/api/main.py`
- Modify: `app_tests/test_app_service.py`
- Modify: `app_tests/test_api.py`
- Modify: `app_tests/test_api_live.py`

**Interfaces:**
- Consumes `QARuntime` and a configured `AnswerProvider`.
- Produces `BookAppService.ask(course_id: str, question: str) -> QAResponse`.
- Produces `POST /api/courses/{course_id}/qa` with JSON `{"question": "..."}`.

- [ ] **Step 1: Write RED service tests**

Add stable DTO assertions:

```python
response = service.ask("functional_analysis_course", "Hölder")
assert response.answer_kind == "generated"
assert response.evidence_status == "sufficient"
assert response.citations[0].source_kind == "object"
```

Inject `DeterministicFakeAnswerProvider` through `BookAppService` constructor or a narrow provider factory. Do not make service tests rely on environment/API keys.

Add mapping tests for invalid question, QA retrieval unavailable, provider unavailable, invalid provider output.

- [ ] **Step 2: Run RED service tests**

```bash
python -m unittest app_tests.test_app_service -v
```

Expected: new QA tests fail because `ask`/DTO/errors are absent; existing tests remain green.

- [ ] **Step 3: Implement API DTOs and service projection**

Add Pydantic types:

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

Use stable App errors rather than exposing Runtime/provider exception text.

- [ ] **Step 4: Write RED HTTP tests**

Required HTTP behavior:

```text
POST valid question                    -> 200 QAResponse
POST insufficient question             -> 200, insufficient_evidence
POST blank/overlong                     -> 400 invalid_qa_question
POST unknown course                     -> 404 course_not_found
retrieval/source trust failure          -> 503 qa_unavailable
provider unavailable                    -> 503 qa_provider_unavailable
provider invalid response/citation      -> 502 qa_provider_invalid_response
```

Also verify request body validation is projected into the chosen stable 400 contract rather than leaking FastAPI/Pydantic internals.

- [ ] **Step 5: Implement POST route and CORS**

Update `allow_methods` from GET-only to exactly the local methods now required, e.g. `['GET', 'POST']`.

Route:

```python
@app.post("/api/courses/{course_id}/qa", response_model=QAResponse)
def qa(course_id: str, payload: QARequest, service: BookAppService = Depends(get_service)) -> QAResponse:
    return service.ask(course_id, payload.question)
```

Keep `127.0.0.1` / localhost origin restriction unchanged.

- [ ] **Step 6: Add real loopback deterministic QA smoke**

Use Uvicorn/live test path and assert a real Functional Analysis query returns at least one verified citation. The test provider remains deterministic and local.

- [ ] **Step 7: Run Task 3 GREEN gates**

```bash
python -m unittest app_tests.test_app_service app_tests.test_api app_tests.test_api_live -v
python -m unittest tests.test_qa_provider tests.test_qa_evidence tests.test_qa_runtime -v
```

Expected: zero failures.

- [ ] **Step 8: Commit Task 3**

```bash
git add app/api/errors.py app/api/models.py app/api/service.py app/api/main.py app_tests/test_app_service.py app_tests/test_api.py app_tests/test_api_live.py
git commit -m "feat: expose source-verified textbook QA api"
```

---

### Task 4: Typed Web Client and Chinese-first QA Page

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
- Produces `bookApi.askCourse(courseId, question) -> Promise<QAResponse>`.
- Produces route `/courses/:courseId/qa`.
- Citation links reuse `/courses/:courseId/sources/:sourceKind/:sourceId`.

- [ ] **Step 1: Write RED typed-client test**

Assert exact request method/body:

```ts
await bookApi.askCourse('functional_analysis_course', 'Hölder 是什么？')
expect(fetch).toHaveBeenCalledWith(
  '/api/courses/functional_analysis_course/qa',
  expect.objectContaining({
    method: 'POST',
    headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ question: 'Hölder 是什么？' }),
  }),
)
```

- [ ] **Step 2: Run RED client test**

```bash
cd app/web && npm test -- --run src/api/client.test.ts
```

Expected: failure because request helper/`askCourse` supports GET only.

- [ ] **Step 3: Extend request helper without regressing GET calls**

Use a narrow optional `RequestInit` path. GET callers continue to send only `Accept`; POST sends `Accept`, `Content-Type: application/json`, method, and JSON body. Preserve stable `ApiError` parsing.

- [ ] **Step 4: Write RED QAPage tests**

Cover:
- initial empty question state does not issue API request;
- submit -> loading status;
- generated result shows persistent label `AI 生成回答，依据下方教材来源`;
- `system_notice` insufficient result does not show generated label;
- citations render title/page metadata and source link from `source_kind + source_id`;
- `qa_unavailable`, `qa_provider_unavailable`, and `qa_provider_invalid_response` show stable user-facing error state;
- course page has `教材问答` link;
- route resolves QAPage.

- [ ] **Step 5: Run RED page tests**

```bash
cd app/web && npm test -- --run src/pages/QAPage.test.tsx src/pages/CoursePage.test.tsx
```

Expected: QAPage/module/entry tests fail only for missing Phase 1F UI.

- [ ] **Step 6: Implement QAPage and typed DTOs**

Keep page state explicit:

```text
empty -> loading -> sufficient | insufficient_evidence | error
```

Do not call QA on every keystroke. Submit only on form submit. Disable duplicate submission while loading. Do not call generated answer “教材原文”.

- [ ] **Step 7: Run Web GREEN gates**

```bash
cd app/web
npm test
npm run typecheck
npm run build
```

Expected: all unit tests, TypeScript, and Vite/PWA build pass.

- [ ] **Step 8: Commit Task 4**

```bash
git add app/web/src/api app/web/src/pages/QAPage.tsx app/web/src/pages/QAPage.test.tsx app/web/src/pages/CoursePage.tsx app/web/src/pages/CoursePage.test.tsx app/web/src/routes/router.tsx app/web/src/styles.css
git commit -m "feat: add textbook QA page"
```

---

### Task 5: QA → Source → Return Context

**Files:**
- Create: `app/web/src/state/qaViewState.ts`
- Create: `app/web/src/state/qaViewState.test.ts`
- Modify: `app/web/src/pages/QAPage.tsx`
- Modify: `app/web/src/pages/QAPage.test.tsx`
- Modify: `app/web/src/pages/SourcePage.tsx`
- Modify: `app/web/src/pages/SourcePage.test.tsx`

**Interfaces:**
- Produces `saveQAViewState(courseId, state)`, `loadQAViewState(courseId)`, `clearQAViewState(courseId)`.
- State shape: `{ route, question, scrollY, activeCitationKey }` only.
- `activeCitationKey` is canonical `${source_kind}:${source_id}` so SourcePage can match without cached answer payloads.

- [ ] **Step 1: Write RED state-helper tests**

Assert:
- namespaced key `book:qa-view:${courseId}`;
- JSON corruption returns `null` and does not crash;
- invalid shape returns `null`;
- helper stores only `route/question/scrollY/activeCitationKey`.

- [ ] **Step 2: Run RED helper test**

```bash
cd app/web && npm test -- --run src/state/qaViewState.test.ts
```

Expected: module missing.

- [ ] **Step 3: Implement minimal QA state helper**

Match existing `searchViewState` validation style; do not generalize unrelated state helpers.

- [ ] **Step 4: Write RED QAPage/SourcePage return tests**

Required behavior:
1. clicking citation first saves current QA route, question, `window.scrollY`, canonical source key;
2. SourcePage detects matching QA state and renders button `返回问答`;
3. matching QA state has priority over stale matching Search state because the current source was entered from QA;
4. clicking `返回问答` navigates to saved QA route;
5. QAPage re-runs `askCourse` from saved question, then restores scroll and marks matching citation `aria-current="true"`;
6. full QA result is not stored in sessionStorage;
7. if no QA match exists, existing Search return behavior remains unchanged;
8. if neither QA nor Search matches, existing Section return behavior remains unchanged.

- [ ] **Step 5: Implement return flow**

SourcePage matching priority:

```text
matching QA state -> 返回问答
matching Search state -> 返回搜索
matching Section state -> 返回学习
fallback -> Course/Section behavior already defined
```

Do not create a second source page.

- [ ] **Step 6: Run Task 5 GREEN gates**

```bash
cd app/web
npm test
npm run typecheck
npm run build
```

Expected: all QA/Search/Source/Section unit tests remain green.

- [ ] **Step 7: Commit Task 5**

```bash
git add app/web/src/state/qaViewState.ts app/web/src/state/qaViewState.test.ts app/web/src/pages/QAPage.tsx app/web/src/pages/QAPage.test.tsx app/web/src/pages/SourcePage.tsx app/web/src/pages/SourcePage.test.tsx
git commit -m "feat: restore textbook QA source context"
```

---

### Task 6: Real Browser Acceptance and CI Hardening

**Files:**
- Modify: `app/web/e2e/functional-analysis.spec.ts`
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Modify: `.github/workflows/app-ui-tests.yml`

**Interfaces:**
- Browser tests use real Functional Analysis assets and the deterministic local provider.
- CI must verify QA trust logic without external network/model dependencies.

- [ ] **Step 1: Add Playwright acceptance cases**

Add cases for:
- English question with real theorem evidence (`Hölder`-based query);
- Chinese question with real textbook evidence;
- clearly nonexistent question returns normal `insufficient_evidence`, not alert/error;
- QA citation -> existing source page -> `返回问答` -> question/citation context restored;
- 390×844 QA/source round trip has `scrollWidth <= clientWidth`.

For generated results, assert the UI label and canonical source route, not exact natural-language wording beyond the deterministic fake-provider contract.

- [ ] **Step 2: Run local E2E gate**

Start API and Vite exactly as current workflow does, then:

```bash
cd app/web && npm run e2e
```

Expected: existing 5 Phase 1D/1E tests plus new QA cases all pass.

- [ ] **Step 3: Harden Runtime workflow**

Extend compile/test commands to include `qa_models.py`, `qa_provider.py`, `qa_evidence.py`, `qa_runtime.py`, and QA unit modules. Add a canonical Functional Analysis smoke that:
- opens real course;
- answers a known query through deterministic provider;
- obtains `sufficient` and at least one citation;
- asks a nonexistent query and obtains `insufficient_evidence` without provider call.

Ensure QA workflow paths trigger when QA files and canonical search/source assets change.

- [ ] **Step 4: Harden App UI workflow**

App API job must run QA service/API tests. Browser job keeps localhost API + Vite + Chromium only. No provider secrets/environment variables are required.

- [ ] **Step 5: Commit Task 6**

```bash
git add app/web/e2e/functional-analysis.spec.ts .github/workflows/runtime-reference-tests.yml .github/workflows/app-ui-tests.yml
git commit -m "ci: gate source-verified textbook QA"
```

---

### Task 7: Documentation, Full Regression, and PR Readiness

**Files:**
- Modify: `README.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/SEARCH_QA.md`

**Interfaces:**
- No new runtime interfaces. This task documents only behavior proven by Tasks 1-6.

- [ ] **Step 1: Update documentation after code gates are green**

Document:
- Phase 1F trusted QA architecture;
- deterministic evidence retrieval and citation verification;
- explicit generated vs system-notice distinction;
- provider-agnostic design and deterministic CI provider;
- QA → Source → Return;
- explicit non-goals: no cross-course QA, no embeddings/vector DB, no StudyRecord/history, no generated textbook writes.

Update ROADMAP Phase 1F checklist only for behavior actually verified. Set the next mainline to Phase 1G long-term StudyRecord only after all final verification gates pass.

- [ ] **Step 2: Run full Python verification**

Run the exact Runtime/App suites used by workflows, including:

```bash
python -m unittest \
  tests.test_qa_provider \
  tests.test_qa_evidence \
  tests.test_qa_runtime \
  tests.test_search_runtime \
  tests.test_source_resolver \
  app_tests.test_app_service \
  app_tests.test_api \
  app_tests.test_api_live -v
```

Then run the repository's existing broader Runtime reference test command from `.github/workflows/runtime-reference-tests.yml` on Python 3.11, 3.12 and 3.13 through GitHub Actions.

- [ ] **Step 3: Run full Web verification**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
npm run e2e
```

Expected: zero failures and browser acceptance includes all existing Search/Section cases plus new QA cases.

- [ ] **Step 4: Verify canonical Functional Analysis invariants**

Confirm existing completion/runtime checks still report:

```text
STRUCTURED_COMPLETE / RUNTIME_READY
8 chapters / 132 sections
442 PageMap rows
1493 unique search records
```

Phase 1F must not modify `books/functional-analysis/**` structured textbook assets.

- [ ] **Step 5: Compare branch to main and inspect scope**

Expected differences are QA Runtime/API/Web/tests/CI/docs only. Reject unrelated changes or modifications to canonical textbook assets.

- [ ] **Step 6: Commit documentation**

```bash
git add README.md docs/ROADMAP.md docs/SEARCH_QA.md
git commit -m "docs: document Phase 1F textbook QA"
```

- [ ] **Step 7: Fresh PR-readiness verification**

Before claiming completion or opening the PR:
- re-run/fetch fresh GitHub Actions on the final head;
- require Runtime reference tests success;
- require App API success;
- require Web unit/typecheck/build success;
- require Chromium acceptance success;
- verify branch head did not move after the validated SHA;
- verify no textbook structured asset changed.

Only after that evidence, create a PR from `feature/textbook-qa-phase-1f` to `main`.
