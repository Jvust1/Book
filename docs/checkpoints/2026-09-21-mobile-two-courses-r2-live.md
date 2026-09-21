# Mobile two-course implementation checkpoint — r2

Date: 2026-09-21

Status: ACTIVE_IMPLEMENTATION / NOT_RELEASE_COMPLETE.

## Base

- Repository: Jvust2/Book
- Base: PR #29 exact head `c80b6aaf90947b5f43e7df67d4a8b1c7b58fc674`
- Implementation branch: `feature/mobile-two-courses-0.1.5-r2-20260921`
- Previous recoverable candidate: Drive `Book-Mobile-TwoCourses-0.1.5-dev-r1-Source.zip`, ID `1LeVVIqmMpYT1X2nXKgYMztL-f8f74pAY`, SHA-256 `4443b513e700875c5799dac7c12edcc94c084b9bf0e7d9104128a8840e69ac46`.

## Current product implementation

The recovered r1 candidate already contains the additive `reader_pack_v1` reader, four differentiated learning modes, offline math rendering, 12–40 px text sizing, user-owned local font import, reader notes/history, PDE 7-chapter normalized data and all 247 Jiang/Sun source page scans.

The current r2 work continues from that exact candidate rather than rebuilding from chat recollection.

## Jiang/Sun transcription progress

Source: `functional_analysis_2e_jiang_sun`, source PDF SHA-256 `dcc04c45d761949290f5a35624b8cdf218520a2ceecace7be0017cf013cd19d1`.

Visually transcribed from the supplied source scans into LaTeX/Markdown, pending independent proofreading:

- ch01_s01
- ch01_s02
- ch01_s03
- ch01_s04
- ch01_s05 — 完备的距离空间
- ch01_s06 — 列紧性
- ch01_s07 — 赋范线性空间
- ch01_s08 — F－空间
- ch01_s09 — 压缩映象原理，Fréchet 导数
- ch01_exercises — 第一章习题 1–30

Current audit after ingestion:
- numbered teaching sections: 29
- transcribed numbered sections: 9
- transcribed exercise entries: 1 (chapter 1)
- remaining numbered sections: 20
- normalized reader records: 1126
- source pages retained: 247
- full textbook content gate: INCOMPLETE

No missing theorem, formula, exercise solution or textbook fact is invented.

## PDE status

- 7 chapters
- 33 numbered sections
- 3449 normalized records
- 95 review source groups
- 194 practice source groups
- 23 source images absent from the supplied files
- 26 presentation-only syntax overlays still require independent source review

Missing diagrams are shown as gaps; they are not regenerated or guessed.

## Verification at this checkpoint

- `python -m pytest tests_reader -q`: 18 passed
- `python -m pytest tests app_tests -q`: 460 passed, 239 subtests passed
- audit bug fixed: exercise entries are tracked separately and no longer inflate numbered-section transcription counts
- reader delivery integrity: PASS
- full content status: INCOMPLETE

These tests do not claim mathematical proofreading, Android execution or physical-device acceptance.

## Remaining release gates

1. Continue source-grounded Jiang/Sun transcription through all remaining numbered sections and exercises.
2. Recover the 23 missing PDE source images if/when the original pages are supplied; otherwise keep explicit source-gap markers.
3. Publish the reviewed application code, transcriptions, generators and tests to this implementation branch while keeping large source scans/artifacts in Drive.
4. Run frontend build/typecheck and Android Studio build/lint.
5. Run Xiaomi 14 physical-device acceptance for four modes, font sizing/local font, persistence/export and upgrade behavior.
6. Produce a new APK/source archive only after the above gates are evidenced.

No direct main write, PR merge, destructive operation, or completeness claim is made.
