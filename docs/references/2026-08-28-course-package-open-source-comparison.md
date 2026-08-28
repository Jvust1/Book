# Foundation A — Course Package Open-Source Source-Level Comparison

Date: 2026-08-28

Status: SOURCE_LEVEL_REVIEW_COMPLETE / SOURCE_ARCHIVE_SNAPSHOTS_PENDING_NON_BLOCKING

Scope: Foundation A Course Package Contract, with direct implications for Tasks 5–10. This review is deliberately limited to architecture and implementation patterns relevant to deterministic course/content packaging, package validation, stable identities, offline/import flows, and Golden/CI verification. It does not change the approved Course Package v1 contract by itself.

## Executive conclusion

The current Foundation A direction is sound and should **not** be redesigned before Task 5. The strongest external implementations reinforce four choices already present in the design:

1. package/manifests should carry explicit version/selection identity and be independently verified rather than trusted;
2. logical content identity should be conceptually distinct from placement/version/package identity;
3. validation should be staged, fail closed, deterministic, and complete before registration/consumption;
4. compile/export, validate/verify, and import/register/update should remain separate stages, with a real Golden round trip used as the high-confidence gate.

The source review therefore hardens the implementation plan instead of replacing it.

## Fixed reference set

| Repository | Fixed commit | Commit date | License | Source-level relevance | Snapshot status |
| --- | --- | --- | --- | --- | --- |
| `learningequality/kolibri` | `109027298ce03d1b97c56e569e02fe05a4f59b2d` | 2026-08-27 | MIT | content manifest integrity, content selection/versioning, idempotent resource import | `PENDING_SYNC_NON_BLOCKING` |
| `learningequality/ricecooker` | `a18a29cbb6d1f91b41097f9024e1e4276a4e9719` | 2026-08-03 | MIT | stable content identity vs tree placement identity, content-addressed file handling | `PENDING_SYNC_NON_BLOCKING` |
| `h5p/h5p-php-library` | `cb64a1f3884408487c3178e31fc140f5d45ca165` | 2026-08-11 | GPL-3.0 | staged package validation, required files, file-size/type policy, dependency checks | `PENDING_SYNC_NON_BLOCKING` |
| `openedx/openedx-platform` | `bae59d903571d65cd4a72578030b4cf69a4e985b` | 2026-08-27 | AGPL-3.0 | course archive upload/import stages, verification before update, explicit import state | `PENDING_SYNC_NON_BLOCKING` |
| `openedx/openedx-demo-course` | `494507ef4ba434e3be3f3f2133dbc8b8a6387cd0` | 2026-07-27 | AGPL-3.0 | source OLX → distributable archive → real platform import/reindex Golden-style loop | `PENDING_SYNC_NON_BLOCKING` |

No third-party source code is copied into Book. GPL/AGPL projects are used only as architecture/behavior references. Even for MIT references, the implementation should be written from the Book contract rather than copied mechanically.

## 1. Kolibri — manifest integrity and versioned selection

Studied at fixed commit:

- `kolibri/core/content/utils/content_manifest.py`
- `kolibri/core/content/utils/resource_import.py`
- `kolibri/core/content/test/test_content_manifest.py`

### Source observations

Kolibri's `ContentManifest` models a selection of content as channel ID + channel version + selected node IDs. Serialization sorts selected IDs and emits a derived `channel_list_hash`. Validation can recompute that hash and reject a stored manifest whose claimed hash does not match its actual channel list.

Its tests explicitly cover valid and invalid manifest hash validation, multiple versions, repeated additions and duplicate-node behavior. The resource-import path then consumes the manifest as a selection contract rather than treating it as the content bytes themselves.

The import manager also behaves idempotently for an already-present destination resource when the expected size matches, while a mismatch is not silently treated as equivalent.

### Implications for Book

**Adopt now:**

- Task 5 must independently recompute `package_identity`; never trust the stored value merely because its shape is valid.
- Artifact hashes must be independently recomputed from canonical bytes.
- Collection ordering and diagnostics should be deterministic.
- Manifest/package identity and artifact bytes remain separate concepts.

