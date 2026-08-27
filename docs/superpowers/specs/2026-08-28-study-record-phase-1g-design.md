# Phase 1G StudyRecord + Sync-Ready Local Persistence Design

Date: 2026-08-28
Status: proposed for implementation after user review
Branch: `feature/study-record-phase-1g`
Base: `main` @ `8d78b5beea8339f4326749ffebd123d1903f1a2b`

## 1. Goal

Phase 1G adds durable, local-first learning progress without introducing accounts, cloud sync, Drive integration, recording, meeting processing, or background AI automation yet.

The implementation must satisfy these product decisions:

- SQLite is the durable local authority for learning progress.
- The UI remains single-user: no login, account picker, or multi-user screen.
- Every installation/device has a hidden stable `profile_id` so records can later be merged across devices without key collisions.
- Preview, learn, review, and practice are four independent progress tracks.
- Entering a section/mode records activity automatically.
- Completion is explicit: the user manually marks a mode complete.
- The app records the most recently studied Course / Section / mode using `last_studied_at`.
- Existing `sessionStorage` state remains short-lived navigation/return state and is not reused as long-term progress storage.
- The schema is sync-ready, but Phase 1G does not implement Drive sync or a full sync-event engine.

## 2. Architectural boundary

Phase 1G introduces a new durable persistence layer under the existing FastAPI app boundary:

```text
React / TypeScript / Vite PWA
            ↓
       local FastAPI
            ↓
   StudyRecordService
            ↓
   StudyRecordRepository
            ↓
      local SQLite
```

The existing textbook runtime remains read-only and canonical:

```text
LibraryRuntime → CourseRuntime → BookRuntime → SectionLearningRuntime
```

`StudyRecord` never modifies textbook assets, runtime indexes, canonical source data, or QA evidence.

The browser does not write directly to SQLite. All durable progress reads/writes go through FastAPI so the persistence implementation stays portable to a future Android shell and can later be replaced or extended with sync.

## 3. Identity model

### 3.1 Single-user UI

The app has no user-management surface in this phase.

### 3.2 Hidden profile identity

On first durable-store initialization, the backend creates one UUID profile and persists it locally. The stable identity is used internally on every durable record.

Conceptually:

```text
profile_id = UUID
```

The UI does not ask the user to name or select the profile.

This avoids future merge collisions if two people later study the same `course_id + section_id + mode` and exchange/sync records.

### 3.3 No shared `local-default` identity

A constant identity such as `local-default` must not be used as the durable sync identity because two devices would then generate colliding logical records for the same course/section/mode.

## 4. StudyRecord semantics

A logical StudyRecord is unique per:

```text
profile_id + course_id + section_id + mode
```

`book_id` is stored as denormalized canonical context for future import/export validation and diagnostics, but it is not part of the logical uniqueness key because the current course runtime owns the active canonical book.

Supported modes are exactly:

```text
preview
learn
review
practice
```

The four modes are independent. Completing `preview` must not complete or unlock `learn`; completing `learn` must not mutate `review` or `practice`.

## 5. StudyRecord schema

Minimum durable record:

```text
study_record_id        UUID
profile_id             UUID
course_id              TEXT
book_id                TEXT
section_id             TEXT
mode                    TEXT
status                  TEXT      // in_progress | completed
progress                INTEGER   // 0..100; Phase 1G uses in-progress vs complete semantics
started_at              TEXT      // ISO-8601 UTC timestamp
last_studied_at         TEXT      // ISO-8601 UTC timestamp
completed_at            TEXT NULL // set only when completed
created_at              TEXT
updated_at              TEXT
revision                INTEGER   // monotonic per record, starts at 1
deleted_at              TEXT NULL // reserved for future tombstone sync
sync_status              TEXT      // local | pending | synced; Phase 1G writes local/pending semantics only as defined below
```

Database constraints:

- primary key: `study_record_id`
- unique: `(profile_id, course_id, section_id, mode)`
- `mode` must be one of the four supported values
- `status` must be `in_progress` or `completed`
- `progress` must be between 0 and 100
- `revision >= 1`

## 6. Progress rules

Phase 1G intentionally does not infer learning quality from scroll position or time-on-page.

### 6.1 First entry

When the user enters a valid Course / Section / mode for the first time:

```text
status = in_progress
progress = 1
started_at = now
last_studied_at = now
completed_at = null
revision = 1
```

`progress = 1` distinguishes a genuinely started mode from a non-existent/never-started record while avoiding a fake fine-grained percentage.

### 6.2 Re-entry

On later entry to the same logical record:

- update `last_studied_at`
- update `updated_at`
- increment `revision`
- preserve `started_at`
- preserve completed state if already completed

