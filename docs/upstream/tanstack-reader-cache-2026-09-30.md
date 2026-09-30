# TanStack Query temporary reader cache

## Verified project and pinned code

- Official repository: https://github.com/TanStack/query
- Official GitHub REST recheck: **50,386 stars**, 2026-09-30 21:32 UTC, https://api.github.com/repos/TanStack/query.
- Exact package: **@tanstack/react-query 5.104.0**, with its exact **@tanstack/query-core 5.104.0** dependency.
- Official `@tanstack/react-query@5.104.0` tag: **d4033eb1e5bdef3c8aa72a6cc614bcdd98b1ddca**. npm integrity is retained in the lockfile; no missing npm gitHead is invented.
- Both packages are **MIT**, with their unmodified package LICENSE files retained in `app/web/public/licenses/` and byte-compared locally.
- Inspected official behavior: https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation, https://tanstack.com/query/latest/docs/framework/react/guides/network-mode and https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults.

Actual runtime: App-owned QueryClientProvider → Source/Search useQuery → exact query key → abortable Book API → existing bounded JSON/Zod validation → upstream QueryCache → route-checked display. This replaces the two pages' handwritten fetch lifecycle, and directly uses QueryClient deduplication, freshness, cancellation and inactive garbage collection.

## User-facing gap and behavior

The reader previously refetched on every return and lost readable results during a local API interruption. It now reuses recent, already-validated Source/Search data within the current page lifetime, while keeping source association and stale state explicit.

- Cache keys contain course, operation, source kind/ID or query/limit. Kind/query normalization mirrors the existing backend. No previous-query placeholder data is used.
- Freshness: 30 seconds. Inactive cache lifetime: 60 seconds. Active entries remain while observed. These are application retention settings, not a hard total-memory bound or proof that source facts have not changed.
- Recent read time is displayed. Returning cached content is labeled; a network TypeError can retain clearly labeled possibly stale content.
- **Every API error**, including invalid response, 401/403/404 and server errors, hides cached content. Unknown non-network exceptions also fail closed. Cached data never overrides a schema rejection or a server access decision.
- Explicit refresh is deduplicated while already running. Explicit cancellation targets only the exact source/query. Unmount consumes the upstream AbortSignal and stops the pending fetch; late results cannot revive abandoned data.
- A cancelled initial request has a visible stopped state and an explicit retry. Cancellation during response-body reading remains AbortError instead of becoming an invalid-response error.
- `networkMode: 'always'` avoids treating the browser's internet-connectivity hint as proof that a local API is unavailable. Actual browser/network restrictions still apply normally.
- Automatic retries, focus refetch and reconnect refetch are disabled. QA and StudyRecord mutation paths are not migrated or automatically replayed.
- No persister, hydration, broadcast, global client singleton, localStorage/IndexedDB body cache or service-worker API cache is added. Browser reload creates a new client. Existing search navigation metadata and QA conversation state are unchanged.
- User-selected PDF bytes/indexes are not query-cached. LocalPdfSource identity now includes course/book/kind/source to preserve isolation during cached route transitions.

This is a temporary reader cache, not offline whole-book storage, content-authenticity verification, a new source authority, or a complete library migration.

## Verification

- Local full web suite: **253/253 tests passed**, TypeScript passed; Playwright lists **33 browser cases**.
- Real upstream QueryClient tests cover simultaneous-read deduplication, fresh reuse, key isolation, exact cancellation without cancelling another request, ignored late completion, local reads with online=false, no automatic retry, stale refetch and inactive GC.
- Source UI tests cover labeled interrupted reads, explicit recovery, schema/authorization rejection hiding old content/PDF controls, cancellation and true production-provider unmount. API tests confirm both GET methods forward AbortSignal and preserve a body-read cancellation.
- Four new production-browser cases cover desktop/390px Search→Source→Search cache reuse, interrupted refresh of both read types, retained physical/printed page identity, invalid-response rejection and recovery, no body persistence across reload, server authorization denial and cancelled/late read recovery. They use original synthetic content only.
- Existing page tests now use isolated real QueryClients. Their original source/citation/history assertions remain; Search request assertions additionally check the limit and AbortSignal.
- Exact-head hosted CI checks all regressions, production build and browser execution. Local browser execution is unavailable in the managed environment; large local builds are avoided after shared-memory limits.
- Optional dependency audit remains **not run**; installation and inherited CI use `--no-audit`.

Stacked on Zod PR #64. No canonical textbook changes, private PDF upload, model call, merge, release or deployment is performed. Independent SymPy PR #61 remains separate pending a whole-candidate integration review.
