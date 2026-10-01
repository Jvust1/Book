# One-command original reader launcher

This is a usability bridge over existing pinned Uvicorn, Vite and the original fixture, not an additional newly adopted upstream. It follows verified QA candidate #77 (`c008045c9db4b161dc5e455283849eb94e367ebd`). No #71 catalog or diagnostics are included.

## User path

With CPython 3.13.x and Node 22.20+ within major 22 installed, run `python tools/run_reader_pilot.py --setup` from the extracted package. Explicit setup creates a project-local `.venv`, uses only existing exact hash-locked Python packages and `npm ci --no-audit --no-fund`, builds the current frontend, then launches. Later, `python tools/run_reader_pilot.py` starts it without automatically installing or rebuilding anything. The source path may contain spaces, and execution does not require shell activation.

The launcher prints a local URL only after checking its original API identity and the built page/proxy. The user opens that URL and can use the established original reader journeys and local QA evidence export. Ctrl+C stops the owned processes. `--check` verifies startup and cleans up instead of waiting interactively; it may be combined with explicit `--setup`.

## Boundaries

- Actual child commands are the project venv Python running only `app_tests.synthetic_pilot_server:create_app` and installed Node running the local Vite preview. There is no default canonical app, reload server, arbitrary target, remote URL or shell command argument.
- Python/Node are prerequisites, not downloaded runtimes. The stricter Node lower bound comes from the existing lock's engine requirements; dependency pins are unchanged.
- Ordinary launch performs no dependency installation, model call, browser installation/opening, paid action, firewall change or PowerShell policy bypass. Explicit setup needs registry network access.
- Binding is fixed to loopback ports 8000 and 5173. Occupied ports fail before startup; existing listeners are never adopted or terminated.
- API data and temporary paths are overridden with a parent-owned temporary root. This also isolates the existing review-schedule repository, whose dependency otherwise follows the normal application data path. Only the launcher's own temporary directory is removed, after its children stop.
- Runtime subprocesses have owned process groups; Windows job ownership covers the venv redirector and descendants. Graceful interruption is attempted before bounded owned-tree cleanup. Failed cleanup is an error, not a ready/success claim.
- The sample uses an original one-chapter fixture and deterministic generation. Progress and review data are temporary; this is not a user's textbook library, native installer, production deployment, full-book acceptance or persistent study installation.

## Acceptance design

Mock-only unit checks cover prerequisite/argv/setup and lifecycle boundaries. These do not constitute host acceptance.

The dedicated exact-head workflow extracts only allowlisted source into a path containing spaces, executes the real `--setup --check`, then `tools/verify_reader_pilot_launcher.py`. The verifier starts the ordinary launcher from a different spaced directory; confirms original API, built frontend and proxy; proves a second launcher cannot adopt/kill it; exercises review repository isolation with an invalid original request; and runs all original browser pilots, including the new QA ZIP export against these actual servers. It then signals the owning launcher, checks ports and temporary data are cleared, verifies immediate restart, and checks each occupied port preserves an unrelated sentinel listener.

Hosted Linux tests send SIGINT; hosted Windows tests send CTRL_BREAK_EVENT. The Windows signal path is not a literal physical Ctrl+C keypress claim. Browser testing uses the already pinned Playwright/Chromium only in CI; ordinary launcher setup does not download the browser. No new public response-body/process-dump diagnostics or private assets are emitted.

Exact candidate Windows and Linux results must be recorded separately after execution. A previous green #77 source package does not establish this launcher's acceptance.
