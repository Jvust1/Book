# Phase 1F 教材内问答 v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 `feature/textbook-qa-phase-1f` 预实现基础上，按已批准 v2 设计补齐 Section 优先→全书 fallback、session-only 连续追问、OpenAI-compatible Provider、双重证据门、严格结构化输出与不重复生成的 QA→Source→QA 往返，并保持 Phase 1D/1E 全部能力不回归。

**Architecture:** 保留现有 Runtime→App Service→FastAPI→React 边界和已有 SearchRuntime/SourceResolver/citation trust chain；把 QA 契约升级为 `question + optional section_id + bounded history`，由 Runtime 先完成确定性检索与服务器 EvidenceGate，再把有限 EvidencePack 交给 `ModelProvider`。Provider 只能返回严格结构化 `ModelResponse` 和服务器发放的 `evidence_id`；CitationValidator 再映射回 canonical source identity。浏览器只持有当前会话已验证回答与 citation identity，不持有 EvidencePack、Key、prompt 或 provider raw response。

**Tech Stack:** Python 3.11–3.13 standard library Runtime, FastAPI/Pydantic, httpx, React 19 + TypeScript + Vite, Vitest/Testing Library, Playwright Chromium, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-textbook-qa-phase-1f-design.md`

## Global Constraints

- Implementation baseline is existing `feature/textbook-qa-phase-1f@f550bd67f3ade9318eac2ef0e6b4acf2d61717d7`; do not discard reusable Phase 1F work merely because it predates the approved spec.
- Approved design source is `design/textbook-qa-phase-1f-v2@95c87b0ca8236834f512edb5f81a2dbdfa4d19a6` plus this plan commit; implementation must first replace the old Phase 1F spec/plan on the feature branch with the approved versions.
- First release answers only from the current course's enabled main textbook; model background knowledge, web search and cross-course sources are forbidden.
- Section entry uses current Section first and expands to current textbook only when the Section server gate is insufficient; Course entry searches the textbook directly.
- Every turn performs fresh textbook retrieval; previous assistant text is dialogue context only and is never evidence.
- Maximum model evidence: 8 items and 12,000 Unicode code points of evidence text.
- Maximum dialogue context: 6 recent messages and 6,000 Unicode code points, dropping oldest messages first.
- Provider output must validate as `answer`, `evidence_ids`, `insufficient_evidence`, `answer_style`; `answer_style ∈ {brief, explain, compare, proof}`.
- A visible generated answer requires server EvidenceGate sufficient AND provider `insufficient_evidence=false` AND CitationValidator valid.
- Unknown citation IDs, empty citations for a successful answer, invalid JSON/schema and canonical identity drift fail closed.
- Online provider credentials are server-side only: `BOOK_QA_BASE_URL`, `BOOK_QA_API_KEY`, `BOOK_QA_MODEL`; optional timeout defaults to 60 seconds.
- Real API keys, EvidencePack text, provider prompts and provider raw responses must never enter browser storage, Git, Drive sync artifacts or default logs.
- CI must never require a paid/external model call; deterministic fake provider drives Runtime/API/Web/Playwright tests.
- Do not modify Functional Analysis canonical textbook facts, search index, PageMap, source IDs, source anchors or structured content merely to satisfy QA tests.
- Chinese remains primary UI language. Existing Phase 1D/1E routes and acceptance behavior must remain green.

---

## Existing-branch gap audit

### Reuse as foundation

- `runtime/qa_runtime.py`: already owns retrieval→provider→citation orchestration and rejects blank/overlong questions.
- `runtime/qa_evidence.py`: already has bounded lexical probes, deterministic dedupe, SourceResolver revalidation, a conservative evidence gate and fail-closed citation validation.
- `runtime/qa_provider.py`: already separates a provider protocol from trusted retrieval and has deterministic fake/unavailable providers.
- `app/api/service.py`, `models.py`, `main.py`: already expose a QA service/endpoint with stable Chinese error semantics.
- `app/web/src/pages/QAPage.tsx`, `SourcePage.tsx`: already have a generated-answer label, citation links and a Source return path.
- Existing Python/App/Web/Playwright/CI tests provide a useful regression base.

### Must change to satisfy the approved spec

1. `QARuntime.answer()` currently accepts only `question` and an evidence limit; it has no `section_id`, history, scope metadata or provider second-gate result.
2. `EvidenceRetriever` currently searches the whole course immediately; it has no Section-first retrieval, no book fallback state and no 12,000-codepoint total evidence budget.
3. `SearchRuntime.search()` has no additive Section filter, so Section scope cannot be applied before result-limit truncation.
4. Current evidence items omit `course_id`, `book_id`, `chapter_id`, `section_id` and `type_zh` required by the v2 trust/DTO contract.
5. Current provider answer is only `answer_text + cited_evidence_ids`; no `insufficient_evidence` or `answer_style` exists.
6. Current provider factory supports only `fake` or unavailable; it does not implement OpenAI-compatible HTTP or the three server-side user configuration variables.
7. API request is `{question}` only; response lacks `answer_style`, `scope_requested`, `scope_used`, `insufficient_evidence`, `message`, and citation chapter/section/type_zh fields.
8. QAPage is one-shot. `qaViewState` stores one question only; there is no shared course conversation session.
9. Source return currently re-runs `bookApi.askCourse()` to reconstruct the answer, causing duplicate model cost and nondeterministic wording.
10. SectionPage has no “问本节内容” entry and QAPage has no `?section=` scope UI.
11. Existing tests validate the old contract and must be migrated before ROADMAP can mark 1F complete.

---

## File structure after the v2 correction

### Runtime trust layer

- Modify `runtime/search_runtime.py` — additive optional Section filter with unchanged default search behavior.
- Modify `runtime/qa_models.py` — QA history, scope, bounded evidence, strict provider response and final result contracts.
- Modify `runtime/qa_evidence.py` — EvidenceBuilder/Gate, Section/book retrieval and citation projection.
- Modify `runtime/qa_runtime.py` — v2 orchestration and double evidence gate.
- Modify `runtime/qa_provider.py` — `ModelProvider` protocol, deterministic fake modes, unavailable provider.
- Modify `runtime/__init__.py` — export final v2 public contracts only.

### Server/provider adapter

- Create `app/api/openai_compatible_provider.py` — httpx implementation of `ModelProvider`; no retrieval logic.
- Modify `app/api/qa_provider_factory.py` — server-only configuration and fake CI selection.
- Create `.env.example` — empty QA configuration template.
- Create `.gitignore` if absent — exclude `.env` and common local secret variants.
- Modify `app/api/models.py`, `service.py`, `main.py`, `errors.py` — v2 request/response/error boundary.

### Web/session layer

- Modify `app/web/src/api/types.ts`, `client.ts` — typed v2 QA request/response.
- Replace `app/web/src/state/qaViewState.ts` with course-level `qaSessionState.ts` semantics; if keeping the old filename for migration, its exported contract must be the v2 session contract.
- Modify `app/web/src/pages/QAPage.tsx` — conversation UI, Section scope, no auto re-call on restore.
- Modify `app/web/src/pages/SectionPage.tsx` and `CoursePage.tsx` — dual QA entry points.
- Modify `app/web/src/pages/SourcePage.tsx` — return against the new QA session identity.
- Modify `app/web/src/styles.css` — scope and conversation presentation, narrow-screen safety.

### Tests/docs/CI

- Modify `tests/test_search_runtime.py`, `tests/test_qa_evidence.py`, `tests/test_qa_runtime.py`, `tests/test_qa_provider.py`.
- Create `app_tests/test_openai_compatible_provider.py`.
- Modify `app_tests/test_qa_provider_factory.py`, `test_qa_service.py`, `test_qa_api.py`, `test_api_live.py`.
- Modify web API/page/state tests and `app/web/e2e/functional-analysis.spec.ts`.
- Modify both GitHub workflows only where required by new test files/commands.
- Update `README.md`, `app/README.md`, `docs/ROADMAP.md` only after all completion-gate tests pass.

---

### Task 1: Align the implementation branch with the approved v2 design

**Files:**
- Replace: `docs/superpowers/specs/2026-08-27-textbook-qa-phase-1f-design.md`
- Replace: `docs/superpowers/plans/2026-08-27-textbook-qa-phase-1f.md` with the approved v2 plan content or remove it after adding `docs/superpowers/plans/2026-08-27-textbook-qa-phase-1f-v2.md`
- Add: `docs/superpowers/plans/2026-08-27-textbook-qa-phase-1f-v2.md`

**Interfaces:**
- Consumes: approved design branch `design/textbook-qa-phase-1f-v2`.
- Produces: one feature branch whose docs and code are governed by the same v2 spec.

- [ ] **Step 1: Create an isolated execution worktree from the existing feature head**

```bash
git fetch origin
git worktree add ../Book-phase1f-v2 feature/textbook-qa-phase-1f
cd ../Book-phase1f-v2
git rev-parse HEAD
```

Expected HEAD: `f550bd67f3ade9318eac2ef0e6b4acf2d61717d7` or a later explicitly reviewed descendant of that branch.

- [ ] **Step 2: Bring only the approved v2 design/plan documents into the worktree**

```bash
git checkout design/textbook-qa-phase-1f-v2 -- \
  docs/superpowers/specs/2026-08-27-textbook-qa-phase-1f-design.md \
  docs/superpowers/plans/2026-08-27-textbook-qa-phase-1f-v2.md
