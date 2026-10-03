# Session view storage recovery

Reliability follow-on to the combined reader and Zod boundary work (#66–#67). Existing upstream versions/licenses remain unchanged; this adds no dependency or new-project count.

## Reproduced failure

QA, search and section state loaders accessed `sessionStorage.getItem()` before their error handler. Browser privacy restrictions could therefore throw `SecurityError` during rendering. A quota error from a write could also interrupt question submission or source navigation. A new integration regression first reproduced the uncaught read error.

## Runtime behavior

The three existing state modules now use `sessionViewStorage` without changing their persisted JSON shape or validation. Healthy browsers keep the existing sessionStorage behavior. If storage access fails, the app switches to a bounded page-memory cache for the remainder of that app instance. The shared accessible warning explicitly states that only recent return positions and QA are temporarily retained, and that refresh/close loses them.

The adapter allows only the existing `book:qa-session:`, `book:search-view:` and `book:section-view:` key families. StudyRecord remains on the existing server-side SQLite path; PDF bytes/indexes and structured search result bodies never enter this adapter. QA cache reads still pass the Zod-backed shape/context and question/ID validation before display.

Memory retains at most 64 entries and 4,194,304 UTF-16 code units total, with a per-entry ceiling of 2,097,152 code units. Oldest unused entries are evicted. Oversized values are discarded rather than partially parsed or silently truncated. Healthy reads observe external sessionStorage clearing. Once degraded, reads do not fall back to older disk snapshots; newer memory writes attempt to remove the older stored value. Failed removals cannot resurrect it within the running app. If the browser denies deletion, no claim is made that an old disk value was deleted across a future reload.

This fallback does not enable blocked browser storage, request new permissions, persist elsewhere or send data externally. Reload creates a new empty memory cache. It is a recoverable reading/session aid, not durable progress storage or unlimited conversation retention.

## Verification

- Adapter tests: healthy round trips, denied getter/read/write/removal, quota failure, stale-snapshot suppression, entry/aggregate limits, LRU eviction, oversized data, key allowlist and deferred warning notification
- Integration test: QA/Search/Section view state remains usable when browser storage operations throw
- React test: the live warning appears while the normal learning interface remains available
- Two new production-browser journeys use the original file-backed chapter/API and deterministic provider without HTTP mocks: storage entirely blocked and quota exhausted. Each asks once, follows the validated citation to source, returns to the same answer from memory without another provider call, then reloads and confirms the memory-only conversation is gone
- Existing 38 regular browser cases and both connected chapter journeys remain in place, for 38 + 4 cases after this change

The exact-head hosted browser gate remains required. Local Chromium startup is unavailable in this sandbox; no bypass is attempted. New screenshots contain only the original chapter fixture. No canonical textbook content, paid-model call, audit transmission, merge or deployment is added.
