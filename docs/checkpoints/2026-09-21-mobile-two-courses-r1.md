# Book mobile two-course source checkpoint — 2026-09-21

Status: **PARTIAL_SOURCE_CANDIDATE; textbook completeness and Android release gates remain open.**

This is an archive/recovery checkpoint, NOT an application-code integration PR. The implementation is in the exact source archive below. The existing application tree and PRs #26/#28/#29 have not been replaced or merged. Before continuing implementation, retrieve and verify the candidate archive; do not resume only from the older application tree on this branch.

## Recoverable source

- Archive: `Book-Mobile-TwoCourses-0.1.5-dev-r1-Source.zip`
- Drive file: `1LeVVIqmMpYT1X2nXKgYMztL-f8f74pAY`
- Folder: `1-lENYa3768x3cYSqCkQGwisyUm8CSqmT` under Book/03_Exports
- Bytes: `29224706`
- SHA-256: `4443b513e700875c5799dac7c12edcc94c084b9bf0e7d9104128a8840e69ac46`
- Drive upload, metadata readback, and a fresh raw-download SHA-256 comparison succeeded.
- ZIP CRC and hashes of all 836 manifested members passed; archive contains 837 files including its self-excluded manifest.
- Fresh extraction reran Python regression: 478 passed, 239 subtests passed.
- Source baseline is the verified 0.1.4 archive at `07b28d3b8541daa25b99937ece136dca32812506`. PR #29 head `c80b6aaf90947b5f43e7df67d4a8b1c7b58fc674` adds one subsequent docs/status-only commit. The candidate does not pretend these source identities are identical.

Open `DELIVERY_README_zh.md`, `governance/two_courses_checkpoint.json`, `governance/two_courses_content_gaps.json`, and `governance/two_courses_verification.json` inside the archive.

## Actual implementation in the archive

The same Android Book app gains an additive data-driven `reader_pack_v1` source reader at `/reader/`, linked from the existing React library page. It is not a claim that the legacy `course_package_v1` multi-book migration is complete.

- Four differentiated modes: source outline/preview, sequential study, recall then source reveal, and complete exercise-source groups with local answers/self-ratings.
- Source exercise continuations, equations, original records and page provenance are retained.
- Offline MathJax 3.2.1 SVG math; unsafe TeX extensions/HTML are not executed.
- 12–40px adjustable text; user-owned local font import. No font binaries are distributed; system serif fallback is not falsely labeled Shusong.
- Separate version-scoped SQLite notes/history with optimistic conflicts. Old StudyRecord schema and existing canonical books/courses/library are unchanged.
- Android export reuses the existing `export-data` bridge. Only the protocol double was tested, not a physical system picker.
- New notes exports are `book_reader_notes_export_v1`, not compatible with the old progress-import format. A complete new-reader cross-device import/merge is not implemented.

## Source coverage and remaining gaps

PDE: seven chapters, 33 numbered sections plus seven intros, 3449 records (2992 supplied JSONL records plus 457 chapter-four Markdown/TeX blocks). There are 95 source review groups and 194 source exercise groups, not necessarily 194 individual questions. Twenty original images are present; 23 are missing (chapter 2: 1; chapter 3: 3; chapter 5: 10; chapter 7: 9). Twenty-six reversible presentation-only syntax overlays are recorded separately from original LaTeX and require source review.

Jiang/Sun Functional Analysis: all 247 scanned source pages are retained. The source's 44 directory entries include only 29 numbered teaching sections. Chapter 1 sections 1 and 2 were visually transcribed from source pages 8–13 into 133 records/375 math fragments, pending independent proofreading. The remaining 27 numbered sections and chapter exercises are NOT fully transcribed. Images and note-taking controls must not be labeled complete four-mode textbook content.

No missing original diagram, formula, official solution or textbook fact was invented. No real relationship data, screenshot or credentials were copied into this project.

## Verification boundaries

- Python legacy plus reader: **478 passed**, 239 subtests, 4 warnings.
- Imported math: **7085/7085 syntax/SVG render checks**; not independent mathematical correctness review.
- Chromium in-memory DOM + explicit FastAPI TestClient bridge: **19 checks passed**. Browser storage and native export were test doubles; this is not live-navigation/Android E2E.
- Deterministic rebuild: all **363 reader-pack files unchanged** with identical inputs.
- Protected canonical file hashes: unchanged.
- Changed TSX library file: transpilation syntax passed, not full dependency/typecheck/build.
- npm install: blocked by DNS.
- Managed Chromium live navigation: blocked by administrator policy; policy was not modified or bypassed.
- Android wrapper CRLF was fixed; actual retry then failed at `services.gradle.org` DNS. Android SDK/device unavailable. No new APK/build/lint/signing/upgrade/physical-font acceptance is claimed.
- `verify_reader_delivery.py --require-complete` correctly exits 2. Complete-content gate is still closed.

## Next bounded work

1. Restore and verify the archive, then inspect its actual changes rather than repeating prior chat claims.
2. Continue source-grounded FA transcription from ch01_s03 and independently proofread the existing two sections.
3. Recover the 23 missing PDE original images or corresponding original PDF pages; keep source IDs and original content.
4. Publish reviewed application changes from this archived candidate into a dedicated implementation branch. This checkpoint itself publishes no application changes.
5. Run full frontend and Android Studio builds, then physical ARM64 four-mode/font/persistence/export/upgrade acceptance.

No direct main write, automatic PR merge, destructive operation, or paid inference occurred.
