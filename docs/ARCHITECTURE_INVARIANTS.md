# Book Architecture Invariants

Updated: 2026-08-28

These invariants are cross-phase constraints. A feature that requires breaking one must first create an explicit versioned decision and migration plan.

## A. Authority and provenance

1. **Repository evidence outranks conversational recollection.** GitHub is the authority for code, governance, current project state, contracts, and next step.
2. Drive stores raw/binary/large artifacts and snapshots; important Drive artifacts must be traceable through stable IDs and, where available, cryptographic hashes.
3. Canonical textbook facts, source anchors, page identity, and historical versions are not silently fabricated or overwritten by AI-derived output.
4. Raw sources and historical/frozen evidence are preserved. Derived or refined revisions never masquerade as the original source.

## B. Course and book identity

5. Course is the product-level learning unit.
6. Book roles are `primary / supplementary / reference / translation`.
7. Each Book keeps independent `book_id`, `logical_book_id`, `book_version_id`, page map, sections, objects, and source anchors.
8. Different editions or translations do not overwrite prior versions.
9. In the first multi-book model, exactly one enabled `primary` book supplies the Course chapter/section reading skeleton. Cross-book unification happens later at the Concept layer.

## C. Runtime and storage boundaries

10. The browser never becomes canonical storage authority and does not directly own SQLite identity or owner secrets.
11. StudyRecord records learning activity; it is not equivalent to Mastery.
12. Learning and Meeting are separate business/privacy domains even if they reuse storage, ASR, sync, or processing infrastructure.
13. Long-lived secrets, owner Drive credentials, API keys, or tokens are never embedded in browser/APP static assets or Course Packages.

## D. Foundation A Course Package

14. `books/**` and `courses/**` are canonical read inputs for the Foundation A compiler/validator. Foundation A must not write readiness, hashes, source maps, or generated package data back into canonical books.
15. Generated Course Packages live outside canonical content, under `.build/course-packages/...`.
16. Package paths are repository/package-relative; absolute paths and repository escapes fail closed.
17. Package/artifact identities are deterministic and independently recomputable. Timestamps, randomness, temp paths, and machine-specific absolute paths do not participate in identity.
18. Required artifact hashes are verified against bytes, not trusted because a manifest claims them.
19. Exactly one enabled `primary` book is required.
20. Compile, validate, and future register/import are separate responsibilities. Validation is read-only and never repairs the package or canonical source in place.
21. A stored `PASS` cannot override independently discovered validator failures.
22. Foundation A preserves the current Phase 1A–1G Runtime/API/App behavior; package-driven Runtime migration is a later explicit step.

## E. Quality gates

23. Functional Analysis is the Golden Course. Its canonical identity/source facts are protected regression evidence.
24. Architecture fitness checks must remain executable, not merely prose.
25. CI is layered: FAST for targeted contract/architecture checks, PR FULL for integrated Runtime/App/Golden regression, HEAVY for expensive canonical rebuild/release checks.
26. Stage completion claims require evidence from the exact final HEAD.

## F. External learning

27. Third-party repositories are `BACKUP_OR_REFERENCE`, never project authority and never writable merely because they were studied.
28. Source-level conclusions must record exact upstream commit and license and be adapted, not mechanically copied.
29. When a third-party project enters real source-level study, the exact studied source snapshot is archived to Drive when the approved archival path is available; old snapshots remain provenance and are not overwritten.
