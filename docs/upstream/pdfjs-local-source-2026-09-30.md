# PDF.js local source-page reader

## Upstream and implementation identity

- Official repository: https://github.com/mozilla/pdf.js
- Official GitHub REST observation: **53,965 stars**, 2026-09-30 18:30 UTC, https://api.github.com/repos/mozilla/pdf.js
- Exact package: **pdfjs-dist 6.3.289**, locked with npm integrity.
- Official release tag and npm gitHead: **1c8020a7d4e43668ac287a3ecf9a8dbea17e4c56**, `v6.3.289`.
- License: Apache-2.0. The unmodified package license is included in `public/licenses/PDFjs-LICENSE.txt` and the built resource directory. Bundled CMap, ICC, standard-font and WebAssembly asset licenses are copied unchanged with those resources.
- Sources inspected: published `build/pdf.mjs`, `types/src/display/api.d.ts`, `webpack.mjs`, resource layout and the official API/examples at https://mozilla.github.io/pdf.js/api/draft/module-pdfjsLib.html and https://mozilla.github.io/pdf.js/examples/.

The current React/PWA source page had structured source metadata but no original-page viewer. This integrates the actual PDF.js parser, worker, page renderer and text extraction in the source page. It complements the KaTeX reader. It does not replace the independent Windows application's artifact-based implementation.

## Runtime path and user benefit

`SourcePage` → `LocalPdfSource` → `loadLocalPdf` → deferred `pdfjs-dist.getDocument({data})` → `getPage` / `render` / `getTextContent`.

A user selects a local PDF they have the right to use. The viewer goes to the existing canonical **PDF physical page number**, never the printed-page label. It supports previous/next, an explicit page input, return to the source page and zoom. The optional extracted-text view is labeled auxiliary and bounded to 50,000 characters; scanned pages do not pretend to have OCR.

The selected file has **unverified identity**. Filename, page count or successful rendering are not proof of matching textbook, edition or source. This warning remains visible. Missing/out-of-range source page numbers render no replacement page until the user explicitly selects one; manually browsing another page is separately labeled.

## Boundaries and cleanup

- Local file bytes only; no PDF URL, upload, provider, credential, browser persistence or StudyRecord write is introduced.
- Worker, fonts, character maps and decoders are from the exact local dependency, prepared before dev/build and included in static precache. No CDN is configured.
- Files are limited to 100 MiB, canvas output to approximately 8 million pixels and each dimension to 8192; image decode/display budgets are bounded.
- No scripting/HTML annotation/form/link/attachment UI is loaded. XFA is disabled; canvas annotation mode is disabled. The UI explicitly warns that interactive annotations/forms and over-budget images may be omitted, so the preview is not a substitute for the full original.
- A late result from an older file cannot overwrite a newer selection. Close, unmount, source changes and repeated selections cancel/destroy old loaders, render tasks and canvases.
- Canonical source facts, API contracts and server-owned durable study records are unchanged.
- Source PDFs, scans, textbook text and generated user content are not included in this PR. Browser fixtures are a three-page original synthetic PDF generated from code.

## Verification

- Local: 90 web tests pass, including 22 new loader/bounds/lifecycle checks; TypeScript and production build pass.
- Three new real-browser acceptance cases exercise actual PDF.js worker/canvas/text output at desktop and 390px widths, page return, zoom, close/reload, corrupt-file retry and mismatched page counts.
- The browser test checks rendered ink pixels and extracted synthetic text, and asserts no non-GET or off-origin request occurs during local PDF use.
- Exact-head GitHub CI, including the inherited Runtime/App suite and 16 browser cases, is the publication gate. Local Chromium cannot launch in this managed environment, and cloud-browser localhost navigation is blocked; local unit results are not presented as browser evidence.
- Only synthetic preview screenshots are uploaded by the added CI artifact step. No original textbook preview image is published.

No whole-book proofread, mathematical correctness certification, Windows/Android host acceptance or new native executable is implied.
