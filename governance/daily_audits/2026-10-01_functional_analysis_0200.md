# Functional Analysis audit 2026-10-01

Scope: Jiang/Sun 2e only. Main unchanged. Baseline main: 805510f86546709b6f67c9e9079943f205c2c245.

Confirmed derived metadata corrections: 3 issue groups, 7 fields. Source pages visually rechecked: 39, 138, 146, 214, 215, 219. Source scan and raw OCR remain unchanged.

Derived V2.1 ZIP SHA-256: f09e991bfd3c4d3e896765334d1468c4db9cfdc318724ee081ea0e3086ec5950.

Confirmed layout finding: current 15px preview/learn/review/practice PDFs use about 892.91 x 1262.83 pt page boxes, about 1.5x A4 in each dimension, affecting 487 pages. This violates the recorded A4-page invariant. Existing binaries were not destructively cropped/rescaled because that would either clip content or shrink the 11.25pt body back to about 7.5pt. Source reflow is required.

QA: v4 combined (309 pages) and v5 learning (198 pages) are A4. Current 15px set has zero blank pages, replacement characters and NUL; Poppler sampling found no clipping, black blocks, overlap or broken glyphs. No new confirmed math/formula error found.

Pending: independent expert sign-off for 110 reference-solution units.

Drive audit folder created: 1PqnecCTsNl58EarDM9gk2zoA2auxgMdE. Binary upload is still pending because the container-to-Library upload bridge returned container_session_expired.
