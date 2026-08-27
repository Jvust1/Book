# Phase 1F Textbook QA Design

Date: 2026-08-27
Status: Proposed for user review
Branch: `feature/textbook-qa-phase-1f`
Base: `main@7e191693cd84174b2229337e411bcd44dde68612`

## 1. Goal

Phase 1F adds course-scoped textbook question answering on top of the completed Phase 1E search/source identity stack.

The core product guarantee is not merely that the app can generate prose. The guarantee is that every answer is generated from an explicit, course-approved evidence pack, every citation resolves back to a real textbook source, and insufficient evidence is reported explicitly instead of being filled with unsupported model claims.

Phase 1F must preserve the existing separation between textbook facts and generated learning material:

- textbook facts remain owned by Runtime / structured textbook assets;
- generated answers are always marked as generated;
- generated answers are never persisted as textbook content;
- a model cannot invent source identities, pages or anchors;
- citations must round-trip through the existing `SourceResolver`.

## 2. Scope

Phase 1F includes:

1. a course-scoped `QARuntime`;
2. deterministic evidence retrieval using the existing `SearchRuntime` and `SourceResolver`;
3. a provider-agnostic `AnswerProvider` protocol;
4. an `EvidencePack` that is the only textbook context exposed to the provider;
5. citation verification after provider output;
6. explicit `sufficient` / `insufficient_evidence` result status;
7. stable App/API DTOs and FastAPI endpoint(s);
8. a Chinese-first QA page in the React app;
9. QA → Source → Return context restoration;
10. deterministic fake-provider tests and real-browser acceptance.

Phase 1F does not include:

- multi-course or cross-book QA;
- classroom recordings or lecture sources;
- personal notes, mistakes or StudyRecord sources;
- embedding infrastructure or a vector database;
- cloud account sync;
- writing generated answers back into textbook assets;
- model-provider-specific product logic;
- unrestricted repository or filesystem access for the model;
- autonomous tool use by the model.

## 3. Architectural classification

This is an architectural subsystem because it introduces a new trust boundary between deterministic textbook data and nondeterministic answer generation.

The selected architecture is:

```text
QAPage
  ↓
FastAPI
  ↓
BookAppService
  ↓
QARuntime
  ├─ SearchRuntime
  ├─ SourceResolver
  ├─ EvidencePolicy
  └─ AnswerProvider
        ↓
     EvidencePack only
        ↓
   ProviderAnswer
        ↓
 CitationVerifier
        ↓
     QAResponse
```

`BookAppService` remains the stable App-facing DTO boundary. The web app never reads raw `books/`, `courses/`, `library/`, search-index or chunk assets.

## 4. Core invariants

### 4.1 Current-course scope

The first QA implementation is always scoped to exactly one App course and that course's enabled main textbook.

Input must include `course_id`. `QARuntime` obtains the corresponding `CourseRuntime` through the existing Library/App path. The provider receives no other course assets.

### 4.2 Evidence before generation

Generation is impossible until deterministic retrieval has produced and validated an `EvidencePack`.

The provider never receives:

- repository paths;
- arbitrary files;
- raw search-index files;
- unresolved object IDs;
- browser/session state;
- API keys or application internals.

It receives only normalized evidence items already resolved by Runtime.

### 4.3 Citation identities are not model-owned

The provider is not allowed to create arbitrary source identities.

Each evidence item receives a short opaque `evidence_id`, for example `E1`, `E2`, `E3`. The provider may cite only those evidence IDs.

After generation, `CitationVerifier` maps cited evidence IDs back to server-owned canonical identities:

- `course_id`
- `book_id`
- `source_kind`
- `source_id`
- `source_anchor`
- `pdf_page`
- `printed_page`

Unknown or duplicated citation IDs are rejected or normalized according to the rules below.

### 4.4 Generated content is visibly generated

Every successful QA response includes:

```text
answer_kind = generated
```

The UI displays a persistent Chinese label equivalent to “AI 生成回答，依据下方教材来源”.

No field or component may call generated text “教材原文”.

### 4.5 Fail closed on insufficient evidence

If deterministic retrieval cannot produce enough validated evidence, `QARuntime` must not ask the provider to fabricate a complete answer.

It returns:

```text
evidence_status = insufficient_evidence
answer_kind = generated
answer = a stable non-assertive user-facing explanation
citations = [] or the limited relevant evidence that was actually found
```

