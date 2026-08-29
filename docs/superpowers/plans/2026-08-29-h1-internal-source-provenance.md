# H1 Internal Source Provenance Implementation Plan

> **For implementers:** Use Superpowers TDD. H0 must already be merged/available. Do not begin H2 in this PR.

**Goal:** Add collision-safe internal `SourceIdentity` provenance and freeze every existing external serialization boundary so future internal fields cannot leak into Search/Source/QA/provider/browser contracts.

**Architecture:** Keep provenance neutral in `book_core.provenance`, add a Runtime-only adapter for canonical source identity creation, and leave legacy DTO dataclasses untouched. Replace provider `asdict(EvidenceItem)` serialization with an explicit allow-list that emits exactly the current fields.

**Tech stack:** Python 3.11–3.13 stdlib, Pydantic v2 App models, `unittest`, TypeScript/Vitest characterization tests.

---

## Task 1: Define the neutral `SourceIdentity` contract with RED tests

**Files:**
- Create: `tests/test_source_identity.py`
- Create later: `book_core/provenance.py`

**Step 1: Write the failing tests**

Create tests equivalent to:

```python
from __future__ import annotations

import unittest

from book_core.identity import BookIdentity
from book_core.provenance import SourceIdentity


class SourceIdentityTests(unittest.TestCase):
    def test_collision_key_includes_book_version(self) -> None:
        source_a = SourceIdentity(
            course_id="course",
            book=BookIdentity("book", "book", "book@v1", "primary"),
            source_kind="object",
            source_id="thm_1",
        )
        source_b = SourceIdentity(
            course_id="course",
            book=BookIdentity("book", "book", "book@v2", "primary"),
            source_kind="object",
            source_id="thm_1",
        )
        self.assertNotEqual(source_a.collision_key, source_b.collision_key)
        self.assertEqual(source_a.collision_key, ("book@v1", "object", "thm_1"))

    def test_blank_source_parts_fail_closed(self) -> None:
        book = BookIdentity("book", "book", "book@v1", "primary")
        with self.assertRaises(ValueError):
            SourceIdentity("course", book, "", "thm_1")
        with self.assertRaises(ValueError):
            SourceIdentity("course", book, "object", "")
```

**Step 2: Verify RED**

```bash
python -m unittest tests.test_source_identity -v
```

Expected: FAIL because `book_core.provenance` does not exist.

**Step 3: Commit RED test**

```bash
git add tests/test_source_identity.py
git commit -m "test: define internal source identity contract"
```

---

## Task 2: Implement neutral provenance without Runtime imports

**Files:**
- Create: `book_core/provenance.py`
- Test: `tests/test_source_identity.py`

**Step 1: Implement the minimal neutral dataclass**

Use this shape:

```python
from __future__ import annotations

from dataclasses import dataclass

from .identity import BookIdentity


@dataclass(frozen=True)
class SourceIdentity:
    course_id: str
    book: BookIdentity
    source_kind: str
    source_id: str

    def __post_init__(self) -> None:
        if not str(self.course_id).strip():
            raise ValueError("course_id must be non-blank")
        if not str(self.source_kind).strip():
            raise ValueError("source_kind must be non-blank")
        if not str(self.source_id).strip():
            raise ValueError("source_id must be non-blank")

    @property
    def collision_key(self) -> tuple[str, str, str]:
        return (
            self.book.book_version_id,
            self.source_kind,
            self.source_id,
        )
```

Do not import `runtime`, `course_package`, Pydantic, or App code.

**Step 2: Run tests and compile**

```bash
python -m unittest tests.test_book_identity tests.test_source_identity -v
python -m py_compile book_core/*.py
```

Expected: PASS.

**Step 3: Commit**

```bash
git add book_core/provenance.py tests/test_source_identity.py
git commit -m "feat: add neutral source provenance identity"
```

---

## Task 3: Freeze Search/Source/QA HTTP serialization before provenance integration

**Files:**
- Create: `app_tests/test_serialization_contracts.py`
- Reference: `app/api/models.py`
- Reference: `app/api/service.py`

**Step 1: Write exact-key characterization tests**

Create focused tests that instantiate current Pydantic models and assert exact key sets. Use these frozen sets:

```python
SEARCH_RESULT_KEYS = {
    "rank", "score", "source_kind", "source_id", "object_type", "number",
    "title_zh", "title_en", "formula", "pdf_page", "printed_page",
    "source_anchor", "snippet",
}
SOURCE_KEYS = {
    "course_id", "book_id", "section_id", "kind", "source_id", "type",
    "type_zh", "number", "title_zh", "title_en", "content_zh", "formula",
    "printed_page", "pdf_page", "source_anchor", "source_batch",
    "translation_available", "context_before", "context_after",
}
QA_RESPONSE_KEYS = {
    "course_id", "book_id", "question", "answer", "answer_kind",
    "answer_style", "scope_requested", "scope_used", "insufficient_evidence",
    "message", "citations",
}
QA_CITATION_KEYS = {
    "evidence_id", "source_kind", "source_id", "chapter_id", "section_id",
    "object_type", "type_zh", "number", "title_zh", "title_en",
    "printed_page", "pdf_page", "source_anchor",
}
```

