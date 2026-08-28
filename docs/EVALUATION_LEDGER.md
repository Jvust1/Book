# Book Evaluation Ledger

Updated: 2026-08-28

This ledger records verification evidence that affects future development. It is not a frozen benchmark ledger; no entry below may be described as unseen/frozen evidence unless explicitly marked so.

## E-001 — Integrated Phase 1G baseline

Status: `PASS / INTEGRATED`

Repository evidence in `docs/CURRENT_STATE.md` records Phase 1G merge commit `4b111e4b1ffde86a365aaad2a3164f8aedccc819` and post-merge Book App UI run #194:

- Runtime discovery: 146 / 146
- Functional Analysis readiness: `READY`
- App discovery: 87 / 87
- Web tests: PASS
- TypeScript typecheck: PASS
- production build: PASS
- real Chromium acceptance: PASS

This is the integrated baseline Foundation A must not regress.

## E-002 — Foundation A Tasks 1–4 implementation checkpoint

Status: `PASS / FEATURE_BRANCH`

Last verified implementation HEAD before the external-reference documentation checkpoint:

`df5346c0598495bf8e84f5d214afbf2e9cd55c63`

Verified work completed before that checkpoint:

1. Course Package v1 contract and published JSON Schemas.
2. Legacy `course_manifest_v1` normalization into canonical book roles.
3. Canonical artifact inventory, SHA-256, and deterministic Book content identity.
4. Deterministic Course Package compiler with idempotent same-bytes reuse and fail-closed conflict behavior.

Task 4 exact-head verification recorded:

- compiler focused tests: 3 / 3 PASS
- Python full discovery: 167 / 167 PASS on Python 3.13
- Python 3.11 / 3.12 / 3.13 workflow jobs: success
- App API: success
- Web tests / typecheck / Vite build: success
- Chromium acceptance: success
- Golden Functional Analysis Runtime: `READY`
- `books/functional-analysis/**`: zero implementation mutation

## E-003 — Source-level external comparison

Status: `SOURCE_LEVEL_REVIEW_COMPLETE`

Checkpoint commit:

`16ee8acfafda4558dbbc30a2cfbd1f7d51a5d0d6`

Fixed upstream references:

- `learningequality/kolibri@109027298ce03d1b97c56e569e02fe05a4f59b2d` — MIT
- `learningequality/ricecooker@a18a29cbb6d1f91b41097f9024e1e4276a4e9719` — MIT
- `h5p/h5p-php-library@cb64a1f3884408487c3178e31fc140f5d45ca165` — GPL-3.0
- `openedx/openedx-platform@bae59d903571d65cd4a72578030b4cf69a4e985b` — AGPL-3.0
- `openedx/openedx-demo-course@494507ef4ba434e3be3f3f2133dbc8b8a6387cd0` — AGPL-3.0

Conclusion: no Course Package v1 redesign is required. Mature implementations reinforce independent identity/hash verification, fail-closed staged validation, separation of compile/validate/import, and Golden real-consumer testing as the later end state.

Source archive synchronization is tracked separately in `governance/pending_sync.json`; it is not marked complete until Drive IDs and snapshot hashes exist.

## Next evaluation

Foundation A Task 5 must first demonstrate RED tests for invalid packages, then GREEN validator behavior, followed by exact-head Runtime/App regressions appropriate to the changed paths.