```

- [ ] **Step 3: Verify no runtime/app code changed in this alignment step**

```bash
git status --short
git diff --name-only
```

Expected changed paths are documentation only.

- [ ] **Step 4: Commit the approved design baseline**

```bash
git add docs/superpowers/specs/2026-08-27-textbook-qa-phase-1f-design.md \
        docs/superpowers/plans/2026-08-27-textbook-qa-phase-1f-v2.md
git commit -m "docs: align Phase 1F with approved v2 design"
```

---

### Task 2: Add Section filtering to SearchRuntime without changing normal search

**Files:**
- Modify: `runtime/search_runtime.py`
- Modify: `tests/test_search_runtime.py`

**Interfaces:**
- Consumes: `RuntimeObject.section_id`; for figures, canonical `SourceResolver.resolve(...).section_id` at index-load time.
- Produces: `SearchRuntime.search(query: str, *, limit: int = 30, section_id: str | None = None) -> list[SearchHit]`.

- [ ] **Step 1: Write failing tests for additive Section filtering and default-regression equality**

Add tests equivalent to:

```python
def test_section_filter_is_applied_before_limit(self) -> None:
    runtime = SearchRuntime.from_course(self.course)
    hits = runtime.search("空间", limit=1, section_id="sec_b")
    self.assertEqual([hit.source_id for hit in hits], ["def_b_only"])


