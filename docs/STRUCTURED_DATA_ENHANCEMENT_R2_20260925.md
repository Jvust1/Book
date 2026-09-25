# Book 六本教材结构化数据完善 r2

Artifact: `book-six-textbooks-enhancement-20260925-r2`

Base: `book-structured-repair-20260924-r1`

This is a source-preserving incremental text/table/quality layer for the six Chinese textbooks. It does not replace r1 historical evidence or unchanged image assets.

## Improvements

- Six books: 24,702 records, 1,901 PDF page maps, 23,380 unified search rows.
- Public Finance: five new full-table scan retranscriptions; six source-verified numeric tables total including r1 table 13-1. Four ratio tables passed 160 arithmetic consistency comparisons within displayed rounding precision.
- Financial Economics: 42 targeted corrected records across 26 source pages. Martingale-variant hotspot scan reduced to zero; PDF219 sigma-field corruption was source-adjudicated separately instead of globally replacing the OCR character.
- Every record/page now carries an explicit quality tier and QA evidence mode. A/B/C/D layers prevent machine draft text from being silently promoted.

## Delivery

Drive ZIP ID: `1eKimb6q3BhCIOeTOtThdWSqQZFs35bwG`

ZIP SHA-256: `0d8efa419886ee2601a7a15e9470852f03ebd4a744bfa545d43627e57e1ed983`

ZIP bytes: 19,275,031

Drive report ID: `1GrX4UWAchfjdFt6nB2FeR0lVzAG5cxTt`

Report SHA-256: `a20459065b722e6a97f21dc6ad196159e300f7a40f45b4719d8f83a51e4c736f`

The r2 ZIP is an overlay and reuses unchanged r1 image assets. Base r1 full-archive SHA-256 is `c7afb8e26078b635d78c78882cace9284e1cb839f0e4c6f9e5b84264a207c2ee`.

## Verification

- 58 r2 validation checks PASS / 0 FAIL.
- Extracted package verifier checked 2,203 manifest-listed files / 0 failures.
- Drive ZIP and report were freshly read back and SHA-256 matched.
- r1 source_text and source_record are byte-stable for all six-book record IDs.
- This pass did not rerun r1 MathJax/App/whole-proof acceptance.

## Remaining boundaries

- 66 Public Finance table-part candidates remain source-review candidates (about 45 tables/comparison tables).
- Financial Economics ordinary OCR outside the targeted corrections is not whole-book character-level accepted.
- Contemporary China Economy retains machine-draft rows where already labeled.
- Math semantic/proof acceptance, 110 Functional Analysis reference derivations, and complete PDE worked solutions remain separate independent-review work.

No main write, PR merge, App replacement, or Runtime migration is authorized or performed by this r2 checkpoint.
