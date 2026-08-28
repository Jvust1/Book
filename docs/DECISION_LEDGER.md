# Book Decision Ledger

Updated: 2026-08-28

This ledger records durable decisions and why they exist. It does not replace Git history or phase-specific design specs.

| ID | Status | Decision | Rationale / evidence |
| --- | --- | --- | --- |
| D-001 | ACCEPTED | Book is a Course OS; **App 通用，教材是数据**. | Avoid per-book application forks; make course ingestion a data/contract problem. |
| D-002 | ACCEPTED | A Course may contain `primary / supplementary / reference / translation` books, preserving each Book's original identity and provenance. | Different books/editions must not be merged into a fake single source. |
| D-003 | ACCEPTED | First multi-book version has exactly one enabled `primary`; Concept-level alignment is a later layer. | Keeps a deterministic reading skeleton while preserving future extensibility. |
| D-004 | ACCEPTED | Formal Foundation A contract is `course_package_v1` / package version `1.0.0`; legacy `course_manifest_v1` remains a compatibility input. | Contract-first migration without breaking Phase 1A–1G Runtime/App. |
| D-005 | ACCEPTED | Foundation A compiler/validator treats canonical `books/**` and `courses/**` as read-only and emits generated packages under `.build/`. | Product state or generated outputs must not mutate textbook facts. |
| D-006 | ACCEPTED | Package and content identities are deterministic and independently recomputable using canonical JSON + SHA-256. | Enables idempotency, drift detection, reproducibility, and Golden gates. |
| D-007 | ACCEPTED | Compile, validate, and future register/import are separate stages. Validation is fail-closed and read-only. | Reinforced by source review of Kolibri, H5P, and Open edX; avoids repair-and-trust workflows. |
| D-008 | ACCEPTED | Task 5 validator uses deterministic staged checks: shape/closed fields and secret-like keys → path boundaries → required artifacts/primary role → artifact/content hashes → package identity → structural baseline → readiness. | Source-level comparison found the same verify-before-consume pattern in mature content systems. |
| D-009 | DEFERRED | Generalized content identity distinct from placement identity. | ricecooker demonstrates the value, but Course Package v1 already has sufficient Book/version/content/package identities. Add only when a real cross-course/Concept consumer needs it. |
| D-010 | DEFERRED | External archive bomb/extension/expanded-size defenses. | H5P validates archive transport aggressively, but Foundation A v1 currently materializes a local directory package rather than accepting external ZIP uploads. |
| D-011 | ACCEPTED | External source learning uses fixed upstream commits and licenses, with Drive source snapshots for real source-level study when archival tooling is available. | Required by the all-project GitHub learning and source snapshot rules. |

Detailed Foundation A design authority:
- `docs/superpowers/specs/2026-08-28-foundation-a-course-package-design.md`
- `docs/superpowers/plans/2026-08-28-foundation-a-course-package.md`
- `docs/references/2026-08-28-course-package-open-source-comparison.md`
