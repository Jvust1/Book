# Phase 1H Learning Slices Implementation Plan

> **For implementers:** Use Superpowers TDD. H0–H4a must be available first. Execute S1–S6 as separate reviewable slices/PRs when practical. Do not couple these UI slices to H3b, B4b, B5, or StudyRecord schema changes.

**Goal:** Turn the existing canonical Section learning payload into a materially better study experience: formula recall, practice filtering, deterministic flashcards, organized learning objects, review-duration presets, and clearer figure/source metadata.

**Architecture:** Prefer derived client-side study views over new server contracts because the current `ModeResponse` already carries the canonical fields needed by S1–S6. Add pure TypeScript selectors under `app/web/src/learning/` and small UI components. Preserve the existing four modes and StudyRecord identity (`preview|learn|review|practice`). No new textbook facts are generated.

**Tech stack:** React 18, TypeScript, Vite, Vitest/Testing Library, Playwright; existing Python API remains unchanged unless a slice proves the current payload is insufficient.

---

## Task 1: Freeze the Phase 1H input contract before UI changes

**Files:**
- Create: `app/web/src/learning/studyViews.test.ts`
- Create later: `app/web/src/learning/studyViews.ts`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Reference: `app/web/src/api/types.ts`

**Step 1: Characterize the current `ModeItem` inputs**

The pure selector tests should use fixtures containing exactly the existing fields:

```ts
const item = {
  kind: 'object',
  source_id: 'thm_1',
  object_type: 'theorem',
  type_zh: '定理',
  number: '1.3',
  title_zh: 'Hölder 不等式',
  title_en: 'Holder inequality',
  formula: '1/p + 1/q = 1',
  printed_page: 3,
  pdf_page: 22,
  content_zh: '教材中的中文学习内容',
  translation_available: true,
} satisfies ModeItem
```

Add a SectionPage regression asserting the four top-level tabs remain exactly:

```text
预习 / 学习 / 复习 / 刷题
```

and StudyRecord calls continue to use only those four modes.

**Step 2: Run characterization**

```bash
cd app/web
npm test -- --run src/pages/SectionPage.test.tsx
npm run typecheck
```

Expected: PASS.

**Step 3: Commit characterization**

```bash
git add app/web/src/pages/SectionPage.test.tsx
git commit -m "test: freeze phase 1h learning input contract"
```

---

# S1 — Formula Preview + Recall

## Task 2: Add deterministic formula selectors with RED tests

**Files:**
- Create: `app/web/src/learning/studyViews.ts`
- Create/Modify: `app/web/src/learning/studyViews.test.ts`

**Step 1: Write RED tests**

Define:

```ts
export const formulaItems = (items: readonly ModeItem[]): ModeItem[] => ...
```

Contract:

- include only items with a non-blank `formula`;
- preserve incoming canonical item order;
- do not alter formula text;
- do not synthesize formulas from content/title;
- return a new array without mutating input.

Test blank/null formulas are excluded and the original formula string is byte-for-byte preserved.

**Step 2: Verify RED**

```bash
cd app/web
npm test -- --run src/learning/studyViews.test.ts
```

Expected: FAIL because selector does not exist.

**Step 3: Implement minimally**

```ts
export const formulaItems = (items: readonly ModeItem[]): ModeItem[] =>
  items.filter((item) => typeof item.formula === 'string' && item.formula.trim().length > 0)
```

Do not normalize or rewrite the formula.

**Step 4: Run GREEN**

```bash
npm test -- --run src/learning/studyViews.test.ts
```

Expected: PASS.

**Step 5: Commit**

```bash
git add app/web/src/learning/studyViews.ts app/web/src/learning/studyViews.test.ts
git commit -m "feat: derive canonical formula study items"
```

## Task 3: Show formula summary in Preview and hide formula during Review recall

**Files:**
- Create: `app/web/src/components/FormulaSummary.tsx`
- Create: `app/web/src/components/FormulaSummary.test.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/components/LearningObjectCard.tsx`
- Create/Modify: `app/web/src/components/LearningObjectCard.test.tsx`
- Modify: `app/web/src/styles.css`

**Step 1: Write RED UI tests**

Preview test:

```text
formula items are listed in a dedicated “本节公式” summary
formula text equals the canonical ModeItem.formula exactly
no formula summary is rendered when there are no formulas
```