The message must distinguish “evidence insufficient” from “QA subsystem unavailable”.

## 5. Components

## 5.1 `QARuntime`

Recommended file:

`runtime/qa_runtime.py`

Responsibilities:

1. validate the question contract;
2. invoke deterministic evidence retrieval;
3. build an immutable `EvidencePack`;
4. apply sufficiency policy;
5. invoke `AnswerProvider` only when allowed;
6. verify all provider citations;
7. return a canonical `QAResult`.

`QARuntime` must not contain provider-specific HTTP/client code.

Suggested public API:

```python
QARuntime.from_course(course, provider=provider)
QARuntime.answer(question, *, evidence_limit=8)
```

Question constraints for Phase 1F:

- trim surrounding whitespace;
- reject blank questions;
- maximum 1000 Unicode code points;
- `evidence_limit` integer 1..12;
- current course only.

## 5.2 `EvidenceRetriever`

Evidence retrieval should reuse Phase 1E rather than introducing a second index.

First implementation:

1. run `SearchRuntime.search(question, limit=N)`;
2. take only hits with canonical source identities;
3. resolve each hit again through `SourceResolver`;
4. deduplicate by `(source_kind, source_id)`;
5. retain deterministic rank order;
6. project a bounded evidence representation.

The resolver step is mandatory even though SearchRuntime already emits source identities. This provides a second integrity boundary before model exposure.

No embeddings are required in Phase 1F. The architecture leaves room for an alternate retriever later, but the initial production path is deterministic lexical search over the audited 1493-record index.

## 5.3 `EvidencePack`

`EvidencePack` is immutable and contains server-selected evidence only.

Suggested structure:

```text
course_id
book_id
question
evidence_status
evidence[]
```

Each evidence item contains:

```text
evidence_id          # server-generated E1, E2, ...
source_kind          # object | figure
source_id
object_type
title_zh
title_en
number
formula
content_zh
source_anchor
pdf_page
printed_page
```

Optional source context may be included only if it was resolved by `SourceResolver` and bounded to a small deterministic window.

The provider does not receive full raw objects or arbitrary chunk content.

## 5.4 `EvidencePolicy`

Phase 1F needs an explicit deterministic sufficiency decision before generation.

Initial policy:

`insufficient_evidence` if any of the following is true:

- search index is unavailable;
- no validated evidence items remain after SourceResolver verification;
- the highest search score is only a type-only match (`<= 300` in the current SearchRuntime scoring model);
- the only matches are generic object-type matches that do not contain the question text in title, identity, formula or known concepts.

Otherwise status is `sufficient`.

This is intentionally conservative. Phase 1F should prefer declining to answer over producing an unsupported answer.

Search subsystem unavailability is not converted into ordinary insufficiency. It maps to a QA unavailable error because the trusted retrieval path is unavailable.

## 5.5 `AnswerProvider`

Provider interface is protocol-based and contains no textbook retrieval logic.

Conceptual contract:

```python
class AnswerProvider(Protocol):
    def answer(self, request: ProviderRequest) -> ProviderAnswer: ...
```

`ProviderRequest` contains only:

- question;
- course/book display identity if useful;
- evidence items;
- explicit generation rules.

Provider rules include:

1. answer only from supplied evidence;
2. do not claim knowledge not supported by the evidence;
3. cite evidence using only supplied `evidence_id` values;
4. distinguish uncertainty explicitly;
5. do not invent page numbers, source IDs, theorem numbers or anchors;
6. return structured output.

Suggested `ProviderAnswer`:

```text
answer_text
cited_evidence_ids[]
provider_metadata?     # non-product-critical diagnostics only
```

No provider metadata is treated as textbook evidence.

## 5.6 Provider implementations

Phase 1F requires two implementations at minimum:

### `DeterministicFakeAnswerProvider`

Used by unit, API, CI and Playwright tests.

It produces a stable answer entirely from the `EvidencePack` and cites deterministic evidence IDs. This ensures CI has no network, API-key, quota or model-version dependency.

### External model adapter

A separate optional adapter may be implemented after the trusted QA core works.

It must:

- live outside Runtime trust logic;
- implement the same `AnswerProvider` interface;
- be configured at application startup;
- never be required by repository CI;
- never receive more context than `ProviderRequest`.

