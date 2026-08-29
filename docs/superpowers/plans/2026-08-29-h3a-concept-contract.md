# H3a Concept / ConceptAlignment Contract Implementation Plan

> **For implementers:** Use Superpowers TDD. H0–H2 must be available. H3a is contract/validation only; creating a real Functional Analysis Concept dataset is explicitly forbidden in this stage.

**Goal:** Define a deterministic, versioned Concept/ConceptAlignment contract and repository-bound reference validator without activating Concept in Search, QA, learning UI, Library, or StudyRecord.

**Architecture:** Pure `book_core.concepts` owns local data semantics and canonical serialization. JSON Schema mirrors that contract. `runtime.concept_validation` owns repository-aware checks through H0 identity and existing canonical Runtime/SourceResolver. Synthetic fixtures only.

**Tech stack:** Python 3.11–3.13 stdlib, JSON Schema documents as published contract artifacts, `unittest`, GitHub Actions.

---

## Task 1: Define the local Concept contract with RED tests

**Files:**
- Create: `tests/test_concept_graph_contract.py`
- Create later: `book_core/concepts.py`

**Step 1: Write RED tests for the minimal contract**

Test these exported symbols:

```python
from book_core.concepts import (
    ALIGNMENT_RELATIONS,
    CONCEPT_GRAPH_SCHEMA_VERSION,
    Concept,
    ConceptAlignment,
    ConceptGraph,
    ConceptGraphValidationError,
    concept_graph_to_canonical_json,
    find_prerequisite_cycles,
    parse_concept_graph,
)
```

Freeze constants:

```python
self.assertEqual(CONCEPT_GRAPH_SCHEMA_VERSION, "concept_graph_v1")
self.assertEqual(
    ALIGNMENT_RELATIONS,
    frozenset({
        "defines", "explains", "proves", "examples",
        "exercises", "extends", "contrasts",
    }),
)
```

Create a minimal valid mapping:

```python
VALID = {
    "schema_version": "concept_graph_v1",
    "concepts": [
        {
            "concept_id": "concept.lp-space",
            "title": "L^p space",
            "aliases": ["Lp space"],
            "prerequisite_concept_ids": [],
            "revision": "r1",
            "provenance": "synthetic-test",
        },
        {
            "concept_id": "concept.holder",
            "title": "Hölder inequality",
            "aliases": [],
            "prerequisite_concept_ids": ["concept.lp-space"],
            "revision": "r1",
            "provenance": "synthetic-test",
        },
    ],
    "alignments": [
        {
            "alignment_id": "align.holder.definition",
            "concept_id": "concept.holder",
            "book_version_id": "fixture_book@v1",
            "section_id": "ch01_s01",
            "source_kind": "object",
            "source_id": "thm_holder",
            "relation": "explains",
            "confidence": 1.0,
            "revision": "r1",
            "provenance": "synthetic-test",
        }
    ],
}
```

Add RED tests for:

- same logical data in different input ordering serializes identically;
- duplicate concept ID rejects;
- duplicate alignment ID rejects;
- dangling prerequisite rejects;
- self-loop rejects;
- duplicate prerequisite edge rejects;
- illegal relation rejects;
- confidence outside `[0.0, 1.0]` rejects;
- blank IDs/title/revision/provenance reject;
- cycles are detected and returned by `find_prerequisite_cycles()` but do **not** cause `parse_concept_graph()` to reject in H3a.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_concept_graph_contract -v
```

Expected: FAIL because `book_core.concepts` does not exist.

**Step 3: Commit RED tests**

```bash
git add tests/test_concept_graph_contract.py
git commit -m "test: define concept graph contract"
```

---

## Task 2: Implement pure Concept dataclasses, parser, canonical serializer, and cycle reporting

**Files:**
- Create: `book_core/concepts.py`
- Test: `tests/test_concept_graph_contract.py`

**Step 1: Implement immutable types**

Use the approved shape:

```python
@dataclass(frozen=True)
class Concept:
    concept_id: str
    title: str
    aliases: tuple[str, ...] = ()
    prerequisite_concept_ids: tuple[str, ...] = ()
    revision: str = ""
    provenance: str = ""


@dataclass(frozen=True)
class ConceptAlignment:
    alignment_id: str
    concept_id: str
    book_version_id: str
    relation: str
    section_id: str | None = None
    source_kind: str | None = None
    source_id: str | None = None
    confidence: float | None = None
    revision: str = ""
    provenance: str = ""


@dataclass(frozen=True)
class ConceptGraph:
    schema_version: str
    concepts: tuple[Concept, ...]
    alignments: tuple[ConceptAlignment, ...]
```

Use one explicit error:

```python
class ConceptGraphValidationError(ValueError):
    pass