Review card test:

```text
when mode=review and collapsed, formula is not visible
click “显示内容” -> formula and content become visible
learn/practice behavior remains unchanged
```

This fixes the current behavior where `LearningObjectCard` renders formula before review reveal.

**Step 2: Verify RED**

```bash
cd app/web
npm test -- --run src/components/FormulaSummary.test.tsx src/components/LearningObjectCard.test.tsx src/pages/SectionPage.test.tsx
```

Expected: new tests fail.

**Step 3: Implement Preview summary**

`FormulaSummary` receives `ModeItem[]` and renders source labels + exact formula text. Use `formulaItems(payload.items)` in `SectionPage` only when `mode === 'preview'`.

**Step 4: Implement formula recall hiding**

In `LearningObjectCard`, move formula rendering behind the same review reveal rule:

```ts
const showFormula = mode !== 'review' || reviewExpanded
```

Render formula only when `showFormula && item.formula`.

**Step 5: Run S1 tests**

```bash
npm test -- --run src/learning/studyViews.test.ts src/components/FormulaSummary.test.tsx src/components/LearningObjectCard.test.tsx src/pages/SectionPage.test.tsx
npm run typecheck
```

Expected: PASS.

**Step 6: Commit S1 UI**

```bash
git add app/web/src/components app/web/src/pages/SectionPage.tsx app/web/src/pages/SectionPage.test.tsx app/web/src/styles.css
git commit -m "feat: add formula preview and recall"
```

**S1 PR gate:** run full `npm test`, `npm run typecheck`, `npm run build`, plus relevant Python App tests to prove API unchanged.

---

# S2 — Deterministic Practice Filters

## Task 4: Add pure practice-filter policy with RED tests

**Files:**
- Modify: `app/web/src/learning/studyViews.ts`
- Modify: `app/web/src/learning/studyViews.test.ts`

**Step 1: Define the only initial filters**

Use:

```ts
export type PracticeFilter = 'all' | 'exercise' | 'problem'

export const filterPracticeItems = (
  items: readonly ModeItem[],
  filter: PracticeFilter,
): ModeItem[] => ...
```

Tests:

- `all` preserves all payload order;
- `exercise` keeps only `object_type === 'exercise'`;
- `problem` keeps only `object_type === 'problem'`;
- comparison is case-normalized only for type matching;
- selector does not infer difficulty or reorder items.

**Step 2: Verify RED and implement**

```bash
cd app/web
npm test -- --run src/learning/studyViews.test.ts
```

Expected first run: FAIL; after minimal implementation: PASS.

**Step 3: Commit selector**

```bash
git add app/web/src/learning/studyViews.ts app/web/src/learning/studyViews.test.ts
git commit -m "feat: add deterministic practice filters"
```

## Task 5: Add Practice filter controls without changing the API

**Files:**
- Create: `app/web/src/components/PracticeFilters.tsx`
- Create: `app/web/src/components/PracticeFilters.test.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/styles.css`

**Step 1: Write RED tests**

In practice mode with one exercise and one problem:

```text
“All / 练习 / 习题” controls are visible
All shows both in canonical order
练习 shows exercise only
习题 shows problem only
switching filter does not call bookApi.getMode again
StudyRecord remains mode='practice'
```

**Step 2: Implement local filter state**

Reset filter to `all` when `courseId`, `sectionId`, or top-level mode changes. Derive displayed items from already fetched `payload.items`.

Do not add query parameters or server filtering in S2.

**Step 3: Run tests**

```bash
npm test -- --run src/components/PracticeFilters.test.tsx src/pages/SectionPage.test.tsx src/learning/studyViews.test.ts
npm run typecheck
```

Expected: PASS.

**Step 4: Commit S2 UI**

```bash
git add app/web/src/components/PracticeFilters* app/web/src/pages/SectionPage* app/web/src/styles.css
git commit -m "feat: filter section practice items"
```

---

# S3 — Deterministic Flashcards

## Task 6: Define fixed flashcard templates with RED tests

**Files:**
- Modify: `app/web/src/learning/studyViews.ts`
- Modify: `app/web/src/learning/studyViews.test.ts`

**Step 1: Define flashcard type and deterministic generator**

