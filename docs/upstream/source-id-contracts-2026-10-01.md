# Encodable source response identities

This repair branches directly from verified receipt candidate #70. It does not include the separate #71 catalog changes or its pending browser-recovery investigation. It reuses the pinned `zod@4.6.5` MIT implementation, without adding dependencies or changing the existing CI workflows/output.

## Reproduced failure

JSON can legally carry escaped lone UTF-16 surrogates. The shared Source/Search/QA ID validator previously accepted them, while `encodeURIComponent` throws for them. Search-result and QA-citation links could fail while rendering. A Source response with such a section ID could fail when the reader chose its return-to-study button. Source context IDs are currently text-only; their rejection is contract consistency, not a claim that they are clickable today.

Fifteen API and three UI regressions failed before this repair. The UI tests use the real fetch client, Zod boundary, query provider and components with original synthetic JSON; malformed Search and QA IDs reach a render-failure boundary before the repair, and the invalid Source return button remains exposed instead of a validation error. Six positive cases already passed and remain preserved.

## Runtime contract

The existing shared ID schema now checks that an ID is nonblank, within the existing 512-code-unit budget, and encodable. It uses a caught encoding probe solely as validation; the original string is returned unchanged. All existing exact requested course/source/question identities, citation semantics and schema field sets stay intact.

No replacement characters, URL decoding, normalization or silent remapping is introduced. Legitimate Unicode, paired emoji, combining sequences, percent signs and reserved characters are preserved. Existing links perform their usual path-segment encoding. Invalid responses fail closed through the existing API error UI before rendering a link or offering a Source return action. The existing QA session schema also rechecks cached answers, so malformed citation identities do not return through browser-session restoration.

## Verification boundary

Focused tests cover both lone surrogate halves and embedded malformed UTF-16 in Search IDs, QA citation IDs, Source return IDs and text-only context IDs; valid identity preservation; actual Search/QA link navigation and Source return navigation; and malformed versus valid cached QA restoration. Original synthetic fixture content only is used. The existing exact-head full-reader and clean extracted-source gates remain required before delivery. No new public diagnostic output, catalog changes, textbook material, paid API call, merge or deployment is part of this repair.