```

**Step 2: Implement deterministic normalization**

`parse_concept_graph()` should:

- require a mapping with exactly or at least the supported top-level fields `schema_version`, `concepts`, `alignments`; choose strict exact fields for v1 to prevent silent contract drift;
- validate all strings as non-blank;
- normalize aliases/prerequisites to tuples;
- reject duplicates rather than silently dedupe;
- validate prerequisite targets against the same document;
- reject self-loop;
- validate relation enum;
- validate optional confidence with `0.0 <= confidence <= 1.0` and reject bool-as-number;
- sort Concepts by `concept_id` and Alignments by `alignment_id` in the returned graph so canonical serialization is independent of input order.

**Step 3: Implement canonical JSON**

Use stdlib only:

```python
def concept_graph_to_canonical_json(graph: ConceptGraph) -> str:
    value = {
        "schema_version": graph.schema_version,
        "concepts": [...],
        "alignments": [...],
    }
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
```

Do not include timestamps, paths, random IDs, or machine-specific values.

**Step 4: Implement cycle reporting but not rejection**

`find_prerequisite_cycles(graph)` should return deterministic cycle descriptions. Normalize each cycle so the lexicographically smallest concept ID is first and sort the returned cycles; tests must not depend on DFS incidental order.

Do not reject a graph solely because a cycle is present in H3a.

**Step 5: Run tests/compile**

```bash
python -m unittest tests.test_concept_graph_contract -v
python -m py_compile book_core/concepts.py
```

Expected: PASS.

**Step 6: Commit**

```bash
git add book_core/concepts.py tests/test_concept_graph_contract.py
git commit -m "feat: add deterministic concept graph contract"
```

---

## Task 3: Publish the v1 JSON Schema and prove it mirrors the Python contract

**Files:**
- Create: `schemas/concept-graph/v1/concept-graph.schema.json`
- Modify: `tests/test_concept_graph_contract.py`

**Step 1: Add RED schema consistency tests**

Without adding a new runtime dependency, load the JSON Schema as JSON and assert:

```python
schema = json.loads((ROOT / "schemas/concept-graph/v1/concept-graph.schema.json").read_text())
self.assertEqual(schema["properties"]["schema_version"]["const"], CONCEPT_GRAPH_SCHEMA_VERSION)
self.assertEqual(
    set(schema["$defs"]["alignment"]["properties"]["relation"]["enum"]),
    set(ALIGNMENT_RELATIONS),
)
```

Also assert schema declares `additionalProperties: false` at top-level and inside Concept/Alignment definitions.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_concept_graph_contract -v
```

Expected: FAIL because schema file does not exist.

**Step 3: Create schema**

Schema root should contain:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "concept-graph-v1.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "concepts", "alignments"],
  "properties": {
    "schema_version": {"const": "concept_graph_v1"},
    "concepts": {"type": "array", "items": {"$ref": "#/$defs/concept"}},
    "alignments": {"type": "array", "items": {"$ref": "#/$defs/alignment"}}
  },
  "$defs": {
    "concept": {},
    "alignment": {}
  }
}
```

Fill `$defs` to match exactly the Python v1 fields/types and relation enum. The Python validator remains the executable semantic validator for duplicate IDs, dangling refs, self-loops, and cycles.

**Step 4: Run tests**

```bash
python -m unittest tests.test_concept_graph_contract -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add schemas/concept-graph/v1/concept-graph.schema.json tests/test_concept_graph_contract.py
git commit -m "docs: publish concept graph v1 schema"
```

---

## Task 4: Add one synthetic fixture and canonical fixture round-trip

**Files:**
- Create: `tests/fixtures/concept-graph/valid-minimal.json`
- Modify: `tests/test_concept_graph_contract.py`

**Step 1: Add the synthetic fixture**

Use only invented fixture IDs such as `fixture_book@v1`, `concept.lp-space`, and `thm_holder`. Do not copy or generate a production Concept graph for Functional Analysis.

**Step 2: Add fixture round-trip test**

```python
raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
graph = parse_concept_graph(raw)
first = concept_graph_to_canonical_json(graph)
second = concept_graph_to_canonical_json(parse_concept_graph(json.loads(first)))
self.assertEqual(first, second)
```

**Step 3: Run test**

```bash
python -m unittest tests.test_concept_graph_contract -v
```

Expected: PASS.

**Step 4: Commit**

```bash
git add tests/fixtures/concept-graph/valid-minimal.json tests/test_concept_graph_contract.py
git commit -m "test: add synthetic concept graph fixture"
```

---

## Task 5: Define repository reference validation with RED tests

**Files:**
- Create: `tests/test_concept_reference_validation.py`
- Create later: `runtime/concept_validation.py`
- Reference: `runtime/course_runtime.py`
- Reference: `runtime/source_resolver.py`

**Step 1: Write RED repository-bound tests**

Using a temporary Runtime fixture course, test:

```text
valid main-book book_version_id + section + object source -> PASS
unknown book_version_id -> reject
unknown section_id -> reject
unknown source_id -> reject
unsupported source kind -> reject
alignment section_id inconsistent with resolved source.section_id -> reject
source-bearing alignment for a mounted non-main book -> reject as unsupported in H3a adapter
alignment with no source_id but valid mounted book version -> PASS if local contract allows location-less alignment
```

Test that validation does not mutate the graph or canonical repository.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_concept_reference_validation -v
```

Expected: FAIL because `runtime.concept_validation` does not exist.

**Step 3: Commit RED tests**

```bash
git add tests/test_concept_reference_validation.py
git commit -m "test: define concept repository reference validation"
```