def test_omitting_section_filter_preserves_existing_result_order(self) -> None:
    runtime = SearchRuntime.from_course(self.course)
    baseline = runtime.search("空间", limit=20)
    explicit_none = runtime.search("空间", limit=20, section_id=None)
    self.assertEqual(baseline, explicit_none)
```

The fixture must contain at least two matching sources in different Sections, with the globally higher-ranked source outside `sec_b`, so filtering-after-limit would fail.

- [ ] **Step 2: Run the new SearchRuntime tests and confirm failure**

```bash
python -m unittest tests.test_search_runtime -v
```

Expected: failure because `search()` does not accept `section_id`.

- [ ] **Step 3: Add canonical Section identity to `_SearchCandidate` and filter before ranking/limit**

Implement the public signature:

```python
def search(
    self,
    query: str,
    *,
    limit: int = 30,
    section_id: str | None = None,
) -> list[SearchHit]:
```

Candidate rules:

```python
if source_id in book.objects:
    section_id = book.objects[source_id].section_id
elif source_id in book.figures:
    section_id = SourceResolver(course).resolve("figure", source_id).section_id
```

Normalize an explicitly supplied Section ID with `str(section_id).strip()` and reject a blank supplied value with `SearchQueryError`. During the candidate loop, skip candidates whose canonical Section differs before `_score()` results are sliced to `limit`.

- [ ] **Step 4: Run SearchRuntime plus Phase 1E regression tests**

```bash
python -m unittest tests.test_search_runtime app_tests.test_search_api -v
```

If `app_tests.test_search_api` does not exist in the branch, run the existing search App/API test module named by `.github/workflows/app-ui-tests.yml`; do not invent a replacement command in CI.

- [ ] **Step 5: Commit the additive search capability**

```bash
git add runtime/search_runtime.py tests/test_search_runtime.py
git commit -m "feat: add section-scoped textbook search"
```

---

### Task 3: Upgrade immutable QA contracts for scope, history, evidence and structured model output

**Files:**
- Modify: `runtime/qa_models.py`
- Modify: `tests/test_qa_provider.py`
- Modify: `tests/test_qa_runtime.py`

**Interfaces:**
- Consumes: canonical Section/source identity.
- Produces:
  - `QAHistoryMessage(role, content)`
  - `EvidenceItem` with course/book/chapter/section/type_zh fields
  - `EvidencePack(scope_requested, scope_used, evidence)`
  - `ModelRequest(question, section_id, history, evidence)`
  - `ModelResponse(answer, evidence_ids, insufficient_evidence, answer_style)`
  - `QAResult` with `answer_style`, scopes, `insufficient_evidence`, `message`.

- [ ] **Step 1: Write failing model-contract tests**

Add tests covering these exact valid/invalid cases:

```python
valid = ModelResponse.from_mapping({
    "answer": "巴拿赫空间是完备赋范线性空间。",
    "evidence_ids": ["E1"],
    "insufficient_evidence": False,
    "answer_style": "brief",
})
self.assertEqual(valid.answer_style, "brief")

with self.assertRaises(ModelResponseValidationError):
    ModelResponse.from_mapping({
        "answer": "回答",
        "evidence_ids": [],
        "insufficient_evidence": False,
        "answer_style": "brief",
    })

with self.assertRaises(ModelResponseValidationError):
    ModelResponse.from_mapping({
        "answer": "回答",
        "evidence_ids": ["E1"],
        "insufficient_evidence": False,
        "answer_style": "essay",
    })
```

- [ ] **Step 2: Run provider/runtime tests and verify contract failures**

```bash
python -m unittest tests.test_qa_provider tests.test_qa_runtime -v
```

- [ ] **Step 3: Replace the old `ProviderRequest/ProviderAnswer` shape with v2 names and strict validation**

Use these type domains:

```python
AnswerStyle = Literal["brief", "explain", "compare", "proof"]
ScopeRequested = Literal["book", "section_then_book"]
ScopeUsed = Literal["section", "book"]
HistoryRole = Literal["user", "assistant"]
```

`ModelResponse.from_mapping()` must reject unknown/invalid types, reject a successful blank answer, reject successful empty evidence IDs, and accept an insufficient response with `answer=None` and an empty evidence list.

- [ ] **Step 4: Add stable server notice construction to `QAResult`**

The insufficient result must carry:

```python
answer=None
answer_kind="system_notice"
insufficient_evidence=True
message="根据当前教材中检索到的内容，暂时无法可靠回答这个问题。"
citations=()
```

Generated results carry `message=None` and `insufficient_evidence=False`.

- [ ] **Step 5: Run the contract tests**

```bash
python -m unittest tests.test_qa_provider tests.test_qa_runtime -v
```

Expected: PASS.

- [ ] **Step 6: Commit the v2 contracts**

```bash
git add runtime/qa_models.py tests/test_qa_provider.py tests/test_qa_runtime.py
git commit -m "refactor: upgrade textbook QA contracts"
```

---

### Task 4: Implement bounded history and Section→book EvidenceBuilder/Gate

**Files:**
- Modify: `runtime/qa_evidence.py`
- Modify: `runtime/qa_runtime.py`
- Modify: `runtime/__init__.py`
- Modify: `tests/test_qa_evidence.py`
- Modify: `tests/test_qa_runtime.py`
- Modify fixture helpers only if needed: `tests/runtime_fixture_factory.py`

**Interfaces:**
- Consumes: `SearchRuntime.search(..., section_id=...)`, `SourceResolver`, v2 QA models.
- Produces:
  - `normalize_history(history) -> tuple[QAHistoryMessage, ...]`
  - `EvidenceBuilder.build(question, *, section_id, limit=8) -> EvidencePack`
  - `EvidenceGate.status(pack) -> sufficient|insufficient_evidence`
  - `QARuntime.answer(question, *, section_id=None, history=()) -> QAResult`.

- [ ] **Step 1: Write failing tests for all scope transitions**

Fixture must contain at least `sec_a` and `sec_b`. Add tests asserting:

```python
result = runtime.answer("A 中的概念是什么？", section_id="sec_a")
self.assertEqual(result.scope_requested, "section_then_book")
self.assertEqual(result.scope_used, "section")

