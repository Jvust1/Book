# Android Recorder MVP Design

Date: 2026-08-30
Status: USER-APPROVED APPROACH / WRITTEN SPEC FOR REVIEW
Repository: `Jvust2/Book`
Base: `main@2675d2cecab63b28b6ab81a4554e9b7f010afd72`
Design branch: `design/android-recorder-mvp-20260830`

## 1. Objective

Deliver the fastest useful Android recording companion for Book as an installable APK without coupling the work to unfinished Phase 1H or waiting for a full native rewrite of the Course OS.

The MVP must be able to record a real lecture reliably while the screen is locked or the app is backgrounded, preserve the original audio locally, list and play prior recordings, attach lightweight course/section metadata, rename the displayed recording title, and share/export the original recording file.

The first APK is intentionally recording-first. ASR transcription, AI summaries, Lecture authority, Drive sync, and full Book Android learning UI remain follow-up stages and must not block the first installable recorder.

## 2. Product boundary

The Android recorder is a new isolated subsystem under:

```text
android-recorder/
```

It does not replace or embed the current FastAPI + React Book App. It does not modify canonical textbook data, Search/QA behavior, StudyRecord schema, Course Package contracts, or Phase 1H code.

The first version is a local-only companion:

```text
Microphone
  -> foreground recording service
  -> original M4A/AAC file
  -> local recording metadata
  -> recording library
  -> playback / rename / share
```

Future integration is additive:

```text
original audio
  -> ASR transcript (derived)
  -> Lecture record (derived/linked)
  -> course/section association
  -> AI summary / key points (derived)
```

Original audio remains source evidence and is never overwritten by transcript or AI-derived content.

## 3. Technical baseline

- Language: Kotlin.
- Build: Gradle wrapper, Android Gradle Plugin 8.7.3, Gradle 8.9, JDK 17.
- `compileSdk = 35`.
- `targetSdk = 35`.
- `minSdk = 26` so native `MediaRecorder.pause()` / `resume()` is always available.
- Application ID: `com.jvust.book.recorder`.
- Version: `0.1.0`, versionCode `1`.
- UI: lightweight native Android Views, no WebView and no Compose dependency for MVP.
- Audio: `MediaRecorder`, source `MIC`, output format `MPEG_4`, encoder `AAC`, mono, 44.1 kHz, 128 kbps.
- Playback: platform `MediaPlayer`.
- Metadata: app-private JSON index using platform `org.json`; no database dependency for v0.1.0.
- Share/export: `androidx.core.content.FileProvider` with read-only URI grants.
- No INTERNET permission in v0.1.0.

## 4. Android permissions and foreground execution

Manifest permissions:

```text
android.permission.RECORD_AUDIO
android.permission.FOREGROUND_SERVICE
android.permission.FOREGROUND_SERVICE_MICROPHONE
android.permission.POST_NOTIFICATIONS
```

`RecorderForegroundService` declares:

```text
android:foregroundServiceType="microphone"
```

Recording may only start from a visible Activity after microphone permission is granted. On Android 13+, notification permission is requested but denial must not corrupt recording state. The service immediately calls `startForeground(...)` after a valid start command.

Foreground notification shows recording state and elapsed duration. It exposes safe actions for pause/resume and stop. Locking the device or leaving the Activity must not stop an active recording.

## 5. Storage model

### 5.1 Audio files

Original audio is stored under app-specific external storage:

```text
getExternalFilesDir(Environment.DIRECTORY_MUSIC)/book-recordings/
```

Physical filenames are immutable and generated once:

```text
REC_yyyyMMdd_HHmmss_<short-id>.m4a
```

Renaming in the UI changes metadata title only; it does not rename the physical evidence file in v0.1.0.

No broad storage permission is required.

### 5.2 Metadata

Internal app files contain one atomic JSON index:

```text
files/recordings-index-v1.json
```

Each record contains:

```json
{
  "recording_id": "stable-uuid",
  "file_name": "REC_20260830_183000_ab12cd.m4a",
  "display_title": "高等数学第 3 讲",
  "created_at_epoch_ms": 0,
  "duration_ms": 0,
  "size_bytes": 0,
  "course_ref": "",
  "section_ref": "",
  "note": "",
  "status": "complete"
}
```

`recording_id` is stable and independent from the display title.

Index writes are atomic: write a temporary file, fsync/close, then replace the active index. Startup reconciliation scans the recordings directory and keeps readable audio even when metadata is missing; an orphan file is surfaced with a generated fallback title instead of being deleted.

## 6. Recorder state machine

Stable states:

```text
IDLE
RECORDING
PAUSED
STOPPING
ERROR
```

Allowed transitions:

```text
IDLE -> RECORDING
RECORDING -> PAUSED
PAUSED -> RECORDING
RECORDING -> STOPPING -> IDLE
PAUSED -> STOPPING -> IDLE
RECORDING/PAUSED -> ERROR -> IDLE after cleanup
```

