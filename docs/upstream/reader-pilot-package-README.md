# Book original-chapter source pilot

This is a code-only, original-chapter reader package. It includes the verified reader integrations from Draft PRs #58–#68, full retained upstream notices, exact JavaScript lockfile, a hash-pinned Python API environment and the separate hash-pinned SymPy checker. It excludes canonical `books/`, `courses/`, `library/`, PDFs, user data, credentials, node_modules and generated binaries.

The test-only API creates a wholly original one-chapter repository and SQLite database in a temporary directory. It exercises actual source retrieval, QA evidence/citation checks, PDF.js local viewing, Fuse page search, math.js calculation, Zod validation, TanStack request handling and the isolated SymPy diagnostic. QA generation uses the deterministic test provider; no external model/API key is required. No textbook content or file edition is authenticated by this pilot.

## Start locally

Verified target: Linux x86-64, CPython 3.13 and Node.js 22. This is source delivery, not a Windows installer or a deployed service. The `pilot-api.txt` lock is derived from passing Linux CI, rather than an ambient workstation freeze. Other platforms require their own validation.

From the extracted `book-reader-pilot` directory, create an isolated Python environment and install only the pinned pilot dependencies:

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-extras/pilot-api.txt -r requirements-extras/symbolic.txt
npm --prefix app/web ci --no-audit
python -m unittest app_tests.test_synthetic_chapter tests.test_symbolic_answer tests.test_symbolic_safety -v
npm --prefix app/web run build
python -m uvicorn app_tests.synthetic_pilot_server:create_app --factory --host 127.0.0.1 --port 8000
```

Keep that shell open. In another shell from the same directory:

```sh
cd app/web
npx vite preview --host 127.0.0.1 --port 5173 --strictPort
```

Open http://127.0.0.1:5173 in your own browser. Choose the original course and chapter; try preview, study, review and practice. The source screen can display a PDF you explicitly select, but it stays unverified and local. The browser tests generate their own original two-page PDF automatically.

To run the complete original-chapter and storage-failure browser pilots, activate the same Python environment in a third shell so the test harness can invoke the real SymPy CLI:

```sh
cd app/web
npx playwright install chromium
npm run e2e -- --config playwright.pilot.config.ts
```

The four pilot cases include the connected reader workflow on desktop and narrow screens, blocked sessionStorage and quota exhaustion. The default `npm run e2e` configuration is not a full textbook acceptance suite in this reduced package. No canonical textbook fixtures are included. The test API uses temporary SQLite storage and deletes it on graceful shutdown; it is not a deployment or a permanent study database.

## Verify and reproduce the source archive

The archive contains `pilot-source-manifest.json`. Every entry records the exact source path, mode, byte length and SHA-256. The root README is an explicitly declared byte-identical alias of this document. The manifest identifies the source Git commit but is not a signed publisher attestation.

With the builder available from the repository or extracted package:

```sh
python tools/build_reader_pilot_source.py verify /path/to/book-reader-pilot.tar.gz
python tools/build_reader_pilot_source.py extract /path/to/book-reader-pilot.tar.gz /new/empty/destination
python tools/build_reader_pilot_source.py repack /new/empty/destination --output /new/path/repacked.tar.gz
```

Extraction verifies every member before creating a new destination. It refuses symlinks, traversal, duplicate/unlisted paths, altered source data and trailing archive payload. Repack reads only manifest-listed source files, so subsequently installed dependencies/build outputs are not exported. It rejects changed source files rather than claiming they belong to the original commit.

`build --repository /full/Book/checkout --ref <exact-commit-SHA> --output /new/path/book-reader-pilot.tar.gz` reads immutable Git blobs, ignoring dirty/untracked files. Archive order, metadata and gzip timestamp are deterministic. CI checks byte-identical build/extract/repack using the same Python/zlib toolchain; the per-file manifest also verifies content across platforms. This does not claim bit-identical application binaries on every platform or an offline dependency installer. npm/PyPI downloads are needed for installation; no dependency audit upload is performed.

## Upstream identity and limitations

The seven newly integrated projects are KaTeX, PDF.js, react-markdown, math.js, Fuse.js, Zod and TanStack Query. Their exact package pins, upstream commits and license/notice records are in `app/web/package-lock.json`, `app/web/public/licenses/` and the included `docs/upstream/` records. Existing SymPy safety hardening is separate from the new-project count; its complete BSD core/bundled notices are retained at `docs/upstream/licenses/SymPy-1.14.0-LICENSE.txt`. No new license grant or relicensing of Book's own code is implied.

Calculations are diagnostics, not automatic grades or textbook standard answers. PDF bytes and indexes stay local and are not persisted. Source/search caches and storage-failure recovery are bounded and explicitly temporary. Full textbook correctness, real paid-model quality, private assets, native Windows delivery and production deployment are outside this package's verification.
