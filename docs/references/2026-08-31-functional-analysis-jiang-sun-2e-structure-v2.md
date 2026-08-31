# Book Textbook Ingest Checkpoint — 2026-08-31

## New additive textbook source

`functional_analysis_2e_jiang_sun` — 《泛函分析（第2版）》江泽坚 / 孙善利，高等教育出版社。

This is a separate source snapshot. It does **not** replace the existing Stein & Shakarchi Functional Analysis canonical dataset.

## Completed artifacts

- V1 hierarchy: book -> chapter -> section -> page
- V2 hierarchy: book -> chapter -> section -> page -> block -> semantic_unit
- Source PDF: 247 pages
- Chapters: 5
- Sections: 44
- Page PDFs: 247
- Page blocks: 4877
- Semantic units: 425
- Formula candidates: 1494

Semantic units:
- theorem 110
- proof 137
- definition 79
- example 48
- proposition 45
- corollary 6

## Drive location

`Book/01_Textbooks/FunctionalAnalysis2_Structured_V2_2026-08-31`
Folder ID: `1IroInYg8M0yw6FOrsrXiYYDIAA3Kjwcx`

Primary complete artifact:
- `FunctionalAnalysis2_Structured_V2_Complete.zip`
- Drive file ID: `1NblcrHjMGl7fN_vJxAk9IeKRGPCDC-_l`
- SHA-256: `52e30b99419a4a5f5fc7cd36b9febf9ecb2719f0cef95e7bd050dace065af60d`

Source SHA-256:
`dcc04c45d761949290f5a35624b8cdf218520a2ceecace7be0017cf013cd19d1`

## GitHub publication

Target branch:
`data/functional-analysis-jiang-sun-2e-structure-v2-20260831`

Publication scope is documentation + artifact manifest only. Heavy binary artifacts stay in Drive. No default-branch direct write and no automatic merge.

## Next safe step

Convert semantic units into the Book standard knowledge relationship layer (`knowledge point -> definition -> prerequisite -> theorem -> proof -> example -> formula -> exercise`) on a reviewable branch without mutating existing canonical textbook facts.