Assert `set(model.model_dump().keys()) == ...`, and for nested items assert their exact keys too.

**Step 2: Run characterization**

```bash
python -m unittest app_tests.test_serialization_contracts -v
```

Expected: PASS immediately. This is a characterization gate, not a feature RED.

**Step 3: Commit**

```bash
git add app_tests/test_serialization_contracts.py
git commit -m "test: freeze app serialization contracts"
```

---

## Task 4: Freeze browser session contracts before any future book-aware fields

**Files:**
- Modify: `app/web/src/state/qaSessionState.test.ts`
- Modify: `app/web/src/state/searchViewState.test.ts`
- Modify: `app/web/src/state/sectionViewState.test.ts`

**Step 1: Add exact shape tests**

Ensure tests explicitly verify:

```text
QA session stores only route/messages/scrollY/activeCitationSourceId plus the existing verified QAResponse shape.
Search state stores only route/query/scrollY/activeSourceKey.
Section state stores only route/scrollY/expandedSourceIds/activeSourceId.
Malformed or extra-key-invalid payloads fail closed according to the current validators.
No provenance/book-version/index metadata is persisted.
```

For QA cached response, add a test that an unexpected citation field such as `book_version_id` is rejected by the current exact-key parser. This documents the B5 migration hazard instead of changing it now.

**Step 2: Run web state tests**

```bash
cd app/web
npm test -- --run src/state/qaSessionState.test.ts src/state/searchViewState.test.ts src/state/sectionViewState.test.ts
```

Expected: PASS after characterization is aligned with current parser behavior.

**Step 3: Commit**

```bash
git add app/web/src/state/*.test.ts
git commit -m "test: freeze browser session state contracts"
```

---

## Task 5: Replace provider `asdict(EvidenceItem)` with exact allow-list projection

**Files:**
- Modify: `app/api/openai_compatible_provider.py`
- Modify: `app_tests/test_openai_compatible_provider.py`

**Step 1: Add a RED test for an explicit evidence projection helper**

Add a test that calls a new private helper or inspects `_request_body()` and asserts each evidence object has exactly:

```python
EVIDENCE_PAYLOAD_KEYS = {
    "evidence_id",
    "source_kind",
    "source_id",
    "object_type",
    "title_zh",
    "title_en",
    "number",
    "formula",
    "content_zh",
    "source_anchor",
    "pdf_page",
    "printed_page",
    "search_score",
    "course_id",
    "book_id",
    "chapter_id",
    "section_id",
    "type_zh",
}
```

Also assert history rows remain exactly `{role, content}` and the top-level user payload remains exactly:

```python
{
    "question",
    "course_id",
    "book_id",
    "section_id",
    "history",
    "evidence",
    "allowed_answer_styles",
}
```

Before the helper exists, the helper-specific test should fail while current wire content still matches.

**Step 2: Implement allow-list helpers**

Replace:

```python
"history": [asdict(message) for message in request.history],
"evidence": [asdict(item) for item in request.evidence],
```

with explicit projections, for example:

```python
@staticmethod
def _history_payload(message: QAHistoryMessage) -> dict[str, object]:
    return {"role": message.role, "content": message.content}

@staticmethod
def _evidence_payload(item: EvidenceItem) -> dict[str, object]:
    return {
        "evidence_id": item.evidence_id,
        "source_kind": item.source_kind,
        "source_id": item.source_id,
        "object_type": item.object_type,
        "title_zh": item.title_zh,
        "title_en": item.title_en,
        "number": item.number,
        "formula": item.formula,
        "content_zh": item.content_zh,
        "source_anchor": item.source_anchor,
        "pdf_page": item.pdf_page,
        "printed_page": item.printed_page,
        "search_score": item.search_score,
        "course_id": item.course_id,
        "book_id": item.book_id,
        "chapter_id": item.chapter_id,
        "section_id": item.section_id,
        "type_zh": item.type_zh,
    }
```

Import the concrete types directly from `runtime.qa_models` if needed. Remove the provider's now-unused `asdict` import.

**Step 3: Run provider tests**

```bash
python -m unittest app_tests.test_openai_compatible_provider tests.test_qa_provider tests.test_qa_runtime -v
```

Expected: PASS and serialized JSON remains byte-equivalent at the user-payload semantic level.

**Step 4: Commit**

