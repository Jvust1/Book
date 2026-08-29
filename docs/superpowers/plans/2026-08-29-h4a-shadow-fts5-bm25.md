# H4a Shadow FTS5/BM25 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a deterministic, evaluation-only SQLite FTS5/BM25 shadow retrieval experiment for the Functional Analysis Golden Course, compare `unicode61` and `trigram` profiles against the existing H2 Exact baseline, and produce exact-HEAD evidence without changing public Search/QA behavior.

**Architecture:** Keep `RetrievalEngine.exact` as the only production retrieval path. Add an isolated `runtime/shadow_fts.py` for ephemeral in-memory FTS5 indexing/search, an `evaluation/h4a_runtime.py` layer for query-set validation/metrics/reporting, a checked-in Golden query dataset authored before FTS tuning, and a small CLI under `tools/`. Extend the existing Foundation B focused gate and Runtime matrix; do not modify canonical textbook content, App DTOs, production ranking, or StudyRecord.

**Tech Stack:** Python 3.11/3.12/3.13 stdlib (`sqlite3`, `json`, `hashlib`, `dataclasses`, `pathlib`, `unittest`), existing Book Runtime/SourceResolver/SourceIdentity/H2 Retrieval seam, SQLite FTS5 built-ins (`unicode61`, `trigram`, `bm25()`), GitHub Actions, existing Golden Course fixtures and regression suites.

**Design authority:** `docs/superpowers/specs/2026-08-29-h4a-shadow-fts5-bm25-design.md`

**Implementation base:** branch `design/h4a-shadow-fts5-bm25-20260829`, currently based on integrated `main` commit `f0f1951dff24e49e4eb25f968e208cdc69b7b577`.

---

## Guardrails for every task

Before changing implementation files, preserve these invariants:

- `books/functional-analysis/**` is canonical read-only input. Never edit or normalize it to make H4a pass.
- `runtime/retrieval.py`, `runtime/search_runtime.py`, `BookAppService`, QARuntime, public DTOs, and App routes remain production Exact-only unless a later task proves a strictly necessary internal change. The default plan assumes **no change** to those production files.
- FTS/BM25 output is evaluation-only. Do not place BM25 floats into `RetrievalHit.score` or public Search/QA serialization.
- No Exact+FTS fusion, no public ranking activation, no H3b, no B4b, no B5, and no StudyRecord book-version migration.
- Use only parameterized SQL for query values. Internal fixed profile/table identifiers may be selected from a closed constant map; never derive SQL identifiers from user text.
- The v1 Golden query dataset is authored and committed before the first Golden FTS evaluation/tuning run. Once a real v1 result exists in branch/PR history, do not rewrite v1 relevance judgments; create v2 if correction is required.
- Record a real RED checkpoint before each behavior implementation. Do not write implementation first and fabricate RED evidence later.
- Commit after each cohesive GREEN checkpoint. Do not squash/rewrite history through agent operations.
- Do not add generated `.build/evaluations/**` output to Git unless an explicit later governance decision says otherwise.
- Exact final-head completion evidence must come from the exact final implementation HEAD, not earlier green runs.

---

## Task 1: Establish the H4a query-set contract and validator

**Files:**
- Create: `evaluation/__init__.py`
- Create: `evaluation/h4a_runtime.py`
- Create: `tests/test_h4a_evaluation.py`

### Step 1: Write the failing query-set contract tests

Create `tests/test_h4a_evaluation.py` with a minimal fixture dictionary and tests for the design contract before `evaluation.h4a_runtime` exists.

Cover at least:

```python
class H4aQuerySetValidationTests(unittest.TestCase):
    def test_accepts_positive_and_negative_queries(self): ...
    def test_rejects_unknown_top_level_field(self): ...
    def test_rejects_duplicate_query_ids(self): ...
    def test_rejects_blank_query(self): ...
    def test_positive_query_requires_expected_source(self): ...
    def test_negative_query_requires_empty_expected_sources(self): ...
    def test_rejects_duplicate_expected_source_identity(self): ...
    def test_rejects_invalid_source_kind(self): ...
    def test_rejects_blank_section_id(self): ...
    def test_canonical_json_hash_is_deterministic(self): ...
```

Use a closed category vocabulary matching the design:

```python
H4A_QUERY_CATEGORIES = {
    "english_exact",
    "english_partial",
    "chinese_complete",
    "chinese_partial",
    "formula_symbol",
    "section_scoped",
    "negative_zero_result",
}
```

Expected source keys are exactly `source_kind` and `source_id`.

### Step 2: Run the focused test and confirm RED

Run:

```bash
python -m unittest tests.test_h4a_evaluation -v
```

Expected RED: import failure because `evaluation.h4a_runtime` does not yet exist, or missing query-set contract symbols.

Record the RED commit before adding implementation:

```bash
git add tests/test_h4a_evaluation.py
git commit -m "test: define H4a query set contract"
```

### Step 3: Implement the minimal query-set types and fail-closed parser

Create `evaluation/__init__.py` as a minimal package marker.

Create `evaluation/h4a_runtime.py` with only the contract needed by these tests. Prefer immutable dataclasses:

```python
@dataclass(frozen=True)
class ExpectedSource:
    source_kind: str
    source_id: str

@dataclass(frozen=True)
class H4aQuery:
    query_id: str
    category: str
    query: str
    section_id: str | None
    expected_sources: tuple[ExpectedSource, ...]
    notes: str | None

@dataclass(frozen=True)
class H4aQuerySet:
    schema_version: str
    dataset_id: str
    course_id: str
    queries: tuple[H4aQuery, ...]
```

