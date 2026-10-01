# JSZip local QA evidence export

## Qualified upstream and retained identity

- Official repository: https://github.com/Stuk/jszip
- Official GitHub REST recheck: **10,386 stars**, 2026-10-01 03:19 UTC, https://api.github.com/repos/Stuk/jszip.
- Exact npm package: **jszip 3.10.1**, registry artifact `https://registry.npmjs.org/jszip/-/jszip-3.10.1.tgz`.
- Lock integrity: `sha512-xXDvecyTpGLrqFrvkrUSoxxfJI5AH7U8zxxtVclpsUtMCq4JQ290LY8AW5c7Ggnr/Y/oK+bQMbqK2qmtk3pN4g==`.
- Official v3.10.1 release commit: **0f2f1e4d0509514417db83fe5b86bde90e0ffe8d**. Development HEAD's version is not used as a release.
- License choice: **MIT**, expressly allowed by the upstream `(MIT OR GPL-3.0-or-later)` dual license. GitHub aggregate identification is NOASSERTION; the complete unchanged `LICENSE.markdown`, including both choices and notices, is retained as `app/web/public/licenses/JSZip-LICENSE.txt`. Its SHA-256 is `566c953c6090b1218ca6217dd7359d45dde46581968586dc607d59a78af6a9c4` and matches the installed exact package.
- Inspected actual implementation: [release lib/object.js](https://github.com/Stuk/jszip/blob/0f2f1e4d0509514417db83fe5b86bde90e0ffe8d/lib/object.js), particularly `file` and `generateAsync`; [release license](https://github.com/Stuk/jszip/blob/0f2f1e4d0509514417db83fe5b86bde90e0ffe8d/LICENSE.markdown).

This is the eighth newly adopted reader project after KaTeX, PDF.js, react-markdown, math.js, Fuse.js, Zod and TanStack Query. Existing SymPy and Playwright remain separate reuse/hardening, not extra new-library counts.

## User-visible execution

The reader previously had no local evidence-export control for a completed QA turn. The explicit export button now connects one completed assistant turn and its exact preceding question to `buildQAEvidenceZip` → strict QA/context checks → real `new JSZip().file(...)` → `generateAsync(...)` → a locally owned Blob URL and browser download.

The static ZIP members are `README.txt`, `question.txt`, `answer.txt` and `qa-response.json`. They preserve the exact question, answer and structured citation identities already in that turn. No source filename or model-authored path becomes an archive member. README explains that citation locators do not establish a textbook edition, source truth or mathematical correctness.

The export does not additionally read or package textbook/PDF files. A question or answer may itself contain quotations; this feature does not certify that its text is independent of source material. It is not a whole-book export, study-progress backup, automatic grade, signed provenance certificate or supported import format.

## Runtime boundaries

- No automatic export, upload, provider call, source/PDF read, StudyRecord mutation or ZIP import is added.
- Only completed generated answers are eligible, with exact course/book/question/content binding and the existing strict source-bearing schema. Pending work and abandoned asynchronous generations cannot trigger a download.
- UTF-8 payload bytes are counted before ZIP generation, with a 1 MiB contents budget, structural budgets and rejection of ill-formed UTF-16. No silent character replacement is used to make an invalid string exportable.
- Fixed member names, explicit dates and STORE compression avoid filename injection and compression work. ZIP container overhead is additional to the contents budget; this is not an OS memory sandbox.
- Double clicks share one current operation; a new route/turn/unmount invalidates an old generation. Owned object URLs are revoked. The UI says the file was handed to the browser, without claiming the user completed saving it.
- No new key, model/weight download, canonical textbook mutation or #71 catalog/diagnostic change is included.

Focused tests and original-fixture browser download/round-trip checks must run on the final combined candidate. Package installation uses `--no-audit`; no current vulnerability-audit result is claimed. Exact-head launcher acceptance must also include this new browser journey before delivery is called complete.
