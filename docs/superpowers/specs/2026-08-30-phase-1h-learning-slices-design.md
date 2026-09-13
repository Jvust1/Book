# Phase 1H User-Visible Learning Slices Design

Date: 2026-08-30
Status: APPROVED-IN-CHAT / SPEC FOR REVIEW
Repository: `Jvust2/Book`
Base integration commit: `2675d2cecab63b28b6ab81a4554e9b7f010afd72`
Design branch: `design/phase-1h-learning-slices-20260830`
Stage: `PHASE_1H_PREPARATION`

## 1. Context

Book is a provenance-preserving personal Course OS. The current product already has a stable Section learning shell with four parallel modes:

```text
Preview / Learn / Review / Practice
```

Phase 1D–1G established the current user-visible and persistence baseline:

- local-first FastAPI + React/TypeScript/Vite PWA;
- Library → Course → Chapter → Section navigation;
- source-backed Section learning payloads;
- explicit source navigation and Section → Source → Section restoration;
- Search and source-grounded QA;
- durable SQLite StudyRecord with hidden local `profile_id`;
- four learning modes that are independent and never lock one another;
- manual `completed / 100%` semantics rather than fabricated scroll/time progress.

Foundation A and H0–H4a established the cross-cutting architecture needed before richer user-facing learning work. H4a has now completed with a valid negative result:

```text
FTS_EVIDENCE_NOT_PROMISING
public Search / QA = EXACT_ONLY_UNCHANGED
```

Therefore Phase 1H is not a retrieval activation stage. It is the next approved user-visible product stage.

Current approved dependency sequence:

```text
H0 neutral Book identity                 COMPLETE_MERGED
→ H1 internal source provenance          COMPLETE_MERGED
→ H2 Exact-only shared Retrieval seam    COMPLETE_MERGED
→ H3a inert Concept contract             COMPLETE_MERGED
→ H4a shadow FTS5/BM25 evaluation        COMPLETE_MERGED
→ Phase 1H user-visible learning slices  THIS STAGE
```

The existing `SectionLearningRuntime` already produces deterministic source-backed candidates for the four modes, and `BookAppService.mode(...)` resolves those candidates into App-facing `ModeItem` objects. The current UI, however, still treats most learning modes as a flat list of source cards. Phase 1H enriches that learning experience without changing canonical textbook authority.

## 2. Design objective

Phase 1H turns the existing four-mode shell into a useful learning workflow while preserving the product rule:

> **App 通用，教材是数据。**

The design introduces a lightweight deterministic **Learning Slice presentation layer** on top of the existing source-backed Section runtime. This layer organizes already-authoritative Section evidence into mode-specific learning structures without creating a new textbook fact authority.

The intended user-visible outcome is:

```text
Section canonical sources
        ↓
SectionLearningRuntime
        ↓
Learning Slice deterministic presentation
        ↓
Preview / Learn / Review / Practice UI
        ↓
existing Source navigation + StudyRecord
```

The presentation layer may derive labels, grouping, fixed-template learning prompts, coverage presets, and filters. It must never invent a theorem, prerequisite, explanation, answer, source, mastery judgment, or textbook fact.

## 3. Goals

Phase 1H MUST:

1. Preserve the existing four independent learning modes and current route model.
2. Preserve current `ModeResponse.items` and `source_refs` semantics for compatibility.
3. Add a versioned deterministic presentation contract for richer mode-specific UI.
4. Make every derived learning objective, recall prompt, quick check, grouping decision, and preset traceable to one or more existing source references.
5. Distinguish textbook content from deterministic system-generated study prompts.
6. Enrich Preview with source-grounded objectives, core definitions/concepts, formulas, figure references, explicit prerequisite availability, and quick checks.
7. Enrich Review with `1 minute / 5 minute / full` deterministic recall presets.
8. Enrich Practice with exercise/problem filtering and clearer no-solution semantics.
9. Enrich Learn with type-aware grouping and presentation for definitions, theorem-family objects, formulas, examples/other objects, figures, and translations.
10. Preserve StudyRecord semantics: mode-level `in_progress / completed`, progress only `0 / 100`.
11. Preserve current Section source-roundtrip restoration without changing the H1-frozen browser persistence object shape.
12. Keep Search and QA Exact-only and behaviorally unchanged.
13. Keep `books/functional-analysis/**` and `courses/**` canonical inputs read-only.
14. Keep H3b, B4b, B5, multi-book Runtime consumer migration, and StudyRecord book-version migration outside this stage.
15. Remain deterministic and fully testable without an LLM.

