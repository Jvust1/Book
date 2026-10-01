# Catalog identity and interrupted navigation

This bounded follow-on to #70 reuses the existing pinned MIT-licensed `zod@4.6.5` engine. It introduces no new dependency, content fixture from a textbook, backend DTO change, catalog ordering change or durable progress write.

## Reproduced failures

Four new UI regressions failed before the repair: Course and Chapter pages retained old catalog content/links while a new route was pending, and retained a prior failure after a successful next route. A Chapter page could assemble an old section ID under a newly navigated course URL. Eighteen API regressions also showed unchecked malformed catalogs or mismatched identities reaching the caller.

## Runtime contract

Library, Course and Chapter reads now use bounded JSON and exact Zod objects. Required labels, IDs, arrays, nonnegative integer metadata counts, unique row identities and physical PDF ranges are checked. Course and Chapter responses bind to the requested identity. The shared SectionCard validator is also reused by the existing Section response validation so physical page rules cannot diverge.

Nullable and absent-content labels, Roman printed-page labels, Unicode IDs, non-READY runtime status, empty catalogs and declared counts that differ from returned row counts remain supported. No sorting, inferred completeness, cross-book remapping or new ID character whitelist is introduced. Browser navigation links encode their ID path segments, matching the existing API path encoding. Independent review reproduced an unpaired-surrogate JSON ID that could throw during encoding; the boundary now rejects non-encodable IDs before rendering, while valid emoji and reserved characters remain accepted. Six negative client regressions cover both surrogate halves on all three link surfaces.

Catalog pages abort their obsolete GET on cleanup. The active request ownership flag also rejects a late result or error from transports that do not honor AbortSignal. Visible data and errors are bound to the route during render, before effects clear state. There are no stale clickable row IDs under a new route, and a successful next navigation does not inherit an earlier error. Browser Back/Forward uses the same owned read path; no catalog result is persisted locally.

## Verification and limits

Focused tests include malformed catalogs, all preserved label forms, empty/partial catalogs, response identities, direct ID encoding, cancellation forwarding, deferred/out-of-order success and failure, and Back/Forward navigation. A local read-only pass through the current real Python BookAppService produced one course, eight chapters and 132 section cards; all were accepted without mutation by the new runtime validators. This checks current DTO compatibility, not full textbook content correctness.

Six added production-browser cases fetch the real original-chapter catalog, corrupt only the returned catalog shape/identity or inject an unpaired-surrogate ID, verify a visible error with no entry links, then recover and navigate using fresh valid responses. They assert no catalog-triggered mutation, browser errors or horizontal overflow. The source-only extracted package includes these cases and their original fixture server. All original reader, receipt and storage journeys remain.

Exact-head hosted browser and clean-source acceptance are required and pending at publication. Current tests are not a claim of Windows/offline packaging, private textbook verification or a production deployment.