The first spec does not commit the architecture to OpenAI or any other vendor.

## 5.7 `CitationVerifier`

After provider generation, all citations are validated against the exact `EvidencePack` used for that answer.

Rules:

- cited ID not in EvidencePack → provider response invalid;
- duplicate citations → deduplicate while retaining first occurrence;
- zero citations for a non-empty successful factual answer → provider response invalid;
- citations are projected from server-owned evidence, not provider-provided metadata;
- every final citation must remain resolvable through `SourceResolver`;
- if citation validation fails, return `qa_provider_invalid_response`, not a partially trusted answer.

## 6. Result model

Suggested internal `QAResult`:

```text
course_id
book_id
question
answer_kind                 # generated
answer
 evidence_status             # sufficient | insufficient_evidence
citations[]
```

Each final citation:

```text
citation_id                  # C1, C2...
evidence_id                  # E1, E2...
source_kind
source_id
object_type
number
title_zh
title_en
source_anchor
pdf_page
printed_page
```

`citation_id` is presentation identity only. Canonical textbook identity remains `(course_id, book_id, source_kind, source_id)` plus anchor/page data.

## 7. App/API boundary

`BookAppService` should gain a QA method rather than exposing Runtime directly.

Suggested method:

```python
service.ask(course_id, question)
```

FastAPI endpoint:

```text
POST /api/courses/{course_id}/qa
```

Request:

```json
{
  "question": "Hölder 不等式的作用是什么？"
}
```

Successful response example shape:

```json
{
  "course_id": "functional_analysis_course",
  "book_id": "stein_shakarchi_functional_analysis_2011",
  "question": "Hölder 不等式的作用是什么？",
  "answer_kind": "generated",
  "evidence_status": "sufficient",
  "answer": "...",
  "citations": [
    {
      "citation_id": "C1",
      "evidence_id": "E1",
      "source_kind": "object",
      "source_id": "...",
      "object_type": "theorem",
      "title_zh": "...",
      "title_en": "...",
      "source_anchor": "...",
      "pdf_page": 0,
      "printed_page": 0
    }
  ]
}
```

## 8. Stable error semantics

The API must continue the existing Chinese stable JSON error convention.

Recommended mappings:

- blank / overlong question → HTTP 400, `invalid_qa_question`;
- unknown course → HTTP 404, `course_not_found`;
- search/index/source trust path unavailable → HTTP 503, `qa_unavailable`;
- configured answer provider unavailable → HTTP 503, `qa_provider_unavailable`;
- provider returns invalid structured data or invalid citations → HTTP 502, `qa_provider_invalid_response`.

`insufficient_evidence` is a normal HTTP 200 product result, not an infrastructure error.

## 9. QA page

Recommended route:

```text
/courses/:courseId/qa
```

Course page receives a second top-level study utility link near “搜索教材”:

```text
教材问答
```

The page contains:

- question input;
- submit action;
- loading state;
- generated-answer label;
- evidence status;
- answer body;
- citation cards;
- source links;
- explicit insufficient-evidence state;
- infrastructure/provider error state.

Chinese is primary UI language. English source titles may appear as supporting evidence.

## 10. QA → Source → Return

Clicking a citation uses the existing source route:

```text
/courses/:courseId/sources/:sourceKind/:sourceId
```

No QA-specific duplicate source page is created.

A separate session state helper is required:

```text
qaViewState
```

It may store only short-term navigation state:

```text
route
question
scrollY
activeCitationKey
```

Phase 1F does not persist full generated answers or citation payloads into `sessionStorage` as a long-term record.

When returning from Source:

1. restore QA route and question;
2. rerun QA through the normal API path;
3. restore scroll position;
4. mark the originating citation.

This mirrors the Phase 1E search round trip and avoids stale cached answer objects pretending to be authoritative records.

If rerunning an external provider would introduce undesirable nondeterminism, that optimization is deferred to Phase 1G or a later explicit QA-history design. Phase 1F prioritizes trust-boundary correctness over answer-history persistence.

## 11. Security and privacy boundary

Phase 1F provider adapters must not receive:

- filesystem paths;
- repository credentials;
- GitHub/Drive credentials;
- unrelated course data;
- personal StudyRecord data;
- browser storage;
- raw application logs.

