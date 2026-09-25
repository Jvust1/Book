# Book Android 0.1.3

Package: `com.jvust.book.app`; versionCode: `4`; Android 7.0+; ARM64 and x86_64.
Development branch: `build/book-app-android-apk-20260913`; review PR: [#29](https://github.com/Jvust2/Book/pull/29).

## Result

Textbook content, search results, sources and answers now render safe Markdown and LaTeX with bundled KaTeX fonts. Formula fields support common delimiters and preserve grouped exponents in the existing source notation. Unsupported syntax retains its original text. Long equations scroll within their own container.

The interface uses a consistent paper/green palette, course artwork, responsive cards, accessible controls and a mobile bottom navigation bar. An active recording remains visible when navigating to other app pages.

Android recordings use an explicit, visible foreground microphone service. AudioRecord writes 16 kHz mono PCM16 WAV files into private storage, updating headers and syncing while recording. Pause/resume, lock-screen/background capture, notification controls, playback/seeking/speed, search, rename, reversible archive, SAF export, sharing and recovery of interrupted audio are implemented. Browser recordings use MediaRecorder with IndexedDB checkpoints. Existing IndexedDB audio survives the upgrade and can also use Android's system export window.

## Fixes

- Recording continues across internal page navigation; native service survives activity backgrounding.
- Paused time is excluded; rapid pause/resume discards stale microphone reads.
- Completed IndexedDB transactions determine save success; failed saves retain audio for retry/export.
- Empty recordings return to a usable idle state.
- Denied microphone permission remains visible despite native status polling.
- Exports retain the actual audio extension and are serialized to avoid overlapping transfer sessions.
- Audio object URLs are released when recording cards unmount or change.

## Validation and limits

Validation commands are in [the Android README](../android-app/README.md). The release manifest records source commit, artifact SHA-256 and per-suite results. Typecheck and 98 Vitest tests passed; Android compile/lint passed (0 errors, 4 warnings); 7 existing app smoke stages and 4 browser acceptance stages passed. Native recording coverage includes 9 core stages plus 2 permission/notification stages. Acceptance exercises the actual debug APK in an Android 15 x86_64 emulator, including permission refusal/retry, notification actions, force-stop recovery and exported legacy audio byte length. Browser checks use synthetic audio in Windows Chrome and inspect widths 320, 390, 768 and 1440.

This is a debug-signed sideload build. Physical ARM64 microphone quality, manufacturer battery restrictions, Bluetooth input and actual phone-call interruptions have not been verified. Browser background behavior is subject to browser policies. Audio is not automatically transcribed or uploaded; users can export it for their own ChatGPT workflow. No new model/API is configured. Canonical textbook data, exact search behavior and StudyRecord semantics remain unchanged.

The original 0.1.1/0.1.2 deliverables remain historical files. This version supplies a separately verified source ZIP; a previously found 0.1.2 manifest described an empty source ZIP and must not be used as source-recovery evidence.