---

## Task 6: Implement repository-bound validator without product activation

**Files:**
- Create: `runtime/concept_validation.py`
- Test: `tests/test_concept_reference_validation.py`

**Step 1: Implement the adapter interface**

Use:

```python
class ConceptReferenceValidationError(RuntimeError):
    pass


class ConceptReferenceValidator:
    def __init__(self, course: CourseRuntime):
        self.course = course

    def validate(self, graph: ConceptGraph) -> None:
        ...
```

Build mounted identity map from existing Runtime entries:

```python
identities = {
    course.book_identity(book_id).book_version_id: course.book_identity(book_id)
    for book_id in course.book_ids()
}
```

For each alignment:

1. require `book_version_id` in mounted identities;
2. if `section_id` exists, validate it through the current main Section skeleton only when the alignment book version is the main book version;
3. if `source_kind/source_id` are present, require both together;
4. because H3a's current `SourceResolver` is intentionally main-book only, reject source-bearing alignments for non-main book identities rather than resolving them against the wrong book;
5. resolve main-book source through `SourceResolver` and require resolved section to match an explicit alignment `section_id` when both exist.

Do not export the validator through `runtime.__init__.py`.

**Step 2: Run tests**

```bash
python -m unittest \
  tests.test_concept_graph_contract \
  tests.test_concept_reference_validation \
  tests.test_source_resolver \
  tests.test_course_runtime -v
```

Expected: PASS.

**Step 3: Compile**

```bash
python -m py_compile runtime/concept_validation.py
```

Expected: PASS.

**Step 4: Commit**

```bash
git add runtime/concept_validation.py tests/test_concept_reference_validation.py
git commit -m "feat: validate concept references against canonical runtime"
```

---

## Task 7: Add an architecture isolation gate proving Concept is inert

**Files:**
- Create: `tests/test_foundation_b_isolation.py`

**Step 1: Write isolation tests**

Tests should statically or behaviorally prove:

```text
runtime/search_runtime.py does not import book_core.concepts or runtime.concept_validation
runtime/qa_evidence.py does not import Concept types
runtime/section_learning_runtime.py does not import Concept types
app/api/service.py does not import Concept types
app/study/** does not import Concept types
```

Also open the Golden course and assert normal Search/QA/SectionLearning behavior without loading any Concept file.

Do not add Concept files under `books/**`, `courses/**`, `tests/golden/**`, or `.build/**` as product authority.

**Step 2: Run isolation test**

```bash
python -m unittest tests.test_foundation_b_isolation -v
```

Expected: PASS after H3a implementation.

**Step 3: Commit**

```bash
git add tests/test_foundation_b_isolation.py
git commit -m "test: keep concept contract isolated from product runtime"
```

---

## Task 8: Add a focused Foundation-B CI gate

**Files:**
- Create: `.github/workflows/foundation-b-contract-tests.yml`

**Step 1: Create narrowly scoped workflow**

Trigger on:

```yaml
paths:
  - "book_core/**"
  - "schemas/concept-graph/**"
  - "runtime/concept_validation.py"
  - "tests/test_concept_graph_contract.py"
  - "tests/test_concept_reference_validation.py"
  - "tests/test_foundation_b_isolation.py"
  - "tests/fixtures/concept-graph/**"
  - ".github/workflows/foundation-b-contract-tests.yml"
```

Job matrix can use Python 3.11/3.12/3.13 or a single 3.13 FAST job plus existing Runtime matrix; prefer a single 3.13 focused gate to keep feedback small.

Run:

```bash
python -m py_compile book_core/*.py runtime/concept_validation.py
python -m unittest tests.test_concept_graph_contract tests.test_concept_reference_validation tests.test_foundation_b_isolation -v
```

Do not repurpose Course Package FAST as the Concept-specific authority.

**Step 2: Run the local equivalent**

```bash
python -m py_compile book_core/*.py runtime/concept_validation.py
python -m unittest tests.test_concept_graph_contract tests.test_concept_reference_validation tests.test_foundation_b_isolation -v
```

Expected: PASS.

**Step 3: Commit**

```bash
git add .github/workflows/foundation-b-contract-tests.yml
git commit -m "ci: add focused foundation b contract gate"
```

---

## Task 9: Exact-HEAD H3a verification and scope audit

**Files:**
- No product file changes expected.

**Step 1: Run Python Runtime/full regression**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s app_tests -p "test_*.py" -v
```

Expected: PASS.

**Step 2: Run web regression**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
```

Expected: PASS even though browser does not consume Concept.

**Step 3: Audit diff for forbidden authority**

```bash
git diff --name-only <H3A_BASE_SHA>...HEAD
```

Expected: no real Concept dataset under `books/**`, `courses/**`, `tests/golden/**`, or `.build/**`; no Search/QA/App activation; no StudyRecord changes. Replace `<H3A_BASE_SHA>` with the actual branch base SHA.

**Step 4: Record exact HEAD and prepare H3a PR**

```bash
git rev-parse HEAD
```

Attach exact-HEAD evidence. Do not begin H3b. H3b remains a hard stop requiring new human design approval.
