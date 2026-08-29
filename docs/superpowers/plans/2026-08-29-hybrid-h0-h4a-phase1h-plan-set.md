# Hybrid H0–H4a → Phase 1H Plan Set

> **For implementers:** Execute this plan set in order. Use Superpowers TDD for implementation. Each stage is independently reviewable and rollbackable. Do not collapse stages into one giant PR.

**Goal:** Implement the approved hybrid route `H0 → H1 → H2 → H3a → H4a → Phase 1H` without changing canonical textbook facts, without activating public FTS/multi-book behavior, and without migrating StudyRecord.

**Design source:** `docs/superpowers/specs/2026-08-29-hybrid-h0-h4a-phase1h-design.md`

**Base design branch:** `design/hybrid-h0-h4a-phase1h`

## Hard stops

These are not part of this plan set and must not be implemented without a new approved design:

- H3b production Concept authority/lifecycle
- B4b FTS/fusion/ranking activation
- B5 public multi-book API/DTO/browser/session migration
- StudyRecord book-version migration

## Execution order

1. `docs/superpowers/plans/2026-08-29-h0-neutral-book-identity.md`
2. `docs/superpowers/plans/2026-08-29-h1-internal-source-provenance.md`
3. `docs/superpowers/plans/2026-08-29-h2-exact-retrieval-seam.md`
4. `docs/superpowers/plans/2026-08-29-h3a-concept-contract.md`
5. `docs/superpowers/plans/2026-08-29-h4a-shadow-fts-evaluation.md`
6. `docs/superpowers/plans/2026-08-29-phase1h-learning-slices.md`

Each stage should normally use its own non-default implementation branch and PR. Phase 1H should be further split into independently reviewable S1–S6 PRs when practical.

## Cross-stage invariants

Before and after every stage, verify:

```text
Golden Course chapters     = 8
Golden Course sections     = 132
Golden search records      = 1493
Golden PDF pages           = 442
Golden final printed page  = 423
```

Through H4a, additionally verify:

- legacy `course.json` role semantics remain unchanged;
- Search/Source/QA HTTP field sets remain unchanged;
- provider request evidence field sets remain unchanged;
- public Search remains Exact-only;
- QA still re-resolves candidates with `SourceResolver`, gates evidence, and independently verifies citations;
- browser session-state contracts remain unchanged;
- StudyRecord schema/storage remain unchanged;
- no canonical `books/**` mutation is committed.

## Stage review protocol

For every PR:

1. Record the exact PR HEAD SHA.
2. Run the targeted RED→GREEN tests named in that stage plan.
3. Run the stage's relevant regressions against that exact HEAD.
4. Verify the diff contains only the intended stage scope.
5. Do not claim `course-package-heavy` ran unless it was manually dispatched and actually completed.
6. Do not auto-merge. Merge requires explicit human authorization for the specific PR.

## Completion

The plan set is complete only when H0–H4a and Phase 1H S1–S6 are independently verified and merged through normal governance. The stable product at that point is still single-primary-book and Exact-only, with no production Concept graph and no StudyRecord version migration.