Add a dedicated validation error such as:

```python
class H4aEvaluationError(RuntimeError): ...
class H4aDatasetError(H4aEvaluationError): ...
```

Implement:

```python
def parse_h4a_query_set(payload: object) -> H4aQuerySet: ...
def canonical_query_set_json(query_set: H4aQuerySet) -> str: ...
def query_set_sha256(query_set: H4aQuerySet) -> str: ...
```

Rules:

- top-level keys are closed: `schema_version`, `dataset_id`, `course_id`, `queries`;
- schema exactly `h4a_query_set_v1`;
- nonblank dataset/course/query IDs and query text;
- unique query IDs;
- categories closed to the seven v1 categories;
- `negative_zero_result` must have `expected_sources == []`;
- all other categories require at least one expected source;
- source identity pairs unique inside each query;
- v1 accepts current supported `source_kind` values `object` and `figure` only;
- optional `section_id` and `notes` are either nonblank strings or null;
- canonical JSON uses deterministic key order/separators/UTF-8 semantics and no timestamps.

Do **not** add metrics or FTS code yet.

### Step 4: Run focused tests and confirm GREEN

Run:

```bash
python -m unittest tests.test_h4a_evaluation -v
```

Expected: all Task 1 tests PASS.

Also compile:

```bash
python -m py_compile evaluation/__init__.py evaluation/h4a_runtime.py
```

Expected: exit 0.

### Step 5: Commit Task 1 GREEN

```bash
git add evaluation/__init__.py evaluation/h4a_runtime.py tests/test_h4a_evaluation.py
git commit -m "feat: validate H4a evaluation query sets"
```

---

## Task 2: Curate and freeze the Functional Analysis v1 query dataset before FTS tuning

**Files:**
- Create: `evaluation/h4a/functional_analysis_queries.v1.json`
- Modify: `tests/test_h4a_evaluation.py`

**Important ordering:** Complete and commit this task before running any Golden Course FTS profile against these queries. Unit tests with synthetic fixtures are allowed later; do not use actual FTS results to choose the v1 relevance labels.

### Step 1: Add a failing checked-in-dataset validation test

Extend `tests/test_h4a_evaluation.py` with a test that expects the real dataset file and validates:

```python
def test_functional_analysis_v1_dataset_has_required_category_coverage(self):
    path = REPO_ROOT / "evaluation/h4a/functional_analysis_queries.v1.json"
    query_set = load_h4a_query_set(path)
    self.assertEqual(query_set.course_id, "functional_analysis_course")
    self.assertEqual(query_set.dataset_id, "functional_analysis_h4a_v1")
    self.assertGreaterEqual(len(query_set.queries), 24)
    self.assertLessEqual(len(query_set.queries), 30)
    ...
```

Minimum category counts:

```text
english_exact          >= 4
english_partial        >= 4
chinese_complete       >= 4
chinese_partial        >= 4
formula_symbol         >= 4
section_scoped         >= 3
negative_zero_result   >= 2
```

Also require each `expected_source` to resolve against the Golden Course and, for `section_scoped`, verify the expected source belongs to the specified section through `SourceResolver`/canonical runtime data.

### Step 2: Run and confirm RED because the dataset is absent

```bash
python -m unittest tests.test_h4a_evaluation.H4aGoldenDatasetTests -v
```

Expected RED: file-not-found or explicit missing-dataset assertion.

Commit the RED test:

```bash
git add tests/test_h4a_evaluation.py
git commit -m "test: require H4a Golden query dataset"
```

### Step 3: Inspect canonical source objects read-only to curate labels

Do **not** use Exact or FTS output as label authority. Use canonical Runtime/SourceResolver only.

Run a read-only helper from repository root, adapting the displayed fields if necessary but not writing files:

```bash
python - <<'PY'
from pathlib import Path
from runtime.course_runtime import CourseRuntime
from runtime.source_resolver import SourceResolver

root = Path.cwd()
course = CourseRuntime.open(root / "courses/functional-analysis")
book = course.main_book()
resolver = SourceResolver(course)

print("course", course.course_id)
print("book", book.book_id)
for source_id, obj in sorted(book.objects.items()):
    title_zh = getattr(obj, "title_zh", None)
    title_en = getattr(obj, "title_en", None)
    formula = getattr(obj, "formula", None)
    number = getattr(obj, "number", None)
    section_id = getattr(obj, "section_id", None)
    haystack = " ".join(str(x or "") for x in (title_zh, title_en, formula, number))
    if any(term.casefold() in haystack.casefold() for term in (
        "holder", "hölder", "banach", "linear", "compact", "dual", "norm", "hilbert"
    )):
        print(source_id, section_id, number, title_zh, title_en, formula)
PY
```

Then inspect additional Chinese/formula candidates using canonical fields, not search ranking. For figures, enumerate `book.figures` and resolve them with `SourceResolver` before using any figure ID.

For every positive query, manually verify every `expected_source` resolves and genuinely supports the intended query. Use source IDs exactly as stored; never invent them.

For deliberate negatives, choose strings not present in canonical titles/concepts/formulas and keep `expected_sources: []`.

### Step 4: Create the v1 JSON dataset

Create `evaluation/h4a/functional_analysis_queries.v1.json` with 24–30 queries satisfying the category minimums.

Required top-level shape:

```json
{
  "schema_version": "h4a_query_set_v1",
  "dataset_id": "functional_analysis_h4a_v1",
  "course_id": "functional_analysis_course",
  "queries": []
}
```

For each positive query:

```json
{
  "query_id": "en_exact_holder_001",
  "category": "english_exact",
  "query": "Hölder",
  "section_id": null,
  "expected_sources": [
    {"source_kind": "object", "source_id": "<verified canonical id>"}
  ],
  "notes": "Curated from canonical source metadata, not retriever output."
}
```

For each negative query:

```json
{
  "query_id": "negative_001",
  "category": "negative_zero_result",
  "query": "<verified absent text>",
  "section_id": null,
  "expected_sources": [],
  "notes": "Deliberate no-relevant-source query."
}
```

### Step 5: Implement the small file loader needed by the test

If not already present in Task 1, add:

```python
def load_h4a_query_set(path: Path) -> H4aQuerySet: ...
```

It must:

- read UTF-8;
- report stable `H4aDatasetError` for missing/unreadable/invalid JSON;
- delegate shape validation to `parse_h4a_query_set`;
- never modify the file.

### Step 6: Run dataset validation and confirm GREEN

```bash
python -m unittest tests.test_h4a_evaluation.H4aGoldenDatasetTests -v
python -m unittest tests.test_h4a_evaluation -v
```

Expected: PASS.

Print the dataset identity for the commit record without running FTS:

```bash
python - <<'PY'
from pathlib import Path
from evaluation.h4a_runtime import load_h4a_query_set, query_set_sha256
p = Path("evaluation/h4a/functional_analysis_queries.v1.json")
q = load_h4a_query_set(p)
print(q.dataset_id, len(q.queries), query_set_sha256(q))
PY
```

Expected: deterministic dataset ID, count 24–30, 64-hex SHA-256.

### Step 7: Commit the v1 dataset before any Golden FTS run

```bash
git add evaluation/h4a/functional_analysis_queries.v1.json evaluation/h4a_runtime.py tests/test_h4a_evaluation.py
git commit -m "data: freeze H4a v1 Golden query set"
```

From this commit onward, if the first real Golden FTS evaluation later exposes a bad label, create `functional_analysis_queries.v2.json`; do not rewrite v1 history.

---

## Task 3: Build the ephemeral shadow corpus and FTS5 capability gate

**Files:**
- Create: `runtime/shadow_fts.py`
- Create: `tests/test_shadow_fts.py`

### Step 1: Write RED tests for corpus projection and capability detection

Create fixture repos with `tests.runtime_fixture_factory` helpers. Include:

- a valid object row;
- an unsupported row ID that current Exact would skip;
- a row with `initial_concepts_zh` in deliberate source order;
- a valid section identity;
- an eligible source that becomes inconsistent/unresolvable in a separate failure test.

Write tests for:

```python
class ShadowFtsCorpusTests(unittest.TestCase):
    def test_detects_fts5_by_creating_virtual_table(self): ...
    def test_builds_in_memory_index_only(self): ...
    def test_skips_rows_outside_existing_exact_candidate_boundary(self): ...
    def test_preserves_canonical_search_index_order_in_rowids(self): ...
    def test_projects_concepts_in_source_list_order(self): ...
    def test_missing_text_projects_to_empty_string(self): ...
    def test_eligible_provenance_mismatch_fails_closed(self): ...
    def test_document_count_matches_search_runtime_candidate_count(self): ...
```

Use `SearchRuntime.from_course(course).searchable_candidate_count` as the Golden count-equivalence check; do not access/modify private production fields merely to satisfy the test.

### Step 2: Run and confirm RED

```bash
python -m unittest tests.test_shadow_fts.ShadowFtsCorpusTests -v
```

Expected RED: `ModuleNotFoundError: runtime.shadow_fts` or missing symbols.

Commit RED:

```bash
git add tests/test_shadow_fts.py
git commit -m "test: define H4a shadow corpus contract"
```

### Step 3: Implement minimal shadow corpus primitives

Create `runtime/shadow_fts.py` with evaluation-only names. Do not export them from public API modules unless tests prove an existing project convention requires it.

Suggested closed profile definitions:

```python
UNICODE61_PROFILE = "fts_unicode61_bm25_v1"
TRIGRAM_PROFILE = "fts_trigram_bm25_v1"
H4A_PROFILES = (UNICODE61_PROFILE, TRIGRAM_PROFILE)
```

Suggested errors:

```python
class ShadowFtsError(RuntimeError): ...
class ShadowFtsUnavailableError(ShadowFtsError): ...
class ShadowFtsInvariantError(ShadowFtsError): ...
class ShadowFtsQueryError(ShadowFtsError): ...
```

Suggested internal document:

```python
@dataclass(frozen=True)
class ShadowDocument:
    rowid: int
    identity: SourceIdentity
    source_kind: str
    source_id: str
    section_id: str | None
    object_type: str | None
    number: str
    title_zh: str
    title_en: str
    formula: str
    concepts_zh: str
    snippet: str
```

Implement a capability probe by actually creating/dropping an FTS5 table in an isolated in-memory connection. Do not rely only on `pragma compile_options`, because runtime availability is the capability that matters.

Implement deterministic corpus loading by reading `course.main_book().search_index_path` read-only, applying the design candidate boundary, and resolving eligible object/figure identities through existing canonical Runtime/SourceResolver/provenance helpers.

Do not copy SearchRuntime's scoring logic.

