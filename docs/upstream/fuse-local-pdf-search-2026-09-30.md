# Fuse.js local PDF page retrieval

## Verified upstream and actual execution

- Official project: https://github.com/krisk/Fuse
- Official GitHub REST observation: **20,496 stars**, rechecked 2026-09-30 20:18 UTC via https://api.github.com/repos/krisk/Fuse.
- Exact npm dependency: **fuse.js 7.5.0**. The lockfile retains registry integrity `sha512-sQtrEfA+ez/3G0cCZecF70oqpCRttCexYUG4mUrtWL49ULUzUyxokt5kyqwtKzj1270RaKih+hcP3qLcumccow==`.
- Official `v7.5.0` annotated tag peels to **45bac9fe2e71fe8c680c861a35a8b226c4ae6d5a**. npm gitHead is its documentation-version follow-up **457fe762c6418357896d78311f7def8c937a64f8**; both identities are recorded rather than treating them as equal.
- License: **Apache-2.0**. The exact package LICENSE is preserved in `app/web/public/licenses/Fuse.js-LICENSE.txt`; its copyright notice and generated source banners remain intact. The package contains no separate NOTICE file.
- Inspected actual upstream `FuseWorker` implementation and official guidance: https://www.fusejs.io/web-workers.html and https://www.fusejs.io/fuzzy-search.html.

Runtime path: SourcePage → selected local PDF.js document → explicit bounded `streamTextContent` extraction → upstream **FuseWorker.search** with a local emitted worker asset → original-page/offset validation → inert snippets and physical-page navigation. This reuses upstream matching and worker management directly, not a new matching algorithm. Unit tests use the same real Fuse engine; browser tests require a real emitted Fuse worker and a misspelled query absent from the source text.

## Gap and user-visible behavior

The PDF viewer could navigate pages but could not find a passage across a local page range. The new panel adds explicit range extraction, typo-tolerant text search, matched snippets and page jump. It does not alter canonical Search, QA retrieval ranking, citations, source anchors, textbook facts or StudyRecord.

- No automatic indexing on file selection. Default range is at most the first 20 physical PDF pages; the user can choose another range of at most 50 pages.
- Index scope and actual processed end page are displayed. Empty pages and truncation are explicit; no-match does not imply absence from the whole book.
- Text limits are 20,000 characters per page and 250,000 total. Extraction stops consuming the text stream at the limit; some oversized PDF parser work can already have occurred in the existing PDF.js worker.
- Thirty-second extraction timeout, five-second search timeout, Cancel/Clear controls, stale-result guards and unmount cleanup. A search uses one fresh upstream worker, terminated on every terminal outcome. Extraction cancellation stops stream consumption; closing the file destroys the viewer document. These are application budgets, not a hard browser memory sandbox.
- Query length is 2–64 characters; matching uses threshold 0.3 with location/field-length bias disabled. Extended search is disabled. Scores are never represented as source confidence or answer correctness.
- Returned page identity, original text, refIndex and bounded match offsets are checked before navigation. Display snippets are derived from the original local index, escaped by React, with a maximum of ten matched pages.
- Search results remain explicitly unverified-file matches, not textbook citations or answers. Physical PDF and printed textbook page labels remain separate.
- No PDF/index/query/result upload, provider call or durable browser storage. Closing/replacing the local file removes its index. The previous document is cleared synchronously when another filename is selected.
- Image-only scans are not OCR'd; math extraction, line order and reading order can be incomplete. No full-book verification is claimed.

## Verification and boundaries

- Local **188/188 web tests** and TypeScript pass, including extraction, real-engine matching, provenance, worker lifecycle, UI state and inherited reader coverage. Exact-head production CI is checked after publication.
- Negative tests cover invalid ranges, per-page/total budgets, pre-cancelled and stalled operations, late PDF responses, forged page/text/offset results, duplicate pages, timeout, clear/unmount and malicious-looking plain text.
- Four real-browser cases cover desktop/390px input→extraction→typo match→correct physical page, unchanged canonical labels, no unexpected network requests or storage writes, no-match/range recovery, close/reopen/clear/reload, and interrupted worker startup followed by successful retry.
- Synthetic PDFs contain only original test text. No canonical textbook content or private PDF is added or uploaded.
- Production build and browser acceptance run in exact-head GitHub CI. Local Chromium execution is unavailable in this managed environment; large local build reruns are avoided after shared-memory limits were observed.
- Optional dependency audit was not run. CI installs use `npm ci --no-audit`; no audit result from an earlier branch is inherited. All tests, type checks, build and browser gates remain enabled.

This review branch is stacked on math.js Practice PR #62. It does not include the independent SymPy safety PR #61, publish a native release, merge or deploy.
