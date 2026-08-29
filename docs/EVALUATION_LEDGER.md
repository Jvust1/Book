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

- RED: `ac9cdd62fe38d683079d6f5aa63a0895ea09c1b0`
- GREEN: `bf49326b0e54c20b4e24a36cb56c1485a5cd6a16`
- exact-head: `e0a303a51a3c4ac8cc1970ece067260b7d17a57c`
- fitness focused 6 / 6; Python full 188 / 188
- Runtime #154 Python 3.11 / 3.12 / 3.13 success
- App UI #210 App/Web/browser success; Chromium 11 / 11
- no `books/functional-analysis/**` path changed

## E-007 — Foundation A Task 8 compiler and validator CLI gates

Status: `PASS / FEATURE_BRANCH`

TDD checkpoints:

- RED: `dc127a67f01bfdf7c8a786b2e7bab1ebc803d20c`; Python full discovery reached 192 tests with only the intended missing CLI/public-export failures.
- Functional implementation completed through `1ef50ebe284adff6c33218e6d7d8d2a43f472756`.
- exact-head verification: `116cf4275b8006bc48860943c8e50987547cb5a5`.

Verified at exact HEAD:

- Course Package CLI focused tests: 4 / 4 PASS
- Python 3.13 full discovery: 192 / 192 PASS
- Runtime reference run #156: Python 3.11 / 3.12 / 3.13 all success
- Functional Analysis Runtime remained `READY` with 8 chapters / 132 sections / 1493 search records / 442 PDF pages / printed final page 423
- Book App UI run #212: App API success, Web tests success, TypeScript typecheck success, production build success
- real Chromium acceptance: 11 / 11 PASS
- pure Task 8 compare from `6170643faad663406a6f2e2120bec0169df05848` to exact HEAD contains only `course_package/__init__.py`, `tests/test_course_package_cli.py`, `tools/compile_course_package.py`, and `tools/validate_course_package.py`; no canonical textbook path changed
- compile CLI produces stable JSON with `status`, `course_id`, `package_identity`, `package_dir`; successful generated package independently validates PASS
- compile/validator invalid path invocations return exit 2 without Python traceback leakage

The CLI layer exposes the already-verified compiler/validator trust roots without changing the Runtime/App consumer and without permitting the default CLI output root to escape the repository.

## E-008 — Foundation A Task 9 layered CI gates

Status: `PASS / FEATURE_BRANCH`

Implementation HEAD:

`94fee411b5f8d67a5db2ef5779657f39c226c220`

Pure Task 9 compare from `03b23305710e361bde9caf17470c1a2e75510092` to the implementation HEAD contains exactly:

- `.github/workflows/course-package-fast.yml`
- `.github/workflows/course-package-heavy.yml`
- `.github/workflows/runtime-reference-tests.yml`
- `.github/workflows/app-ui-tests.yml`

No canonical textbook or App source file is in the Task 9 diff.

Verified automatically at the Task 9 implementation HEAD:

- Course Package FAST run #1 (`33190233674`): success
- Foundation FAST focused suite: 46 / 46 PASS
- Architecture Fitness: PASS
- Runtime reference run #157 (`33190233583`): Python 3.11 / 3.12 / 3.13 all success
- Python 3.13 PR FULL path: Golden Course Package compile PASS, independent validation PASS, architecture fitness PASS
- Book App UI run #213 (`33190233579`): app-api success, web-client success, browser-acceptance success
- real Chromium acceptance: 11 / 11 PASS

HEAVY is intentionally `workflow_dispatch` only. Its implementation rebuilds/recovery-checks an isolated `/tmp` copy rather than using canonical `--promote-safe` writes, then checks canonical readiness and Golden package/fitness read-only. No HEAVY execution result is claimed without an actual run record.

Task 9 proves the automatic FAST + Runtime PR FULL + App PR FULL wiring and defines a non-canonical-writing manual HEAVY gate. Foundation A was subsequently completed and merged through PR #13.

## E-009 — H0 neutral Book identity seam

Status: `PASS / INTEGRATED`