Create one `shadow_documents` metadata table and the two FTS5 tables in the same `:memory:` connection. Insert explicit deterministic rowids.

Do not use persistent disk databases.

### Step 4: Run focused tests and confirm GREEN

```bash
python -m unittest tests.test_shadow_fts.ShadowFtsCorpusTests -v
python -m py_compile runtime/shadow_fts.py
```

Expected: PASS/exit 0.

### Step 5: Commit Task 3 GREEN

```bash
git add runtime/shadow_fts.py tests/test_shadow_fts.py
git commit -m "feat: build ephemeral H4a FTS5 corpus"
```

---

## Task 4: Implement safe profile querying, BM25 ranking, and section scope

**Files:**
- Modify: `runtime/shadow_fts.py`
- Modify: `tests/test_shadow_fts.py`

### Step 1: Write RED tests for query compilation and ranking

Add tests covering:

```python
class ShadowFtsSearchTests(unittest.TestCase):
    def test_rejects_blank_query(self): ...
    def test_rejects_invalid_limit_values(self): ...
    def test_rejects_blank_section_id(self): ...
    def test_operator_words_are_literal_user_text(self): ...
    def test_embedded_quotes_are_safe(self): ...
    def test_match_query_is_parameterized(self): ...
    def test_unicode61_returns_unicode_fixture_match(self): ...
    def test_trigram_returns_substring_fixture_match(self): ...
    def test_trigram_under_three_unicode_characters_is_valid_zero_match(self): ...
    def test_bm25_is_sorted_ascending_then_rowid_for_ties(self): ...
    def test_section_scope_never_returns_other_section(self): ...
    def test_shadow_hit_revalidates_canonical_identity(self): ...
```

Do not assert a particular absolute BM25 float unless the fixture makes that portable. Assert ordering and finite numeric values instead.

### Step 2: Run and confirm RED

```bash
python -m unittest tests.test_shadow_fts.ShadowFtsSearchTests -v
```

Expected RED: missing search/query compiler/ShadowHit behavior.

Commit RED:

```bash
git add tests/test_shadow_fts.py
git commit -m "test: define H4a shadow query semantics"
```

### Step 3: Implement evaluation-only result types and safe query compiler

Add:

```python
@dataclass(frozen=True)
class ShadowHit:
    profile_id: str
    rank: int
    bm25_score: float
    identity: SourceIdentity
    source_kind: str
    source_id: str
    section_id: str | None
```

Use a fixed internal map from profile ID to known table name/tokenizer. Reject unknown profile IDs before SQL execution.

Implement a helper that converts arbitrary human text to one quoted FTS phrase. Embedded `"` characters must be escaped according to SQLite FTS5 string rules. Words such as `AND`, `OR`, `NOT`, `NEAR`, and strings resembling column filters must remain literal text, not query operators.

Bind the MATCH expression, section ID, and limit as SQL parameters. The table name is chosen only from the closed internal profile map.

Query ordering:

```sql
ORDER BY bm25(<fixed-profile-table>) ASC, d.rowid ASC
```

Validate the returned `(source_kind, source_id)` again against canonical identity before constructing each `ShadowHit`.

Reject non-finite BM25 values with `ShadowFtsInvariantError`.

### Step 4: Run all shadow tests and confirm GREEN

```bash
python -m unittest tests.test_shadow_fts -v
```

Expected: PASS.

Also run existing Exact seam tests to prove this task did not change production behavior:

```bash
python -m unittest tests.test_search_runtime tests.test_retrieval -v
```

Expected: PASS.

### Step 5: Commit Task 4 GREEN

```bash
git add runtime/shadow_fts.py tests/test_shadow_fts.py
git commit -m "feat: query H4a FTS5 shadow profiles safely"
```

---

## Task 5: Add deterministic metrics and report assembly

**Files:**
- Modify: `evaluation/h4a_runtime.py`
- Modify: `tests/test_h4a_evaluation.py`

### Step 1: Write RED metric tests with synthetic result signatures

Do not use Golden FTS yet. Build small in-memory synthetic source-rank fixtures to prove metric math independently.

Add tests for:

```python
class H4aMetricTests(unittest.TestCase):
    def test_positive_hit_at_1_5_10_and_recall_at_10(self): ...
    def test_reciprocal_rank_and_mrr(self): ...
    def test_multiple_expected_sources_recall(self): ...
    def test_fts_only_and_exact_only_recovery(self): ...
    def test_negative_queries_are_excluded_from_recall_and_mrr(self): ...
    def test_negative_clean_and_unexpected_hit_count(self): ...
    def test_non_finite_metric_input_fails_closed(self): ...
    def test_aggregate_metrics_are_deterministic(self): ...
```

Add report-shape tests:

```python
class H4aReportTests(unittest.TestCase):
    def test_report_has_closed_top_level_shape(self): ...
    def test_report_records_sqlite_version_and_profile_ids(self): ...
    def test_report_omits_wall_clock_and_absolute_paths(self): ...
    def test_report_has_no_activation_flag(self): ...
    def test_report_canonical_json_is_repeatable(self): ...
```

### Step 2: Run and confirm RED

```bash
python -m unittest tests.test_h4a_evaluation.H4aMetricTests tests.test_h4a_evaluation.H4aReportTests -v
```

Expected RED: missing metric/report types/functions.

Commit RED:

```bash
git add tests/test_h4a_evaluation.py
git commit -m "test: define H4a metric and report contract"
```

### Step 3: Implement minimal metric/report logic

