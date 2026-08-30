# Phase 1H User-Visible Learning Slices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended where subagents are available) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved deterministic `learning_slice_v1` presentation layer and deliver useful Preview, Review, Practice, and Learn learning experiences without changing canonical textbook authority, Search/QA retrieval behavior, StudyRecord semantics, or frozen browser persistence shapes.

**Architecture:** Keep `SectionLearningRuntime` as the source-backed mode-candidate selector. Add an isolated `LearningSliceRuntime` that projects those candidates into reference-only, deterministic presentation metadata. `BookAppService` validates every presentation reference against the current mode response and adapts the projection into strongly typed Pydantic DTOs. React renders four focused learning-slice components and stores durable-enough view choices only in the URL query string. Canonical body text continues to come only from existing `ModeItem` / `SourceResolver` paths.

**Tech Stack:** Python 3.13 stdlib, existing Book Runtime, FastAPI, Pydantic v2, React 19, TypeScript 5.9, React Router 7, Vitest + Testing Library, Playwright Chromium, existing SQLite StudyRecord, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-30-phase-1h-learning-slices-design.md`

**Implementation branch:** `design/phase-1h-learning-slices-20260830`

**Implementation base:** `main@2675d2cecab63b28b6ab81a4554e9b7f010afd72`; approved design commit `bb0f20f3c70a44958dbce0f8630ec94e0c3242f6`.

## Global Constraints

- Run the project security pre-write gate before implementation writes and again after any repository/branch switch.
- Never write directly to `main`.
- `books/functional-analysis/**` and `courses/**` are canonical read-only inputs for Phase 1H.
- Preserve all existing `ModeResponse` fields and semantics; Phase 1H adds exactly one top-level field: `presentation`.
- Preserve H1-frozen Search, Source, and QA external DTOs exactly.
- Preserve the existing Section session-storage object shape exactly. New Review/Practice selection state lives in URL query parameters only.
- Preserve StudyRecord schema and semantics exactly: no record = not started, `in_progress/0`, `completed/100`.
- Do not activate FTS5/BM25/fusion, semantic retrieval, H3b Concept authority, B4b, B5, multi-book consumer migration, Lecture authority, Mastery, durable per-question answers, or StudyRecord book-version migration.
- Do not generate textbook facts, solutions, prerequisites, importance, difficulty, exam relevance, mastery, or correctness with AI or heuristics.
- Do not render or fabricate figure pixels unless a canonical figure asset contract already exposes them. Phase 1H v1 uses figure metadata/source links only.
- Every behavior-changing task follows real RED → GREEN. Record the failing test before implementation; do not fabricate RED evidence after implementation exists.
- Commit each cohesive GREEN checkpoint. Do not squash/rewrite history through agent operations.
- Keep PR #26 draft during implementation until exact-head verification is complete. Do not merge it without explicit user authorization naming PR #26.

---

## Contract Map Before Tasks

### Existing interfaces consumed unchanged

`SectionLearningRuntime.from_course(course, section_id)` produces one source-backed runtime for a Section.

`SectionLearningRuntime.source()` exposes canonical Section metadata and source rows:

- `objects`: stable source order; rows contain `kind`, `id`, `type`, `number`, `name_en`, `name_zh`, `formula`, page/anchor/batch metadata.
- `figures`: deterministic page/id order; rows contain `kind`, `id`, titles and page/anchor/batch metadata.
- `translation_sources`: stable deduplicated source-batch order; rows contain `batch_id`, `available`.

Existing mode methods remain authoritative for candidate membership:

- `preview()` → objects + figures + translations.
- `learn()` → objects + figures + translations.
- `review()` → current exact normalized review-family objects only.
- `practice()` → current exact `exercise` / `problem` objects only.

`BookAppService.mode(course_id, section_id, mode)` continues to resolve every candidate through `SourceResolver` and produce `ModeItem[]` plus matching `source_refs`.

### New Runtime interface

Create `runtime/learning_slice_runtime.py` with:

```python
LEARNING_SLICE_SCHEMA_VERSION = "learning_slice_v1"
REVIEW_PRESET_IDS = ("one_minute", "five_minute", "full")
PRACTICE_KIND_IDS = ("all", "exercise", "problem")

class LearningSliceRuntimeError(RuntimeError): ...
class LearningSliceIntegrityError(LearningSliceRuntimeError): ...
class LearningSliceModeError(LearningSliceRuntimeError): ...

@dataclass(frozen=True)
class LearningSliceProjection:
    payload: dict[str, object]
    source_refs: tuple[tuple[str, str], ...]

class LearningSliceRuntime:
    def __init__(self, learning: SectionLearningRuntime): ...
    def preview(self) -> LearningSliceProjection: ...
    def review(self) -> LearningSliceProjection: ...
    def practice(self) -> LearningSliceProjection: ...
    def learn(self) -> LearningSliceProjection: ...
    def presentation(self, mode: str) -> LearningSliceProjection: ...
```

The constructor reads `learning.source()` once and may read current mode payloads, but it must not call Search, QA, model providers, Concept runtime, StudyRecord, FTS, or external I/O.

### Shared source reference JSON

Every presentation reference uses exactly:

```json
{"kind": "object", "source_id": "def_lp"}
```

No canonical body text is copied into `presentation`.

### Shared deterministic prompt JSON

```json
{
  "text": "你能说出「L^p 空间」的定义吗？",
  "derivation": "deterministic_template",
  "source_ref": {"kind": "object", "source_id": "def_lp"}
}
```

### Preview presentation JSON

```json
{
  "schema_version": "learning_slice_v1",
  "mode": "preview",
  "overview": {
    "object_count": 0,
    "figure_count": 0,
    "translation_available": false
  },
  "object_counts": [
    {"object_type": "definition", "count": 2}
  ],
  "objectives": [],
  "prerequisites": {"status": "unavailable", "items": []},
  "core_definitions": [],
  "core_formulas": [],
  "key_figures": [],
  "quick_checks": []
}
```

Rules:

- `object_counts` uses normalized object type (`strip().casefold()`) in first-seen type order.
- objective templates apply only to definition, theorem-family, formula, example, exercise/problem.
- objective display cap = 8.
- objective selection is diversity-first by category order `definition`, `theorem_family`, `formula`, `example`, `practice`; then fill unused eligible objects in canonical source order to 8.
- `source label` = first non-empty of `name_zh`, `name_en`, `number`, normalized type fallback.
- `core_definitions` = all normalized `definition` objects in source order.
- `core_formulas` = every source object that is explicit type `formula` OR has a non-empty canonical `formula`; deduplicate by `(kind, source_id)` preserving first occurrence.
- `key_figures` = all Preview figure references in existing figure order.
- quick-check eligible categories = definition, theorem-family, formula; display cap = 6; same diversity-first category order then source-order fill.
- prerequisites stay exactly `{"status":"unavailable","items":[]}` in Phase 1H v1 because no current production prerequisite authority exists.

Fixed objective templates:

```text
definition      -> 理解并能复述：{label}
theorem family  -> 理解并能说明结论与条件：{label}
formula         -> 识别并能写出：{label}
example         -> 能够跟随教材例题：{label}
exercise/problem-> 尝试教材练习：{label}
```

Fixed quick-check templates:

```text
definition      -> 你能说出「{label}」的定义吗？
theorem family  -> 你能说明「{label}」的条件和结论吗？
formula         -> 你能不看教材写出「{label}」吗？
```

### Review presentation JSON

```json
{
  "schema_version": "learning_slice_v1",
  "mode": "review",
  "presets": [
    {"id": "one_minute", "label": "1 分钟", "source_refs": []},
    {"id": "five_minute", "label": "5 分钟", "source_refs": []},
    {"id": "full", "label": "完整复习", "source_refs": []}
  ],
  "prompts": []
}
```

Review selection rules are exactly those in the approved spec:

- `full` = every current review candidate in canonical source order.
- `one_minute` max 3: first definition, first theorem-family, first formula; fill remaining slots with earliest unused review candidates.
- `five_minute` max 10: same diversity-first seed; fill remaining slots with earliest unused review candidates.
- no importance, difficulty, mastery, or exam ranking.
- one prompt per review candidate, keyed by `source_ref`.

Fixed Review prompt templates:

```text
definition      -> 先回忆「{label}」的定义，再显示教材内容。
theorem family  -> 先回忆「{label}」的条件和结论，再显示教材内容。
formula         -> 先尝试写出「{label}」，再显示教材公式。
```

### Practice presentation JSON

```json
{
  "schema_version": "learning_slice_v1",
  "mode": "practice",
  "filters": [
    {"id": "all", "label": "全部", "source_refs": []}
  ],
  "items": [
    {
      "source_ref": {"kind": "object", "source_id": "..."},
      "solution_status": "unavailable"
    }
  ]
}
```

Rules:

- `all` is always present.
- add `exercise` only if at least one normalized exercise candidate exists.
- add `problem` only if at least one normalized problem candidate exists.
- each filter preserves current practice candidate source order.
- every item has `solution_status = "unavailable"` in v1; do not parse body text to guess solutions.

### Learn presentation JSON

```json
{
  "schema_version": "learning_slice_v1",
  "mode": "learn",
  "groups": [
    {"id": "definitions", "label": "定义 / 概念入口", "source_refs": []},
    {"id": "theorem_family", "label": "定理与命题", "source_refs": []},
    {"id": "formulas", "label": "公式", "source_refs": []},
    {"id": "examples", "label": "例题", "source_refs": []},
    {"id": "other_objects", "label": "其他教材对象", "source_refs": []},
    {"id": "figures", "label": "教材图示", "source_refs": []},
    {"id": "translations", "label": "中文学习层", "source_refs": []}
  ],
  "extensions": {
    "supplementary": {"status": "unavailable"},
    "lecture": {"status": "unavailable"}
  }
}
```

Omit empty groups from the emitted `groups` array. Grouping is mutually exclusive for object references:

- `definition` → `definitions`
- theorem/proposition/lemma/corollary → `theorem_family`
- explicit `formula` type → `formulas`
- `example` → `examples`
- every remaining object type, including proof/remark/concept/exercise/problem/unknown → `other_objects`
- figures → `figures`
- translations → `translations`

A theorem carrying a canonical formula remains in `theorem_family`; formula rendering stays a property of the existing `ModeItem`, avoiding duplicated source membership.

### API DTO interface

In `app/api/models.py`, after `SourceRef`, introduce strongly typed Pydantic models:

- `LearningSliceDerivedPrompt`
- `LearningSliceObjectCount`
- `LearningSliceOverview`
- `LearningSlicePrerequisites`
- `LearningSlicePreset`
- `LearningSlicePracticeFilter`
- `LearningSlicePracticeItem`
- `LearningSliceGroup`
- `LearningSliceExtensionStatus`
- `PreviewLearningSlicePresentation`
- `ReviewLearningSlicePresentation`
- `PracticeLearningSlicePresentation`
- `LearnLearningSlicePresentation`
- `LearningSlicePresentation` as a discriminated union on `mode`.

Then add:

```python
presentation: LearningSlicePresentation
```

to `ModeResponse` and no other existing top-level response model.

### Frontend TypeScript interface

Mirror the API as a discriminated union:

```ts
export type LearningSlicePresentation =
  | PreviewLearningSlicePresentation
  | ReviewLearningSlicePresentation
  | PracticeLearningSlicePresentation
  | LearnLearningSlicePresentation

export interface ModeResponse {
  // all current fields unchanged
  presentation: LearningSlicePresentation
}
```

### Service closure invariant

After existing `ModeItem[]` construction, `BookAppService.mode(...)` builds:

```python
allowed_refs = {(item.kind, item.source_id) for item in items}
projection = LearningSliceRuntime(learning).presentation(normalized_mode)
```

Every pair in `projection.source_refs` must be in `allowed_refs`. A missing reference maps to:

```text
AppUnavailableError
code = learning_slice_integrity_error
user_message = 学习内容暂不可用
HTTP = 503 through the existing AppUnavailable handler
```

Do not expose path/internal exception detail in the HTTP body.

---

## Task 1: Establish `LearningSliceRuntime` with the Preview contract

**Files:**
- Create: `runtime/learning_slice_runtime.py`
- Create: `tests/test_learning_slice_runtime.py`
- Modify: `runtime/__init__.py`

**Consumes:** `SectionLearningRuntime.source()`, `SectionLearningRuntime.preview()`.

**Produces:** deterministic `LearningSliceProjection` for Preview plus exported Runtime symbols.

- [ ] **Step 1: Write failing Runtime contract tests before the module exists**

Create `tests/test_learning_slice_runtime.py`. Reuse the synthetic fixture pattern in `tests/test_section_learning_runtime.py`, but include at least:

- two definitions;
- theorem + proposition;
- explicit formula;
- theorem with non-empty formula;
- example;
- exercise;
- problem;
- remark/other;
- one in-range figure and one out-of-range figure;
- one available and one unavailable translation batch.

Tests must cover:

```python
class LearningSlicePreviewTests(unittest.TestCase):
    def test_preview_uses_learning_slice_v1_and_mode_discriminator(self): ...
    def test_preview_overview_matches_source_counts_without_copying_body_text(self): ...
    def test_preview_object_counts_preserve_first_seen_type_order(self): ...
    def test_preview_objectives_are_deterministic_diversity_first_and_capped_at_eight(self): ...
    def test_preview_objectives_use_only_fixed_templates_and_source_refs(self): ...
    def test_preview_prerequisites_are_explicitly_unavailable(self): ...
    def test_preview_core_definitions_preserve_source_order(self): ...
    def test_preview_core_formulas_include_formula_type_and_formula_bearing_objects_once(self): ...
    def test_preview_key_figures_use_only_in_range_section_figures(self): ...
    def test_preview_quick_checks_are_deterministic_and_capped_at_six(self): ...
    def test_preview_projection_reports_every_nested_source_ref_for_closure_validation(self): ...
    def test_preview_does_not_mutate_section_learning_source(self): ...
```

Also add one dispatch test proving unsupported mode raises `LearningSliceModeError`.

- [ ] **Step 2: Run focused tests and confirm real RED**

```bash
python -m unittest tests.test_learning_slice_runtime -v
```

Expected RED: import/module failure for `runtime.learning_slice_runtime`.

Commit the RED test checkpoint before implementation:

```bash
git add tests/test_learning_slice_runtime.py
git commit -m "test: define Phase 1H learning slice contract"
```

- [ ] **Step 3: Implement only the shared helpers and Preview projection**

Implement the exact interfaces and fixed selection/template rules in the Contract Map. Keep helper functions private unless tests need a stable public seam. Required implementation properties:

- normalize types only with `str(value or "").strip().casefold()`;
- build source labels only from source row metadata;
- never read translation text or source body text;
- collect `projection.source_refs` from every nested emitted reference and stable-deduplicate them;
- copy source row lists before iterating if mutation could otherwise leak;
- reject blank/duplicate source identities with `LearningSliceIntegrityError` rather than silently fabricating identities.

Export `LearningSliceRuntime`, `LearningSliceRuntimeError`, `LearningSliceIntegrityError`, `LearningSliceModeError`, `LearningSliceProjection`, and `LEARNING_SLICE_SCHEMA_VERSION` from `runtime/__init__.py`.

- [ ] **Step 4: Run focused Runtime tests to GREEN**

```bash
python -m unittest tests.test_learning_slice_runtime tests.test_section_learning_runtime -v
python -m py_compile runtime/learning_slice_runtime.py runtime/section_learning_runtime.py
```

- [ ] **Step 5: Commit the Preview Runtime implementation**

```bash
git add runtime/learning_slice_runtime.py runtime/__init__.py tests/test_learning_slice_runtime.py
git commit -m "feat: add deterministic Preview learning slice"
```

---

## Task 2: Add the strongly typed API presentation contract and closure validation

**Files:**
- Modify: `app/api/models.py`
- Modify: `app/api/service.py`
- Modify: `app_tests/test_app_service.py`
- Modify: `app_tests/test_api.py`
- Modify: `app_tests/test_serialization_contracts.py`

**Consumes:** `LearningSliceRuntime.presentation(mode)`, existing `ModeItem[]` / `SourceResolver` resolution.

**Produces:** `ModeResponse.presentation` with a typed Preview variant and a stable 503 integrity boundary.

- [ ] **Step 1: Write failing service/API/serialization tests**

Add tests proving:

```python
def test_preview_mode_adds_learning_slice_v1_presentation_without_changing_existing_fields(): ...
def test_preview_presentation_refs_are_subset_of_mode_items(): ...
def test_preview_presentation_contains_no_internal_provenance_or_canonical_body_copy(): ...
def test_learning_slice_integrity_failure_maps_to_stable_app_unavailable_error(): ...
def test_preview_endpoint_serializes_presentation_contract(): ...
def test_search_source_and_qa_frozen_keys_remain_exactly_unchanged(): ...
```

For the integrity-failure test, patch/inject the presentation seam at the smallest practical boundary so a projection refers to `("object", "missing_source")`. Do not corrupt canonical fixture files to trigger the error.

Define a new ModeResponse key set in serialization tests:

```python
MODE_RESPONSE_KEYS = {
    "mode", "course_id", "book_id", "chapter_id", "section_id",
    "source_status", "items", "source_refs", "presentation",
}
```

Keep existing Search/Source/QA frozen key sets byte-for-byte unchanged.

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
python -m unittest \
  app_tests.test_app_service \
  app_tests.test_api \
  app_tests.test_serialization_contracts \
  -v
```

Expected RED: `ModeResponse` has no `presentation` field and service does not construct/validate a learning-slice projection.

Commit RED tests:

```bash
git add app_tests/test_app_service.py app_tests/test_api.py app_tests/test_serialization_contracts.py
git commit -m "test: define learning slice API projection contract"
```

- [ ] **Step 3: Implement typed models and service wiring**

In `models.py` use `Literal` mode/status values and an `Annotated[..., Field(discriminator="mode")]` union for the four presentation variants. Only Preview is behaviorally populated at this checkpoint; the other variants may already have their final structural model definitions because the union must be closed and typed, but do not fabricate data for unimplemented Runtime modes.

In `BookAppService.mode(...)`:

1. keep all current candidate resolution unchanged;
2. construct `LearningSliceRuntime(learning).presentation(normalized_mode)`;
3. validate `projection.source_refs` against the exact resolved mode `items` set;
4. map Runtime integrity errors to stable `AppUnavailableError(code="learning_slice_integrity_error", user_message="学习内容暂不可用", detail=...)`;
5. pass `projection.payload` into `ModeResponse(presentation=...)`.

Until Tasks 4/6/8 implement Review/Practice/Learn Runtime projections, `LearningSliceRuntime.presentation()` must already return valid minimal final-shape projections for those modes without introducing user-visible feature behavior beyond empty/reference-safe structure. This keeps all four existing endpoints valid after adding the required non-optional `presentation` field. The later tasks fill each mode according to the frozen contract; they do not change the top-level schema.

- [ ] **Step 4: Run App/API tests to GREEN**

```bash
python -m unittest \
  app_tests.test_app_service \
  app_tests.test_api \
  app_tests.test_serialization_contracts \
  tests.test_learning_slice_runtime \
  -v
```

- [ ] **Step 5: Commit API integration**

```bash
git add app/api/models.py app/api/service.py app_tests/test_app_service.py app_tests/test_api.py app_tests/test_serialization_contracts.py
git commit -m "feat: expose learning slice presentation contract"
```

---

## Task 3: Deliver the Preview vertical slice in React

**Files:**
- Modify: `app/web/src/api/types.ts`
- Create: `app/web/src/components/PreviewLearningSlice.tsx`
- Create: `app/web/src/components/PreviewLearningSlice.test.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/styles.css`

**Consumes:** Preview `ModeResponse.presentation`, existing `ModeItem[]`, existing `SourceLink` and source-navigation save callback.

**Produces:** source-derived Preview overview/objectives/prerequisite notice/core definitions/formulas/figures/quick checks.

- [ ] **Step 1: Add failing TypeScript/component/page tests**

Mirror the exact discriminated union from the API. Add fixture builders to `SectionPage.test.tsx` so every `ModeResponse` includes the correct minimal presentation variant.

Create focused component tests covering:

- Preview heading/overview counts;
- visible label that derived objectives/quick checks are system learning guidance, not textbook quotations;
- objective text and source link;
- prerequisite text `暂无可验证的前置知识关系`;
- core definition/formula/figure reference sections only when non-empty;
- quick-check answer hidden initially;
- clicking quick-check reveal shows the corresponding existing `ModeItem.content_zh` or formula without generating a separate answer;
- source navigation callback fires with the source identity;
- empty optional groups are not rendered.

Update `SectionPage.test.tsx` to prove Preview no longer relies on the old locally computed `previewCounts`; presentation drives the Preview blocks.

- [ ] **Step 2: Run web tests and confirm RED**

```bash
cd app/web
npm test -- --run src/components/PreviewLearningSlice.test.tsx src/pages/SectionPage.test.tsx
npm run typecheck
```

Expected RED: TypeScript `ModeResponse` lacks `presentation` typing and Preview component does not exist.

Commit RED tests only:

```bash
git add app/web/src/components/PreviewLearningSlice.test.tsx app/web/src/pages/SectionPage.test.tsx
git commit -m "test: define Preview learning slice UI"
```

- [ ] **Step 3: Implement TypeScript types and `PreviewLearningSlice`**

Component props must stay narrow:

```ts
interface PreviewLearningSliceProps {
  courseId: string
  items: ModeItem[]
  presentation: PreviewLearningSlicePresentation
  expandedSourceIds: string[]
  onExpandedChange: (sourceId: string, expanded: boolean) => void
  onBeforeSourceNavigate: (sourceId: string) => void
}
```

Build a local `Map<string, ModeItem>` keyed by `${kind}:${source_id}`. Every presentation reference must resolve in that map; if a reference is unexpectedly missing client-side, render a generic non-sensitive `学习内容暂不可用` status rather than fabricating content.

Quick-check reveal may reuse the page-level `expandedSourceIds` so Source round trips preserve reveals where the existing mechanism already supports them. It must not write StudyRecord or localStorage.

Replace the old `previewCounts` branch in `SectionPage.tsx` with this component only when `payload.presentation.mode === "preview"`.

- [ ] **Step 4: Run web focused tests/typecheck/build to GREEN**

```bash
cd app/web
npm test -- --run src/components/PreviewLearningSlice.test.tsx src/pages/SectionPage.test.tsx src/api/client.test.ts
npm run typecheck
npm run build
```

- [ ] **Step 5: Commit Preview UI**

```bash
git add \
  app/web/src/api/types.ts \
  app/web/src/components/PreviewLearningSlice.tsx \
  app/web/src/components/PreviewLearningSlice.test.tsx \
  app/web/src/pages/SectionPage.tsx \
  app/web/src/pages/SectionPage.test.tsx \
  app/web/src/styles.css
git commit -m "feat: render source-grounded Preview learning slice"
```

---

## Task 4: Implement deterministic Review presets in Runtime and API

**Files:**
- Modify: `runtime/learning_slice_runtime.py`
- Modify: `tests/test_learning_slice_runtime.py`
- Modify: `app_tests/test_app_service.py`
- Modify: `app_tests/test_api.py`

**Consumes:** current `SectionLearningRuntime.review()` candidate order.

**Produces:** exact `one_minute`, `five_minute`, `full` source subsets and deterministic recall prompts.

- [ ] **Step 1: Add failing Review Runtime tests**

Cover exact membership/order:

```python
class LearningSliceReviewTests(unittest.TestCase):
    def test_full_preset_is_all_review_candidates_in_source_order(self): ...
    def test_one_minute_seeds_definition_theorem_family_formula_then_fills_to_three(self): ...
    def test_five_minute_uses_same_diversity_seed_then_fills_to_ten(self): ...
    def test_presets_never_duplicate_source_refs(self): ...
    def test_review_prompts_use_only_fixed_templates(self): ...
    def test_empty_review_is_valid_and_all_presets_are_empty(self): ...
    def test_review_projection_refs_are_closed_over_review_mode_candidates(self): ...
```

Add App/API tests that `presentation.mode == "review"`, labels and IDs serialize exactly, and `items/source_refs` stay unchanged.

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
python -m unittest tests.test_learning_slice_runtime app_tests.test_app_service app_tests.test_api -v
```

Expected RED: Review presentation is still the initial empty reference-safe structural Review projection and lacks required preset membership/prompts.

Commit RED tests:

```bash
git add tests/test_learning_slice_runtime.py app_tests/test_app_service.py app_tests/test_api.py
git commit -m "test: define deterministic Review presets"
```

- [ ] **Step 3: Implement Review projection only**

Use the exact preset algorithm from the Contract Map. Use current review candidate membership; do not re-include non-review source objects. Preserve original source type text outside normalization used for category selection.

- [ ] **Step 4: Run Runtime/App tests to GREEN**

```bash
python -m unittest tests.test_learning_slice_runtime tests.test_section_learning_runtime app_tests.test_app_service app_tests.test_api -v
```

- [ ] **Step 5: Commit Review Runtime/API behavior**

```bash
git add runtime/learning_slice_runtime.py tests/test_learning_slice_runtime.py app_tests/test_app_service.py app_tests/test_api.py
git commit -m "feat: add deterministic Review recall presets"
```

---

## Task 5: Deliver Review preset UI and preserve source round-trip state

**Files:**
- Create: `app/web/src/components/ReviewLearningSlice.tsx`
- Create: `app/web/src/components/ReviewLearningSlice.test.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/styles.css`
- Verify unchanged: `app/web/src/state/sectionViewState.ts`
- Verify unchanged: `app/web/src/state/sectionViewState.test.ts`

**Consumes:** Review presentation + `?review_preset=` URL state + existing `expandedSourceIds`.

**Produces:** `1 分钟 / 5 分钟 / 完整复习` active-recall UI with think → reveal behavior.

- [ ] **Step 1: Add failing component/page tests**

Cover:

- missing `review_preset` normalizes to `full` in rendered selection;
- invalid value falls back to `full` and URL is replace-normalized to `review_preset=full`;
- selecting `one_minute` writes only URL query state and does not call `touchStudy` again for the same Review mode payload;
- selecting `five_minute` renders exactly the refs in that preset;
- recall prompt appears before reveal;
- canonical body/formula remains hidden before reveal;
- reveal uses existing `expandedSourceIds` and displays current `ModeItem` only;
- Source navigation saves a route containing both `mode=review` and the selected `review_preset`;
- `sectionViewState` serialized object still contains only `route`, `scrollY`, `expandedSourceIds`, `activeSourceId`.

- [ ] **Step 2: Run tests and confirm RED**

```bash
cd app/web
npm test -- --run src/components/ReviewLearningSlice.test.tsx src/pages/SectionPage.test.tsx src/state/sectionViewState.test.ts
```

Expected RED: Review component/preset query behavior does not exist.

Commit RED tests:

```bash
git add app/web/src/components/ReviewLearningSlice.test.tsx app/web/src/pages/SectionPage.test.tsx
git commit -m "test: define Review preset interaction"
```

- [ ] **Step 3: Implement Review UI**

`ReviewLearningSlice` receives current `selectedPresetId` from `SectionPage` and a callback to update URL query params. `SectionPage` owns URL normalization so the component does not know router internals.

When changing mode away from Review, preserve unrelated safe query params only if they remain semantically meaningful; remove stale `review_preset` when entering a non-Review mode. When entering Review with no valid preset, normalize to `full` with `replace: true`.

Do not add any new key to sessionStorage or localStorage.

- [ ] **Step 4: Run web regression to GREEN**

```bash
cd app/web
npm test -- --run src/components/ReviewLearningSlice.test.tsx src/pages/SectionPage.test.tsx src/state/sectionViewState.test.ts
npm run typecheck
npm run build
```

- [ ] **Step 5: Commit Review UI**

```bash
git add \
  app/web/src/components/ReviewLearningSlice.tsx \
  app/web/src/components/ReviewLearningSlice.test.tsx \
  app/web/src/pages/SectionPage.tsx \
  app/web/src/pages/SectionPage.test.tsx \
  app/web/src/styles.css
git commit -m "feat: add Review preset recall workflow"
```

---

## Task 6: Implement Practice filters and explicit no-solution semantics in Runtime/API

**Files:**
- Modify: `runtime/learning_slice_runtime.py`
- Modify: `tests/test_learning_slice_runtime.py`
- Modify: `app_tests/test_app_service.py`
- Modify: `app_tests/test_api.py`

**Consumes:** current `SectionLearningRuntime.practice()` candidate order.

**Produces:** filter refs and `solution_status="unavailable"` for every current practice item.

- [ ] **Step 1: Add failing Practice tests**

Cover:

```python
class LearningSlicePracticeTests(unittest.TestCase):
    def test_all_filter_always_exists_and_preserves_candidate_order(self): ...
    def test_exercise_filter_exists_only_when_exercise_candidate_exists(self): ...
    def test_problem_filter_exists_only_when_problem_candidate_exists(self): ...
    def test_every_practice_item_has_explicit_unavailable_solution_status(self): ...
    def test_practice_does_not_parse_body_text_for_solution_detection(self): ...
    def test_empty_practice_is_valid_with_only_empty_all_filter(self): ...
    def test_practice_projection_refs_are_closed_over_practice_candidates(self): ...
```

The no-parsing test should include fixture content containing words such as `solution` or `解析` and still assert `solution_status == "unavailable"`.

Add API tests for exact serialized filter IDs/labels and solution status.

- [ ] **Step 2: Confirm RED**

```bash
python -m unittest tests.test_learning_slice_runtime app_tests.test_app_service app_tests.test_api -v
```

Commit RED tests:

```bash
git add tests/test_learning_slice_runtime.py app_tests/test_app_service.py app_tests/test_api.py
git commit -m "test: define Practice learning slice filters"
```

- [ ] **Step 3: Implement Practice projection**

Use only current practice candidates. Do not inspect `content_zh`, translations, Search, or QA to infer a solution relationship.

- [ ] **Step 4: Run focused regression to GREEN**

```bash
python -m unittest tests.test_learning_slice_runtime tests.test_section_learning_runtime app_tests.test_app_service app_tests.test_api -v
```

- [ ] **Step 5: Commit Practice Runtime/API**

```bash
git add runtime/learning_slice_runtime.py tests/test_learning_slice_runtime.py app_tests/test_app_service.py app_tests/test_api.py
git commit -m "feat: add Practice filters with explicit solution state"
```

---

## Task 7: Deliver Practice filter UI without creating a new answer store

**Files:**
- Create: `app/web/src/components/PracticeLearningSlice.tsx`
- Create: `app/web/src/components/PracticeLearningSlice.test.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/components/LearningObjectCard.tsx`
- Modify: `app/web/src/styles.css`

**Consumes:** Practice presentation + `?practice_kind=` URL state.

**Produces:** visible all/exercise/problem filtering, filtered count, per-card expansion, canonical Source links, exact unavailable-solution wording.

- [ ] **Step 1: Add failing web tests**

Cover:

- missing `practice_kind` behaves as `all`;
- invalid value replace-normalizes to `all`;
- absent subtype filter is not rendered;
- selecting `exercise` shows only exercise refs and correct filtered count;
- selecting `problem` shows only problem refs;
- changing filters does not call StudyRecord `touch` again for the same mode;
- Source round-trip route preserves `practice_kind`;
- each practice card states `教材数据中暂未提供可验证解析`;
- no answer textbox, correctness control, durable answer write, or localStorage use is introduced.

- [ ] **Step 2: Confirm RED**

```bash
cd app/web
npm test -- --run src/components/PracticeLearningSlice.test.tsx src/pages/SectionPage.test.tsx
```

Commit RED tests:

```bash
git add app/web/src/components/PracticeLearningSlice.test.tsx app/web/src/pages/SectionPage.test.tsx
git commit -m "test: define Practice filter interaction"
```

- [ ] **Step 3: Implement Practice UI**

`PracticeLearningSlice` maps presentation refs back to existing `ModeItem`s. Replace the older generic `LearningObjectCard` Practice wording with the exact verified-data wording from the approved spec. If expansion is used, keep it UI-local/page-level only; no persistence schema change.

Remove stale `practice_kind` when switching to a non-Practice mode. Do not carry `review_preset` into Practice.

- [ ] **Step 4: Run web tests/typecheck/build to GREEN**

```bash
cd app/web
npm test -- --run src/components/PracticeLearningSlice.test.tsx src/pages/SectionPage.test.tsx
npm run typecheck
npm run build
```

- [ ] **Step 5: Commit Practice UI**

```bash
git add \
  app/web/src/components/PracticeLearningSlice.tsx \
  app/web/src/components/PracticeLearningSlice.test.tsx \
  app/web/src/pages/SectionPage.tsx \
  app/web/src/pages/SectionPage.test.tsx \
  app/web/src/components/LearningObjectCard.tsx \
  app/web/src/styles.css
git commit -m "feat: add source-backed Practice filters"
```

---

## Task 8: Implement Learn type-aware grouping in Runtime/API

**Files:**
- Modify: `runtime/learning_slice_runtime.py`
- Modify: `tests/test_learning_slice_runtime.py`
- Modify: `app_tests/test_app_service.py`
- Modify: `app_tests/test_api.py`

**Consumes:** current `SectionLearningRuntime.learn()` source order.

**Produces:** non-empty reference-only groups and unavailable extension statuses.

- [ ] **Step 1: Add failing Learn grouping tests**

Cover:

```python
class LearningSliceLearnTests(unittest.TestCase):
    def test_learn_groups_are_mutually_exclusive_for_objects(self): ...
    def test_learn_groups_preserve_source_order_within_each_group(self): ...
    def test_learn_omits_empty_groups(self): ...
    def test_formula_bearing_theorem_remains_theorem_family_not_duplicate_formula_group(self): ...
    def test_figures_and_translations_keep_existing_runtime_order(self): ...
    def test_supplementary_and_lecture_extensions_are_explicitly_unavailable(self): ...
    def test_learn_projection_contains_no_body_text(self): ...
    def test_learn_projection_refs_are_closed_over_learn_candidates(self): ...
```

Add App/API tests for group IDs/order and extension statuses.

- [ ] **Step 2: Confirm RED**

```bash
python -m unittest tests.test_learning_slice_runtime app_tests.test_app_service app_tests.test_api -v
```

Commit RED tests:

```bash
git add tests/test_learning_slice_runtime.py app_tests/test_app_service.py app_tests/test_api.py
git commit -m "test: define Learn grouping contract"
```

- [ ] **Step 3: Implement Learn projection**

Use the exact mutually-exclusive grouping contract from the Contract Map. Do not create supplementary/lecture refs; emit only `status="unavailable"` extension metadata.

- [ ] **Step 4: Run focused tests to GREEN**

```bash
python -m unittest tests.test_learning_slice_runtime tests.test_section_learning_runtime app_tests.test_app_service app_tests.test_api -v
```

- [ ] **Step 5: Commit Learn Runtime/API**

```bash
git add runtime/learning_slice_runtime.py tests/test_learning_slice_runtime.py app_tests/test_app_service.py app_tests/test_api.py
git commit -m "feat: add type-aware Learn grouping"
```

---

## Task 9: Deliver Learn grouped UI with focused source-backed cards

**Files:**
- Create: `app/web/src/components/LearnLearningSlice.tsx`
- Create: `app/web/src/components/LearnLearningSlice.test.tsx`
- Create: `app/web/src/components/FigureReferenceCard.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/styles.css`

**Consumes:** Learn presentation groups + current `ModeItem[]`.

**Produces:** grouped definitions/theorem-family/formulas/examples/other objects/figures/translations without changing canonical content.

- [ ] **Step 1: Add failing Learn UI tests**

Cover:

- non-empty groups render in presentation order;
- empty groups are absent;
- theorem carrying formula renders once in theorem group and still displays its existing formula field;
- explicit formula object renders in formula group;
- figure reference card displays available title/page metadata and Source link only, never a fabricated `<img>`;
- translation group displays availability status from `ModeItem.translation_available`;
- supplementary/lecture areas are not rendered as evidence cards when status is unavailable;
- Source links use the existing save-before-navigation callback.

- [ ] **Step 2: Confirm RED**

```bash
cd app/web
npm test -- --run src/components/LearnLearningSlice.test.tsx src/pages/SectionPage.test.tsx
```

Commit RED tests:

```bash
git add app/web/src/components/LearnLearningSlice.test.tsx app/web/src/pages/SectionPage.test.tsx
git commit -m "test: define grouped Learn presentation"
```

- [ ] **Step 3: Implement Learn UI and figure metadata card**

Keep `LearningObjectCard` for source-backed objects where it already fits. `FigureReferenceCard` must accept a `ModeItem` and never attempt image discovery or screenshotting.

`SectionPage` should dispatch exactly one focused component per current `payload.presentation.mode`; do not retain a second flat list that duplicates the same Learn/Review/Practice content.

- [ ] **Step 4: Run web regression to GREEN**

```bash
cd app/web
npm test -- --run src/components/LearnLearningSlice.test.tsx src/pages/SectionPage.test.tsx
npm run typecheck
npm run build
```

- [ ] **Step 5: Commit Learn UI**

```bash
git add \
  app/web/src/components/LearnLearningSlice.tsx \
  app/web/src/components/LearnLearningSlice.test.tsx \
  app/web/src/components/FigureReferenceCard.tsx \
  app/web/src/pages/SectionPage.tsx \
  app/web/src/pages/SectionPage.test.tsx \
  app/web/src/styles.css
git commit -m "feat: render grouped Learn learning slice"
```

---

## Task 10: Add isolation, frozen real-Golden coverage, and browser acceptance

**Files:**
- Create: `tests/test_learning_slice_isolation.py`
- Modify: `app/web/e2e/functional-analysis.spec.ts`
- Modify: `app/web/e2e/study-record-persistence.spec.ts`
- Modify: `.github/workflows/app-ui-tests.yml` only if an exact-head focused command/path needs explicit inclusion; current `runtime/**`, `tests/**`, `app/**`, `app_tests/**` path coverage already catches all planned implementation files.

**Consumes:** completed Phase 1H Runtime/API/Web flow.

**Produces:** proof that Phase 1H remains isolated from forbidden later authorities and works in real Chromium.

### Frozen real-course fixtures for this plan

The fixture selection below was performed during plan authoring from canonical read-only evidence. Tests must exercise the selected identities through Runtime/API product paths; structure JSON is selection evidence only, not a second product authority.

Primary Section / Review fixture:

```text
course_id = functional_analysis_course
section_id = ch01_s01
```

Reason: this is already the existing SectionLearning/Chromium Golden smoke Section and exposes real review-family source evidence including `def_lp`.

Formula/theorem-heavy fixture:

```text
section_id = ch01_s05_04
```

Reason: canonical `chunk_003a_structure.json` fixes Section 5.4 (`ch01_s05_04`) to PDF 42–46 and records definition/theorem/corollary objects with formula-bearing source evidence inside that Section page range.

Practice fixtures:

```text
exercise_section_id = ch01_s08
problem_section_id = ch01_s09
```

Reason: canonical `chunk_004a_structure.json` fixes `ch01_s08` as “Exercises” (PDF 53–62) and `ch01_s09` as “Problems” (PDF 62–65), and records explicit `ch01_ex_*` exercise identities plus `ch01_prob_*` problem identities in those ranges. Product tests must obtain them through `SectionLearningRuntime.practice()` / the Practice endpoint, not by reading the structure file.

Figure fixture:

```text
figure_section_id = ch01_s05_01
```

Reason: canonical `chunks/chunk_002_structure.json` fixes Section 5.1 (`ch01_s05_01`) to PDF 35–38 and records Figure 1 at PDF 36 and Figure 2 at PDF 37, both within that Section range. Product tests must resolve the figure item through the Learn/Preview Runtime paths and verify metadata/source navigation only.

- [ ] **Step 1: Add failing isolation tests**

Parse `runtime/learning_slice_runtime.py` with `ast` and assert it imports no module under:

```text
runtime.shadow_fts
evaluation
book_core.concepts
runtime.concept_validation
runtime.qa_*
app.study
```

Also assert the source contains no model-provider construction and that `runtime/retrieval.py` / `runtime/shadow_fts.py` are not modified by the Phase 1H diff.

- [ ] **Step 2: Extend frozen Golden Runtime/API and real Chromium tests**

Add acceptance scenarios covering:

1. open `ch01_s01` in Preview;
2. verify `learning_slice_v1` through API and visible Preview blocks;
3. reveal one quick check and follow its Source link;
4. return and confirm mode/query/scroll/reveal state remains coherent;
5. switch to Review and choose `one_minute`, then `five_minute`, then `full`;
6. assert preset changes do not create additional StudyRecord identities for Review;
7. open `ch01_s08` Practice, assert an `exercise` filter exists, select it, and verify every visible source ref is an exercise candidate;
8. open `ch01_s09` Practice, assert a `problem` filter exists, select it, and verify every visible source ref is a problem candidate;
9. open `ch01_s05_01` Learn/Preview, verify at least one figure reference resolves, verify metadata/source navigation, and verify Phase 1H did not fabricate an `<img>`;
10. use `ch01_s05_04` in a real Runtime/API smoke assertion for theorem/formula-bearing presentation;
11. mark one mode complete, reload, and confirm `completed/100` persists;
12. verify existing scoped QA entry remains accessible and existing QA tests still pass;
13. set viewport to exactly `390x844` and assert `document.documentElement.scrollWidth <= window.innerWidth` on Preview, Review, Practice, and Learn pages visited.

Do not use elapsed-time assertions for the `1 分钟` / `5 分钟` labels; they are coverage presets, not timers.

- [ ] **Step 3: Confirm RED where new acceptance behavior is not yet wired**

Before final fixes, run the new focused isolation/browser test and record any genuine failure caused by missing Phase 1H behavior. Do not force a RED by corrupting the environment.

```bash
python -m unittest tests.test_learning_slice_isolation -v
cd app/web
npm run e2e -- functional-analysis.spec.ts study-record-persistence.spec.ts
```

- [ ] **Step 4: Make only acceptance-level fixes needed for GREEN**

Allowed fixes: accessible labels, scoped CSS overflow, missing stable selectors/roles, route-normalization defects, closure-validation defects revealed by real data. Do not broaden into unrelated redesign/refactor.

- [ ] **Step 5: Run focused acceptance to GREEN**

```bash
python -m unittest tests.test_learning_slice_isolation -v
cd app/web
npm run e2e -- functional-analysis.spec.ts study-record-persistence.spec.ts
```

- [ ] **Step 6: Commit isolation/browser acceptance**

```bash
git add tests/test_learning_slice_isolation.py app/web/e2e/functional-analysis.spec.ts app/web/e2e/study-record-persistence.spec.ts
git commit -m "test: gate Phase 1H learning slices end to end"
```

---

## Task 11: Exact-head regression, canonical-diff gate, and PR readiness

**Files:**
- No product file changes expected.
- Update PR #26 body/status only after all exact-head checks succeed.
- If a genuine regression requires code changes, return to the responsible task, write a failing regression test first, implement the minimal fix, commit, and restart this exact-head gate from the new HEAD.

**Consumes:** exact final implementation HEAD.

**Produces:** trustworthy final evidence for review; no merge.

- [ ] **Step 1: Record exact HEAD and compare scope**

```bash
git rev-parse HEAD
git status --short --branch
git diff --name-status 2675d2cecab63b28b6ab81a4554e9b7f010afd72...HEAD
```

Expected protected-area diff:

```text
books/functional-analysis/**   EMPTY
courses/**                     EMPTY
runtime/retrieval.py           EMPTY
runtime/shadow_fts.py          EMPTY
evaluation/**                  EMPTY
app/study/**                   EMPTY
schemas/concept-graph/**       EMPTY
```

If any protected-area diff appears unexpectedly, stop and classify it as `CONFLICT_NEEDS_REVIEW`; do not normalize it away.

- [ ] **Step 2: Run full Python Runtime/App gates on exact HEAD**

```bash
python -m py_compile runtime/*.py app/api/*.py app/study/*.py
python -m unittest discover -s tests -p "test_*.py" -v
python tools/check_runtime_readiness.py books/functional-analysis
python -m unittest discover -s app_tests -p "test_*.py" -v
```

- [ ] **Step 3: Run exact Search/QA/frozen-contract focused gates**

```bash
python -m unittest \
  tests.test_retrieval \
  tests.test_search_runtime \
  tests.test_qa_evidence \
  tests.test_qa_provider \
  tests.test_qa_runtime \
  app_tests.test_serialization_contracts \
  app_tests.test_qa_service \
  app_tests.test_qa_api \
  -v
```

Pass condition: Search/QA behavior remains Exact-only and existing frozen DTO tests are unchanged except the separately approved additive `ModeResponse.presentation` contract.

- [ ] **Step 4: Run exact StudyRecord gates**

```bash
python -m unittest \
  app_tests.test_study_repository \
  app_tests.test_study_service \
  app_tests.test_study_api \
  app_tests.test_study_connection_hygiene \
  app_tests.test_study_initialization_error \
  -v
```

Pass condition: no schema/identity migration, only `0/100`, completed remains durable/idempotent.

- [ ] **Step 5: Run complete web gates**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
npx playwright install --with-deps chromium
npm run e2e
```

- [ ] **Step 6: Run architecture fitness and H4a regression evidence without activating it**

From repository root:

```bash
python tools/check_architecture_fitness.py
python -m unittest tests.test_foundation_b_isolation tests.test_h4a_isolation tests.test_h4a_evaluation tests.test_shadow_fts -v
```

Do not tune H4a or change its frozen dataset/results as part of Phase 1H.

- [ ] **Step 7: Verify exact-head GitHub Actions**

Push the final non-default branch head and verify the relevant workflows complete against that exact commit. At minimum the existing `Book App UI tests` workflow must exercise Python Runtime/App, web tests/typecheck/build, and Chromium acceptance because its current path filters already include every planned Phase 1H implementation area.

If workflow fixes are necessary, add only the minimal path/command change, commit it, and restart all exact-head gates from Step 1.

- [ ] **Step 8: Update PR #26 for review, but do not merge**

Update the PR body with:

- final exact HEAD;
- design/spec path;
- implementation-plan path;
- completed slice summary A–E;
- exact test commands and outcomes;
- canonical diff = empty statement backed by compare output;
- Search/QA = Exact-only unchanged;
- StudyRecord = schema/semantics unchanged;
- H3b/B4b/B5/multi-book/StudyRecord migration = not entered.

Once checks are green, mark Draft PR #26 ready for review if the tooling supports it. This is review readiness only, not merge authorization.

- [ ] **Step 9: Stop at the explicit merge gate**

Report the exact PR #26 head and checks to the user. Do not merge. Only an explicit instruction naming PR #26 (for example `合并 PR #26`) may authorize the later merge step, subject to a fresh exact-head/security verification.

---

## Implementation Completion Definition

Implementation is ready for PR review only when all conditions below hold simultaneously on the exact same final HEAD:

- `LearningSliceRuntime` is deterministic and isolated.
- `ModeResponse.presentation` is the only additive Section mode top-level field.
- Preview has source-derived objectives, honest unavailable prerequisites, core definitions/formulas/figure refs, statistics, and deterministic quick checks.
- Review has exact `one_minute`, `five_minute`, `full` recall presets with think → reveal of canonical content.
- Practice has exact available subtype filters and `solution_status="unavailable"` with no answer fabrication/store.
- Learn has mutually exclusive type-aware groups with metadata-only figures and honest unavailable extensions.
- All presentation references are closed over the corresponding current mode items and canonical resolver.
- Source round trips preserve route/scroll/reveal using the existing Section session-state shape.
- `review_preset` and `practice_kind` live only in URL query state.
- StudyRecord remains mode-level `in_progress/0` or `completed/100`; preset/filter/reveal actions create no new durable progress semantics.
- Search/Source/QA frozen contracts pass unchanged; Search/QA remains Exact-only.
- H3b/B4b/B5/StudyRecord migration/multi-book/Lecture/AI learning authority are absent from the diff.
- `books/functional-analysis/**` and `courses/**` have no Phase 1H changes.
- Python Runtime/App, web unit/type/build, Chromium, architecture fitness, Golden readiness, H4a isolation, and GitHub Actions are green on the exact final HEAD.
- PR #26 is reviewable with no unresolved correctness blocker and remains unmerged until explicit user authorization.

---

## Execution Handoff

The implementation plan itself is now the approved execution authority for the next ordinary development step. The next action is **Task 1, Step 1**: create the failing `tests/test_learning_slice_runtime.py` contract tests on this same non-default branch, confirm a real RED, and record the RED checkpoint before implementation. No additional architecture choice is required before beginning Task 1.
