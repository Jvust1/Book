# Encodable learning identities and actual return links

This independent follow-on to verified #73 reuses the existing `zod@4.6.5` MIT guard introduced for Source/Search/QA in #72. It excludes #71 catalog changes, recovery cases and diagnostic output. The guard is factored into one small shared response-ID module; no new dependency or public DTO field is introduced.

## Reproduced user path

A Mode reply could contain a lone-surrogate item ID and an identically malformed source_ref. Both passed the previous Mode schema, then LearningObjectCard rendered SourceLink, whose path encoding threw. A Section reply could also contain a malformed chapter return identity. Separately, a valid Unicode/reserved chapter ID was placed into the return link without path-segment encoding.

Before the repair, ten API and five negative UI regressions failed, as did the legitimate encoded-chapter navigation case. Four existing positive cases passed. The negative UI cases exercise the actual fetch client, SectionPage, all four learning modes and LearningObjectCard/SourceLink inside a test render boundary. An invalid Mode item must not create a source link; an invalid Section must not create a chapter return link. Both must produce the existing validation state without a study touch.

## Runtime change

Section and Mode IDs now use the same input-preserving encodability schema as Source/Search/QA: nonblank, at most 512 UTF-16 code units, and no lone surrogate that makes encodeURIComponent throw. Section back links now encode their course/chapter path segments, matching the existing source and QA links. Legitimate Unicode, paired emoji, combining sequences, percent signs and reserved characters remain unchanged as identities.

Existing course/section/mode/book binding, ordered source_refs, source kinds, nullable chapter IDs, page metadata and progress semantics remain. No normalization, replacement character, guessed identity or automatic mutation is introduced. The browser still cannot submit book/profile IDs.

Restored expanded/active source IDs are view hints, not link constructors. The regression explicitly restores malformed/unknown hints beside a legitimate ID, then verifies that the sole link comes from the validated current Mode item and navigates with that exact ID. This is not a claim that all legacy view-state fields or return routes have been redesigned or sanitized; their wire shapes remain unchanged.

## Verification limits

Focused API/jsdom tests reproduce malformed IDs, all four modes, Section return validation, actual valid source/chapter navigation and restored hint isolation. The existing exact-head full-reader and five original chapter/storage/receipt browser journeys remain required; these new negative cases are not claimed as additional real-browser coverage. Source-only packaging retains original synthetic fixtures. No textbook/private asset, payload logging, #71 inclusion, paid API, merge or deployment is added.
