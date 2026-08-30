# Phase 1H User-Visible Learning Slices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended where subagents are available) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved deterministic `learning_slice_v1` presentation layer and deliver useful Preview, Review, Practice, and Learn learning experiences without changing canonical textbook authority, Search/QA retrieval behavior, StudyRecord semantics, or frozen browser persistence shapes.

**Architecture:** Keep `SectionLearningRuntime` as the source-backed mode-candidate selector. Add an isolated `LearningSliceRuntime` that projects those candidates into reference-only, deterministic presentation metadata. `BookAppService` validates every presentation reference against the current mode response and adapts the projection into strongly typed Pydantic DTOs. React renders four focused learning-slice components and stores durable-enough view choices only in the URL query string. Canonical body text continues to come only from existing `ModeItem` / `SourceResolver` paths.

**Tech Stack:** Python 3.13 stdlib, existing Book Runtime, FastAPI, Pydantic v2, React 19, TypeScript 5.9, React Router 7, Vitest + Testing Library, Playwright Chromium, existing SQLite StudyRecord, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-30-phase-1h-learning-slices-design.md`

**Implementation branch:** `design/phase-1h-learning-slices-20260830`

**Implementation base:** `main@2675d2cecab63b28b6ab81a4554e9b7f010afd72`; approved design commit `bb0f20f3c70a44958dbce0f8630ec94e0c3242f6`.

## Execution checkpoint — 2026-08-30

Task 1 (Preview Runtime contract) completed by TDD on the review branch.

- RED checkpoint: `2b0529377fb13326bee3888c052ba9303329601d` (`ModuleNotFoundError: runtime.learning_slice_runtime` observed in CI as expected).
- GREEN Runtime implementation: `f4181347d693ab91b80e4421064394e7403835a3`.
- GREEN export checkpoint / exact verified HEAD: `66518cb314a744685b06594d736dae54f3e58d86`.
- Runtime Reference Tests run `33290906604`: success across Python 3.11 / 3.12 / 3.13; Python 3.13 full discovery ran 323 tests and passed.
- Book App UI Tests run `33290906587`: success at the same exact HEAD.
- Task 1 scope diff is limited to `runtime/learning_slice_runtime.py`, `runtime/__init__.py`, and `tests/test_learning_slice_runtime.py` in addition to this plan and the approved design spec.
- Canonical `books/functional-analysis/**` and `courses/**` remain unchanged.
- Review / Practice / Learn presentation behavior remains intentionally unimplemented until their own RED tests.

Next ordinary implementation gate: Task 2, which adds the strongly typed API `presentation` contract and `BookAppService` source-reference closure validation via TDD. This checkpoint does not authorize PR merge.

## Global Constraints

- Run the project security pre-write gate before implementation writes and again after any repository/branch switch.
- Never write directly to `main`.
- `books/functional-analysis/**` and `courses/**` are canonical read-only inputs for Phase 1H.
- Preserve all existing `ModeResponse` fields and semantics; Phase 1H adds exactly one top-level field: `presentation`.
- Preserve H1-frozen Search, Source, and QA external DTOs exactly.
- Preserve the existing Section session-storage object shape exactly. New Review/Practice selection state lives in URL query parameters only.
- Preserve StudyRecord schema and semantics exactly: no record = not started, `in_progress/0`, `completed/100`.
- Do not activate FTS5/BM25/fusion, semantic retrieval, H3b Concept authority, B4b, B5, multi-book consumer migration, Lecture authority, Mastery, durable per-question answers, or StudyRecord book-version migration.
- Do not generate textbook facts, solutions, prerequisites, importance, difficulty, exam relevance, mastery, or correctness with AI or heuristics.
- Do not render or fabricate figure pixels unless a canonical figure asset contract already exposes them. Phase 1H v1 uses figure metadata/source links only.
- Every behavior-changing task follows real RED → GREEN. Record the failing test before implementation; do not fabricate RED evidence after implementation exists.
- Commit each cohesive GREEN checkpoint. Do not squash/rewrite history through agent operations.
- Keep PR #26 draft during implementation until exact-head verification is complete. Do not merge it without explicit user authorization naming PR #26.
