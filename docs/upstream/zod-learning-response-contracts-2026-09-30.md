# Zod learning-route response contracts

A follow-on to the combined reader candidate (#66), reusing the existing pinned `zod@4.6.5`. This is deeper runtime integration and hardening, not another newly counted upstream project. Official `colinhacks/zod` metadata was checked at 2026-09-30 22:19 UTC: 44,046 stars, MIT. The exact upstream commit, package integrity and complete license are unchanged from the original Zod integration record.

## Reproduced gap

Source, search and QA responses were already validated before rendering, but `getSection` and `getMode` still cast successful JSON directly to TypeScript types. Sixteen new failing tests proved that wrong course/section/mode, malformed page metadata, missing or mismatched source references, duplicate source identities and malformed learning-item shapes were accepted. A same-course mode could also carry a different book identity from the displayed section.

## Runtime path

Both methods now use the real Zod schemas in `app/web/src/api/learningContracts.ts` through the existing streaming JSON reader. The transport enforces JSON content type, strict UTF-8 and a 2 MiB actual-byte budget before parsing. Schemas bound text and arrays, preserve printed Roman labels separately from positive physical PDF pages, validate page-range order, retain valid empty modes, and check request course/section/mode identity. Source-reference pairs must exactly match displayed item pairs and order. Object, figure and translation kinds remain distinct, including when IDs coincide.

SectionPage waits for section identity before showing mode content or touching StudyRecord. It also checks book agreement and guards visible data by the active route and mode, preventing stale content from being displayed while navigation effects run. Existing asynchronous cleanup remains in place. On rejection, the normal Chinese error state is shown and no progress touch occurs; switching to a valid mode recovers through the normal path.

No API endpoint, persisted DTO, source record, study grading rule, package pin or paid service is changed. Schema/context validation is not factual textbook verification or file-edition authentication.

## Checks

- Original negative cases first fail on the previous client; they now reject with the stable `invalid_response` error
- Positive tests retain all four modes, empty review/practice, Roman page labels and same-ID/different-kind sources
- UI tests cover mismatched books, delayed section metadata and an old mode response arriving after newer navigation
- Five production-browser cases cover wrong Section/course, wrong mode/course, wrong mode name, missing source references and mismatched book, including valid-mode recovery and no invalid progress writes
- The earlier full original chapter journey and real PDF.js/Fuse/math.js/SymPy pipeline remain in the suite
- Local target: 287 web tests plus TypeScript; exact-head hosted CI provides production build and all 38 regular + 2 connected-pilot browser cases

Only original synthetic strings are used in the new tests/screenshots. Canonical `books/`, `courses/` and `library/` trees are unchanged. No new audit request is made; `npm ci --no-audit` remains in CI.

The initial hosted browser run passed 35/38 regular cases. The three practice cases shared a synthetic Section fixture with an extra top-level `section_id`, unlike the real API DTO. That fixture was corrected without changing assertions or relaxing the schema; an explicit rejection regression was added. The complete exact-head browser gate must rerun after the correction.