```ts
export interface Flashcard {
  id: string
  source_kind: string
  source_id: string
  prompt: string
  answer: string
}

export const buildFlashcards = (items: readonly ModeItem[]): Flashcard[] => ...
```

Template policy:

1. If an item has `formula`, create one formula card:
   - prompt: `回忆${label}的公式`
   - answer: exact `item.formula`
2. If an item has non-blank `content_zh`, create one content card:
   - prompt: `回忆${label}的教材内容`
   - answer: exact `item.content_zh`
3. `label` is deterministic: `title_zh || number || type_zh || source_id`.
4. ID is deterministic: `${kind}:${source_id}:formula` or `${kind}:${source_id}:content`.
5. Do not generate cards with invented answers or LLM calls.
6. Preserve item order; formula card precedes content card for the same item.

**Step 2: Verify RED**

```bash
cd app/web
npm test -- --run src/learning/studyViews.test.ts
```

Expected: FAIL.

**Step 3: Implement minimally and run GREEN**

```bash
npm test -- --run src/learning/studyViews.test.ts
```

Expected after implementation: PASS.

**Step 4: Commit**

```bash
git add app/web/src/learning/studyViews.ts app/web/src/learning/studyViews.test.ts
git commit -m "feat: derive deterministic textbook flashcards"
```

## Task 7: Add a local flashcard deck to Review mode

**Files:**
- Create: `app/web/src/components/FlashcardDeck.tsx`
- Create: `app/web/src/components/FlashcardDeck.test.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/styles.css`

**Step 1: Write RED interaction tests**

Require:

```text
Review mode offers a “卡片复习” section when cards exist
front prompt visible initially
answer hidden initially
explicit “显示答案” reveals canonical answer
next/previous navigation is local and deterministic
no provider/API call occurs when cards are generated or flipped
no cards -> no flashcard deck
```

Do not store flashcard state in StudyRecord or session storage in S3.

**Step 2: Implement**

Use `buildFlashcards(payload.items)` in Review mode. Keep the existing normal review list below or alongside the deck; flashcards are an additive derived view, not a replacement for canonical source links.

**Step 3: Run tests**

```bash
npm test -- --run src/components/FlashcardDeck.test.tsx src/pages/SectionPage.test.tsx src/learning/studyViews.test.ts
npm run typecheck
```

Expected: PASS.

**Step 4: Commit S3 UI**

```bash
git add app/web/src/components/FlashcardDeck* app/web/src/pages/SectionPage* app/web/src/styles.css
git commit -m "feat: add deterministic review flashcards"
```

---

# S4 — Example/Object Learning Organization

## Task 8: Add stable object grouping policy with RED tests

**Files:**
- Modify: `app/web/src/learning/studyViews.ts`
- Modify: `app/web/src/learning/studyViews.test.ts`

**Step 1: Define group order**

Use a fixed display grouping without changing payload order inside each group:

```ts
export const LEARNING_GROUP_ORDER = [
  'definition',
  'theorem',
  'proposition',
  'lemma',
  'corollary',
  'formula',
  'example',
  'exercise',
  'problem',
  'figure',
  'translation',
  'other',
] as const
```

`groupLearningItems(items)` maps each item into a group; unknown/null types become `other`. Figures use `kind === 'figure'`; translations use `kind === 'translation'`.

Tests prove stable group order and stable original order within groups.

**Step 2: Verify RED, implement, run GREEN**

```bash
cd app/web
npm test -- --run src/learning/studyViews.test.ts
```

Expected: RED before implementation, PASS after.

**Step 3: Commit**

```bash
git add app/web/src/learning/studyViews.ts app/web/src/learning/studyViews.test.ts
git commit -m "feat: group canonical learning objects"
```

## Task 9: Render grouped Learn sections without changing source cards

