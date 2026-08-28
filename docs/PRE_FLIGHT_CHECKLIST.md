# Book Pre-Flight Checklist

Updated: 2026-08-28

Run this before material development, synchronization, route changes, or release/merge actions.

## 1. Global startup

- [ ] Confirm target repository and target branch.
- [ ] Read Drive root `全项目`.
- [ ] Dynamically scan and fully read every root `全项目_` baseline.
- [ ] If any required baseline is unavailable, truncated, conflicting, or appears weakened: stop and report `READ_ONLY_LOCKED`.

## 2. Repository governance

- [ ] Read `AGENTS.md`.
- [ ] Read target-branch `SECURITY_POLICY.md`.
- [ ] Read `governance/project_state.json`.
- [ ] Read `docs/PROJECT_NORTH_STAR.md`.
- [ ] Read `docs/ARCHITECTURE_INVARIANTS.md`.
- [ ] Read `docs/CURRENT_STATE.md`.
- [ ] Read `docs/DECISION_LEDGER.md` and `docs/EVALUATION_LEDGER.md`.
- [ ] Read `governance/artifact_manifest.json`.
- [ ] Read `governance/pending_sync.json`.
- [ ] Read the active Spec/Plan.

## 3. Safety and branch

- [ ] First write of a new task has freshly read both the Drive global safety baseline and target-branch `SECURITY_POLICY.md`.
- [ ] Target is not the protected default branch for ordinary development.
- [ ] Current branch/ref has not moved unexpectedly since preflight.
- [ ] Planned operation is not `DESTRUCTIVE_LOCKED`.
- [ ] Scope is minimal and recoverable.
- [ ] No frozen/history/provenance object will be overwritten.

## 4. Artifact/sync state

- [ ] Classify candidates as `NEW / CHANGED / SKIP_IDENTICAL / HISTORICAL_DUPLICATE_PRESERVED / CONFLICT_NEEDS_REVIEW` before sync writes.
- [ ] No blocking `pending_sync` item affects the current operation.
- [ ] Drive writes use stable file/folder identities and hashes when available.
- [ ] Identical artifacts are reused rather than reuploaded.
- [ ] Source snapshots use exact immutable upstream commits/tags.
- [ ] If a trusted self-hosted runner is already configured and usable for the project, evaluate it first for large archive/snapshot work.

## 5. Foundation A special gates

- [ ] `books/functional-analysis/**` is treated as canonical read-only input.
- [ ] Existing Phase 1A–1G Runtime/API/App behavior remains in scope for regression.
- [ ] Course Package output is under `.build/course-packages/...`, never canonical book folders.
- [ ] Deterministic identity excludes timestamps, randomness, temp paths, and absolute machine paths.
- [ ] Package paths remain inside repository/package boundaries.
- [ ] Exactly one enabled `primary` book.
- [ ] Validation is independent and read-only.
- [ ] TDD RED is observed before GREEN for behavior changes.

## 6. Completion evidence

- [ ] Focused tests pass.
- [ ] Required integrated Runtime/App/Web/Chromium checks pass for the exact final HEAD.
- [ ] Golden Course facts remain unchanged.
- [ ] `git diff -- books/functional-analysis` equivalent is empty.
- [ ] Write-back/read-back matches expected files and ref.
- [ ] Unexpected scope/concurrent change => stop as `CONFLICT_NEEDS_REVIEW`.
- [ ] If synchronizing, report all required sync counts and verify idempotency when applicable.
