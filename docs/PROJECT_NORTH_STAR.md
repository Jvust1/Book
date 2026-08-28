# Book Project North Star

Updated: 2026-08-28

## Purpose

Book is a long-term personal **Course OS**, not a “PDF + AI chat” wrapper. The product must turn versioned textbooks, course structure, lectures, exam evidence, and personal learning state into one provenance-preserving learning system while keeping Meeting as a separate private domain.

The durable product rule is:

> **App 通用，教材是数据。**

New courses should ultimately enter through a repeatable data/contract pipeline rather than requiring a new App implementation for every book.

## Outcomes that define success

1. A Course can contain a primary textbook plus supplementary, reference, and translation books without merging their original text or provenance.
2. Every textbook fact, page, section, source anchor, version, and derived artifact remains traceable to its source.
3. The same App can provide preview / learn / review / practice, search, QA, StudyRecord, and later richer learning intelligence across courses.
4. AI may connect, explain, rank, and recommend, but must not silently overwrite canonical textbook facts, lecture facts, exam facts, raw sources, or personal evidence.
5. The system is local-first where practical, versioned, deterministic where possible, testable, and recoverable across devices and future model/agent handoffs.
6. Learning and private Meeting data may reuse infrastructure but remain separate authorization and retrieval domains.

## Current strategic stage

The integrated product baseline is Phase 1A–1G. The current engineering stage is **Foundation A: Course Package Contract / Golden Course / Architecture Fitness / CI foundations**.

Foundation A exists to make future course ingestion boring and verifiable:

```text
canonical course + canonical books
→ deterministic Course Package
→ independent validation
→ readiness
→ later registration / consumption
```

Foundation A intentionally does **not** migrate the existing Runtime/App consumer yet and does not pull forward recording, Drive Sync, Meeting, ExamPoint, Unified Retrieval, Mastery, or Android work.

## Golden reference

Stein & Shakarchi, *Functional Analysis* is the Golden Course baseline:

- `course_id = functional_analysis_course`
- `book_id = stein_shakarchi_functional_analysis_2011`
- 8 chapters
- 132 sections
- 1493 search records
- 442 PDF pages
- final printed page 423
- `STRUCTURED_COMPLETE`
- Runtime `READY`

The Golden Course is evidence, not a target to manipulate. Canonical facts must never be changed merely to make a test pass.

## Authority

- GitHub is the authority for code, contracts, project state, governance, decisions, tests, and next step.
- Google Drive is the vault for raw uploads, large/binary artifacts, source snapshots, exports, and backups.
- Chat or model memory is not project authority.