result = runtime.answer("B 中的概念是什么？", section_id="sec_a")
self.assertEqual(result.scope_requested, "section_then_book")
self.assertEqual(result.scope_used, "book")

result = runtime.answer("B 中的概念是什么？")
self.assertEqual(result.scope_requested, "book")
self.assertEqual(result.scope_used, "book")
```

Also assert the provider is not called when both Section and book gates fail.

- [ ] **Step 2: Write failing tests for history validation/bounding**

Use more than six alternating messages and more than 6,000 code points. Assert output keeps at most six most-recent messages, total content length `<= 6000`, and malformed roles/blank content raise `QAQuestionError`.

- [ ] **Step 3: Write failing tests for EvidencePack metadata and text budget**

Assert every evidence row contains canonical `course_id`, `book_id`, `chapter_id`, `section_id`, `type_zh`; total included `content_zh + formula` code points are `<= 12000`; item count is `<= 8`; `source_anchor` remains `None` when canonical source has no anchor.

- [ ] **Step 4: Run the evidence/runtime tests and verify failures**

```bash
python -m unittest tests.test_qa_evidence tests.test_qa_runtime -v
```

- [ ] **Step 5: Refactor `EvidenceRetriever` into the v2 builder/gate behavior**

Required orchestration:

```python
if section_id is not None:
    section_pack = builder.build(question, section_id=section_id)
    if EvidenceGate.status(section_pack) == "sufficient":
        return section_pack.with_scope("section_then_book", "section")

book_pack = builder.build(question, section_id=None)
return book_pack.with_scope(
    "section_then_book" if section_id is not None else "book",
    "book",
)
```

Book fallback may include canonical hits from the original Section; do not artificially exclude them.

EvidenceGate minimums: at least one resolved item, at least one item with nonblank `content_zh` or `formula`, and max search score > 300.

- [ ] **Step 6: Enforce deterministic evidence budgets**

Use constants:

```python
MAX_EVIDENCE_ITEMS = 8
MAX_EVIDENCE_TEXT_CODEPOINTS = 12000
MAX_HISTORY_MESSAGES = 6
MAX_HISTORY_TEXT_CODEPOINTS = 6000
```

Add evidence in deterministic rank order. When a source would exceed the remaining text budget, include only the canonical fields and the prefix of `content_zh`/`formula` that fits; never append invented explanatory text. A truncated excerpt is model context only and must not overwrite the source citation payload.

- [ ] **Step 7: Upgrade QARuntime double-gate orchestration**

`QARuntime.answer()` validates `section_id` by resolving it through the current course before generation, normalizes history, performs server-gated retrieval, calls the provider only after sufficiency, treats `ModelResponse.insufficient_evidence=True` as a normal server-authored insufficient result, and only then calls CitationValidator.

- [ ] **Step 8: Run all Runtime QA and search tests**

```bash
python -m unittest tests.test_search_runtime tests.test_qa_evidence tests.test_qa_provider tests.test_qa_runtime -v
```

- [ ] **Step 9: Commit the trusted v2 QA core**

```bash
git add runtime/search_runtime.py runtime/qa_models.py runtime/qa_evidence.py runtime/qa_runtime.py runtime/__init__.py \
        tests/test_search_runtime.py tests/test_qa_evidence.py tests/test_qa_provider.py tests/test_qa_runtime.py tests/runtime_fixture_factory.py