## 4. Non-goals and hard exclusions

Phase 1H MUST NOT:

- activate FTS5, BM25, Exact+FTS fusion, semantic retrieval, or any H4a shadow implementation in the public Search/QA path;
- create production Concept authority, Concept lifecycle, or H3b data;
- infer prerequisite relationships from lexical similarity or model output;
- claim a concept is important, difficult, exam-relevant, or mastered without an authoritative signal;
- create AI-written textbook explanations, worked solutions, summaries, or practice answers;
- generate variant questions in v1;
- add durable per-question answer history in v1;
- change StudyRecord into Mastery;
- create per-card percentage progress or infer progress from time/scroll/view counts;
- change the H1-frozen Search, Source, QA external DTOs;
- change the H1-frozen QA/Search/Section session-storage object shapes;
- migrate StudyRecord identity to `book_version_id`;
- make supplementary books visible as if the current Runtime already consumes them;
- present lecture material before a real Lecture authority exists;
- render a figure bitmap/crop unless an existing canonical asset contract supplies that exact image; metadata-only figures must not be turned into fabricated images;
- mutate canonical textbook/course data to make a learning slice look richer.

## 5. Architecture

### 5.1 Existing boundary

Current Section mode flow:

```text
BookAppService.mode(...)
        ↓
SectionLearningRuntime.from_course(...)
        ↓
preview / learn / review / practice
        ↓
kind + source_id candidates
        ↓
SourceResolver
        ↓
ModeItem[]
        ↓
ModeResponse
```

This source-backed candidate pipeline is retained.

### 5.2 New presentation layer

Add a small isolated runtime unit conceptually named `LearningSliceRuntime` under `runtime/`.

Its responsibility is only:

- consume the already-loaded `SectionLearningRuntime` / `SectionLearningSource`;
- compute deterministic mode-specific presentation metadata;
- emit source references and fixed-template prompts;
- never resolve or duplicate canonical source body text;
- never write state;
- never call Search, QA, FTS, Concept, StudyRecord, or model providers.

The intended dependency direction is:

```text
canonical Course/Book
        ↓
SectionLearningRuntime
        ↓
LearningSliceRuntime
        ↓
BookAppService DTO adapter
        ↓
React presentation components
```

`LearningSliceRuntime` is not canonical authority. It is a presentation projection and can always be rebuilt.

### 5.3 Why this is a separate unit

The current `SectionLearningRuntime` already has one clear responsibility: select source-backed candidates for each learning mode. Phase 1H should not turn that file into a large UI policy engine.

Keeping the presentation composer separate provides:

- a small deterministic unit that can be tested without FastAPI or React;
- stable preservation of current candidate semantics;
- an explicit place for mode-specific study policy;
- a clean future replacement path when real Concept, Lecture, Mistake, or Mastery authorities exist;
- reduced risk that UI-only heuristics leak back into canonical data or retrieval.

## 6. App-facing contract

### 6.1 Additive evolution of `ModeResponse`

The four existing endpoints remain unchanged:

```text
GET /api/courses/{course_id}/sections/{section_id}/preview
GET /api/courses/{course_id}/sections/{section_id}/learn
GET /api/courses/{course_id}/sections/{section_id}/review
GET /api/courses/{course_id}/sections/{section_id}/practice
```

