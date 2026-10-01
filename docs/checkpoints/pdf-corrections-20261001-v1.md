# Book PDF correction checkpoint — 2026-10-01 v1

Local repair QA passed. Global Book release acceptance remains incomplete.

Drive deliverables: https://drive.google.com/drive/folders/17bUbKi_wR5anBIBmsDJGkq0IcpUGenrv

| Artifact | Repair | SHA-256 |
|---|---|---|
| [泛函分析_12px_公式整体与编号修正版_v1.pdf](https://drive.google.com/file/d/1e8HuPpKOt8vESCn7d94LdReV8ghAZenr/view?usp=drivesdk) | 12px functional analysis: 41 intact equations on pages 152–158; original character counts preserved. | `c5b8a7488e5e72ff4980c94e3fc6c0e4b1595cc6cb8d5cd0c34a1dccd0944bfe` |
| [金融经济学十讲_12px_第五讲原页校勘修正版_v1.pdf](https://drive.google.com/file/d/1H9nGRW_UK_nLnOWuAY6rDYl8XEqNAYhM/view?usp=drivesdk) | 12px financial economics: source-verified prose and math on page 75; lower validated equations preserved. | `6f01a283130dd0ad9e6745e6eeb00dd386bbf0a398906fe8ecded8045eac6529` |
| [金融经济学十讲_15px_原页校勘修正版_v1.pdf](https://drive.google.com/file/d/1xVrRmG5A9yjAeO6cB9mBDsSpGPklKXRG/view?usp=drivesdk) | 15px financial economics: source-verified corrections on pages 75, 139, 276, 334. | `0cc4dbaa0aef8d4bde073b99d1ad8cc4f9665e934b3ea74ea8b8cc619837395b` |
| [公共财政概论_12px_页眉字体编码修正版_v1.pdf](https://drive.google.com/file/d/1SePLFppRuENcleNqC43djjzwbAbSztU1/view?usp=drivesdk) | 12px public finance: corrected embedded CFF CID charset; all 287 pages retain identical body pixels and extracted text. | `cab8d2c150362a13e592c629f9ac0d790db6deea7d07510e2cd010954d0edbc4` |
| [数学物理方程_第四版_学习_全书_15px清爽版_图题重复修正版_v1.pdf](https://drive.google.com/file/d/1OvXJGTKJWCzinAggxLje9LBMck8ML8Rq/view?usp=drivesdk) | 15px mathematical physics: reuse of existing 6 duplicate-caption repair; no further edits. | `c508c2ddfa55969bb7291bb470b72b5d0a1e53338627532a841efe8bbdb62980` |

Unmodified-page text and pixel comparisons passed: functional analysis 302 pages, financial economics 12px 148 pages, financial economics 15px 330 pages. Page geometry and page counts remain identical to each input. Public-finance body pixels y=50..800 pt remain identical across all 287 pages. Detailed QA, original hashes, and visual contacts are in the Drive version folder.

Pending release gates: genuine Shu Song font file and mapping; six-book fixed A4 reflow at 10/12/15px; per-chapter/per-mode common-source alignment; complete proofreading of machine-draft OCR (financial-economics pages 74, 76, 140, 275, 277, 333 remain visibly defective); Windows reader checks. The newly located six-book LaTeX archive is a raw r3 reading transcription, not a verified common source for all preview/review/practice outputs.

Originals and all learning modes retained. No existing artifact or main-branch file was overwritten. Source page matches used for financial economics: scan PDF 129–130 for 12px page 75; PDF 45, 106, 204–205, 251 for 15px repairs. Functional-analysis equations match v3 review PDF pages 28–33 by mathematical content; prior incorrect scan-page mapping was not used.

Requested Luna/highest model selection is unavailable in this execution environment; this checkpoint was not run with that requested configuration.
