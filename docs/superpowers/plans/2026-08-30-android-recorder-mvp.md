# Android Recorder MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an installable Android debug APK that records lectures reliably in the foreground service, preserves local M4A audio, and supports library playback, metadata editing, rename, and share.

**Architecture:** Add a fully isolated `android-recorder/` Android application. Pure Kotlin domain classes own recorder state, timing, naming, and metadata rules; Android service/activity classes adapt those rules to `MediaRecorder`, `MediaPlayer`, app-private storage, and `FileProvider`. A dedicated GitHub Actions workflow builds and uploads the exact-head APK artifact.

**Tech Stack:** Kotlin, Android Views, AGP 8.7.3, Gradle 8.9, JDK 17, compile/target SDK 35, min SDK 26, MediaRecorder, MediaPlayer, org.json, AndroidX core/appcompat.

**Spec:** `docs/superpowers/specs/2026-08-30-android-recorder-mvp-design.md`

## Global Constraints

- All implementation stays under `android-recorder/**` plus one scoped `.github/workflows/android-recorder.yml` workflow and project status docs if needed.
- Do not modify canonical `books/**`, `courses/**`, Phase 1H product code, Search/QA, StudyRecord schema, or Course Package contracts.
- No INTERNET permission, analytics, hidden upload, ASR, or AI processing in v0.1.0.
- Original `.m4a` files are immutable source evidence; title rename changes metadata only.
- No delete UI.
- Physical audio format: MPEG-4/AAC, mono, 44.1 kHz, 128 kbps.
- Recording uses a microphone foreground service and survives normal Activity recreation/backgrounding.
- Debug APK only; no private signing keys in GitHub.
- Development occurs only on non-default branches and through reviewable PRs; no automatic PR merge.

---

### Task 1: Android build skeleton and CI RED gate

**Files:**
- Create: `android-recorder/settings.gradle.kts`
- Create: `android-recorder/build.gradle.kts`
- Create: `android-recorder/gradle.properties`
- Create: `android-recorder/app/build.gradle.kts`
- Create: `android-recorder/app/src/main/AndroidManifest.xml`
- Create: `.github/workflows/android-recorder.yml`
- Test: CI `:app:testDebugUnitTest`, `:app:lintDebug`, `:app:assembleDebug`

**Interfaces:**
- Produces Android application ID `com.jvust.book.recorder` and module `:app`.
- Workflow uses Gradle 8.9 through `gradle/actions/setup-gradle` and Java 17.

- [ ] **Step 1: Add the build and workflow skeleton with a test source set that references not-yet-existing recorder domain classes.**
- [ ] **Step 2: Push and verify the workflow fails for the expected missing domain types rather than infrastructure errors.**
- [ ] **Step 3: Keep CI scoped to `android-recorder/**`, its workflow file, and manual dispatch.**

### Task 2: Pure Kotlin recorder domain GREEN

**Files:**
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/domain/RecorderState.kt`
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/domain/RecorderStateMachine.kt`
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/domain/RecordingClock.kt`
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/domain/RecordingFileNamer.kt`
- Test: `android-recorder/app/src/test/java/com/jvust/book/recorder/domain/RecorderDomainTest.kt`

**Interfaces:**
- `enum class RecorderState { IDLE, RECORDING, PAUSED, STOPPING, ERROR }`
- `RecorderStateMachine.apply(Command): RecorderState`
- `RecordingClock.start(nowMs)`, `pause(nowMs)`, `resume(nowMs)`, `elapsed(nowMs): Long`
- `RecordingFileNamer.create(now: Instant, shortId: String): String`

- [ ] **Step 1: Write tests for valid/invalid state transitions, duplicate Start rejection, and stop from recording/paused.**
- [ ] **Step 2: Write tests for elapsed time excluding paused intervals.**
- [ ] **Step 3: Write deterministic filename tests.**
- [ ] **Step 4: Run RED and confirm failures name missing domain behavior.**
- [ ] **Step 5: Implement the minimal pure Kotlin classes and run tests GREEN.**

### Task 3: Metadata index and reconciliation