`ModeResponse` retains all existing fields:

```text
mode
course_id
book_id
chapter_id
section_id
source_status
items
source_refs
```

Phase 1H adds exactly one new top-level field:

```text
presentation
```

The presentation contract is versioned:

```text
schema_version = learning_slice_v1
```

No second Section learning API is introduced.

### 6.2 Presentation is reference-oriented

Presentation structures should reference already-resolved `ModeItem`s by stable source identity rather than duplicate canonical content.

Conceptual shared source reference:

```json
{
  "kind": "object",
  "source_id": "..."
}
```

A deterministic derived prompt/objective contains:

```json
{
  "text": "...",
  "derivation": "deterministic_template",
  "source_ref": {"kind": "object", "source_id": "..."}
}
```

This makes the difference visible between:

- textbook/source content in `items`; and
- system-generated study framing in `presentation`.

The UI must label derived material as system-generated learning guidance, not as a textbook quotation.

### 6.3 Fail-closed internal invariant

Every source reference emitted by `presentation` MUST resolve to a source represented by the mode response and canonical resolver.

If presentation refers to a missing/non-canonical source, the request fails as a stable internal learning-slice integrity error rather than silently dropping or inventing content.

Optional empty presentation groups are valid and are not errors.

## 7. Common deterministic source taxonomy

Phase 1H uses normalized source type categories only for presentation. Original source type text remains unchanged.

Review-family object types:

```text
definition
theorem
proposition
lemma
corollary
formula
```

Practice-family object types:

```text
exercise
problem
```

Learn grouping may additionally distinguish:

```text
example
remark
proof
other object types
figure
translation
```

Normalization is limited to whitespace trim + casefold for classification. It must not rewrite canonical type strings.

Order rules:

- canonical source order is preserved unless a specific presentation preset explicitly selects a subset;
- within a presentation group, original source order is preserved;
- figure ordering remains the existing deterministic page/id ordering from `SectionLearningRuntime`;
- translation batch order remains current stable deduplicated source-batch order.

## 8. Slice A — Preview

Preview is the first implementation slice because it establishes the shared presentation contract with minimal persistence or behavior risk.

### 8.1 User-visible blocks

Preview v1 contains:

```text
Section overview
Learning objectives (source-derived)
Prerequisite status
Core concepts / definitions
Core formulas
Key figure references
Existing object statistics
Quick checks
```

### 8.2 Learning objectives

Objectives are generated only from actual Section source objects using fixed templates.

Examples of allowed templates:

```text
definition       → “理解并能复述：{source label}”
theorem family   → “理解并能说明结论与条件：{source label}”
formula           → “识别并能写出：{source label}”
example           → “能够跟随教材例题：{source label}”
exercise/problem  → “尝试教材练习：{source label}”
```

`source label` is assembled only from canonical `title_zh`, `title_en`, `number`, and type fallback already available through the source.

Rules:

- no objective is emitted without a source reference;
- no arbitrary learning outcome such as “掌握证明技巧” is invented unless a corresponding canonical source type supports the fixed template;
- objectives are capped for display using a deterministic diversity-first selector;
- the full source set remains available through the mode items.

### 8.3 Prerequisites

Phase 1H v1 has no production prerequisite authority. H3a is only an inert contract and cannot be used as production knowledge.

Therefore prerequisite presentation is explicit and honest:

```text
status = unavailable
items = []
```

unless an already-authoritative current Runtime field explicitly encodes a prerequisite relation. Lexical similarity, Section order, earlier definitions, Search hits, or AI output MUST NOT be converted into prerequisite facts.

The UI wording should be equivalent to:

```text
暂无可验证的前置知识关系
```

This slot is intentionally ready for a future approved Concept/Prerequisite authority without faking data in Phase 1H.

### 8.4 Core concepts / definitions

In v1, “core concepts” means source-backed `definition` objects, not production ConceptGraph entities.

The UI label must avoid implying H3b Concept authority. Recommended wording:

```text
核心定义 / 概念入口
```

Each entry links to the canonical source.

### 8.5 Core formulas

Formula preview includes:

- explicit `formula` object types; and
- source objects with a non-empty canonical formula field when that object is already in the mode source set.

The presentation references the existing item; formula body is never copied into a derived fact store.

### 8.6 Key figures

Preview may surface canonical figure references already discovered inside the Section page range.

If the current source contract has metadata but no canonical image asset URI, the UI displays a dedicated figure reference card containing available title/page/source information and a source link. It MUST NOT synthesize, screenshot, crop, or pretend to display the original figure pixels.

### 8.7 Quick checks

Quick checks are deterministic recall prompts, not AI-generated questions.

Allowed examples:

```text
definition      → “你能说出「{label}」的定义吗？”
theorem family  → “你能说明「{label}」的条件和结论吗？”
formula          → “你能不看教材写出「{label}」吗？”
```

The reveal action shows the existing source-backed `ModeItem` content/formula. The answer is not separately generated or stored.

Quick-check state is UI-local and does not create StudyRecord sub-progress.

## 9. Slice B — Review

Review becomes an active-recall interface over the same source-backed review candidates.

### 9.1 Presets

User-visible presets:

```text
1 分钟
5 分钟
完整复习
```

These are approximate coverage presets, not timers and not claims of required study duration.

Stable internal IDs:

```text
one_minute
five_minute
full
```

### 9.2 Deterministic selection

Candidate set remains the current review-family source types.

`full`:

- every review candidate in canonical source order.

`one_minute`:

- maximum 3 candidates;
- diversity-first: first available definition, first available theorem-family object, first available formula;
- if fewer than three categories are available, fill remaining slots from the earliest unused review candidates in source order.

`five_minute`:

- maximum 10 candidates;
- start with the same diversity-first category coverage;
- fill remaining slots from unused review candidates in canonical source order.

This algorithm is intentionally simple, deterministic, and non-personalized. It is not importance ranking, exam ranking, or mastery ranking.

### 9.3 Recall card behavior

Every review candidate gets one deterministic prompt based on source type.

Before reveal:

- show type/number/title and recall prompt;
- keep source link available.

After reveal:

- show the already-resolved textbook content/formula;
- never create a generated answer.

Existing `expandedSourceIds` remains the reveal/source-roundtrip mechanism where practical.

### 9.4 URL state

Selected review preset is represented additively in the Section route query string:

```text
?mode=review&review_preset=one_minute
?mode=review&review_preset=five_minute
?mode=review&review_preset=full
```

Invalid/missing values fall back deterministically to `full`.

No new field is added to the H1-frozen Section `sessionStorage` object. Existing route preservation already carries the query string through Source navigation.

## 10. Slice C — Practice

Practice remains strictly textbook-source-backed in v1.

### 10.1 Candidate authority

Only current explicit practice-family types are candidates:

```text
exercise
problem
```

No theorem/example is silently converted into a generated question.

### 10.2 Filters

The Practice presentation exposes only filters that exist in the current candidate set:

```text
all
exercise
problem
```

If one type is absent, its filter is omitted/disabled rather than pretending results exist.

Route state:

```text
?mode=practice&practice_kind=all
?mode=practice&practice_kind=exercise
?mode=practice&practice_kind=problem
```

Invalid values fall back to `all`.

As with Review, no session-storage schema change is required.

### 10.3 Problem interaction

Phase 1H v1 supports:

- type filtering;
- source-order navigation/listing;
- per-card expansion;
- visible count of the current filtered set;
- source navigation;
- UI-local viewed/open state if useful.

Viewed/open state is not mastery, not durable learning progress, and must not update StudyRecord beyond the existing mode touch behavior.

### 10.4 Solution semantics

Current canonical runtime does not expose a dedicated verified solution relationship for each exercise/problem.

Therefore v1 does not attempt free-text parsing to guess whether content contains an answer.

