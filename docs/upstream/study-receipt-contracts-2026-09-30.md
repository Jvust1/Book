# StudyRecord receipt integrity

A bounded frontend follow-on to the coherent reader candidate #69. It reuses pinned `zod@4.6.5`; no new dependency, wire DTO, SQLite schema, grading behavior or book-version migration is introduced. `app/study/repository.py` and the older #35 timezone/import work are untouched.

## Reproduced gap and contract

Seventeen regression cases first showed the client accepting mismatched course/section/mode, inconsistent completion fields, malformed timestamps, hidden internal fields and duplicate logical records. Successful StudyRecord responses previously used an unchecked TypeScript cast. SectionPage also accepted a response for another book, and its failure notice said progress was not saved even though an invalid/lost reply cannot establish whether SQLite committed.

The existing Phase 1G contract remains authoritative: server-side SQLite; hidden profile identity; course + section + mode logical uniqueness; in-progress/0 versus completed/100; explicit completion; completed touches do not downgrade; repeated completion is idempotent. The browser cannot supply a book/profile identity in the mutation request.

## Runtime changes

- Touch, completion, course-record lists and recent-record responses now use real Zod validation through the bounded 2 MiB JSON reader
- Receipts bind to requested course/section/mode; SectionPage additionally binds them to its verified book identity before displaying progress
- Status, 0/100 value and nullable/completed timestamp must agree; timestamp strings must be aware ISO datetimes, without rewriting offsets or inferring wall-clock ordering
- The exact public DTO is retained; internal profile/revision/sync fields are rejected rather than displayed or persisted
- A rejected or interrupted receipt says the save result is unconfirmed. Any prior valid record is labeled as the last confirmed state, including while a mutation is pending
- No mutation is replayed automatically. Existing explicit retry and reload paths remain; no client-side rollback or assumed “not saved” claim is made

A malformed receipt does **not** mean no server write occurred. This repair protects what the reader claims, not a distributed rollback guarantee. Durable progress never moves into browser storage.

## Verification

Focused client/UI tests cover all four modes, valid empty recent state, aware offset preservation, wrong course/section/mode/book, malformed/inconsistent receipts, hidden fields, duplicate list identities, no automatic replay and explicit retry recovery.

The added browser case uses the real original-chapter API/SQLite repository. It permits the completion to commit, alters only the returned course ID, verifies an unconfirmed UI and one completion request, reads the actual completed record, then reloads and recovers that same completion from SQLite. Original review/preview modes provide fresh test state; no real user database is touched.

Pilot cases now run serially because they share one temporary SQLite profile. This prevents the new mutation test from changing the whole-record snapshot used by the scratchpad no-progress-write test. Existing assertions and cases remain. Restart the temporary API between complete manual browser runs to reset original test progress.

The full source-package workflow also exercises the receipt case from a clean, code-only extraction. All new content remains original synthetic data; canonical books/courses/library and the already-delivered #69 archive stay unchanged. Exact-head hosted CI is required before considering this follow-on verified.
