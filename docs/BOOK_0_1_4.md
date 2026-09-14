# Book 0.1.4

Book 0.1.4 packages the existing Functional Analysis study app for Android and Windows and adds manual study-progress transfer between devices.

## Deliverables

- Android debug APK, versionCode 5, with native foreground recording and Android system file pickers for sync import/export.
- Windows x64 desktop executable. Desktop microphone capture remains disabled; use Android for recording.
- `/sync` page for exporting and importing `book_study_sync_v1` JSON packages.
- LaTeX/Markdown rendering and responsive visual design remain included from the 0.1.3 release.

## Sync behavior

Only study progress records are transferred. Recordings, textbook files, profile identity and model/API settings are excluded. Imports validate course, book, section, mode, status, progress and timezone-aware timestamps. Records with the newer `updated_at` value win, and importing the same package again is safe.

See [manual sync instructions](MANUAL_PROGRESS_SYNC.md).

## Verification

- Python API tests: 111 passed.
- Web tests: 20 files, 100 tests passed.
- Android build and lint: passed with 0 errors.
- Android emulator smoke: 8 suites passed, including API sync and system pickers.
- Windows packaged `--self-test`: exit code 0.

The desktop Playwright sync smoke script is checked in as `desktop-app/smoke_sync.cjs`; this machine does not have the Playwright Chromium binary installed, so that browser-only check is not claimed as passed.