Keep relevance keys based on canonical `(source_kind, source_id)` pairs, never titles.

Suggested internal result summary:

```python
@dataclass(frozen=True)
class RankedSource:
    source_kind: str
    source_id: str
    rank: int

@dataclass(frozen=True)
class QueryMetrics:
    hit_at_1: bool | None
    hit_at_5: bool | None
    hit_at_10: bool | None
    recall_at_10: float | None
    reciprocal_rank: float | None
    negative_clean_at_10: bool | None
    unexpected_hit_count_at_10: int | None
```

Use `None` for positive-only fields on deliberate negative queries, and `None` for negative-only fields on positive queries. Do not fake zero denominators.

Implement profile/category aggregation deterministically. Sort report entries by dataset query order and profile order, not dictionary incidental order.

Record environment facts only when explicitly provided by evaluator orchestration, including SQLite version and FTS5 availability. No timestamp.

Implement canonical report serialization and reject NaN/Inf recursively before JSON encoding.

### Step 4: Run tests and confirm GREEN

```bash
python -m unittest tests.test_h4a_evaluation -v
python -m py_compile evaluation/h4a_runtime.py
```

Expected: PASS.

### Step 5: Commit Task 5 GREEN

```bash
git add evaluation/h4a_runtime.py tests/test_h4a_evaluation.py
git commit -m "feat: evaluate H4a retrieval metrics deterministically"
```

---

## Task 6: Orchestrate the Golden Exact-vs-shadow evaluation and stable CLI

**Files:**
- Modify: `evaluation/h4a_runtime.py`
- Create: `tools/evaluate_h4a_retrieval.py`
- Create: `tests/test_h4a_cli.py`
- Modify: `tests/test_h4a_evaluation.py`

This is the first task allowed to execute both real FTS profiles against the checked-in Golden v1 dataset. At this point the v1 dataset must already exist in branch history from Task 2.

### Step 1: Write RED orchestration tests

Add a Golden integration test that requires:

- Exact baseline created through `RetrievalEngine.exact(course)`;
- both shadow profiles queried for each dataset row;
- all returned shadow identities resolve canonically;
- section-scoped results never escape scope;
- report contains Exact + both shadow profiles;
- two runs in the same environment have identical ordered source signatures and aggregate metric payloads.

Suggested test names:

```python
class H4aGoldenEvaluationTests(unittest.TestCase):
    def test_golden_evaluation_uses_h2_exact_baseline(self): ...
    def test_golden_evaluation_runs_both_shadow_profiles(self): ...
    def test_all_shadow_hits_have_valid_provenance(self): ...
    def test_section_scoped_queries_do_not_escape_scope(self): ...
    def test_repeat_run_source_signatures_are_identical(self): ...
```

For verifying the H2 boundary, patch/spy `RetrievalEngine.exact` at the evaluator import seam rather than changing production code.

### Step 2: Write RED CLI tests

Create `tests/test_h4a_cli.py` covering:

```python
class H4aCliTests(unittest.TestCase):
    def test_cli_writes_report_under_build_by_default(self): ...
    def test_cli_success_stdout_is_stable_json_summary(self): ...
    def test_cli_invalid_dataset_returns_exit_2_without_traceback(self): ...
    def test_cli_fts_unavailable_returns_nonzero_stable_error_without_fallback(self): ...
    def test_cli_rejects_output_path_outside_repository_build_area(self): ...
```

Follow the existing Course Package CLI safety style: stable JSON/exit code, no Python traceback leakage for expected user/configuration errors, and repository-bounded default output.

### Step 3: Run and confirm RED

```bash
python -m unittest tests.test_h4a_evaluation.H4aGoldenEvaluationTests tests.test_h4a_cli -v
```

Expected RED: missing evaluator orchestration/CLI.

Commit RED:

```bash
git add tests/test_h4a_evaluation.py tests/test_h4a_cli.py
git commit -m "test: define H4a Golden evaluation CLI"
```

### Step 4: Implement Golden evaluator orchestration

In `evaluation/h4a_runtime.py`, add a high-level function with dependencies injectable for tests, conceptually:

```python
def evaluate_h4a_course(
    repository_root: Path,
    query_set_path: Path,
) -> dict[str, object]:
    ...
```

Required flow:

1. open `courses/functional-analysis` through current Runtime;
2. validate dataset course ID;
3. resolve every expected source before retrieval starts;
4. build one Exact engine through `RetrievalEngine.exact(course)`;
5. build the ephemeral shadow index;
6. execute Exact/unicode61/trigram for every query with the same requested `limit=10` and section scope;
7. convert all results to canonical source identity signatures;
8. compute positive/negative metrics separately;
9. record SQLite version and FTS5 capability/profile definitions;
10. produce deterministic report payload.

Do not inject the shadow retriever into BookAppService/QARuntime.

### Step 5: Implement the CLI

Create `tools/evaluate_h4a_retrieval.py` with default inputs:

```text
repository root: current repo
query set: evaluation/h4a/functional_analysis_queries.v1.json
output: .build/evaluations/h4a/functional_analysis_course/report.json
```

CLI behavior:

- successful run: exit 0, write canonical UTF-8 JSON report and print a small stable JSON summary;
- dataset/query error: exit 2;
- shadow/FTS infrastructure/invariant failure: exit 3;
- no fallback to Exact-only report when FTS5 is unavailable;
- expected failures do not print traceback;
- output must remain inside `.build/evaluations/h4a/` under repository root;
- create parent generated directories if needed; never create/write under `books/**` or `courses/**`.