Only the question and bounded EvidencePack are provider inputs.

Secrets for an external model provider must be server-side configuration only and must never be shipped in Vite client bundles.

## 12. Determinism boundary

The following must remain deterministic and testable without a model:

- question validation;
- course selection;
- evidence retrieval;
- evidence ranking;
- source resolution;
- evidence sufficiency decision;
- EvidencePack construction;
- citation verification;
- API DTO projection;
- navigation state behavior.

Only answer wording is provider-dependent.

## 13. Tests and acceptance

### Runtime unit tests

Cover:

- blank and overlong questions;
- evidence retrieval from the real Functional Analysis course;
- canonical identity preservation;
- SourceResolver revalidation;
- deterministic evidence IDs;
- deduplication;
- sufficient evidence;
- insufficient evidence;
- unavailable index;
- provider not called when evidence is insufficient;
- provider invalid citation rejected;
- provider duplicate citations normalized;
- successful fake-provider answer.

### App/API tests

Cover:

- valid QA 200;
- insufficient evidence 200;
- invalid question 400;
- unknown course 404;
- QA retrieval unavailable 503;
- provider unavailable 503;
- invalid provider response 502;
- final citations preserve canonical source identity.

### Web unit tests

Cover:

- empty state;
- loading;
- generated-answer label;
- sufficient answer and citations;
- insufficient evidence;
- provider/infrastructure errors;
- citation source links use `source_kind + source_id`;
- QA state save/restore.

### Playwright acceptance

Use the deterministic fake provider in CI and real Functional Analysis data.

Representative flows:

1. English question with a real theorem hit;
2. Chinese question with real textbook evidence;
3. insufficient-evidence question;
4. QA → citation source → return QA context;
5. 390×844 narrow QA/source round trip with no body overflow.

The browser acceptance must not depend on external network model calls.

## 14. CI gates

Runtime reference workflow must include:

- compile `qa_runtime.py`;
- QA unit tests on Python 3.11/3.12/3.13;
- real Functional Analysis fake-provider smoke on Python 3.13.

Book App UI workflow must include:

- App service/API QA tests;
- existing Web unit tests;
- TypeScript typecheck;
- Vite/PWA build;
- Playwright QA acceptance.

No secret or provider key is required for CI.

## 15. Data integrity

Phase 1F must not modify canonical Functional Analysis structured textbook assets merely to make QA pass.

Specifically, implementation should not rewrite:

- `books/functional-analysis/search_index_v0_36.jsonl`;
- PageMap;
- chunk structure files;
- canonical object IDs;
- source anchors;
- Chinese textbook projections.

If QA reveals a real source-data defect, fix that defect in a separate auditable data change rather than silently compensating inside the provider prompt.

## 16. Observability

Provider-independent diagnostics may record in-memory or standard application logs:

- course ID;
- evidence count;
- evidence status;
- provider adapter name;
- provider latency if available;
- validation error category.

Do not log API keys. Avoid logging full user questions or full generated answers by default in Phase 1F.

## 17. Future extension points

The architecture intentionally leaves room for later work without requiring it now:

- semantic/vector retriever;
- section/chapter QA scope filters;
- original-PDF fallback after PDF Reader exists;
- classroom evidence;
- QA history;
- multiple answer providers;
- citation-level confidence diagnostics;
- multi-course QA.

None of these are acceptance criteria for Phase 1F.

## 18. Phase 1F completion gate

Phase 1F is complete only when all of the following are true:

- `QARuntime` exists and owns the evidence/generation trust boundary;
- provider is abstracted behind `AnswerProvider`;
- deterministic fake provider supports all CI paths;
- real Functional Analysis evidence is retrieved through existing SearchRuntime;
- all evidence is revalidated by SourceResolver before generation;
- provider can cite only server-issued evidence IDs;
- invalid provider citations fail closed;
- insufficient evidence returns a normal explicit product state;
- App API exposes stable QA DTOs/errors;
- QA page visibly distinguishes generated answers from textbook content;
- citation click reaches existing structured Source page;
- returning restores QA question, scroll and active citation context;
- no generated answer is persisted as textbook content;
- Runtime 3.11/3.12/3.13, App API, Web typecheck/build and real-browser acceptance are green.

After this gate, the next mainline remains Phase 1G long-term StudyRecord unless roadmap priorities are explicitly changed.