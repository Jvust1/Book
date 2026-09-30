# Zod source-bearing response contracts

## Exact upstream reuse

- Official repository: https://github.com/colinhacks/zod
- Official GitHub REST observation: **44,047 stars**, rechecked 2026-09-30 20:49 UTC via https://api.github.com/repos/colinhacks/zod.
- Pinned package: **zod 4.6.5**, official `v4.6.5` tag commit **59bbc03e10c636b9eb3c393dfeb552819774ec21**.
- npm integrity: `sha512-v5l/aFXZQeai4awLbOpSoHecE9UiMrnfx75tEXLjNonXVARxQ5mOeipTjROUchszUNCqnE+hqAMujRsRHsut2Q==`, retained in the lockfile. npm did not supply a gitHead; none is invented.
- **MIT** license, unmodified package LICENSE retained as `app/web/public/licenses/Zod-LICENSE.txt`.
- Official API references: https://zod.dev/basics and https://zod.dev/api. Runtime uses actual Zod strict objects, discriminated unions, numeric/string/array validation and cross-field refinement.

The previous successful-response path performed a TypeScript cast, with no runtime check. A new regression test was first run against that implementation: a 200 Source response with a different source_id incorrectly resolved. The same test passes after this integration.

## Runtime path and scope

HTTP Search / QA / Source response → bounded streamed UTF-8 JSON → Zod parse → request-context comparison → page state and source links. Cached QA responses use the same Zod contract instead of a separate handwritten response validator.

- Source course/kind/source ID must match the requested route. Existing object, figure and translation kinds are supported; requested kind normalization mirrors the backend resolver. Search course/query must match; count, sequential ranks, unique source identities and requested limit are checked.
- QA course/question/requested scope must match. Section-scoped citations must identify that section. Generated answers require nonblank text, an answer style and citations; insufficient-evidence notices require no answer/citations and an explicit message. Evidence IDs must be unique.
- Frozen response shapes reject unknown fields rather than silently stripping possible future/private payloads. PDF pages are positive integers; printed labels can remain integers, Roman numerals or other strings. Text, formulas, anchors and identifiers are not coerced, normalized or rewritten.
- Source-bearing responses accept `application/json`, decode UTF-8 strictly, and count actual streamed bytes before parsing, up to **2 MiB**. Declared oversize and unexpected content types cancel the body immediately. Existing network request timing is unchanged; this is not a new server timeout or hard memory sandbox.
- Invalid payloads produce the stable `invalid_response` API error. No raw payload, Zod issue details or parser message is exposed in the UI.
- Restored assistant content must equal the validated answer/notice and belong to its course. Existing frozen session keys remain unchanged.
- A different QA course gets a separate component instance; a delayed response from an unmounted course cannot append or persist an answer. Source/search render guards also reject stale route/query state before a replacement request completes.

This validates structure and request association. It **does not authenticate textbook facts, verify a PDF edition, expand citation authority, replace the backend EvidenceGate, or claim all books are verified**. Library/Chapter/Section/StudyRecord payloads are outside this batch's schema scope.

## Verification

- Local **237/237 web tests** and TypeScript pass. Playwright lists all **29 browser cases**. Exact-head hosted CI verifies the production build and executes the full browser suite after publication.
- Negative coverage includes wrong course/source/query/question, uncited generated answers, contradictory notice states, malformed scope, duplicate identities, wrong page types/ranks/counts, extra fields, malformed JSON/UTF-8, body-size limits and cancelled bodies.
- Session and page tests cover wrong-course restoration, changed display text, malformed cached citations and a delayed old-course answer after navigation.
- Four browser cases use only original synthetic fixtures: malformed QA → retry → verified source round trip at desktop/390px; wrong-source rejection and reload recovery; wrong-course Search rejection and new-query recovery.
- Two inherited synthetic source fixtures previously spread Mode/Citation-only fields into a Source DTO. They now construct the actual frozen Source shape. All original formula, citation, navigation, safety and history assertions remain intact. The old API transport fixture now supplies a real synthetic citation instead of an internally inconsistent uncited generated answer; rejection of that invalid shape is tested explicitly.
- Dependency audit remains **not run**, with inherited CI `--no-audit`. No paid model calls, private asset uploads or canonical textbook edits are introduced.

Stacked on local PDF search PR #63. Independent SymPy safety PR #61 remains separate. No merge, release or deployment is performed.

### Acceptance correction

The initial browser run passed 26/29 cases. Three new assertions incorrectly compared an entire alert (including its existing heading) with just the error message. They now assert both the exact heading and exact error paragraph, retaining all rejection and recovery checks. Compatibility review also preserved existing translation routes and backend-normalized kind inputs, with explicit regression tests.
