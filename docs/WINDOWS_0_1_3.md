# Book Windows 0.1.3

Windows x64 desktop delivery for the Book learning app. The EXE packages the local FastAPI runtime, React/KaTeX frontend and the canonical Functional Analysis content into one file; Python and Node.js are not required on the target computer.

## Desktop behavior

- Reading, search, source navigation, LaTeX rendering and StudyRecord behavior match the Android 0.1.3 source.
- The desktop build does not request microphone permission and disables the recording action. Record on Android, then export audio for the ChatGPT workflow.
- Data is kept offline. The bundled textbook content is the same release as Android, while StudyRecord databases remain device-local. Automatic progress synchronization needs an authenticated sync service and is intentionally not enabled in this no-API release.
- WebView2 Runtime is required. The app listens only on `127.0.0.1:17866` and stores its profile and database under `%LOCALAPPDATA%\BookApp`.

## Build and verification

Run `desktop-app/build.ps1` from the repository root. The resulting file is `dist/Book-0.1.3-Windows-x64.exe`.

Verified on Windows 10/11 environment:

- TypeScript typecheck: PASS
- Vitest: 98 tests across 19 files PASS
- Vite desktop production build: PASS
- PyInstaller single-file packaging: PASS
- Packaged `--self-test`: PASS (title, bundled page, MediaRecorder/IndexedDB capability detection and local API health)

This is an unsigned sideload executable. Physical device microphone testing belongs to the Android build; no desktop microphone access is expected.
