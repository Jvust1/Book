# Mobile two-course candidate — current recovery entry

The newest Book mobile two-course work is on **`feature/mobile-two-courses-content-r2-20260921`** and is still an incomplete development candidate.

## Recovery base

The full runnable r1 candidate remains the immutable Drive recovery base:

- `Book-Mobile-TwoCourses-0.1.5-dev-r1-Source.zip`
- Drive ID: `1LeVVIqmMpYT1X2nXKgYMztL-f8f74pAY`
- SHA-256: `4443b513e700875c5799dac7c12edcc94c084b9bf0e7d9104128a8840e69ac46`

Read the historical r1 checkpoint at `docs/checkpoints/2026-09-21-mobile-two-courses-r1.md`.

## Current r2 delta

Read:

- `docs/checkpoints/2026-09-21-fa-ch01-s03-s04-r2.md`
- `governance/source_candidates/mobile-two-courses-r2.json`
- `content_sources/fa_transcription/ch01_s03.md`
- `content_sources/fa_transcription/ch01_s04.md`

Jiang/Sun Functional Analysis is now **4/29 numbered teaching sections transcribed**, with §3 and §4 newly added in r2. All four transcribed sections still require independent proofreading.

Current exact local verification after §4:

- 480 Python tests passed
- 239 subtests passed
- reader-focused 20 passed
- Chromium in-memory 21 checks PASS
- integrity gate PASS
- complete-content gate correctly remains INCOMPLETE / exit 2

PDE gaps remain unchanged: 23 missing original images and 26 presentation-only LaTeX corrections awaiting source review.

No new verified Android APK exists yet. Do not claim final completion or Android release readiness.