Each practice item presentation uses an explicit status equivalent to:

```text
solution_status = unavailable
```

until an authoritative solution contract exists.

Recommended user wording:

```text
教材数据中暂未提供可验证解析
```

No AI solution or variant question is generated in this stage.

### 10.5 Durable answer recording

Durable user answers require a new persistence/schema decision distinct from current StudyRecord. They are therefore deferred from Phase 1H v1 rather than being stuffed into `StudyRecord` or browser local storage.

## 11. Slice D — Learn enhancement

Learn remains the complete source-backed reading mode. Phase 1H improves information architecture rather than changing textbook authority.

### 11.1 Type-aware groups

The Learn presentation groups existing items into clear sections such as:

```text
Definitions / concepts
Theorems / propositions / lemmas / corollaries
Formulas
Examples
Other textbook objects
Figures
Translations
```

Groups contain source references only; canonical body content remains in `ModeItem`.

Groups that contain no items are not rendered.

### 11.2 Specialized presentation

React may use specialized presentation components for:

- formula blocks;
- theorem-family cards;
- example/object cards;
- figure reference cards;
- translation availability cards.

Specialization must not alter canonical content. It only changes presentation.

### 11.3 Figure limitation

If no existing canonical image asset is available through the source contract, Learn shows figure metadata/source navigation only. Actual bitmap/crop rendering is deferred until a provenance-preserving figure-asset contract exists.

### 11.4 Supplementary and lecture extensions

The architecture should leave clean extension points for future supplementary textbook and Lecture content, but the Phase 1H UI must not render fabricated or placeholder evidence as if those authorities exist.

No multi-book Runtime migration or Lecture authority is introduced here.

## 12. StudyRecord integration

Phase 1H preserves the Phase 1G contract exactly:

```text
no record   = not started
in_progress = progress 0
completed   = progress 100
```

Rules:

1. Mode content must load successfully before existing `touch` behavior occurs.
2. Switching Review presets does not create a new StudyRecord.
3. Switching Practice filters does not create a new StudyRecord.
4. Revealing a recall card does not update durable progress.
5. Viewing a practice item does not update durable progress.
6. Manual `标记完成` remains mode-level and idempotent.
7. `completed` never regresses to `in_progress` because of Phase 1H UI interactions.
8. No scroll/time/card-count derived percentage is added.
9. StudyRecord storage and schema remain unchanged in Phase 1H v1.

## 13. Browser state and navigation

H1 froze the existing Section session persistence shape. Phase 1H must preserve it.

New long-enough-to-matter UI selection state uses URL query parameters rather than new durable/session fields:

```text
mode
review_preset
practice_kind
```

Existing source-navigation save/restore continues to store the route, scroll position, expanded source IDs, and active source ID using the current structure.

Because the stored route already includes `location.search`, additive query parameters survive Source round trips without changing the frozen persistence schema.

Ephemeral reveal/toggle details that do not need source-roundtrip persistence may remain component state.

## 14. Provenance and derived-text rules

Phase 1H introduces more system-generated instructional text than prior phases, so provenance wording is explicit.

### Canonical/source-backed

Examples:

- textbook content;
- formula text;
- title/number/type;
- page/source identity;
- figure metadata;
- translation availability.

These come from current Runtime/SourceResolver authority.

### Deterministic derived presentation

Examples:

- “理解并能复述…” learning objective;
- “你能说出…定义吗？” recall prompt;
- grouping labels;
- `1 minute / 5 minute / full` subset selection;
- exercise/problem filters.

These are UI/study guidance and MUST carry/retain source references. They are not textbook quotations or teacher statements.

### Forbidden unsupported derivation

Phase 1H must not derive:

- prerequisite facts from order or similarity;
- “重点 / 高频 / 必考”;
- difficulty;
- mastery;
- correctness of a user answer;
- hidden answer/solution extraction from unstructured text;
- teacher emphasis;
- AI explanations represented as source facts.

