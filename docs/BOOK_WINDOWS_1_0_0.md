# Book Windows 1.0.0 — teaching r2 delivery

Date: 2026-09-27. Build: `20260927-windows-1.0.0-teaching-r2`.

## Current release identity

Read `governance/CURRENT_WINDOWS_RELEASE.json` and `governance/book_windows_1_0_0_20260927.json`. They supersede the older rc4/rc5 Windows-delivery narrative only; they do not declare the separate main-branch architecture roadmap complete.

Actual source is the artifact-backed seven-book Windows Go/JavaScript application, not the old FastAPI/React app on main. This commit registers exact identities, a recovery tool and a tested pure-JavaScript code snapshot. It is not a full import of all 1306 source files into GitHub.

## User-visible changes

- Actual simplified teaching: 89 topics, each with overview, prerequisites and goals.
- Organized review: 269 authored knowledge points with conditions, methods and pitfalls.
- Worked practice: 178 original supplementary questions with standalone stems, hints, steps, final answers and pitfalls.
- Full-book preview, full-book review, all-worked-question bank and cross-topic practice shortcuts.
- Per-book 10/20/50-question practice selects available distinct questions across topics. It does not invent duplicates to fill a requested count.
- Self-assessment summaries distinguish understood, review, wrong and unrated. No automatic exam grade is fabricated.
- Saved drafts, pause/resume, old-session history, blank wrong-question retries, backups and save-conflict handling remain intact.
- About dialog uses the actual catalog version and build instead of a stale rc4 string.

Compared with rc5: +55 themes, +165 review points and +110 worked questions. Original 1175 source/study/media files are byte-identical to the verified baseline.

## Delivery and source recovery

Drive folder: https://drive.google.com/drive/folders/1oHTT6KPsvEqj4fmLt1KJX4-ltqTot4ry

Users receive a complete single `Book-1.0.0-Windows-x64.exe` and Portable ZIP in the conversation. Full EXE direct Drive upload failed twice; Drive has a fully downloaded/hash-verified three-part backup. Do not require the end user to reconstruct these parts when the full conversation download is available.

Complete source is durably preserved as the existing verified rc4 baseline plus the new cumulative delta. The full source ZIP is also delivered in the conversation. No intermediate rc5 delta is needed.

1. Obtain and concatenate the three rc4 source parts in the checkpoint's exact order; validate baseline SHA-256.
2. Obtain `Book-1.0.0-Source-Delta.zip`, Drive ID `1CjhCMB_J725bceG1RzNeVXts9ZLC1Psx`, SHA-256 `e201b6e6eabefec90559e2ca5ce5f094dae1e222b4e978eaf2215a05f3670b03`.
3. Run `python tools/restore_book_windows_1_0.py --baseline rc4-source.zip --delta Book-1.0.0-Source-Delta.zip --sha256 e201b6e6eabefec90559e2ca5ce5f094dae1e222b4e978eaf2215a05f3670b03 --output NEW_DIRECTORY`.
4. The helper rejects an existing target, unsafe paths, symlinks and hash mismatches. It verifies all 1306 restored files.
5. Follow restored `README_WINDOWS.md`: compile teaching sidecars, pack web assets and cross-compile the Go launcher. Same-toolchain fresh restoration/rebuild was actually performed and produced an EXE byte-identical to the delivered one.

Reports ZIP Drive ID: `13RXbDf4aiVlUmaEco7Pubr-NqwsvB8ce`. Full remote-byte readback record: `1jCYF_f9cHBy500EdqmfsujQRaf-2C3LU`.

## Verification scope

Local completed results: JS 56/56; content 1150/1150 including 146 example checks; Go 15/15; Go race subset 14/14; teaching UI 21/21; new release UI 99/99; legacy workflow 42/42; source-safety UI 4/4; PE/same-source Linux service 32/32; projection integrity 0 issues; archive/rebuild checks 6/6. All 89 topics and 178 worked answers passed MathJax rendering checks. Source ZIP, delta restoration and Portable EXE identities were checked after packaging.

Go race excludes the large read-only embedded-bundle test, which separately passed ordinary Go and full-resource hashing. Do not call a timed-out earlier whole-race attempt a pass.

The managed browser blocks direct loopback navigation. Real Chromium tests use exact packaged JS/CSS/data, local MathJax and the same-source Linux Go backend through an explicit test-only fetch bridge. This is not Windows Edge launch, Windows filesystem/Microsof​t GUI acceptance or direct-CSP-navigation certification. No GitHub CI result is claimed.

## Boundaries

1.0.0 names this software delivery, not academic completion of seven books. Whole-book authored completion, all-original-exercises-solved and independent expert review remain false. New questions are original supplementary teaching, not textbook standard answers. Topic references locate source sections, not proof that the textbook supplied the new answers. Formula rendering is not mathematical truth verification.

Windows x64 with an existing Edge installation is the intended target. EXE is unsigned, cross-compiled and not run on a Windows host in this session. End users need no Python/Node/API key. No font binaries, secrets or user notes are redistributed. Private textbook materials remain for authorized personal use.

No automatic merge, main mutation, old artifact deletion or real personal learning-data mutation.