```bash
git add app/api/openai_compatible_provider.py app_tests/test_openai_compatible_provider.py
git commit -m "refactor: freeze provider evidence serialization"
```

---

## Task 6: Add a Runtime adapter that constructs provenance only after canonical resolution

**Files:**
- Create: `runtime/provenance.py`
- Create: `tests/test_runtime_provenance.py`
- Reference: `runtime/source_resolver.py`
- Reference: `runtime/course_runtime.py`

**Step 1: Write RED adapter tests**

Tests should prove:

```python
identity = source_identity_for(course, "object", "fixture_object")
self.assertEqual(identity.course_id, course.course_id)
self.assertEqual(identity.book, course.main_book_identity())
self.assertEqual(identity.source_kind, "object")
self.assertEqual(identity.source_id, "fixture_object")
```

Also test:

- unknown source fails with a Runtime provenance error;
- canonical resolved source identity must match selected course/main book;
- two `SourceIdentity` values with same `source_kind/source_id` but different book versions have different collision keys.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_runtime_provenance -v
```

Expected: FAIL because `runtime.provenance` does not exist.

**Step 3: Implement adapter**

Use this boundary:

```python
from book_core.provenance import SourceIdentity
from .course_runtime import CourseRuntime
from .source_resolver import SourceResolutionError, SourceResolver


class RuntimeProvenanceError(RuntimeError):
    pass


def source_identity_for(
    course: CourseRuntime,
    source_kind: str,
    source_id: str,
) -> SourceIdentity:
    try:
        resolved = SourceResolver(course).resolve(source_kind, source_id)
    except SourceResolutionError as exc:
        raise RuntimeProvenanceError(str(exc)) from exc
    if resolved.course_id != course.course_id:
        raise RuntimeProvenanceError("Resolved source course identity mismatch")
    if resolved.book_id != course.main_book().book_id:
        raise RuntimeProvenanceError("Resolved source book identity mismatch")
    return SourceIdentity(
        course_id=course.course_id,
        book=course.main_book_identity(),
        source_kind=resolved.kind,
        source_id=resolved.source_id,
    )
```

Do not export this through `runtime.__init__.py` during H1.

**Step 4: Run tests**

```bash
python -m unittest \
  tests.test_source_identity \
  tests.test_runtime_provenance \
  tests.test_source_resolver \
  tests.test_course_runtime -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add runtime/provenance.py tests/test_runtime_provenance.py
git commit -m "feat: add canonical runtime provenance adapter"
```

---

## Task 7: Prove legacy DTO dataclasses did not gain provenance fields

**Files:**
- Modify: `app_tests/test_serialization_contracts.py`
- Modify: `tests/test_qa_evidence.py`
- Modify: `tests/test_source_resolver.py`

**Step 1: Add anti-leak assertions**

Assert `ResolvedSource.to_dict()` does not contain:

```python
{"book_version_id", "logical_book_id", "provenance", "identity", "retriever_id"}
```

Assert `EvidenceItem` serialized by provider still has exactly the frozen evidence keys and no provenance object.

Assert current Search/QA response payloads contain no new identity fields.

**Step 2: Run contract suite**

```bash
python -m unittest \
  app_tests.test_serialization_contracts \
  app_tests.test_openai_compatible_provider \
  app_tests.test_qa_api \
  tests.test_source_resolver \
  tests.test_qa_evidence \
  tests.test_qa_runtime -v
```

Expected: PASS.

**Step 3: Commit**

```bash
git add app_tests tests/test_qa_evidence.py tests/test_source_resolver.py
git commit -m "test: guard provenance from public dto leakage"
```

---

## Task 8: CI and exact-HEAD H1 verification

**Files:**
- Modify if necessary: `.github/workflows/runtime-reference-tests.yml`
- Modify if necessary: `.github/workflows/app-ui-tests.yml`

**Step 1: Ensure new neutral/runtime provenance files are compiled**

Runtime CI should compile:

```bash
python -m py_compile book_core/*.py runtime/provenance.py
```

`book_core/**` path triggers should already exist from H0. Add `runtime/provenance.py` only if current `runtime/**` trigger/compile list does not already cover it.

**Step 2: Run all Python regressions**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s app_tests -p "test_*.py" -v
```

Expected: PASS.

**Step 3: Run browser regressions**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
```

Expected: PASS.

**Step 4: Diff safety check**

```bash
git diff --name-only <H1_BASE_SHA>...HEAD
```

Expected: no canonical `books/**`, `courses/**`, `library/**`, or StudyRecord schema/storage changes. Replace `<H1_BASE_SHA>` with the actual branch base SHA at execution time.

**Step 5: Record HEAD and prepare H1 PR**

```bash
git rev-parse HEAD
```

Attach exact-HEAD test evidence. Do not merge automatically and do not begin H2 until H1 governance is satisfied.