## 15. Error and empty-state semantics

Phase 1H must preserve the current fail-closed source boundary.

### Errors

- unknown course/section: current 404 behavior;
- invalid mode: current 400 behavior;
- source resolution/integrity failure: stable 503 behavior;
- presentation references a non-existent/non-mode source: new internal learning-slice integrity failure mapped to stable 503 without path/internal detail leakage.

### Valid empty states

The following are valid and do not fail the request:

- no verified prerequisites;
- no formulas;
- no figures;
- no review candidates;
- no practice candidates;
- no exercise subtype;
- no problem subtype;
- no canonical practice solution.

The UI should explain the specific empty state instead of using one generic “暂无内容”.

## 16. Frontend component boundaries

Phase 1H should avoid growing `SectionPage.tsx` into a monolith.

Recommended component split:

```text
SectionPage
├── StudyProgressPanel            existing behavior extracted if useful
├── PreviewLearningSlice
├── LearnLearningSlice
├── ReviewLearningSlice
│   ├── ReviewPresetTabs
│   └── RecallCard
├── PracticeLearningSlice
│   └── PracticeFilterTabs
└── source-backed cards
    ├── LearningObjectCard / typed variants
    ├── FormulaCard
    └── FigureReferenceCard
```

The exact file split may follow current App conventions, but each unit should have one clear responsibility and focused tests.

Do not perform unrelated frontend redesign.

## 17. Contract isolation from later architecture

Phase 1H implementation should include tests proving the learning-slice runtime does not depend on or activate:

- `runtime.shadow_fts` / H4a evaluation;
- production FTS/BM25;
- H3b Concept authority;
- StudyRecord schema internals;
- model providers/QA generation;
- Meeting/Lecture data;
- multi-book consumer migration.

A future approved stage may replace deterministic selectors with stronger evidence-aware policies, but Phase 1H v1 stays simple and auditable.

## 18. Implementation sequence

The implementation plan should use vertical slices in this order:

```text
1H-A  shared learning_slice_v1 contract + Preview
  ↓
1H-B  Review recall presets
  ↓
1H-C  Practice filters and explicit solution state
  ↓
1H-D  Learn grouping / specialized presentation
  ↓
1H-E  integrated acceptance + exact-head evidence
```

Each slice must keep the repository runnable and independently testable.

Every behavior-changing task follows real TDD RED → GREEN. No fabricated RED evidence.

## 19. Verification strategy

### 19.1 Runtime unit tests

Use synthetic fixtures covering at least:

- definition;
- theorem-family object;
- formula;
- example/other object;
- exercise;
- problem;
- figures inside/outside Section range;
- translation available/unavailable;
- empty optional groups.

Tests verify:

- deterministic output;
- source-order preservation;
- source-ref closure;
- exact preset membership;
- prerequisite fail-closed semantics;
- no generated canonical body text;
- no source mutation.

### 19.2 App/API tests

Verify:

- existing ModeResponse fields remain present and semantically unchanged;
- `presentation.schema_version == learning_slice_v1`;
- presentation references only valid response sources;
- all four endpoints return the correct presentation variant;
- stable error mapping;
- Search/Source/QA DTO contracts remain unchanged;
- StudyRecord API/storage contract remains unchanged.

### 19.3 Golden Course regression

`functional_analysis_course / ch01_s01` remains a mandatory real Section smoke target because it is already the current SectionLearning Golden fixture.

Additional real Golden checks should be selected deterministically from the canonical repository during plan authoring to ensure coverage of:

- a Section with at least one review-family source;
- a Section with practice-family source when present;
- a Section with a figure when present.

Selection must be read-only and then frozen in tests; canonical data is never changed to satisfy the selected fixture.

### 19.4 Web tests

Verify:

- Preview blocks and quick-check reveal;
- Review preset selection and deterministic subset;
- Practice filter selection;
- Learn grouping;
- empty states;
- URL query normalization;
- no new localStorage/StudyRecord authority;
- TypeScript discriminated presentation typing.