**Do not copy:** Kolibri's manifest format, channel model, database representation or MD5-style list-hash choice. Book keeps SHA-256 and the approved Course Package v1 contract.

## 2. ricecooker — logical identity is not placement identity

Studied at fixed commit:

- `docs/developer/ids.md`
- `ricecooker/classes/nodes.py`
- `ricecooker/classes/files.py`

### Source observations

ricecooker deliberately separates identities. A stable content identity is derived from a canonical source namespace + source identifier, while the tree node identity is derived from parent placement + the content identity. Therefore the same underlying content can appear at different places with different node IDs while retaining the same content ID.

Its node-copy behavior resets placement identity while preserving source/content identity. Its file objects also expose checksum/size around processed content-addressed filenames.

### Implications for Book

This is especially relevant to future multi-book, translation, supplementary-reference and concept-alignment work.

**Already aligned in v1:** Book has separate `logical_book_id`, `book_version_id`, artifact/content identity and package identity.

**Defer after Foundation A:** introduce a general content-level identity distinct from course/package placement identity only when a real downstream consumer requires it. Likely future uses include:

- same logical textbook material across editions/translations;
- the same source section reused in more than one course;
- Concept Graph / alignment across multiple books;
- deduplication without losing placement provenance.

Do **not** add a new identity field to Course Package v1 during Task 5 merely because ricecooker has one. Preserve schema extensibility and address it in a future versioned contract.

## 3. H5P — validate before extraction/registration

Studied at fixed commit:

- `h5p.classes.php`, especially `H5PValidator` and `isValidPackage()`.

### Source observations

H5P validates package structure before trusting/importing it. The validator checks package-level required JSON, validates required field forms, checks file-extension allowlists, enforces per-file maximum size, and later checks library/dependency requirements. Validation reports stable error codes/messages and fails the package rather than repairing it in place.

### Implications for Book

**Adopt now for Task 5 as an internal staged validator:**

1. contract shape / closed-object checks / forbidden secret-like fields;
2. package filenames and repository-relative path boundaries;
3. required artifacts and exactly-one-primary rules;
4. artifact SHA-256 and content identity verification;
5. package identity recomputation;
6. chapter/section/search structural baseline checks;
7. book/runtime readiness aggregation;
8. deterministic `PASS / WARN / FAIL` result.

The validator remains pure/read-only: it must never repair canonical book files or generated package files during validation.

**Defer:** H5P-style archive bomb protection, compressed/uncompressed size budgets, extension allowlists and pre-extraction checks should be added if/when Course Package becomes an external ZIP/archive transport format. Foundation A v1 currently materializes a directory under `.build/`, so adding archive complexity now would be premature.

## 4. Open edX — explicit import stages and clean separation of responsibilities

Studied at fixed commit:

- `openedx/openedx-platform/cms/djangoapps/contentstore/views/import_export.py`
- `openedx/openedx-demo-course/Makefile`

### Source observations

Open edX's course import flow exposes explicit progress stages: upload, unpacking, verifying, updating, then success. It rejects unsupported archive types early and checks chunk continuity while uploading. Repeated final upload requests are handled idempotently rather than blindly duplicating work.

The demo-course repository gives a practical source-to-real-consumer loop: source OLX is packaged into distributable archives; the import target is a real Tutor/Open edX CMS; and the imported content is reindexed. This is stronger evidence than only checking whether a tarball can be generated.

### Implications for Book

**Adopt now:**

- `compile_course_package()` and validation remain separate operations.
- Task 5 validator stays read-only and does not register the package.
- Task 8 CLI keeps compile and validate as separate commands.
- Task 9 PR FULL should compile and validate the Golden Course in addition to existing Runtime/App regressions.
- Task 6 Golden gate should verify actual source facts + deterministic package output + validator PASS, not only schema validity.