**Files:**
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/styles.css`

**Step 1: Write RED UI tests**

In Learn mode, a mixed payload should render headings in deterministic order, e.g.:

```text
定义
定理
例题
练习
图
```

Within each heading, `LearningObjectCard` source links/content remain unchanged. Preview/review/practice rendering remains unchanged.

**Step 2: Implement grouped Learn rendering**

Only when `mode === 'learn'`, render `groupLearningItems(payload.items)` as labeled sections. Continue to use the existing `LearningObjectCard` for every item; do not duplicate source rendering logic.

**Step 3: Run tests**

```bash
npm test -- --run src/pages/SectionPage.test.tsx src/learning/studyViews.test.ts
npm run typecheck
```

Expected: PASS.

**Step 4: Commit S4 UI**

```bash
git add app/web/src/pages/SectionPage* app/web/src/styles.css
git commit -m "feat: organize learn mode by textbook object type"
```

---

# S5 — Review-duration Presets

## Task 10: Define deterministic review selection policy with RED tests

**Files:**
- Modify: `app/web/src/learning/studyViews.ts`
- Modify: `app/web/src/learning/studyViews.test.ts`

**Step 1: Freeze preset policy**

Use:

```ts
export type ReviewPreset = '1m' | '5m' | 'full'

export const selectReviewItems = (
  items: readonly ModeItem[],
  preset: ReviewPreset,
): ModeItem[] => ...
```

Policy:

```text
1m   -> first 3 review items in canonical payload order
5m   -> first 8 review items in canonical payload order
full -> all review items in canonical payload order
```

This is intentionally simple and auditable because no importance metadata exists yet. Formula summary remains separately available from S1; do not invent an importance score.

Tests prove the function is deterministic, preserves order, handles fewer-than-limit inputs, and does not mutate source arrays.

**Step 2: Verify RED, implement, run GREEN**

```bash
cd app/web
npm test -- --run src/learning/studyViews.test.ts
```

Expected: RED then PASS.

**Step 3: Commit**

```bash
git add app/web/src/learning/studyViews.ts app/web/src/learning/studyViews.test.ts
git commit -m "feat: add deterministic review duration presets"
```

## Task 11: Add Review preset controls without changing StudyRecord identity

**Files:**
- Create: `app/web/src/components/ReviewPresetControls.tsx`
- Create: `app/web/src/components/ReviewPresetControls.test.tsx`
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`
- Modify: `app/web/src/styles.css`

**Step 1: Write RED interaction tests**

Review mode must show:

```text
1 分钟 / 5 分钟 / 完整复习
```

Tests:

- default preset is `full` to preserve current behavior;
- choosing `1m` renders at most 3 canonical review items;
- choosing `5m` renders at most 8;
- choosing `full` restores all;
- preset switch does not refetch `bookApi.getMode`;
- `touchStudy`/`completeStudy` still use mode `'review'`, not a new StudyRecord mode;
- changing course/section/mode resets preset to `full`.

**Step 2: Implement local state**

Do not persist preset in StudyRecord. Do not add a fifth learning mode. Use `selectReviewItems(payload.items, preset)` before rendering the review list and building S3 flashcards so both views see the same selected scope.

**Step 3: Run tests**

```bash
npm test -- --run src/components/ReviewPresetControls.test.tsx src/pages/SectionPage.test.tsx src/learning/studyViews.test.ts
npm run typecheck
```

Expected: PASS.

**Step 4: Commit S5 UI**

```bash
git add app/web/src/components/ReviewPresetControls* app/web/src/pages/SectionPage* app/web/src/styles.css
git commit -m "feat: add review duration presets"
```

---

# S6 — Figure / Source Metadata Enhancement

## Task 12: Add deterministic source metadata display to cards

**Files:**
- Create: `app/web/src/components/SourceMetadata.tsx`
- Create: `app/web/src/components/SourceMetadata.test.tsx`
- Modify: `app/web/src/components/LearningObjectCard.tsx`
- Modify: `app/web/src/components/LearningObjectCard.test.tsx`
- Modify: `app/web/src/styles.css`

**Step 1: Write RED tests**

Given current `ModeItem` fields, display only existing metadata:

```text
教材页 <printed_page> when present
PDF <pdf_page> when present
“图” label for figure items
existing number/type/title labels
existing “查看教材来源” link
```

Tests prove:

- no fake page is displayed when page metadata is null;
- figure title/page are shown from the existing payload;
- metadata rendering does not create new source IDs/anchors;
- SourceLink target remains unchanged.

**Step 2: Implement `SourceMetadata`**

Keep it presentation-only; do not fetch Source API just to render the card. `LearningObjectCard` passes `printed_page`/`pdf_page`/kind.

**Step 3: Run tests**

