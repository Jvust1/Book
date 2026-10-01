# Windows clean-extraction acceptance target

This candidate adds a separate hosted Windows check to the verified original-reader stack. The Linux source workflow and its acceptance assertions are unchanged. No user computer is operated and no Windows installer, SDK, signing credential or new runtime dependency is introduced.

## Existing components and pins

The Python API lock was checked against official PyPI JSON for all 17 exact releases under a Windows x86-64 / CPython 3.13 environment. Every active non-extra requirement is satisfied by an existing pin, and the applicable universal or Windows wheel hashes are already in the lock. In particular, Click 8.5.0 has no runtime dependency and minimal Uvicorn 0.54.0 only adds the already-pinned Click/h11 requirements on Python 3.13. No assumed Colorama dependency was added. The existing SymPy/mpmath hash lock and npm lock remain unchanged.

The portable browser configuration reuses installed `@playwright/test@1.62.1` and its documented multi-webServer startup, readiness and owned-process teardown. Both commands are fixed: the original test-only FastAPI factory and the built Vite preview. Their working directories are resolved from the configuration file, not concatenated into shell commands. Existing listeners are never adopted. Raw server stdout/stderr is not forwarded or uploaded. This is existing Apache-2.0 Playwright tooling, not another new SDK or project-count claim.

Sources: [Click release metadata](https://pypi.org/pypi/click/8.5.0/json), [Uvicorn release metadata](https://pypi.org/pypi/uvicorn/0.54.0/json), [Playwright server lifecycle](https://playwright.dev/docs/test-webserver), [Windows filename rules](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file).

## Gate

The new workflow checks out the exact head with read-only repository permissions, then builds, verifies, extracts and repacks the code-only archive. Extraction deliberately uses a temporary Windows path containing spaces. Archive source bytes and POSIX mode metadata remain bound by the manifest; directory repack already uses recorded modes, not Windows filesystem mode emulation. All pre-existing safety tests still run, with additional portable-path and alias cases. Twenty-one path/collision regression subcases first failed locally. The archive now rejects Windows reserved devices (including case/extensions and superscript COM/LPT digits), alternate-stream/drive syntax, invalid/control characters, trailing dots/spaces, and nonportable components. A conservative casefold inventory check rejects ambiguous file/directory spellings and file/directory conflicts before extraction, or before opening source files during repack. Names are never silently changed. Legitimate Unicode/spaces and the current source inventory retain their exact spelling. No Windows long-path system setting is changed. The portable config is optional for legacy v1 archives but explicitly required by this Windows gate. A regression rebuilds/verifies an old exact Git ref without that file after a newer ref adds it; the actual unchanged #74 archive was also checked locally with the new verifier.

Only the extracted directory is used for hash-locked Python installation, import-origin checks, original-fixture Python tests, npm ci --no-audit, web tests, typecheck, production build and Chromium. No canonical books/courses/library, .git or .env is present there. Python UTF-8 I/O is explicit; PowerShell invokes npm.cmd without changing execution policy. Existing pins are used; no license agreement is accepted by this workflow.

Playwright starts and tears down its own two local servers and runs the same five serial original chapter/storage/receipt journeys. Dependencies require network during setup; reader fixtures, PDF selection/search, deterministic QA, SQLite, math.js and symbolic diagnostics use original local data and no paid provider. A source/checksum artifact and original screenshots are uploaded only after all Windows gates pass. No raw response/DOM/server diagnostics are added, and the separate #71 investigation is excluded.

## Meaning of a result

A successful exact-head Windows job verifies source reproduction and headless Chromium behavior on that hosted Windows image. It is not acceptance of a native installer, the user's device, every font, display scaling or a full textbook. Windows process teardown may be forceful; only ephemeral original test data is involved. Per-toolchain build/extract/repack equality is checked, without claiming all zlib/platform combinations emit identical compressed bytes.