A completed record remains completed when reopened.

### 6.3 Manual completion

When the user presses `标记完成`:

```text
status = completed
progress = 100
completed_at = now
last_studied_at = now
updated_at = now
revision += 1
```

Completion is idempotent: repeated completion calls must not create duplicate rows.

### 6.4 Reopen / mark incomplete

Phase 1G does not add an explicit `mark incomplete` action. If needed later, it should be introduced as a deliberate product action rather than inferred from navigation.

## 7. Recent learning

The most recent learning location is determined from the current profile's non-deleted StudyRecords ordered by:

```text
last_studied_at DESC
```

The returned recent-learning object includes at least:

```text
course_id
book_id
section_id
mode
status
progress
last_studied_at
```

This supports a future Home / Course resume button without depending on browser session state.

## 8. SQLite location and portability

The database path must be owned by a persistence-path helper rather than hard-coded into page or service logic.

Requirements:

- writable per-installation application-data location
- no dependency on the current working directory
- deterministic override for tests
- path abstraction suitable for a future Android application-data directory

The exact Android packaging mechanism is outside Phase 1G, but the backend storage layer must not assume Windows-only absolute paths.

## 9. Repository and service boundaries

### 9.1 `StudyRecordRepository`

Owns SQLite schema creation and persistence operations only.

Expected capabilities:

```text
get_profile_id()
get_record(course_id, section_id, mode)
touch_record(course_id, book_id, section_id, mode)
complete_record(course_id, book_id, section_id, mode)
list_course_records(course_id)
get_recent_record()
```

Repository methods must use parameterized SQL and explicit transactions.

### 9.2 `StudyRecordService`

Owns application validation and canonical identity checks.

Before creating/updating a StudyRecord, the service validates through the existing runtime that:

- `course_id` exists
- `section_id` exists in that course
- canonical `book_id` is obtained from the runtime, not trusted from browser input
- mode is valid

The browser must not be able to create arbitrary course/book/section identities that do not exist in the current runtime.

## 10. API contract

Phase 1G should expose a small explicit API rather than letting SectionPage manipulate persistence details.

Recommended routes:

```text
POST /api/courses/{course_id}/sections/{section_id}/study/{mode}/touch
POST /api/courses/{course_id}/sections/{section_id}/study/{mode}/complete
GET  /api/courses/{course_id}/study-records
GET  /api/study/recent
```

The browser sends no `profile_id` and no `book_id`; both are server-owned.

A StudyRecord response should expose useful product fields but may keep sync-internal fields such as `sync_status` private until sync is implemented.

## 11. Web behavior

### 11.1 Entering a mode

Once SectionPage has a valid section and its mode content successfully resolves, it calls the touch endpoint for the active mode.

A failed progress-write must not make textbook content unavailable. The page continues to render and shows a non-blocking progress persistence error/retry affordance if necessary.

### 11.2 Completion control

SectionPage shows an explicit completion control for the current mode:

```text
标记完成
```

After successful completion it shows completed state instead of issuing repeated writes.

### 11.3 Four-mode status

The four mode tabs may show compact progress state, but Phase 1G does not add rich dashboards or mastery calculations.

### 11.4 sessionStorage separation

Current state modules such as `sectionViewState`, `searchViewState`, and `qaSessionState` keep their present navigation responsibility.

They must not become the backing store for StudyRecord.

## 12. Sync-ready fields versus sync implementation

Phase 1G reserves enough metadata to avoid a migration dead-end:

```text
profile_id
study_record_id
revision
updated_at
deleted_at
sync_status
```

However, Phase 1G does **not** implement:

- Google Drive authentication
- upload/download manifests
- `SyncEvent`
- `SyncEngine`
- multi-device conflict resolution
- cloud API
- background sync

A later sync phase can translate durable record changes into globally unique incremental events.

## 13. Future incremental sync model

The future model is event/increment based, not shared-SQLite synchronization.

Conceptually:

```text
local SQLite mutation
        ↓
unique SyncEvent
        ↓
small incremental sync bundle
        ↓
Drive / Sync API
        ↓
remote device applies unseen event_id once
```

Large files such as audio remain files; sync events contain identity, metadata, hash, revision, and path/reference information rather than embedding the file bytes.

This section is a compatibility constraint only; no event tables are required in Phase 1G.

## 14. Long-term recording architecture constraints

The following future architecture is recorded now so Phase 1G does not block it.

### 14.1 Shared infrastructure

Future Learning and Meeting recording domains may share:

```text
Audio capture
VAD / ASR
local SQLite
profile_id
Drive transfer
processing queue
AI refinement pipeline
```

### 14.2 Learning domain

