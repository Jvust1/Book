# Bounded non-2xx responses

This follow-on to verified #72 is independent of the blocked #71 catalog/diagnostic investigation. It reuses the existing pinned `zod@4.6.5` MIT validator and bounded UTF-8 stream reader; no dependency or CI output is added.

## Reproduced gap

The error branch previously called `response.json()` without a byte limit and accepted any nonblank error message/code. A private in-memory probe of the actual client accepted a 3,145,728-character synthetic HTTP 503 message, larger than the 2 MiB successful validated-response ceiling. Fourteen negative regressions subsequently failed before repair, including displayed-message/code size, incomplete/extra error fields, MIME/UTF-8 integrity, declared/chunked byte limits and cancellation during an error-body read.

## Runtime behavior

- Non-2xx JSON is limited to 64 KiB of actual streamed bytes before parsing; an oversized declared length is rejected before payload consumption
- The shared reader permits a caller only to tighten, never enlarge, the existing 2 MiB ceiling; malformed limits fail closed and cancel the body
- Only the current public Book error envelope `{error: {code, message}}` is accepted; code is at most 128 UTF-16 code units and message at most 1024, both nonblank
- Valid bounded messages, codes and HTTP status are preserved without rewriting or truncation
- Malformed, oversized, non-JSON, invalid UTF-8 and body-I/O failures produce the existing stable Chinese fallback with the original HTTP status and no trusted code
- Caller abort remains AbortError, rather than being reclassified as a server failure
- No body content, exception detail or parser error is logged; there is no automatic mutation/read replay

These limits bound decoding/parsing and displayed error text, not the size of a network chunk allocated by the browser or the duration of a stalled server. They do not introduce a new wall-clock timeout or alter successful catalog contracts; #71 remains separate. A failed mutation still cannot establish whether the server committed, and the verified unconfirmed-save UI remains unchanged.

## Verification

Tests cover complete current Chinese errors, exact string boundaries, incomplete/extra fields, MIME, broken JSON/UTF-8, body I/O, cancellation, Content-Length and chunked ceilings, disallowed expanded caller budgets, a failed POST occurring only once, and the actual SourcePage error/retry path. The reader renders a short fallback rather than the oversized message, then recovers only on an explicit read. Test messages and fixtures are original synthetic data.

Full local tests, TypeScript, archive safety, independent review and exact-head existing hosted reader/source gates are required. No new public diagnostic payload, textbook material, paid API call, main merge or deployment is included.