### 19.5 Real Chromium acceptance

At minimum cover:

1. open a real Section in Preview;
2. use a quick-check reveal and Source link;
3. return to Section with route/scroll state preserved;
4. switch to Review and choose a preset;
5. switch to Practice and apply a filter;
6. mark a mode complete and confirm persistence across reload;
7. confirm switching preset/filter does not create fake progress;
8. verify current QA entry still works independently;
9. verify 390×844 no body horizontal overflow.

### 19.6 Exact-head gates

Before Phase 1H implementation completion may be claimed, exact final HEAD must pass the repository-required relevant gates, including current Runtime/App/Web/Chromium and Golden integrity checks.

`books/functional-analysis/**` canonical diff must be empty for Phase 1H product work.

Public Search/QA must remain Exact-only.

## 20. Scope-diff expectations

Expected implementation areas may include:

```text
runtime/learning_slice_runtime.py          new
runtime/__init__.py                        controlled export if approved by plan
app/api/models.py
app/api/service.py
app/web/src/api/types.ts
app/web/src/pages/SectionPage.tsx
app/web/src/components/...                 focused learning-slice components
app/web/src/styles.css                     scoped UI additions
tests/...                                  runtime/Golden tests
app_tests/...                              API/contract tests
app/web/src/**/*.test.ts(x)                component/client tests
app/web/e2e/...                            browser acceptance
.github/workflows/...                      only if path/gate wiring is necessary
```

The implementation plan must minimize files and should not treat this list as permission for unrelated edits.

Expected unchanged protected areas include:

```text
books/functional-analysis/**
courses/**
runtime/retrieval.py production behavior
runtime/shadow_fts.py
H4a frozen/evaluation evidence
Search/Source/QA external contracts
StudyRecord schema/storage identity
ConceptGraph production authority
```

## 21. Completion criteria

Phase 1H v1 is complete only when all of the following are true:

1. `learning_slice_v1` presentation contract is implemented and deterministic.
2. Preview has useful source-derived objectives, core definitions/formulas/figure references, honest prerequisite status, and quick checks.
3. Review has working `1 minute / 5 minute / full` recall presets with canonical reveal.
4. Practice has real exercise/problem filters and explicit no-verified-solution behavior.
5. Learn has type-aware grouped presentation without changing source facts.
6. Existing Source round-trip behavior remains intact without changing the frozen Section session state shape.
7. Existing mode-level StudyRecord remains durable and semantically unchanged.
8. Search and QA remain Exact-only.
9. No H3b/B4b/B5/StudyRecord migration or multi-book consumer work entered the diff.
10. No canonical Functional Analysis content changed.
11. Required exact-head Runtime/App/Web/Chromium/Golden checks pass.
12. The final PR diff is reviewable, contains no unexpected unrelated refactor, and has no unresolved correctness blocker.

## 22. Post-Phase-1H future options

This design intentionally leaves later capabilities for their own evidence and approval gates:

- production Concept/prerequisite authority;
- supplementary-book Runtime consumption;
- Lecture/teacher supplement slots;
- durable practice answers;
- mistake classification;
- Mastery;
- spaced repetition scheduling;
- AI-generated variants/solutions;
- ExamPoint-aware review prioritization;
- FTS/semantic retrieval activation.

These future systems may enrich or replace Phase 1H selectors, but they should consume the same provenance-preserving source identities rather than rewriting textbook facts.

## 23. Final design decision

Phase 1H will use **one shared deterministic Learning Slice presentation contract over the existing SectionLearningRuntime**, not four disconnected frontend-only feature implementations and not a premature Learning Intelligence/Concept subsystem.

Implementation order is:

```text
Preview → Review → Practice → Learn → integrated exact-head gate
```

This gives the current Book App a materially better learning experience while keeping the architecture simple, source-grounded, reversible, and ready for later evidence-aware systems.