### Step 6: Run focused tests, then the first real Golden v1 evaluation

First run tests:

```bash
python -m unittest tests.test_h4a_evaluation tests.test_h4a_cli tests.test_shadow_fts -v
```

Expected: PASS.

Now run the first real v1 evaluation:

```bash
python tools/evaluate_h4a_retrieval.py
```

Expected: exit 0 and report at:

```text
.build/evaluations/h4a/functional_analysis_course/report.json
```

Immediately run it a second time in the same environment and compare deterministic source/metric payloads through a test or helper. Do not require raw BM25 byte identity across different SQLite versions.

If this first real evaluation reveals a bad ground-truth label, **do not edit v1**. Stop and create a v2 dataset in a separate clearly recorded commit before continuing metric interpretation.

### Step 7: Prove public Exact behavior is still unchanged

Run:

```bash
python -m unittest \
  tests.test_search_runtime \
  tests.test_retrieval \
  tests.test_qa_evidence \
  tests.test_qa_provider \
  tests.test_qa_runtime \
  -v
```

Expected: PASS.

### Step 8: Commit Task 6 GREEN

```bash
git add evaluation/h4a_runtime.py tools/evaluate_h4a_retrieval.py tests/test_h4a_evaluation.py tests/test_h4a_cli.py
git commit -m "feat: run deterministic H4a Golden retrieval evaluation"
```

Do not add `.build/evaluations/**` generated output.

---

## Task 7: Wire H4a into focused Foundation B and Runtime matrix CI

**Files:**
- Modify: `.github/workflows/foundation-b-contract-tests.yml`
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Optionally modify only if needed by trigger semantics: `.github/workflows/app-ui-tests.yml`

The default expectation is **no App workflow content change** because existing Runtime/test path triggers already cause App regression; verify before changing it.

### Step 1: Add a CI-shape RED test or static assertion if the repository has a workflow-contract test pattern

Search first:

```bash
grep -R "foundation-b-contract-tests\|runtime-reference-tests" -n tests .github | head -50
```

If a workflow-shape test pattern exists, add RED assertions there. If none exists, do not invent a YAML parser dependency solely for H4a; use fresh workflow diff review plus GitHub Actions as the executable gate.

### Step 2: Extend Foundation B focused workflow paths and tests

Update `.github/workflows/foundation-b-contract-tests.yml` push/pull_request paths to include at least:

```yaml
- "runtime/shadow_fts.py"
- "evaluation/**"
- "tools/evaluate_h4a_retrieval.py"
- "tests/test_shadow_fts.py"
- "tests/test_h4a_evaluation.py"
- "tests/test_h4a_cli.py"
```

In compile step add:

```bash
python -m py_compile runtime/shadow_fts.py
python -m py_compile evaluation/*.py
python -m py_compile tools/evaluate_h4a_retrieval.py
```

In focused tests add the three H4a modules while retaining all H3a tests:

```bash
python -m unittest \
  tests.test_concept_graph_contract \
  tests.test_concept_reference_validation \
  tests.test_foundation_b_isolation \
  tests.test_shadow_fts \
  tests.test_h4a_evaluation \
  tests.test_h4a_cli \
  -v
```

Add a Golden H4a evaluation command after unit tests:

```bash
python tools/evaluate_h4a_retrieval.py
```

### Step 3: Extend Runtime matrix trigger/compile/gates

Update `.github/workflows/runtime-reference-tests.yml` path filters so `evaluation/**` and `tools/evaluate_h4a_retrieval.py` trigger the workflow. `runtime/**` and `tests/**` already trigger it.

Add compile commands:

```bash
python -m py_compile runtime/shadow_fts.py
python -m py_compile evaluation/*.py
python -m py_compile tools/evaluate_h4a_retrieval.py
```

Add H4a focused tests to a dedicated step or the existing Search/QA step:

```bash
python -m unittest tests.test_shadow_fts tests.test_h4a_evaluation tests.test_h4a_cli -v
```

Run the Golden H4a evaluator on every Python matrix member:

```bash
python tools/evaluate_h4a_retrieval.py
```

If Python 3.11/3.12/3.13's bundled SQLite lacks required FTS5 behavior, the job must fail explicitly. Do not `continue-on-error`, skip, or silently downgrade to Exact.

Keep existing H2 Search/QA tests, full discovery, Golden rebuild/readiness/fitness, and Python 3.13 extra gates intact.

### Step 4: Verify App workflow trigger without unnecessary edit

Read `.github/workflows/app-ui-tests.yml` path filters. If `runtime/**`, `tests/**`, or equivalent already covers H4a implementation paths sufficiently for a PR that changes `runtime/shadow_fts.py`, leave the file unchanged.

Only add `evaluation/**` / `tools/evaluate_h4a_retrieval.py` if a later H4a-only change could otherwise bypass required App regression. Do not alter jobs/behavior unless needed.

### Step 5: Run local CI-equivalent focused commands

```bash
python -m py_compile runtime/shadow_fts.py evaluation/*.py tools/evaluate_h4a_retrieval.py
python -m unittest tests.test_shadow_fts tests.test_h4a_evaluation tests.test_h4a_cli -v
python -m unittest tests.test_search_runtime tests.test_retrieval tests.test_qa_evidence tests.test_qa_provider tests.test_qa_runtime -v
python tools/evaluate_h4a_retrieval.py
```

Expected: all PASS/exit 0.

### Step 6: Commit CI wiring

