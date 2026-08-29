# H4a Shadow FTS5 / BM25 Evaluation Implementation Plan

> **For implementers:** Use Superpowers TDD. H0–H3a must be available. H4a is shadow-only; no FTS result may affect public Search or QA.

**Goal:** Build a disposable FTS5/BM25 evaluator over the same canonical candidate universe as Exact Search, produce deterministic comparison evidence, and fail safely without touching product storage or ranking.

**Architecture:** Expose a narrow internal audited-candidate iterator from `SearchRuntime`, then build a disposable SQLite FTS5 index in `runtime.retrieval_shadow`. A CLI compares Exact and FTS ranks for a fixed probe corpus. Every FTS hit must round-trip through `SourceResolver` and H1 provenance before being counted as valid.

**Tech stack:** Python 3.11–3.13 stdlib `sqlite3`, `json`, `unicodedata`, `unittest`; existing Runtime/CLI patterns.

---

## Task 1: Expose SearchRuntime's audited candidate universe without changing Search behavior

**Files:**
- Modify: `runtime/search_runtime.py`
- Modify: `tests/test_search_runtime.py`

**Step 1: Write RED candidate-view tests**

Add an internal immutable view type and expected method to tests:

```python
records = SearchRuntime.from_course(course).candidate_records()
self.assertEqual(len(records), runtime.searchable_candidate_count)
self.assertEqual(
    [(r.source_kind, r.source_id) for r in records],
    [(r.source_kind, r.source_id) for r in runtime.candidate_records()],
)
```

Test that every record exposes only data already audited by `from_course()`:

```text
line_number
source_kind
source_id
object_type
section_id
raw search-index row copy/read-only mapping
```

Add an equivalence test that adding the candidate view does not change query scores/ranks for representative Exact queries.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_search_runtime -v
```

Expected: new `candidate_records()` test fails; all existing Search behavior tests pass.

**Step 3: Implement the narrow internal view**

Prefer:

```python
@dataclass(frozen=True)
class SearchCandidateRecord:
    line_number: int
    source_kind: str
    source_id: str
    object_type: str | None
    section_id: str | None
    raw: dict[str, Any]
```

`candidate_records()` returns a tuple with `dict(candidate.raw)` copies so shadow code cannot mutate SearchRuntime's internal rows.

Keep `_SearchCandidate` private if desired; this new type is Runtime-internal and does not enter `runtime.__init__.py`.

**Step 4: Run Search tests**

```bash
python -m unittest tests.test_search_runtime -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add runtime/search_runtime.py tests/test_search_runtime.py
git commit -m "refactor: expose audited search candidate view"
```

---

## Task 2: Define safe query normalization with RED tests

**Files:**
- Create: `runtime/retrieval_shadow.py`
- Create: `tests/test_retrieval_shadow.py`

**Step 1: Write failing normalizer tests**

Test these inputs explicitly:

```python
queries = [
    "Hölder",
    "Holder",
    "巴拿赫空间",
    "1/p + 1/q = 1",
    "f(x) = x*",
    '"quoted" theorem',
    "AND OR NOT NEAR",
    "a:b - c",
    r"\\int |f|^p",
]
```

Contract:

- non-blank input produces a non-blank safe FTS expression;
- `AND`, `OR`, `NOT`, `NEAR`, `*`, `:`, quotes, parentheses and formula punctuation never become unquoted FTS control syntax;
- Unicode is normalized deterministically with `unicodedata.normalize("NFKC", ...)`;
- blank/whitespace input raises a shadow query error;
- repeated calls return byte-identical expressions.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowQueryNormalizerTests -v
```

Expected: FAIL because shadow module does not exist.

**Step 3: Implement normalizer**

Use a deliberately simple quoted-token strategy. Example public shape:

```python
class ShadowRetrievalError(RuntimeError):
    pass


class ShadowQueryError(ShadowRetrievalError):
    pass


class FtsQueryNormalizer:
    VERSION = "fts_query_v1"

    @classmethod
    def normalize(cls, query: str) -> str:
        text = unicodedata.normalize("NFKC", str(query)).strip()
        if not text:
            raise ShadowQueryError("Shadow query must not be blank")
        tokens = text.split()
        return " AND ".join(cls._quote(token) for token in tokens)

    @staticmethod
    def _quote(token: str) -> str:
        return '"' + token.replace('"', '""') + '"'
```

If SQLite FTS5 semantics show that doubled quotes need a different safe escaping pattern, adjust the implementation based on tests, but keep the contract: user text never becomes FTS operators.

**Step 4: Run normalizer tests**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowQueryNormalizerTests -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add runtime/retrieval_shadow.py tests/test_retrieval_shadow.py
git commit -m "feat: add safe shadow fts query normalizer"
```

---

## Task 3: Define disposable index metadata and output-boundary protection

**Files:**
- Modify: `runtime/retrieval_shadow.py`
- Modify: `tests/test_retrieval_shadow.py`

**Step 1: Write RED boundary tests**

Test allowed paths:

```text
TemporaryDirectory()/shadow.sqlite3
repo/.build/retrieval-shadow/fixture/shadow.sqlite3
```

Test rejected paths:

```text
repo/books/**
repo/courses/**
repo/library/**
BOOK_APP_DATA_DIR/** when env var is set
repo/app/study/**
```

Define metadata contract:

```python
@dataclass(frozen=True)
class ShadowIndexMetadata:
    book_version_id: str
    source_identity: str
    corpus_identity: str
    index_schema_version: str
    normalizer_version: str
    builder_version: str
    record_count: int
```

Freeze version constants such as:

```text
SHADOW_INDEX_SCHEMA_VERSION = shadow_fts_v1
SHADOW_BUILDER_VERSION = shadow_builder_v1
```

**Step 2: Verify RED**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowIndexBoundaryTests -v
```

Expected: FAIL before metadata/boundary code exists.

**Step 3: Implement output validation and metadata hashing helpers**

Add a function such as:

```python
def validate_shadow_output_path(repository_root: Path, output_path: Path) -> Path:
    ...
```

Use resolved paths and `Path.relative_to()` checks. Reject any output inside canonical/data locations. Allow arbitrary external temporary directories and `.build/retrieval-shadow/**`.

Define `corpus_identity` as SHA-256 of canonical JSON over sorted candidate identity/content inputs. It must not include timestamps, absolute paths, SQLite page layout, or timing.

**Step 4: Run tests**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowIndexBoundaryTests -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add runtime/retrieval_shadow.py tests/test_retrieval_shadow.py
git commit -m "feat: protect disposable shadow index boundary"
```

---

## Task 4: Build the FTS5 index only from audited canonical candidates

**Files:**
- Modify: `runtime/retrieval_shadow.py`
- Modify: `tests/test_retrieval_shadow.py`

**Step 1: Write RED build tests**

Using a fixture course, assert build:

- calls `SearchRuntime.from_course(course).candidate_records()`;
- requires every candidate to round-trip through `source_identity_for()`/`SourceResolver`;
- writes one valid shadow document per audited candidate;
- stores exact metadata record count;
- rejects/marks build failure if an audited candidate can no longer resolve;
- does not modify the source search index, canonical book, or StudyRecord DB.

SQLite schema should be tested for the required metadata table and FTS5 virtual table.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowIndexBuildTests -v
```

Expected: FAIL.

**Step 3: Implement build**

Use a schema equivalent to:

```sql
CREATE TABLE shadow_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE VIRTUAL TABLE shadow_documents USING fts5(
    book_version_id UNINDEXED,
    source_kind UNINDEXED,
    source_id UNINDEXED,
    section_id UNINDEXED,
    object_type UNINDEXED,
    title_zh,
    title_en,
    formula,
    concepts,
    tokenize = 'unicode61'
);
```

Populate indexed text only from the candidate's existing audited search-index fields. Do not invent new text with an LLM.

For each row:

```python
identity = source_identity_for(course, candidate.source_kind, candidate.source_id)
assert identity.book.book_version_id == course.main_book_identity().book_version_id
```

Normalize `initial_concepts_zh` into deterministic joined text for the FTS column. Store `section_id` as metadata for scoped comparisons.

If the local Python SQLite build does not support FTS5, raise a specific shadow-unavailable error; do not affect public Runtime.

**Step 4: Run build tests**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowIndexBuildTests -v
```

Expected: PASS on environments with FTS5; tests should explicitly skip only when the standard-library SQLite genuinely lacks FTS5, and should not turn product Runtime red.

**Step 5: Commit**

```bash
git add runtime/retrieval_shadow.py tests/test_retrieval_shadow.py
git commit -m "feat: build canonical shadow fts index"
```

---

## Task 5: Detect missing/corrupt/stale indexes and rebuild rather than migrate

**Files:**
- Modify: `runtime/retrieval_shadow.py`
- Modify: `tests/test_retrieval_shadow.py`

**Step 1: Write RED lifecycle tests**

Test status for:

```text
missing path              -> unavailable/missing
invalid SQLite bytes      -> unavailable/corrupt
metadata schema mismatch  -> unavailable/stale
normalizer mismatch       -> unavailable/stale
book_version mismatch     -> unavailable/stale
corpus_identity mismatch  -> unavailable/stale
valid current index       -> available
```

No test should expect migration of an old shadow DB.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowIndexLifecycleTests -v
```

Expected: FAIL before lifecycle inspection exists.

**Step 3: Implement status/open behavior**

Expose a result such as:

```python
@dataclass(frozen=True)
class ShadowIndexStatus:
    state: Literal["available", "missing", "corrupt", "stale", "unavailable"]
    detail: str | None = None
```

`open()` or `inspect()` must never silently trust mismatched metadata. The CLI may rebuild after non-available status; Runtime public search never reads the shadow index.

**Step 4: Run lifecycle tests**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowIndexLifecycleTests -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add runtime/retrieval_shadow.py tests/test_retrieval_shadow.py
git commit -m "feat: fail safely on stale shadow indexes"
```

---

## Task 6: Query BM25 and revalidate every hit through canonical provenance

**Files:**
- Modify: `runtime/retrieval_shadow.py`
- Modify: `tests/test_retrieval_shadow.py`

**Step 1: Write RED search tests**

Tests must prove:

- BM25 results are sorted lower-is-better internally;
- returned comparison hits expose rank separately from raw BM25;
- section filtering works;
- reserved syntax queries do not raise raw SQLite parser exceptions;
- every returned row is reconstructed into H1 `SourceIdentity` and re-resolved through canonical Runtime;
- a tampered row/source mismatch is counted as provenance failure and not accepted as a valid hit.

Use a separate shadow hit type; do not pretend BM25 score is the same scale as Exact score:

```python
@dataclass(frozen=True)
class ShadowRetrievalHit:
    rank: int
    bm25: float
    identity: SourceIdentity
    source_kind: str
    source_id: str
    section_id: str | None
```

**Step 2: Verify RED**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowSearchTests -v
```

Expected: FAIL.

**Step 3: Implement query**

Run parameterized MATCH queries only:

```python
normalized = FtsQueryNormalizer.normalize(query)
rows = connection.execute(
    """
    SELECT book_version_id, source_kind, source_id, section_id, bm25(shadow_documents)
    FROM shadow_documents
    WHERE shadow_documents MATCH ?
    ORDER BY bm25(shadow_documents), rowid
    LIMIT ?
    """,
    (normalized, limit),
).fetchall()
```

If section scope is supplied, apply it without string concatenation. Re-resolve each source through `source_identity_for()` and require the stored `book_version_id` to match canonical identity.

Catch SQLite query errors and convert them to a shadow-specific unavailable/query error. Never propagate them to App Search/QA because App Search/QA do not call this module.

**Step 4: Run search tests**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowSearchTests -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add runtime/retrieval_shadow.py tests/test_retrieval_shadow.py
git commit -m "feat: query and revalidate shadow fts hits"
```

---

## Task 7: Add fixed probe corpus and deterministic Exact-vs-FTS report

**Files:**
- Create: `tests/fixtures/retrieval-shadow/probes.json`
- Modify: `runtime/retrieval_shadow.py`
- Modify: `tests/test_retrieval_shadow.py`

**Step 1: Create fixed probes**

Use a small human-readable JSON list covering:

```json
[
  {"id": "zh-banach", "query": "巴拿赫空间"},
  {"id": "en-holder", "query": "Hölder"},
  {"id": "holder-ascii", "query": "Holder"},
  {"id": "formula-conjugate", "query": "1/p + 1/q = 1"},
  {"id": "object-type", "query": "exercise"},
  {"id": "reserved-syntax", "query": "AND OR NOT NEAR * :"},
  {"id": "zero-hit", "query": "definitely-no-such-textbook-concept-92831"}
]
```

The probes are evaluation inputs, not textbook facts.

**Step 2: Write RED report tests**

Define deterministic report content for each probe:

```text
probe_id
query
normalized_query
exact_hit_count
fts_hit_count
exact_top_k: [{rank, source_kind, source_id}]
fts_top_k: [{rank, source_kind, source_id}]
overlap_source_keys
fts_new_canonical_source_keys
exact_zero_hit_recovered
provenance_failure_count
shadow_status
```

Global report includes:

```text
schema_version
book_version_id
corpus_identity
record_count
probe_count
probes
```

Timing must not be part of deterministic identity. If timing is captured, keep it in a separate diagnostics object/file.

Generate the report twice and assert canonical JSON bytes are identical.

**Step 3: Verify RED**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowEvaluationReportTests -v
```

Expected: FAIL.

**Step 4: Implement comparator**

Use `RetrievalEngine.exact(course)` for Exact results and shadow query for FTS results. Compare by `(book_version_id, source_kind, source_id)` keys; do not compare/fuse raw scores.

Do not define a pass/fail quality threshold. The report is evidence only.

**Step 5: Run tests**

```bash
python -m unittest tests.test_retrieval_shadow.ShadowEvaluationReportTests -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add runtime/retrieval_shadow.py tests/test_retrieval_shadow.py tests/fixtures/retrieval-shadow/probes.json
git commit -m "feat: compare exact and shadow retrieval deterministically"
```

---

## Task 8: Add the disposable evaluator CLI

**Files:**
- Create: `tools/evaluate_retrieval_shadow.py`
- Create: `tests/test_retrieval_shadow_cli.py`

**Step 1: Write RED CLI tests**

Test a subprocess invocation using a fixture course and temporary output. Required CLI:

```bash
python tools/evaluate_retrieval_shadow.py \
  courses/functional-analysis \
  --repository-root . \
  --output .build/retrieval-shadow/functional-analysis \
  --probes tests/fixtures/retrieval-shadow/probes.json
```

Expected outputs in the chosen derived directory:

```text
shadow.sqlite3
report.json
timing.json   # optional diagnostics; deterministic report must not depend on it
```

CLI JSON/stdout should report status and paths using repository-relative paths where possible, never secrets.

Test forbidden output paths are rejected before writing.

**Step 2: Verify RED**

```bash
python -m unittest tests.test_retrieval_shadow_cli -v
```

Expected: FAIL because tool does not exist.

**Step 3: Implement CLI**

Responsibilities only:

1. resolve repository/course/probe/output paths;
2. validate output boundary;
3. open CourseRuntime;
4. inspect/rebuild disposable index;
5. run comparison;
6. write deterministic `report.json` with sorted keys/UTF-8;
7. write timing diagnostics separately if collected;
8. print a compact machine-readable result.

Do not update `books/**`, `courses/**`, `library/**`, `app/study/**`, or Runtime readiness files.

**Step 4: Run tests and one real Golden evaluation**

```bash
python -m unittest tests.test_retrieval_shadow tests.test_retrieval_shadow_cli -v
rm -rf .build/retrieval-shadow/functional-analysis
python tools/evaluate_retrieval_shadow.py \
  courses/functional-analysis \
  --repository-root . \
  --output .build/retrieval-shadow/functional-analysis \
  --probes tests/fixtures/retrieval-shadow/probes.json
```

Expected: tool completes when FTS5 is available; generated files stay under ignored `.build/retrieval-shadow` and are not committed.

**Step 5: Commit**

```bash
git add tools/evaluate_retrieval_shadow.py tests/test_retrieval_shadow_cli.py
git commit -m "feat: add disposable shadow retrieval evaluator"
```

---

## Task 9: Prove public Search/QA never use shadow ranking

**Files:**
- Modify: `tests/test_foundation_b_isolation.py`
- Modify: `app_tests/test_app_service.py`

**Step 1: Add anti-activation tests**

Assert:

```text
app/api/service.py imports runtime.retrieval but not runtime.retrieval_shadow
runtime/qa_evidence.py imports runtime.retrieval but not runtime.retrieval_shadow
runtime/qa_runtime.py does not import shadow module
```

Behavior test: create a corrupt shadow DB in `.build/retrieval-shadow` or temporary location and prove normal `BookAppService.search()` and deterministic QA still succeed via Exact when canonical Runtime is healthy.

**Step 2: Run tests**

```bash
python -m unittest tests.test_foundation_b_isolation app_tests.test_app_service tests.test_qa_runtime -v
```

Expected: PASS.

**Step 3: Commit**

```bash
git add tests/test_foundation_b_isolation.py app_tests/test_app_service.py
git commit -m "test: keep shadow retrieval off public product path"
```

---

## Task 10: CI wiring and exact-HEAD H4a verification

**Files:**
- Modify: `.github/workflows/runtime-reference-tests.yml`
- Modify if appropriate: `.github/workflows/foundation-b-contract-tests.yml`

**Step 1: Add path trigger for evaluator tool**

Because Runtime workflow enumerates tools selectively, add:

```yaml
- "tools/evaluate_retrieval_shadow.py"
- "tests/fixtures/retrieval-shadow/**"
```

`runtime/**` and `tests/**` already trigger the workflow.

Compile:

```bash
python -m py_compile runtime/retrieval_shadow.py tools/evaluate_retrieval_shadow.py
```

Run correctness tests:

```bash
python -m unittest tests.test_retrieval_shadow tests.test_retrieval_shadow_cli -v
```

Do not add a quality threshold gate such as overlap/recall/latency minimum.

**Step 2: Run full Python regressions**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s app_tests -p "test_*.py" -v
```

Expected: PASS.

**Step 3: Run browser regression**

```bash
cd app/web
npm ci
npm test
npm run typecheck
npm run build
```

Expected: PASS; no browser Shadow code is introduced.

**Step 4: Verify canonical-zero-mutation**

Before the real evaluator run, record:

```bash
git status --short
```

Run evaluator under `.build/retrieval-shadow`, then run:

```bash
git status --short
```

Expected: no tracked canonical textbook changes. `.build/**` remains ignored.

**Step 5: Audit H4a diff**

```bash
git diff --name-only <H4A_BASE_SHA>...HEAD
```

Expected: no public App Search ranking change, no StudyRecord DB/path change, no canonical book mutation, no H3b/B4b/B5 implementation. Replace `<H4A_BASE_SHA>` with the actual implementation base SHA.

**Step 6: Record exact HEAD and prepare H4a PR**

```bash
git rev-parse HEAD
```

Attach correctness and real shadow report evidence separately. Do not interpret the report as permission to activate FTS; B4b remains a hard-stop design decision.