**Files:**
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/data/RecordingMetadata.kt`
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/data/RecordingIndex.kt`
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/data/RecordingRepository.kt`
- Test: `android-recorder/app/src/test/java/com/jvust/book/recorder/data/RecordingRepositoryTest.kt`

**Interfaces:**
- `RecordingMetadata` carries stable `recordingId`, immutable `fileName`, mutable display metadata, duration, size, status.
- `RecordingIndex.encode/decode` is JSON-v1 compatible.
- `RecordingRepository` performs atomic index writes and orphan-file reconciliation without deletion.

- [ ] **Step 1: Test JSON round-trip and stable ID/file name through title edit.**
- [ ] **Step 2: Test orphan `.m4a` reconciliation produces a fallback metadata row and never removes the file.**
- [ ] **Step 3: Verify RED.**
- [ ] **Step 4: Implement minimal metadata/index/repository code.**
- [ ] **Step 5: Verify GREEN.**

### Task 4: Foreground recording service

**Files:**
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/service/RecorderForegroundService.kt`
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/service/RecorderServiceContract.kt`
- Create: `android-recorder/app/src/main/res/drawable/ic_mic.xml`
- Create: `android-recorder/app/src/main/res/values/strings.xml`
- Create: `android-recorder/app/src/main/res/xml/file_paths.xml`
- Modify: `android-recorder/app/src/main/AndroidManifest.xml`
- Test: JVM tests extend command/state policy; Android lint/build validate manifest and FileProvider.

**Interfaces:**
- Intent actions: `START`, `PAUSE`, `RESUME`, `STOP`.
- Binder snapshot exposes state, elapsed duration, current recording ID/title.
- Service owns exactly one `MediaRecorder` and calls `startForeground` immediately after a valid start.

- [ ] **Step 1: Add contract tests for command mapping and invalid duplicate start behavior.**
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement MediaRecorder configure/start/pause/resume/stop and notification actions.**
- [ ] **Step 4: Finalize metadata exactly once after successful stop; preserve readable non-zero file as `recovered` on finalization failure.**
- [ ] **Step 5: Run unit tests, lint, and assemble.**

### Task 5: Main UI, library, playback, metadata edit, share

**Files:**
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/MainActivity.kt`
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/ui/RecordingAdapter.kt`
- Create: `android-recorder/app/src/main/java/com/jvust/book/recorder/ui/PlaybackController.kt`
- Create: `android-recorder/app/src/main/res/layout/activity_main.xml`
- Create: `android-recorder/app/src/main/res/layout/item_recording.xml`
- Create: `android-recorder/app/src/main/res/values/themes.xml`
- Modify: `android-recorder/app/src/main/AndroidManifest.xml`
- Test: `android-recorder/app/src/test/java/com/jvust/book/recorder/ui/PlaybackSelectionTest.kt`

**Interfaces:**
- Activity binds to service to render live state and sends commands only after permissions pass.
- Adapter callbacks: play/pause, rename, edit metadata, share.
- `PlaybackController` guarantees one active `MediaPlayer`.

- [ ] **Step 1: Test single-selection playback policy and metadata-only rename behavior.**
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement simple recording controls and permission flow.**
- [ ] **Step 4: Implement recording list, edit dialogs, playback, and FileProvider share.**
- [ ] **Step 5: Verify unit tests, lint, and assemble GREEN.**

### Task 6: Exact-head APK build, scope audit, and PR

**Files:**
- Modify only if needed: `.github/workflows/android-recorder.yml`
- Create/update: Android recorder README/status note if needed.

**Interfaces:**
- Workflow artifact name: `book-recorder-debug-apk`.
- Artifact source: `android-recorder/app/build/outputs/apk/debug/app-debug.apk`.

- [ ] **Step 1: Run exact-head CI for unit tests, lint, and assembleDebug.**
- [ ] **Step 2: Verify workflow artifact contains the APK.**
- [ ] **Step 3: Compare branch with `main` and confirm no diff under `books/**`, `courses/**`, or Phase 1H product code.**
- [ ] **Step 4: Create a dedicated reviewable Android Recorder PR without merging it.**
- [ ] **Step 5: Download the exact-head workflow artifact and provide the APK to the user.**
