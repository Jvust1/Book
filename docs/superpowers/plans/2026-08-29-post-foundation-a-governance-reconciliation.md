# Post-Foundation-A Governance Reconciliation Plan

> **For implementers:** This is a documentation/governance reconciliation only. It may run before H0 implementation after the written hybrid spec is approved. Do not rewrite historical decisions or mark unimplemented work complete.

**Goal:** Bring current-state narrative documents into agreement with authoritative `governance/project_state.json`, the completed Foundation A merge, and the newly approved hybrid dependency exception.

**Architecture:** Make the smallest factual wording changes in current-state sections. Preserve historical roadmap ordering as historical context, then explicitly record the 2026-08-29 approved exception `H0 → H1 → H2 → H3a → H4a → Phase 1H`. Do not modify product code or canonical data.

**Tech stack:** Markdown/JSON governance documents only; Git diff/read-back review.

---

## Task 1: Reconcile authoritative state before editing narratives

**Files:**
- Read: `governance/project_state.json`
- Read: `governance/pending_sync.json`
- Read: `docs/HANDOFF.md`
- Read: `docs/CURRENT_STATE.md`
- Read: `docs/ROADMAP.md`
- Read: `docs/DEVELOPMENT_STRATEGY.md`
- Read: `docs/superpowers/specs/2026-08-29-hybrid-h0-h4a-phase1h-design.md`

**Step 1: Record authoritative facts from `project_state.json`**

The reconciliation must use the current file at execution time. Expected facts based on the approved design checkpoint include:

```text
phase = POST_FOUNDATION_A_TRANSITION
status = READY_FOR_NEXT_PHASE_DESIGN
Foundation A = COMPLETE_MERGED
Foundation A merged PR = 13
Foundation A merge commit = 82f0cbbcfe5078d304ca7c163b81d4eb01b515f4
Foundation A Tasks 1–10 = COMPLETE
next_task = null
canonical_book_mutation_allowed = false
runtime_consumer_migration_in_scope = false
```

If current authority differs at execution time, stop and reconcile the new authoritative state rather than forcing the old values.

**Step 2: Confirm pending narrative sync scope**

Verify `governance/pending_sync.json` still identifies only the known Foundation A post-merge narrative wording in:

```text
docs/CURRENT_STATE.md
docs/ROADMAP.md
docs/DEVELOPMENT_STRATEGY.md
```

If the pending item was already resolved by another merged change, do not duplicate it.

**Step 3: No commit yet**

This task is read-only reconciliation.

---

## Task 2: Update `docs/CURRENT_STATE.md` to post-merge truth

**Files:**
- Modify: `docs/CURRENT_STATE.md`

**Step 1: Replace only stale current-status statements**

The opening/current-engineering section must no longer say Foundation A is still on `foundation/course-package-contract-a`, Tasks 1–9, or Task 10 PR readiness.

Update it to state factually:

```text
Foundation A: COMPLETE_MERGED
merged PR: #13
merge commit: 82f0cbbcfe5078d304ca7c163b81d4eb01b515f4
Tasks 1–10: COMPLETE
current phase: POST_FOUNDATION_A_TRANSITION
current status: READY_FOR_NEXT_PHASE_DESIGN
```

Do not delete the historical Task 8/9 evidence section. Retitle or annotate it as historical pre-merge evidence if needed so it is not mistaken for current state.

**Step 2: Add the approved next-route statement**

Add a concise current next-route section:

```text
Approved dependency exception (2026-08-29):
H0 neutral Book identity
→ H1 internal source provenance
→ H2 Exact-only shared Retrieval seam
→ H3a Concept/ConceptAlignment contract + reference validation
→ H4a shadow FTS5/BM25 evaluation
→ Phase 1H user-visible slices
```

Explicitly state:

```text
H3b, B4b, B5 and StudyRecord book-version migration remain separately gated.
```

Do not claim any of H0–H4a or Phase 1H are implemented merely because the design/plan exists.

**Step 3: Diff review**

```bash
git diff -- docs/CURRENT_STATE.md
```

Expected: current-state wording only; no historical evidence deletion.

**Step 4: Commit**

```bash
git add docs/CURRENT_STATE.md
git commit -m "docs: reconcile current state after foundation a merge"
```

---

## Task 3: Update `docs/ROADMAP.md` without rewriting history

**Files:**
- Modify: `docs/ROADMAP.md`

**Step 1: Correct Foundation A status**

Replace the top status/current Foundation A section wording that says Tasks 1–9 / Task 10 / not merged with post-merge truth.

Do not change historical checkboxes unrelated to what Foundation A actually completed.

**Step 2: Insert an explicit dependency-exception note before Phase 1H/Foundation B execution sections**

Use wording equivalent to:

