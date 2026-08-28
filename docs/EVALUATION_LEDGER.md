# Book Evaluation Ledger

Updated: 2026-08-29

This ledger records verification evidence that affects future development. It is not a frozen benchmark ledger; no entry below may be described as unseen/frozen evidence unless explicitly marked so.

## E-001 — Integrated Phase 1G baseline

Status: `PASS / INTEGRATED`

Phase 1G merge commit `4b111e4b1ffde86a365aaad2a3164f8aedccc819` and post-merge Book App UI run #194 established the integrated baseline: Runtime discovery 146 / 146, Functional Analysis `READY`, App discovery 87 / 87, Web/typecheck/build/browser acceptance PASS.

## E-002 — Foundation A Tasks 1–4 implementation checkpoint

Status: `PASS / FEATURE_BRANCH`

Verified implementation HEAD before external-reference documentation: `df5346c0598495bf8e84f5d214afbf2e9cd55c63`.

Completed: Course Package v1 contract/schema, legacy manifest normalization, canonical artifact/content identity, deterministic compiler. Task 4 exact-head evidence: compiler 3 / 3, Python full 167 / 167, Python 3.11/3.12/3.13 success, App/Web/browser success, Golden Runtime `READY`, no implementation mutation of `books/functional-analysis/**`.

## E-003 — Source-level external comparison

Status: `SOURCE_LEVEL_REVIEW_COMPLETE`

Checkpoint: `16ee8acfafda4558dbbc30a2cfbd1f7d51a5d0d6`.

Fixed references include Kolibri, Ricecooker, H5P, Open edX platform, and Open edX demo course at the pinned commits recorded in `docs/references/2026-08-28-course-package-open-source-comparison.md`. Conclusion: no Course Package v1 redesign required; source archive synchronization remains separately pending non-blocking.

## E-004 — Foundation A Task 5 fail-closed validator

Status: `PASS / FEATURE_BRANCH`

- RED: `b198f97068137e6deb787c60762501cd0440decc`
- GREEN: `9d92a166d45aaf6493ae2ab9466031a0d69d62b6`
- exact-head: `b133e32c3355f0cac8478beaea960e81c2144b61`
- validator 12 / 12; Python full 179 / 179
- Runtime #150 and App UI #206 success
- Functional Analysis `READY`; Task 5 implementation path does not modify canonical Book assets

## E-005 — Foundation A Task 6 Golden Course gate

Status: `PASS / FEATURE_BRANCH`

- RED: `9b68187c2c0adf4b364c41b42c47ab1a3756219b`
- GREEN: `6823c9c806a9175b4e4444345b40cf406fa5dde2`
- exact-head: `eeb2d4adee699d44924ed2ebfc2207df595f9ed6`
- Golden 3 / 3; Python full 182 / 182
- Runtime #152 and App UI #208 success; Chromium 11 / 11
- Golden gate requires validator PASS, proves deterministic identity/bytes, and verifies canonical tree hashes before/after
- implementation diff contains no `books/functional-analysis/**` path

## E-006 — Foundation A Task 7 executable architecture fitness

Status: `PASS / FEATURE_BRANCH`

TDD checkpoints:

- RED: `ac9cdd62fe38d683079d6f5aa63a0895ea09c1b0`; new test discovery failed for the intended reason: `course_package.fitness` did not exist.
- GREEN: `bf49326b0e54c20b4e24a36cb56c1485a5cd6a16`.
- exact-head verification: `e0a303a51a3c4ac8cc1970ece067260b7d17a57c`.

Verified at exact HEAD:

- architecture fitness focused tests: 6 / 6 PASS
- Python 3.13 full discovery: 188 / 188 PASS
- Runtime reference run #154: Python 3.11 / 3.12 / 3.13 all success
- Functional Analysis Runtime remained `READY`; protected values remained 8 chapters / 132 sections / 1493 search records / 442 PDF pages / final printed page 423; readiness reported no missing/stale files or identity mismatches
- Book App UI run #210: App API success, Web tests success, TypeScript typecheck success, production build success, browser acceptance success
- real Chromium acceptance: 11 / 11 PASS
- implementation diff from `08a91b98c7257e9d9ce8e00f8920aebe8a7e842f` to exact HEAD contains only `course_package/fitness.py`, `tools/check_architecture_fitness.py`, and `tests/test_architecture_fitness.py`; no `books/functional-analysis/**` path changed

The fitness layer composes existing compiler/validator/Golden trust roots, aggregates diagnostics fail-closed, checks browser durable-SQLite leakage, canonical output boundaries, Golden mutation, absolute paths and secret-like compiled fields, and does not activate future-only subsystems.

## Next evaluation

Foundation A Task 8 must add compiler and validator subprocess CLI entry points and public package exports. Verification must prove JSON/exit contracts, invalid-path exit 2 without traceback leakage, compile-then-validate PASS through a temporary output root, focused Foundation tests, and exact-head Runtime/App regressions while preserving canonical Book assets.
