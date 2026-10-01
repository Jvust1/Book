# Book PDF concentrated delivery v6 — 2026-10-01

## Status

**FULL_RELEASE_NOT_READY.** Financial Economics Ten Lectures chapter 5 has a complete first visual source-reading pass and three same-source A4 reading PDFs. The six-book/all-mode release is not complete. No main merge, canonical textbook mutation, deployment or Windows-reader acceptance is claimed.

Branch before this checkpoint: `book/pdf-corrections-20261001-v1` at `50e35c7e4d7842b27bd91f2bb8f56c669ed2e9e1`. Main observed at `805510f86546709b6f67c9e9079943f205c2c245`.

## Delivered chapter

- Original scan PDF pages 120–144 / printed pages 101–125, all 25 pages visually read. Includes all eight sections, 17 numbered equations, two tables, ten original exercises and the mathematical appendix.
- 10px: 7.5 PDF pt, 14 A4 pages, 324350 bytes.
- 12px: 9 PDF pt, 18 A4 pages, 331190 bytes.
- 15px: 11.25 PDF pt, 23 A4 pages, 339814 bytes.
- All have actual A4 page boxes, approximately 595.276 by 841.890 pt. Source-level reflow, no whole-page scaling or cropping.
- Shared final body SHA-256: `790aebe691b9ac1b4836cb5687e074109287650f0f8b723dddb39fbcbb10b4f3`.
- Noto Serif CJK SC substitute, **not Shusong**. Mathematical font: Latin Modern Math. No font files are distributed.
- Ten printed-source doubts are retained with explicit notes; inferred doubts are not represented as confirmed errata. This is not an independent academic proof audit.

The recovered archive has 441 original chapter RECORD blocks; the historical v5 denominator 144+294=438 is not reproduced. The private package preserves the original 441 blocks and a 25-page coverage ledger. Page-level visual checking is not a blanket promotion of every old record to an A-verified status.

## Verification actually executed

- Two XeLaTeX passes for each size: Overfull, missing character, undefined command, LaTeX error and font-warning counts all zero in final logs.
- All 55 new pages rendered and inspected in contact sheets; no out-of-page text, empty page, NUL or U+FFFD replacement character.
- Additional Poppler checks: 15 new-PDF key pages across the three sizes, three math-physics regression-repair pages and two public-finance key pages.
- Same source content, 16961 CJK characters in each size; character multiset agrees after an explicit extensible vertical-bar component normalization. Raw extraction order is not claimed identical because pagination moves footnotes.
- Clean rebuild in a separate path containing spaces: **3/3 PDF byte identities match** in the recorded Linux/TeX/font environment. This is not Windows execution evidence.
- Offline package verifier: **16 local tests pass**. Full package verifies 92 payload hashes. Its Drive raw-download round trip preserves SHA-256 and all payload hashes, and ZIP CRC passes.

Commands:

```sh
python -m unittest discover -s tools/pdf_delivery -p test_verify_package.py -v
python tools/pdf_delivery/verify_package.py /path/to/extracted/delivery
# Inside the private package, with the recorded TeX and system fonts available:
python source/build.py --output rebuilt
```

No new exact-head hosted CI result is claimed by this checkpoint.

## Existing repair selections rechecked

1. Functional Analysis 12px: existing 309-page formula/numbering repair, targets152–158 rendered and reviewed, hash matches. The old report's other302-page comparison was not rerun without that original file.
2. Financial Economics 12px: existing p75 repair, full149 pages retained. Other148 pages freshly compare identical in text and72dpi pixels.
3. Financial Economics 15px: existing75/139/276/334 point repairs. Other330 pages freshly compare identical. The334-page book still has650x842pt boxes, **not A4**. The p139 derivation is in chapter4, so chapter5 reflow does not close its neighboring-page reflow task.
4. Public Finance 12px: exact original hash `5e96b405f3b70891779022301803769921f51182735bd9a05a1ec5d64d486c74` reproduces9/2 header corruption in MuPDF. Existing repair `cab8d2c150362a13e592c629f9ac0d790db6deea7d07510e2cd010954d0edbc4` is reused. After an initial timeout, a complete chunked rerun verifies all287 pages: text, geometry and body-only y50..800pt pixels at72dpi are unchanged. Unit page numbers5/6 and6/6 remain meaningful.
5. Math Physics: prefer the original MD's already correct **nine-caption** version, SHA `43cd8542f08f8c57b3debc44b23f837e6f149c703bb43c7d2f1550a68560e326`. A later six-mask archive regressed three captions. The new three-mask alternative was checked but is not counted as a new unique accomplishment or selected over the correct existing version. Images remain intact. Its203 pages remain735x1030pt, not A4.

## Remaining release gates

- Recover or reconstruct and validate editable sources corresponding to current preview/review/practice outputs; generate and check all six books/all modes/all intended sizes. Existing files are preserved, not silently replaced by chapter5 reading text.
- Source-level A4 reflow and real-font-size checks for the remaining full books, including chapter4 p138–140 and unresolved neighboring/sparse-page flow. No mass scaling/cropping workaround.
- Verified Shusong font/permission/environment and bold/math/punctuation fallback. A Drive file named6号书宋 actually embeds Noto and does not prove this gate.
- Actual target Windows-reader fit-width, fit-page and printing acceptance; not available in this run.
- Complete six-book front/middle/end, math/figure and mode-boundary release sampling, plus independent review of recorded source doubts.

Archive inventory:67chapter TeX files,22922RECORD blocks with mixed inherited quality labels. Those labels were not all independently reverified. No source corresponding one-to-one to every current preview/review/practice PDF was found within the recovered archive and selected PDF-corrections branch; this does not assert that no such source exists anywhere.

## Private Drive delivery

- Folder: https://drive.google.com/drive/folders/1CCMiBebf8EznwJdU7CDC9ALhuAufA0f7
- Full package,8PDFs+source+QA: https://drive.google.com/file/d/1agsQrG_uVbI9nNzj81-nTwBoDm-YyKax/view
- Lightweight chapter-only package,3PDFs+source+QA: https://drive.google.com/file/d/1X2-RzMb1Y1skm5fuREoAXNbVU6Muu9qv/view
- Detailed Chinese task report: https://drive.google.com/file/d/18aHgbd06fAngZ3lz5rZ6JfpG-IYiyO7B/view
- 15pxPDF: https://drive.google.com/file/d/1auscH23Vse7Mr82dnjobnnDhZmiti6kj/view
- 12pxPDF: https://drive.google.com/file/d/1yLhANuLOThAZDp0NGiEomDKXAce3gO74/view
- 10pxPDF: https://drive.google.com/file/d/1Wd9zie7DojIRFqF4jStjCU4xfDj9epV1/view

Writes succeeded and folder listing read back matching names/sizes, with files not shared. The full package was also downloaded again and hash/CRC/payload-verified. Full copyrighted transcriptions and source illustrations remain in the private artifact package; this public commit contains only generic verification code and delivery metadata. No font files, raw textbook pages or full chapter transcription are added to this public repository.