```text
### Approved dependency exception — 2026-08-29

The historical roadmap order below is preserved. For the next implementation cycle,
the approved dependency order is:

H0 → H1 → H2 → H3a → H4a → Phase 1H

This is a deliberate dependency exception, not a retroactive rewrite of the roadmap.
H3b, B4b, B5 and StudyRecord book-version migration remain separately approved future decisions.
```

Keep the original Phase 1H and Foundation B sections so future readers can distinguish the long-term roadmap from the approved near-term execution order.

**Step 3: Do not mark future work complete**

Do not mark Concept Graph, FTS activation, multi-book Runtime/UI, or Phase 1H feature checkboxes complete unless they are actually implemented and verified later.

**Step 4: Diff review**

```bash
git diff -- docs/ROADMAP.md
```

Expected: status correction + explicit exception note only.

**Step 5: Commit**

```bash
git add docs/ROADMAP.md
git commit -m "docs: record approved hybrid roadmap exception"
```

---

## Task 4: Update `docs/DEVELOPMENT_STRATEGY.md` current framing only

**Files:**
- Modify: `docs/DEVELOPMENT_STRATEGY.md`

**Step 1: Remove stale Phase 1G/current-stage framing**

The opening currently describes Phase 1G as current work. Replace that current-stage sentence with post-Foundation-A framing:

```text
Phase 1G and Foundation A are complete and merged.
The approved next dependency sequence is H0 → H1 → H2 → H3a → H4a → Phase 1H.
```

Preserve the document's long-term strategy sections, including Concept Graph, Course Package, LectureEvent, and contract-first guidance.

**Step 2: Clarify Concept/Unified Retrieval staging**

Where necessary, add a short note that the approved next cycle intentionally separates:

```text
H3a = contract/reference validation only
H3b = real production Concept authority, later approval
H4a = shadow retrieval evidence only
B4b = public ranking activation, later approval
```

Do not rewrite long-term strategy as if H3b/B4b already exist.

**Step 3: Diff review**

```bash
git diff -- docs/DEVELOPMENT_STRATEGY.md
```

Expected: small current-framing update; no wholesale strategy rewrite.

**Step 4: Commit**

```bash
git add docs/DEVELOPMENT_STRATEGY.md
git commit -m "docs: refresh development strategy current phase"
```

---

## Task 5: Resolve the pending-sync marker only if its existing schema supports additive resolution

**Files:**
- Modify only if the current record design requires it: `governance/pending_sync.json`

**Step 1: Inspect the current pending-sync schema**

If the file has an established non-destructive mechanism to mark a pending item resolved while preserving its history, use that mechanism after Tasks 2–4 are complete.

If resolving the item would require deleting historical entries, overwriting provenance, or inventing a new governance schema, do not modify it in this task. Leave it pending and record the narrative reconciliation in the PR instead.

**Step 2: Validate JSON if changed**

```bash
python -m json.tool governance/pending_sync.json >/dev/null
```

Expected: PASS.

**Step 3: Commit only if a safe additive resolution was actually required**

```bash
git add governance/pending_sync.json
git commit -m "docs: mark foundation a narrative sync resolved"
```

Do not create an empty commit when the file is intentionally unchanged.

---

## Task 6: Final governance-only verification

**Files:**
- No additional changes expected.

**Step 1: Verify diff scope**

Resolve the implementation branch base dynamically:

```bash
git fetch origin main
git merge-base origin/main HEAD
BASE_SHA=$(git merge-base origin/main HEAD)
git diff --name-only "$BASE_SHA"...HEAD
```

Expected changed files are limited to:

```text
docs/CURRENT_STATE.md
docs/ROADMAP.md
docs/DEVELOPMENT_STRATEGY.md
```

plus `governance/pending_sync.json` only if Task 5 used its existing safe additive resolution mechanism.

**Step 2: Scan for contradictory stale current-state phrases**

```bash
grep -nE 'Tasks 1.?9|Task 10.*current|尚未合并到 `main`|当前开发分支.*foundation/course-package-contract-a' \
  docs/CURRENT_STATE.md docs/ROADMAP.md docs/DEVELOPMENT_STRATEGY.md || true
```

Expected: no stale phrase remains in a section that claims to describe current state. Historical evidence may retain old Task labels when clearly marked historical.

**Step 3: Verify no product/canonical changes**

```bash
git diff --name-only "$BASE_SHA"...HEAD | grep -E '^(app|runtime|course_package|book_core|books|courses|library|schemas|tools|tests)/' && exit 1 || true
```

Expected: no output.

**Step 4: Record exact HEAD and prepare documentation PR**

```bash
git rev-parse HEAD
```

This PR is documentation/governance only and still requires normal review and explicit merge authorization. It must not be used to merge implementation work.