- PR: `#18`
- exact reviewed head: `56c289ccdb5bd692efcbd642dfd9267278f5e5af`
- merge commit: `3dcc600c2c8a39e1ffc41c07fbf290adfba5035c`
- Course Package FAST #22: SUCCESS
- Runtime reference #185: Python 3.11 / 3.12 / 3.13 PASS; Python 3.13 Golden rebuild/validate + architecture fitness PASS
- Book App UI #241: App API, Web and real Chromium acceptance PASS
- scope audit: no `books/**`, `courses/**`, `library/**`, App product code, StudyRecord, H1+, or public API migration

Conclusion: the neutral `BookIdentity` / canonical role owner is integrated without changing legacy product behavior.

## E-010 — H1 internal source provenance and serialization freezes

Status: `PASS / INTEGRATED`

- PR: `#19`
- exact reviewed head: `a225f899fb93faca22c2b1f9ad0c2b1ae2a2fed2`
- merge commit: `7e54e87b9674455e9f3d275016313f6c9e2487ac`
- Course Package FAST #38: SUCCESS
- Runtime reference #209: Python 3.11 / 3.12 / 3.13 PASS; Python 3.13 Golden/readiness/fitness PASS
- Book App UI #271: App API, full Runtime/App discovery, Web and real Chromium acceptance PASS
- public Search/Source/QA DTO shapes and browser persistence shapes remained frozen; internal provenance did not leak into external DTOs

Conclusion: collision-safe `(book_version_id, source_kind, source_id)` identity and internal provenance adapters are integrated while external serialization remains unchanged.

## E-011 — H2 Exact-only shared Retrieval seam

Status: `PASS / INTEGRATED`

- PR: `#20`
- exact reviewed head: `66ac966c5dfe59ebeea82b168b2ee67fc85f9474`
- merge commit: `410cede92bcc0783e4fca9b02faec79e5fe77112`
- Runtime reference #220: SUCCESS across Python 3.11 / 3.12 / 3.13, including Python 3.13 Functional Analysis rebuild/readiness, Golden validation and architecture fitness
- Book App UI #287: App API, Web and Chromium acceptance SUCCESS
- SearchRuntime versus RetrievalEngine equivalence covered English, Chinese, formula, zero-result and Section-scoped queries
- no FTS/BM25/semantic implementation, StudyRecord migration, public multi-book DTO migration or canonical textbook change

Conclusion: Search and QA evidence candidate retrieval share the internal Exact-only Retrieval seam while public ranking, score, order and error semantics remain frozen.

## E-012 — H3a deterministic Concept graph contract

Status: `PASS / INTEGRATED`

- PR: `#21`
- exact reviewed head: `1ed4fc6574417b56b4342ae639f81a69dd842c6b`
- merge commit: `f69166568839b7038b0f0472baefcee34299fa17`
- review-repair RED: `2bc7fb6b215b618298e6d860450087a7ef4c67af`; Foundation B contract #4 failed exactly on source-pair/schema and non-main Section validation gaps
- final exact-head Course Package FAST #45: SUCCESS
- Runtime reference #236: SUCCESS; Python 3.11 / 3.12 / 3.13 PASS
- Foundation B contract #8: SUCCESS
- Book App UI #303: App API, Web tests/typecheck/build and real Chromium acceptance PASS
- final scope remains eight H3a files only; no production Concept dataset, Search/QA/App activation, StudyRecord change, FTS/BM25 implementation, H3b or public multi-book migration

Conclusion: the inert v1 Concept/ConceptAlignment contract, deterministic canonicalization/cycle diagnostics, paired source contract, and repository-bound per-book Section reference validation are integrated. H3b is not authorized by H3a.

## Next evaluation

H4a is the next approved stage. Its evaluation must remain shadow-only: measure FTS5/BM25 retrieval coverage/ranking against the existing Exact baseline through the shared H2 Retrieval boundary without changing public Search/QA behavior. The H4a gate must define deterministic datasets/queries, comparison metrics, provenance checks, failure semantics and exact-head regression evidence before any later activation proposal. `H3b`, `B4b`, `B5`, and StudyRecord book-version migration remain separate human gates.