Invalid commands are ignored safely and must never create a second simultaneous `MediaRecorder`.

A recording session records monotonic timing from `SystemClock.elapsedRealtime()`. Pause duration is excluded from final elapsed duration.

When stop succeeds, metadata is finalized with duration and size. If recorder finalization throws, the app preserves the file if it contains readable non-zero bytes and marks metadata `status = "recovered"`; otherwise it reports a failure without pretending the recording was saved.

## 7. Main screen

The first screen contains:

- large Start recording button when idle;
- active timer while recording/paused;
- Pause/Resume button;
- Stop button;
- optional editable metadata fields: display title, course reference, section reference, note;
- clear state label: Recording / Paused / Idle / Error;
- recording library below the control area.

The MVP does not require login, server configuration, textbook download, or network connectivity.

## 8. Recording library

Each saved recording shows:

- display title;
- date/time;
- duration;
- file size;
- optional course/section labels;
- Play/Pause playback action;
- Rename display title action;
- Edit course/section/note action;
- Share original `.m4a` action.

Deletion is intentionally excluded from the first Agent-built MVP because project governance treats deletion as destructive. Users may manage app data manually outside the Agent workflow if needed; a future product deletion UX requires a separate explicit design and safety treatment.

Only one recording may play at a time. Starting playback of a second recording stops the first.

## 9. Reliability requirements

The APK is not considered usable unless all of these hold:

1. Lock screen/background does not stop a normal active recording while the foreground service remains alive.
2. Rotation or Activity recreation does not create a second recorder.
3. App UI can reconnect to current service/session state.
4. Pause/resume does not create a new file.
5. Stop finalizes exactly one metadata entry.
6. Repeated Start presses cannot create simultaneous recorders.
7. App restart reconciles existing `.m4a` files instead of losing them from the library.
8. Permission denial returns to a visible idle/error state and never claims recording started.
9. Share uses content URI + read grant, not `file://`.
10. No audio/transcript is sent over network in v0.1.0.

## 10. Privacy and provenance

- Original recordings are local-only in v0.1.0.
- No INTERNET permission.
- No analytics SDK.
- No hidden upload.
- No transcript or AI-generated text is presented as original lecture evidence.
- Any future transcript must retain a stable link to `recording_id` and be labeled derived.
- Any future AI summary must retain the transcript/audio provenance chain and never overwrite the original audio.

## 11. Out of scope for first APK

The following are explicitly deferred:

- ASR / Whisper transcription;
- AI summary, key-point extraction, chapter generation;
- Lecture authority schema in the main Book Runtime;
- Drive sync or multi-device sync;
- user accounts;
- Android-native textbook reading/search/QA;
- recording waveform editing;
- silence trimming;
- noise reduction;
- per-recording tags beyond title/course/section/note;
- automatic physical-file rename;
- destructive delete UI;
- release signing / Play Store publication.

## 12. Build and APK delivery

The repository will add a dedicated Android CI workflow scoped to `android-recorder/**` and its workflow file.

Required CI commands:

```bash
./gradlew :app:testDebugUnitTest
./gradlew :app:lintDebug
./gradlew :app:assembleDebug
```

The workflow uploads:

```text
android-recorder/app/build/outputs/apk/debug/app-debug.apk
```

as artifact:

```text
book-recorder-debug-apk
```

The first delivery is an installable debug APK. Release signing is a later stage because private signing keys must not be committed to GitHub.

## 13. Test strategy

Pure Kotlin/JVM tests cover:

- recorder state transition policy;
- elapsed-duration math across pauses;
- generated physical filenames;
- metadata JSON round-trip;
- index reconciliation rules for orphan files;
- display-title rename preserving physical filename and stable recording ID.

Android build/lint verifies manifest service declarations, FileProvider resources, API compatibility, and resource correctness.

Manual acceptance on a real phone for the first APK:

1. grant microphone permission;
2. record at least 60 seconds;
3. lock screen for part of the recording;
4. pause and resume once;
5. stop;
6. play the result;
7. restart the app and verify the recording remains listed;
8. rename title and verify the original file still plays;
9. share the `.m4a` through Android Sharesheet.

## 14. Branch and integration policy

Implementation continues on this separate Android branch lineage and must not modify the active Phase 1H branch.

No direct write to `main` is allowed. The Android implementation will be proposed through its own reviewable PR. The PR is not merged without explicit PR-specific merge authorization.

The existing Phase 1H PR #26 remains independent and unmodified by Android Recorder MVP work.

## 15. Completion definition

The MVP is ready for user APK delivery when one exact branch HEAD simultaneously has:

- successful JVM unit tests;
- successful Android lint;
- successful `assembleDebug`;
- a GitHub Actions artifact containing the debug APK;
- no diff under canonical `books/**` or `courses/**`;
- no Phase 1H product-code modification;
- no network permission or upload path;
- no known blocker preventing start/pause/resume/stop/library/play/rename/edit/share;
- a downloadable APK artifact linked back to the exact build HEAD.