**Defer until package consumption migrates:** once Library Runtime actually consumes Course Package, add a clean-install / clean-registration Golden round trip analogous to source → distribution → real consumer. Foundation A intentionally does not migrate the current Runtime/App consumer yet.

## Concrete hardening for Foundation A Tasks 5–10

### Task 5 — Validator

Keep the approved public interfaces and error codes. Internally enforce deterministic staged validation:

- shape/schema/closed fields;
- forbidden secret-like key scan;
- path-boundary checks before reading referenced files;
- exact required package/artifact set;
- artifact existence + SHA-256;
- independent `package_identity` recomputation;
- structural baseline comparison;
- book/runtime readiness;
- deterministic diagnostic ordering.

A stored `readiness: PASS` must never override independently discovered failures.

### Task 6 — Golden Course

- Compile the Functional Analysis Golden Course twice from the same source.
- Require identical identity and emitted bytes.
- Run validator independently on the materialized package.
- Compare against the frozen structural baseline.
- Snapshot canonical source tree identity before/after and require zero mutation.
- Never alter canonical facts to make the Golden test pass.

### Task 7 — Architecture Fitness

External comparisons reinforce these fitness functions:

- package validation cannot mutate canonical books;
- paths may not escape repository/package boundaries;
- identity is deterministic;
- package registration cannot bypass validation;
- browser remains separated from direct storage authority.

### Task 8 — CLI

Preserve separate `compile` and `validate` surfaces. A future register/import command, if introduced, must consume validation results rather than fold repair + validation + registration into one opaque command.

### Task 9 — CI layering

- FAST: contract/schema + normalization + artifacts + compiler + validator + architecture fitness.
- PR FULL: FAST + existing Runtime/App/API/Web regressions + Golden compile/validate + browser acceptance.
- HEAVY: deeper canonical rebuild/hash reconciliation/release-package checks.

Do not force every small edit through the heaviest rebuild path.

### Task 10 — final checkpoint

Document which external patterns were adopted, deferred or rejected. Re-run exact-head gates and keep `books/functional-analysis/**` unchanged.

## Adopt / defer / reject matrix

### Adopt in Foundation A

- independent identity/hash verification;
- deterministic ordering and diagnostics;
- staged fail-closed validation;
- compile/validate/register separation;
- idempotent generated-output handling;
- Golden source→package→validator verification;
- explicit provenance for versioned inputs.

### Defer to a future version

- generalized content identity vs placement identity;
- external archive transport and pre-extraction bomb/type/size policies;
- package-driven Runtime/Library registration round trip;
- richer import stage/progress API exposed to UI.

### Reject for current scope

- adopting Kolibri channels or database model;
- adopting H5P package format/library dependency model;
- adopting OLX as Book's canonical structure;
- pulling Django or other large framework dependencies into the Course Package core;
- copying third-party schemas/source wholesale;
- replacing the current standard-library-first implementation with a large external validation stack without demonstrated need.

## Drive reference archive status

An additive reference area has been created under Book Drive:

- `Book/00_Project/External_References/`
- `Notes/`
- `Snapshots/`

The source-study policy requests full exact-commit source archives once a project enters source-level study. During this session the connected GitHub reader can retrieve repository text/files but does not expose repository source-archive bytes, and the execution container cannot resolve external GitHub/codeload networking. Therefore the five full source ZIP snapshots could not be materialized and uploaded reliably.

This is recorded as **`PENDING_SYNC_NON_BLOCKING`** for the five fixed references above. It does not block Foundation A implementation because every design conclusion is tied to an exact public `owner/repo@commit` and exact studied file path. When an authenticated archive-download path becomes available, the snapshots should be added to `Book/00_Project/External_References/Snapshots/` with archive SHA-256, source commit, license and Drive File ID. Existing snapshots must not be overwritten.

## Review checkpoint decision

**Decision: CONTINUE_FOUNDATION_A_WITH_HARDENED_VALIDATOR.**

No approved Course Package v1 field or Task 1–4 implementation needs to be rolled back because of this comparison. The next implementation step remains Task 5, with the internal staged-validation hardening listed above.