```bash
git add .github/workflows/foundation-b-contract-tests.yml .github/workflows/runtime-reference-tests.yml
# add app-ui-tests.yml only if it was actually necessary and changed
git commit -m "ci: gate H4a shadow retrieval evaluation"
```

---

## Task 8: Record new external source-study snapshot obligations without rewriting historical pending items

**Files:**
- Modify: `governance/pending_sync.json`
- Test/read-back: JSON parser plus governance diff review

The design studied two additional external repositories at fixed commits:

```text
simonw/sqlite-utils  56dd09702fdb9e899f577ffd51693c1f2176cb08  Apache-2.0
simonw/datasette     0337fba234bf574629d56be631468ea060495fa0  Apache-2.0
```

The existing 2026-08-28 pending item records five earlier repositories. Preserve that historical item unchanged.

### Step 1: Add a new non-blocking pending item

Append one new item such as:

```json
{
  "pending_id": "h4a_external_reference_source_snapshots_2026_08_29",
  "blocking": false,
  "status": "PENDING",
  "scope": "Book/00_Project/External_References/Snapshots",
  "reason": "H4a entered real source-level study of sqlite-utils and Datasette at fixed commits; exact source snapshots are required by the all-project source-snapshot policy but are not yet archived through the available connector path.",
  "references": [
    {
      "repository": "simonw/sqlite-utils",
      "commit": "56dd09702fdb9e899f577ffd51693c1f2176cb08",
      "license": "Apache-2.0"
    },
    {
      "repository": "simonw/datasette",
      "commit": "0337fba234bf574629d56be631468ea060495fa0",
      "license": "Apache-2.0"
    }
  ],
  "resolution": "Archive exact-commit source ZIPs to the existing External_References/Snapshots area with SHA-256/read-back when a trusted Book-accessible transfer path is available; preserve prior snapshots and do not overwrite them.",
  "blocks_next_step": false
}
```

Do not increment `blocking_count`; it remains 0 unless another real blocking item appears.

### Step 2: Validate JSON and historical preservation

Run:

```bash
python -m json.tool governance/pending_sync.json >/dev/null
```

Expected: exit 0.

Then inspect the diff and confirm the old `external_reference_source_snapshots_2026_08_28` item and its five references are byte-semantically preserved; only the new H4a item is appended.

### Step 3: Commit governance tracking

```bash
git add governance/pending_sync.json
git commit -m "chore: track H4a source snapshot sync"
```

This records an obligation only. Do not fake Drive archival success.

---

## Task 9: Add an executable H4a isolation regression proving production Search/QA never use shadow FTS

**Files:**
- Create: `tests/test_h4a_isolation.py`
- Modify: `.github/workflows/foundation-b-contract-tests.yml`
- Modify: `.github/workflows/runtime-reference-tests.yml`

This is the architectural lock that prevents later accidental H4a → B4b scope creep inside the same branch.

### Step 1: Write RED isolation tests

Test observable behavior, not fragile source-string grep wherever possible:

```python
class H4aIsolationTests(unittest.TestCase):
    def test_book_app_service_default_retrieval_remains_exact(self): ...
    def test_qa_runtime_default_retrieval_remains_exact(self): ...
    def test_shadow_types_are_not_present_in_public_search_dto(self): ...
    def test_shadow_types_are_not_present_in_public_qa_dto(self): ...
    def test_public_exact_search_signature_matches_pre_h4a_contract(self): ...
```

Use spies/patches at constructor factories to prove the default path calls `RetrievalEngine.exact` and does not instantiate `ShadowFtsIndex`.

Also assert public serialized Search/QA payloads do not contain:

```text
bm25_score
profile_id
shadow
fts
retriever_id
identity
book_version_id
```

where current frozen contracts already forbid internal keys.

### Step 2: Run and confirm RED only if a missing test seam is required

```bash
python -m unittest tests.test_h4a_isolation -v
```

If all assertions already pass without production changes, that is acceptable: this task adds an executable invariant, not a behavior feature. In that case record the test-only checkpoint honestly instead of forcing an artificial failing product change.

If a test reveals actual H4a leakage, stop and fix the leakage minimally before proceeding.

### Step 3: Add the test to both H4a CI gates

Foundation B focused suite should include:

```text
tests.test_h4a_isolation
```

Runtime H4a focused step should include it as well.

### Step 4: Run and confirm PASS

```bash
python -m unittest tests.test_h4a_isolation -v
python -m unittest tests.test_search_runtime tests.test_retrieval tests.test_qa_evidence tests.test_qa_runtime -v
```

Expected: PASS.

### Step 5: Commit isolation gate

```bash
git add tests/test_h4a_isolation.py .github/workflows/foundation-b-contract-tests.yml .github/workflows/runtime-reference-tests.yml
git commit -m "test: keep H4a shadow retrieval out of production"
```

---

## Task 10: Perform exact-final-HEAD verification and prepare the reviewable PR

**Files:**
- No new product files expected.
- Do not update `docs/EVALUATION_LEDGER.md`, `docs/CURRENT_STATE.md`, or `governance/project_state.json` to claim H4a merged/completed before the PR is actually merged. Avoid another moving-HEAD/self-reference cycle.
- Generated report remains under `.build/` and untracked.

### Step 1: Confirm the final scope before verification

Run:

```bash
git status --short
git diff main...HEAD --name-status
git diff main...HEAD -- books/functional-analysis
```

Expected:

- no uncommitted changes before the exact-head gate;
- only planned H4a spec/plan/implementation/test/workflow/pending-sync files;
- **no output** for `git diff main...HEAD -- books/functional-analysis`.

Also verify no unexpected App/public DTO/StudyRecord/Concept production paths changed.

### Step 2: Run focused H4a tests on exact HEAD

```bash
python -m unittest \
  tests.test_shadow_fts \
  tests.test_h4a_evaluation \
  tests.test_h4a_cli \
  tests.test_h4a_isolation \
  -v
```

Expected: PASS.

### Step 3: Run H2/Search/QA regression on exact HEAD

```bash
python -m unittest \
  tests.test_search_runtime \
  tests.test_retrieval \
  tests.test_qa_evidence \
  tests.test_qa_provider \
  tests.test_qa_runtime \
  -v
```

Expected: PASS.

### Step 4: Run full Python test discovery on exact HEAD

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: all PASS.

If App tests are locally available in the development environment, also run the existing App test discovery according to repository commands. Do not substitute a partial run for CI evidence.

### Step 5: Generate and inspect exact-head H4a evidence

```bash
python tools/evaluate_h4a_retrieval.py
python -m json.tool .build/evaluations/h4a/functional_analysis_course/report.json >/dev/null
```

Expected: exit 0.

Read the report and classify the evidence manually as one of:

```text
FTS_EVIDENCE_PROMISING
FTS_EVIDENCE_MIXED
FTS_EVIDENCE_NOT_PROMISING
FTS_EVALUATION_INVALID
```

This classification is a review conclusion only. Do not write an activation flag and do not begin B4b.

### Step 6: Push/observe exact-head GitHub Actions

After all changes are committed, record the exact final branch HEAD:

```bash
git rev-parse HEAD
```

Required GitHub checks at that exact SHA:

- Foundation B contract tests: success, including H3a + H4a focused tests and H4a evaluator;
- Runtime reference tests: Python 3.11 / 3.12 / 3.13 success, including H2/Search/QA regression and H4a evaluator;
- Book App UI tests: App API/Web/typecheck/build/real Chromium success if triggered by the final diff as expected;
- Golden/readiness/architecture fitness checks already embedded in the Runtime/App workflows remain success.

Do not claim a check passed unless the run is attached to the exact final SHA.

### Step 7: Fresh final diff/read-back review

Verify:

```text
- no books/functional-analysis/** changes
- no courses/** canonical changes
- no public Search/QA DTO shape changes
- no BookAppService/QARuntime default retrieval activation
- no FTS/Exact fusion
- no H3b/B4b/B5/StudyRecord migration
- pending_sync new item is non-blocking and historical items preserved
- v1 dataset commit predates first real Golden FTS evaluation commit
- generated .build report is not tracked
```

### Step 8: Create a reviewable PR only after exact-head evidence is green

Create a PR from:

```text
design/h4a-shadow-fts5-bm25-20260829 -> main
```

Suggested title:

```text
Foundation B: evaluate shadow FTS5/BM25 retrieval
```

PR body should explicitly state:

- public Search/QA remains Exact-only;
- H4a is shadow evaluation only;
- both tokenizer profiles and metrics evaluated;
- exact final HEAD and exact run IDs;
- Golden canonical diff is zero;
- evidence classification;
- H3b/B4b/B5/StudyRecord migration remain unauthorized;
- source snapshot archival remains non-blocking if not yet completed.

Then perform a fresh PR diff/review and stop at the merge gate.

**Do not merge the PR from “下一步/继续”. Merge requires an explicit concrete instruction such as `合并 PR #<number>` after fresh head/check/review revalidation.**

---

## Expected implementation change set

The intended implementation PR should remain close to this list:

```text
docs/superpowers/specs/2026-08-29-h4a-shadow-fts5-bm25-design.md   # already present
docs/superpowers/plans/2026-08-29-h4a-shadow-fts5-bm25.md          # this plan
evaluation/__init__.py
evaluation/h4a_runtime.py
evaluation/h4a/functional_analysis_queries.v1.json
runtime/shadow_fts.py
tools/evaluate_h4a_retrieval.py
tests/test_shadow_fts.py
tests/test_h4a_evaluation.py
tests/test_h4a_cli.py
tests/test_h4a_isolation.py
.github/workflows/foundation-b-contract-tests.yml
.github/workflows/runtime-reference-tests.yml
governance/pending_sync.json
```

`app/**`, public API models, StudyRecord files, production Concept data, and `books/functional-analysis/**` are expected to remain unchanged.

If implementation discovers a need to modify a production boundary not listed above, stop and re-evaluate the design rather than silently expanding scope.

## Completion definition

H4a implementation is complete only when:

1. the v1 dataset is historically frozen before its first real FTS evaluation;
2. Exact baseline is obtained through H2 `RetrievalEngine.exact`;
3. both `unicode61` and `trigram` shadow profiles run with safe parameterized MATCH semantics;
4. positive and negative metrics are deterministic and correctly separated;
5. every shadow hit proves canonical provenance and requested section scope;
6. public Search/QA remains Exact-only with frozen DTO/error/ranking behavior;
7. Golden canonical textbook diff is zero;
8. exact final HEAD passes focused H4a, Runtime 3.11/3.12/3.13, App/Web/Chromium, Golden/readiness/fitness gates required by the final diff;
9. external source-study snapshot obligations are honestly tracked if not archived;
10. a reviewable PR exists and remains unmerged until the user explicitly authorizes that specific PR.