```bash
cd app/web
npm test -- --run src/components/SourceMetadata.test.tsx src/components/LearningObjectCard.test.tsx
npm run typecheck
```

Expected: PASS.

**Step 4: Commit**

```bash
git add app/web/src/components/SourceMetadata* app/web/src/components/LearningObjectCard* app/web/src/styles.css
git commit -m "feat: show textbook source metadata on learning cards"
```

## Task 13: Improve figure visibility in Preview/Learn without reading images with AI

**Files:**
- Modify: `app/web/src/pages/SectionPage.tsx`
- Modify: `app/web/src/pages/SectionPage.test.tsx`

**Step 1: Write RED figure tests**

With a figure ModeItem, assert:

```text
Preview count includes 图
Learn grouping contains 图 section
figure title/page metadata is visible
source link works
no generated image description or OCR text appears
```

**Step 2: Implement using existing group/card behavior**

No new backend fields or AI calls. Figure remains a canonical source entry with existing title/page metadata and SourceLink.

**Step 3: Run tests**

```bash
npm test -- --run src/pages/SectionPage.test.tsx src/components/LearningObjectCard.test.tsx
npm run typecheck
```

Expected: PASS.

**Step 4: Commit S6 UI**

```bash
git add app/web/src/pages/SectionPage* app/web/src/components/LearningObjectCard* 
git commit -m "feat: surface figure metadata in section learning"
```

---

## Task 14: Add end-to-end acceptance for S1–S6

**Files:**
- Modify: `app/web/e2e/functional-analysis.spec.ts`

**Step 1: Add browser assertions against real local deterministic stack**

Use existing Functional Analysis course and avoid assuming a specific object unless the current canonical fixture guarantees it. Cover:

```text
Preview -> formula summary appears when section has formulas
Review -> formula/content hidden until explicit reveal
Practice -> filter controls switch locally
Review -> deterministic flashcard can reveal answer
Learn -> object groups render
Review -> 1m/5m/full controls change visible count without new mode API call
Figure/source metadata remains navigable when figure exists
```

When a section lacks a given data type, choose an existing stable section discovered from the canonical fixture rather than mutating `books/**`.

**Step 2: Run real browser acceptance locally**

Start API with deterministic QA/StudyRecord storage using the same environment as CI, start Vite, then:

```bash
cd app/web
npm run e2e
```

Expected: PASS.

**Step 3: Commit**

```bash
git add app/web/e2e/functional-analysis.spec.ts
git commit -m "test: cover phase 1h learning slices end to end"
```

---

## Task 15: Phase 1H full regression and scope audit

**Files:**
- No new product changes expected.

**Step 1: Run web unit/type/build**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
```

Expected: PASS.

**Step 2: Run relevant Python regressions to prove API/StudyRecord unchanged**

From repository root:

```bash
python -m unittest \
  tests.test_section_learning_runtime \
  tests.test_source_resolver \
  app_tests.test_app_service \
  app_tests.test_api \
  app_tests.test_study_repository \
  app_tests.test_study_service \
  app_tests.test_study_api -v
```

Expected: PASS.

Then:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s app_tests -p "test_*.py" -v
```

Expected: PASS.

**Step 3: Verify no backend contract expansion was accidentally introduced**

```bash
git diff --name-only <PHASE1H_BASE_SHA>...HEAD
```

Expected for the client-derived approach:

```text
primarily app/web/** changes
no books/**
no courses/**
no app/study schema/storage changes
no H3b Concept dataset
no public FTS ranking changes
no multi-book DTO/session migration
```

If implementation discovers a real need to change `ModeResponse` or Python API fields, stop that slice and return to a bounded/architectural design review rather than silently expanding the approved client-derived contract.

**Step 4: Verify Golden baseline still passes**

```bash
python -m unittest tests.test_course_runtime tests.test_search_runtime tests.test_golden_course_package -v
```

Expected: 8 chapters / 132 sections / 1493 search records / 442 PDF pages / final printed page 423 remain unchanged.

**Step 5: Record exact HEAD for each S1–S6 PR**

```bash
git rev-parse HEAD
```

Each slice should carry its own exact-HEAD evidence and explicit merge authorization. Do not bundle H3b/B4b/B5/StudyRecord migration into a Phase 1H cleanup PR.