git commit -m "feat: add scoped evidence and double-gated QA"
```

---

### Task 5: Implement strict ModelProvider behavior and deterministic fake scenarios

**Files:**
- Modify: `runtime/qa_provider.py`
- Modify: `tests/test_qa_provider.py`
- Modify: `tests/test_qa_runtime.py`

**Interfaces:**
- Consumes: `ModelRequest`, `ModelResponse`.
- Produces: `ModelProvider` protocol, `DeterministicFakeModelProvider`, `UnavailableModelProvider`, stable provider errors.

- [ ] **Step 1: Write failing fake-provider scenario tests**

The fake provider must support deterministic modes:

```python
provider = DeterministicFakeModelProvider(mode="answer")
provider = DeterministicFakeModelProvider(mode="insufficient")
provider = DeterministicFakeModelProvider(mode="invalid_citation")
provider = DeterministicFakeModelProvider(mode="empty_answer")
provider = DeterministicFakeModelProvider(mode="unavailable")
```

Assert `answer` produces a legal evidence ID and deterministic style, `insufficient` returns `insufficient_evidence=True`, invalid/empty modes exercise fail-closed paths, and unavailable raises the provider-unavailable error.

- [ ] **Step 2: Run provider tests and verify failure**

```bash
python -m unittest tests.test_qa_provider -v
```

- [ ] **Step 3: Implement the v2 protocol and fake modes**

Protocol signature:

```python
class ModelProvider(Protocol):
    def answer(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError
```

The deterministic normal fake must use only `request.evidence[0]`, cite that row's `evidence_id`, and never synthesize source/page identities.

- [ ] **Step 4: Make QARuntime tests use the renamed provider contracts**

Update old `AnswerProvider*` names consistently; do not leave compatibility aliases unless an existing public import outside QA requires them and a regression test demonstrates that need.

- [ ] **Step 5: Run Runtime QA suite**

```bash
python -m unittest tests.test_qa_provider tests.test_qa_runtime -v
```

- [ ] **Step 6: Commit provider-contract cleanup**

```bash
git add runtime/qa_provider.py runtime/__init__.py tests/test_qa_provider.py tests/test_qa_runtime.py
git commit -m "refactor: enforce structured QA model provider"
```

---

### Task 6: Add the OpenAI-compatible server adapter and secret-safe configuration

**Files:**
- Create: `app/api/openai_compatible_provider.py`
- Modify: `app/api/qa_provider_factory.py`
- Modify: `app/api/requirements.txt` only if httpx version constraints need no change; current branch already has `httpx>=0.27,<1`, so no dependency addition is expected.
- Create: `app_tests/test_openai_compatible_provider.py`
- Modify: `app_tests/test_qa_provider_factory.py`
- Create: `.env.example`
- Create: `.gitignore`

**Interfaces:**
- Consumes: `ModelProvider`, `ModelRequest`, `ModelResponse.from_mapping()`.
- Produces: `OpenAICompatibleModelProvider(base_url, api_key, model, timeout_seconds=60.0)` and server factory selection.

- [ ] **Step 1: Write provider-adapter tests with `httpx.MockTransport`**

Test request URL, Authorization header, model name and strict response parsing without touching the network. A successful mock response body should be:

```json
{
  "choices": [
    {
      "message": {
        "content": "{\"answer\":\"教材回答\",\"evidence_ids\":[\"E1\"],\"insufficient_evidence\":false,\"answer_style\":\"brief\"}"
      }
    }
  ]
}
```

Also test timeout/HTTP errors map to provider-unavailable, malformed JSON content is retried exactly once, the second malformed response maps to provider-invalid-response, and raw upstream body/Key are absent from raised public messages.

- [ ] **Step 2: Run adapter tests and verify failure because the module does not exist**

```bash
python -m unittest app_tests.test_openai_compatible_provider -v
```

- [ ] **Step 3: Implement `OpenAICompatibleModelProvider` with httpx**

Use endpoint construction:

```python
endpoint = f"{base_url.rstrip('/')}/chat/completions"
```

Send `Authorization: Bearer <key>`, `Content-Type: application/json`, configured model, a system message containing the approved textbook-only rules, a user message containing JSON-serialized current question, bounded history and bounded evidence, and `response_format={"type": "json_object"}`.

No repository path, browser state, API key or unrelated course data may appear in the user payload.

- [ ] **Step 4: Implement exactly-one retry for invalid model JSON/schema**

Transport/timeouts do not loop indefinitely. JSON/schema-invalid content gets one second attempt with the same bounded request; a second failure raises the stable invalid-response error.

- [ ] **Step 5: Write and run factory tests**

Factory behavior:

```text
BOOK_QA_PROVIDER=fake -> DeterministicFakeModelProvider (CI/test only)
all of BOOK_QA_BASE_URL/API_KEY/MODEL present -> OpenAICompatibleModelProvider
none of the three present -> UnavailableModelProvider
partial real-provider config -> QAProviderConfigurationError
```

Run:

```bash
python -m unittest app_tests.test_openai_compatible_provider app_tests.test_qa_provider_factory -v
```

- [ ] **Step 6: Add secret-safe templates**

`.env.example` must contain only:

```text
BOOK_QA_BASE_URL=
BOOK_QA_API_KEY=
BOOK_QA_MODEL=
BOOK_QA_TIMEOUT_SECONDS=60
```

Root `.gitignore` must include:

```text
.env
.env.local
.env.*.local
```

Do not ignore `.env.example`.

- [ ] **Step 7: Commit the provider adapter/configuration**

```bash
git add app/api/openai_compatible_provider.py app/api/qa_provider_factory.py \
        app_tests/test_openai_compatible_provider.py app_tests/test_qa_provider_factory.py \
        .env.example .gitignore
git commit -m "feat: add OpenAI-compatible textbook QA provider"
```

---

### Task 7: Upgrade FastAPI/App DTOs and stable error semantics

**Files:**
- Modify: `app/api/models.py`
- Modify: `app/api/service.py`
- Modify: `app/api/main.py`
- Modify: `app/api/errors.py`
- Modify: `app_tests/test_qa_service.py`
- Modify: `app_tests/test_qa_api.py`
- Modify: `app_tests/test_api_live.py`

**Interfaces:**
- Consumes: v2 `QARuntime.answer(question, section_id, history)`.
- Produces: `POST /api/courses/{course_id}/qa` with v2 request/response and stable 400/404/502/503 semantics.

- [ ] **Step 1: Write failing DTO/service tests for Section, history and response metadata**

Request fixture:

```python
payload = {
    "question": "那为什么必须要求完备？",
    "section_id": "ch01_s01",
    "history": [
        {"role": "user", "content": "巴拿赫空间是什么？"},
        {"role": "assistant", "content": "完备赋范线性空间称为巴拿赫空间。"},
    ],
}
```

Assert response includes `answer_style`, `scope_requested`, `scope_used`, `insufficient_evidence`, `message`, and citations with `chapter_id`, `section_id`, `type_zh`.

- [ ] **Step 2: Write failing error tests**

Cover:

```text
400 invalid_qa_question: blank question or malformed history
404 course_not_found
404 section_not_found
503 qa_unavailable
503 qa_provider_unconfigured
503 qa_provider_unavailable
502 qa_provider_invalid_response
```

Also assert response JSON never contains configured API key or base URL.

- [ ] **Step 3: Run App QA tests and verify failure on the old contract**

```bash
python -m unittest app_tests.test_qa_service app_tests.test_qa_api app_tests.test_api_live -v
```

- [ ] **Step 4: Upgrade Pydantic request/response DTOs**

Add:

```python
class QAHistoryMessageDTO(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class QARequest(BaseModel):
    question: str
    section_id: str | None = None
    history: list[QAHistoryMessageDTO] = []
```

Use a Pydantic safe default factory for `history` in actual code rather than a shared mutable list.

Response fields follow the approved spec exactly; do not expose raw EvidencePack or provider metadata.

- [ ] **Step 5: Update `BookAppService.ask()` and FastAPI endpoint**

Service signature:

```python
def ask(
    self,
    course_id: str,
    question: str,
    *,
    section_id: str | None = None,
    history: tuple[QAHistoryMessage, ...] = (),
) -> QAResponse:
```

Map unknown/wrong Section to `section_not_found`. Distinguish provider-unconfigured from provider-unavailable. Map provider invalid JSON/schema/citation to 502.

- [ ] **Step 6: Run App/API regression suite**

```bash
python -m unittest app_tests.test_qa_provider_factory app_tests.test_openai_compatible_provider \
  app_tests.test_qa_service app_tests.test_qa_api app_tests.test_api_live app_tests.test_app_service -v
```

- [ ] **Step 7: Commit the v2 API boundary**

```bash
git add app/api/models.py app/api/service.py app/api/main.py app/api/errors.py \
        app_tests/test_qa_service.py app_tests/test_qa_api.py app_tests/test_api_live.py
git commit -m "feat: expose scoped conversational textbook QA API"
```

---

### Task 8: Replace one-shot browser QA state with a shared course session

**Files:**
- Create: `app/web/src/state/qaSessionState.ts`
- Create: `app/web/src/state/qaSessionState.test.ts`
- Delete after migration: `app/web/src/state/qaViewState.ts`, `qaViewState.test.ts`
- Modify: `app/web/src/api/types.ts`
- Modify: `app/web/src/api/client.ts`
- Modify: `app/web/src/api/client.test.ts`

**Interfaces:**
- Consumes: v2 API DTO.
- Produces: `book:qa-session:${courseId}` state and `bookApi.askCourse(courseId, request)`.

- [ ] **Step 1: Write failing session-state tests**

Use the contract:

```ts
export interface QASessionState {
  route: string
  messages: QASessionMessage[]
  scrollY: number
  activeCitationSourceId: string | null
}
```

Test save/load, corrupt JSON cleanup, wrong shape cleanup, and assert serialized JSON does not contain `evidence`, `BOOK_QA_API_KEY`, `prompt`, or `raw_response` keys.

- [ ] **Step 2: Define message types that preserve verified display state but not EvidencePack**

Use discriminated types:

```ts
export type QASessionMessage =
  | { id: string; role: 'user'; content: string }
  | { id: string; role: 'assistant'; content: string; response: QAResponse }
```

`QAResponse` contains only validated server DTO/citations, so restoring it does not create a second authority source.

- [ ] **Step 3: Run state tests and verify failure**

```bash
cd app/web
npm test -- qaSessionState.test.ts
```

- [ ] **Step 4: Implement v2 API TypeScript types and request function**

Client signature:

```ts
askCourse(courseId: string, request: QARequest): Promise<QAResponse>
```

Request contains `question`, `section_id`, `history`; response includes v2 answer/style/scope/insufficient/message/citation fields.

- [ ] **Step 5: Run client/state unit tests**

```bash
cd app/web
npm test -- client.test.ts qaSessionState.test.ts
npm run typecheck
```

- [ ] **Step 6: Commit browser data contracts**

```bash
git add app/web/src/api/types.ts app/web/src/api/client.ts app/web/src/api/client.test.ts \
        app/web/src/state/qaSessionState.ts app/web/src/state/qaSessionState.test.ts
git rm app/web/src/state/qaViewState.ts app/web/src/state/qaViewState.test.ts
git commit -m "refactor: store textbook QA as a course session"
```

---

### Task 9: Add dual QA entry, conversation UI and no-recall Source return

**Files:**
- Modify: `app/web/src/pages/CoursePage.tsx`, `CoursePage.test.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx` and its test module
- Rewrite: `app/web/src/pages/QAPage.tsx`, `QAPage.test.tsx`
- Modify: `app/web/src/pages/SourcePage.tsx`, `SourcePage.test.tsx`
- Modify: `app/web/src/routes/router.tsx` only if query handling needs no route change; keep `/courses/:courseId/qa` canonical.
- Modify: `app/web/src/styles.css`

**Interfaces:**
- Consumes: `qaSessionState`, v2 `bookApi.askCourse()`.
- Produces: Course full-book QA, Section `?section=<id>` QA, continuous session, verified Source round trip without model re-call.

- [ ] **Step 1: Write failing Course/Section entry tests**

Assert Course page links to `/courses/{courseId}/qa` and Section page renders `问本节内容` linking to:

```text
/courses/{courseId}/qa?section={sectionId}
```

- [ ] **Step 2: Write failing QAPage scope and conversation tests**

Cover:

```text
Course route -> 当前范围：整本教材
?section=ch01_s01 -> 当前范围 shows loaded Section and 优先本节，必要时扩展到全书
scope_used=section -> 回答依据：当前小节
scope_used=book from Section request -> 回答依据：本节 + 教材其他章节
second question sends bounded user/assistant history from the current session
```

Spy on `bookApi.askCourse` and inspect the second request body.

- [ ] **Step 3: Write the critical Source-return regression before implementation**

Test flow:

1. seed `qaSessionState` with one user and one assistant response containing a real-looking validated citation DTO from the test fixture;
2. render QAPage;
3. click `查看教材来源`;
4. return via SourcePage;
5. assert original response/citations remain visible;
6. assert `bookApi.askCourse` call count did not increase during restore.

This test replaces the current behavior that re-calls the provider on mount.

- [ ] **Step 4: Run page tests and confirm failures**

```bash
cd app/web
npm test -- CoursePage.test.tsx SectionPage.test.tsx QAPage.test.tsx SourcePage.test.tsx
```

Use the actual SectionPage test filename present in the repository if it differs.

- [ ] **Step 5: Implement conversation submit semantics**

For each submit:

```ts
const history = messages.map(({ role, content }) => ({ role, content }))
const response = await bookApi.askCourse(courseId, {
  question,
  section_id: sectionIdFromQuery,
  history,
})
```

Append the user message before the assistant message. If the API fails, preserve the user's input/message and present a retryable error; do not fabricate an assistant answer.

- [ ] **Step 6: Implement restore from session state with zero provider calls**

On mount, load `book:qa-session:${courseId}` and render the stored validated messages. Restore scroll and active citation after DOM content exists. Remove the current mount-time `askCourse(saved.question)` effect and its StrictMode microtask workaround because restoration no longer needs network generation.

- [ ] **Step 7: Implement scope/citation presentation**

Citation cards show canonical `type_zh`, number/title, printed/PDF pages and `教材锚点暂未提供` when `source_anchor` is null. Answer cards show the generated label and answer style presentation; insufficient messages use server `message` and are not labeled as generated.

- [ ] **Step 8: Update SourcePage to use `qaSessionState` active source identity**

The return button remains `返回问答` only when the opened source matches `activeCitationSourceId`, and navigation returns to the stored QA route including `?section=`.

- [ ] **Step 9: Run Web unit/type/build tests**

```bash
cd app/web
npm test
npm run typecheck
npm run build
```

- [ ] **Step 10: Commit the complete Web QA interaction**

```bash
git add app/web/src/pages app/web/src/state app/web/src/api app/web/src/styles.css
git commit -m "feat: add conversational scoped textbook QA UI"
```

---

### Task 10: Expand real-browser QA acceptance and CI gates

**Files:**
- Modify: `app/web/e2e/functional-analysis.spec.ts`
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Modify: `.github/workflows/app-ui-tests.yml`

**Interfaces:**
- Consumes: real Functional Analysis Runtime + deterministic fake model provider.
- Produces: CI proof for the full Phase 1F completion path without external model secrets.

- [ ] **Step 1: Add Playwright Section QA→Source→QA→follow-up acceptance**

Use a real Functional Analysis query already proven to hit canonical data. The flow must:

```text
Library -> Functional Analysis -> Chapter -> ch01_s01 -> 问本节内容
-> ask -> generated answer -> real citation -> SourcePage -> 返回问答
-> same answer still present without a second provider-generated replacement
-> follow-up question succeeds
```

Do not hardcode a fake source ID as if it were textbook truth; read canonical identities from the real API/fake-provider response where practical.

- [ ] **Step 2: Add Course-book, fallback, insufficient and 390×844 scenarios**

Acceptance must explicitly observe `当前范围：整本教材`, one Section→book fallback indicator, one `根据当前教材中检索到的内容，暂时无法可靠回答这个问题。`, and no horizontal body overflow at 390×844.

- [ ] **Step 3: Run Playwright locally with fake provider**

FastAPI environment:

```bash
BOOK_QA_PROVIDER=fake python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Web/test shell:

```bash
cd app/web
npm run dev -- --host 127.0.0.1 --port 5173
npm run e2e
```

Expected: all existing Phase 1D/1E and new Phase 1F Chromium tests pass.

- [ ] **Step 4: Update Runtime CI to include v2 QA tests on 3.11/3.12/3.13**

Ensure workflow runs:

```bash
python -m unittest tests.test_search_runtime tests.test_qa_evidence tests.test_qa_provider tests.test_qa_runtime -v
```

and preserves all existing readiness/reference tests.

- [ ] **Step 5: Update App UI CI with fake provider only**

Set test-server environment `BOOK_QA_PROVIDER=fake`. Run App/API QA tests, Web Vitest, typecheck, build and Chromium acceptance. Do not add `BOOK_QA_API_KEY` to repository secrets as a CI requirement.

- [ ] **Step 6: Commit CI/acceptance coverage**

```bash
git add app/web/e2e/functional-analysis.spec.ts .github/workflows/runtime-reference-tests.yml .github/workflows/app-ui-tests.yml
git commit -m "test: gate Phase 1F textbook QA in CI"
```

---

### Task 11: Documentation, completion gate and final regression verification

**Files:**
- Modify: `README.md`
- Modify: `app/README.md`
- Modify: `docs/ROADMAP.md`
- Review only unless a real defect is separately identified: `books/functional-analysis/**`

**Interfaces:**
- Consumes: all passing implementation/test tasks.
- Produces: user-facing setup docs and a truthful Phase 1F COMPLETE roadmap state.

- [ ] **Step 1: Run the full Python regression gate before changing completion status**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s app_tests -p "test_*.py" -v
```

Expected: all tests pass on the local supported Python version; CI later proves the 3.11/3.12/3.13 matrix.

- [ ] **Step 2: Run the full Web gate**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
npm run e2e
```

Expected: all tests pass, including 390×844 acceptance.

- [ ] **Step 3: Verify repository secret/data hygiene**

```bash
git grep -n "BOOK_QA_API_KEY=" -- ':!.env.example'
git grep -n "Bearer " -- ':!app/api/openai_compatible_provider.py' ':!app_tests/test_openai_compatible_provider.py'
git status --short
```

Expected: no real key assignment is committed; working tree contains no `.env` file staged for commit.

- [ ] **Step 4: Verify canonical textbook assets were not changed**

```bash
git diff main...HEAD -- books/functional-analysis
```

Expected: empty diff unless a separately reviewed source-data fix was intentionally made. If non-empty, stop completion and review that data change independently.

- [ ] **Step 5: Update README/App README with exact local provider configuration**

Document:

```text
BOOK_QA_BASE_URL
BOOK_QA_API_KEY
BOOK_QA_MODEL
BOOK_QA_TIMEOUT_SECONDS=60
```

State explicitly that full textbook data remains local but selected EvidencePack excerpts and recent dialogue are sent to the configured online model provider.

- [ ] **Step 6: Mark Phase 1F COMPLETE only after the full gate is green**

`docs/ROADMAP.md` must list Phase 1F complete and keep Phase 1G StudyRecord as the next mainline unless priorities were explicitly changed.

- [ ] **Step 7: Commit final documentation**

```bash
git add README.md app/README.md docs/ROADMAP.md
git commit -m "docs: complete Phase 1F textbook QA"
```

- [ ] **Step 8: Run final verification at the exact final HEAD**

```bash
git rev-parse HEAD
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s app_tests -p "test_*.py" -v
cd app/web && npm test && npm run typecheck && npm run build && npm run e2e
```

Do not claim Phase 1F complete or open a merge-ready PR until the exact final HEAD has passing local gates and GitHub Actions confirms the matrix.

---

## Self-review against the approved spec

### Spec coverage

- Current textbook only: Tasks 3–7 provider/runtime contracts.
- Section-first → book fallback: Tasks 2 and 4.
- Course direct book scope: Task 4.
- Evidence item/text bounds: Task 4.
- Session-only history and fresh retrieval: Tasks 4, 7, 8, 9.
- `brief/explain/compare/proof`: Tasks 3, 5, 7, 9.
- OpenAI-compatible server provider: Task 6.
- server-side Key boundary: Tasks 6 and 11.
- strict structured JSON and one retry: Tasks 3 and 6.
- server gate + model second gate: Task 4.
- citation fail closed: Tasks 3–5.
- dual Course/Section entry: Task 9.
- QA→Source→QA without re-generation: Task 9.
- Fake provider CI and real-browser flow: Task 10.
- 390×844: Tasks 9–10.
- no textbook data mutation: Global Constraints and Task 11.
- README/ROADMAP completion semantics: Task 11.

### Type consistency

- Runtime uses `ModelProvider`, `ModelRequest`, `ModelResponse`, `QAHistoryMessage`, `EvidencePack`, `QAResult` consistently.
- API request uses `question`, `section_id`, `history`; Web client sends the same names.
- Final response consistently uses `answer`, `answer_kind`, `answer_style`, `scope_requested`, `scope_used`, `insufficient_evidence`, `message`, `citations`.
- Browser session stores validated `QAResponse`, not `EvidencePack` or provider raw output.

### Placeholder scan

The plan contains no deferred implementation placeholders. Every task has an explicit test-first action, concrete contract, verification command and commit boundary.