Learning recordings remain linked to Course / Book / Section and may later be shared according to course-sharing rules.

Teacher material and textbook material remain separate authorities:

```text
Textbook fact layer
Lecture fact layer
Derived / AI fusion layer
```

AI may identify a missing definition, theorem, proof, formula, example, or exam point in a lecture and retrieve canonical textbook evidence to supplement the learning view, but must never rewrite teacher speech as if the teacher said the textbook supplement.

### 14.3 Meeting domain

Meeting is a business domain independent of Course / Book / Section.

Meeting data is private by default and is never included in shared-learning synchronization to a friend.

Future Meeting structures may include:

```text
Meeting
MeetingTranscriptSegment
MeetingEvent
Decision
ActionItem
Deadline
FollowUp
```

### 14.4 Raw recordings

Raw recordings are retained permanently by product decision.

Future derived layers remain separate:

```text
raw_audio
raw_transcript
local_refined
ai_refined
```

No derived transcript overwrites the immutable raw source.

### 14.5 Nightly refinement workflow

The initial future workflow is manually triggered by the owner, not automated:

```text
new recording
→ local first-pass processing
→ Drive pending_ai
→ owner manually asks ChatGPT to process today's pending recordings
→ Learning and private Meeting refined separately
→ processed output written back
→ apps sync results
```

This workflow is explicitly outside Phase 1G implementation.

## 15. Privacy and sharing decisions

- Learning data can later participate in owner/friend synchronization.
- Meeting data is private.
- Personal StudyRecord sharing is not required for the first sync implementation unless explicitly enabled later.
- Raw recording files are not encrypted by the app in the current product decision; privacy therefore depends on access control in the eventual storage/sync layer.
- No cloud/Drive credentials may be embedded into browser JavaScript or APK-visible static configuration.

## 16. Error handling

Phase 1G must fail safely:

- invalid course/section/mode → 4xx, no database mutation
- SQLite write failure → explicit API failure, textbook reading remains usable
- duplicate touch/complete → idempotent logical result
- corrupt local profile identity → fail clearly rather than silently creating multiple identities in one store
- schema initialization must be deterministic and testable

## 17. Testing and acceptance

### Runtime / repository tests

Must cover:

- first-run profile UUID creation and stability
- SQLite schema initialization
- first touch creates one record
- repeated touch updates one record, not duplicates
- completion sets 100/completed
- reopening completed record preserves completion
- four modes remain independent
- two sections remain independent
- different profile IDs can coexist without collision in repository-level fixtures
- recent record ordering
- revision increments
- invalid constraints fail

### App/API tests

Must cover:

- canonical course/section validation
- browser cannot choose profile/book identity
- touch endpoint
- complete endpoint
- course record list
- recent record endpoint
- deterministic API error shapes

### Web tests

Must cover:

- entering a valid mode performs touch
- completion button updates UI
- changing modes creates/updates independent records
- persistence error does not hide textbook content
- existing source/search/QA session restoration remains unchanged

### Browser acceptance

Using the real Functional Analysis canonical course:

1. open a Section in `preview`
2. confirm progress begins
3. switch to `learn`
4. confirm independent progress
5. mark `learn` complete
6. reload/restart the web client against the same API store
7. confirm completion is still present
8. confirm recent-learning points to the last touched mode
9. confirm source navigation/return behavior still works
10. confirm 390×844 has no horizontal overflow regression

## 18. Non-goals for Phase 1G

Do not implement in this phase:

- account/login system
- user-facing profile management
- Google Drive sync
- GitHub data sync
- SyncEvent / SyncEngine
- recording UI
- VAD / ASR
- Lecture processing
- Meeting UI or meeting storage
- ChatGPT nightly processing
- cloud AI processing
- import/export UI
- mastery scoring
- time-based or scroll-based learning percentages
- automatic unlock dependencies between modes

## 19. Documentation changes expected at completion

When implementation is complete:

- mark Phase 1G complete in `docs/ROADMAP.md`
- update `docs/DATA_MODEL.md` with the concrete durable StudyRecord/profile/sync-ready semantics
- update `app/README.md` with local database location/configuration and durability behavior
- describe the distinction between session navigation state and durable StudyRecord
- leave future Recording / Meeting / Drive Sync phases explicitly unimplemented

## 20. Definition of done

Phase 1G is done only when:

- a fresh installation creates one stable hidden profile UUID
- the four learning modes persist independently in SQLite
- opening a mode records activity
- manual completion survives reload/restart
- recent learning can be queried durably
- browser session state remains separate
- canonical textbook assets are unchanged
- sync-ready fields are present without prematurely implementing sync
- full runtime/app/web/browser regression gates pass
