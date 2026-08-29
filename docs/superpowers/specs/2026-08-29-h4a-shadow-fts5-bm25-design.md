# H4a Shadow FTS5/BM25 Evaluation Design

Date: 2026-08-29
Status: APPROVED-IN-CHAT / SPEC FOR REVIEW
Repository: `Jvust1/Book`
Base integration commit: `f0f1951dff24e49e4eb25f968e208cdc69b7b577`
Stage: `H4a shadow FTS5/BM25 evaluation`

## 1. Context

Book is a provenance-preserving Course OS. The current public Search and QA behavior is intentionally Exact-only. H2 introduced one shared internal Retrieval seam so Search and QA evidence candidate retrieval no longer depend directly on separate search implementations. H3a then added an inert Concept/ConceptAlignment contract without activating production Concept data.

The approved dependency sequence is:

```text
H0 neutral Book identity                  COMPLETE_MERGED
→ H1 internal source provenance           COMPLETE_MERGED
→ H2 Exact-only shared Retrieval seam     COMPLETE_MERGED
→ H3a Concept graph contract              COMPLETE_MERGED
→ H4a shadow FTS5/BM25 evaluation         THIS STAGE
→ Phase 1H user-visible slices            AFTER H4a
```

H4a exists to answer one evidence question before any public ranking change:

> Can SQLite FTS5/BM25 improve retrieval coverage or ranking on the Golden Course, especially for natural-language, substring, Chinese, and formula-like queries, while preserving canonical provenance and section scope?

H4a is an evaluation stage, not an activation stage. A valid H4a result is allowed to conclude that FTS5/BM25 should not be activated.

## 2. Goals

H4a MUST:

1. Build a deterministic, evaluation-only FTS5 index from the existing canonical main-book search corpus.
2. Evaluate two fixed FTS5 tokenizer profiles:
   - `fts_unicode61_bm25_v1`
   - `fts_trigram_bm25_v1`
3. Compare both profiles against the existing Exact baseline obtained through `RetrievalEngine.exact(...)`.
4. Use a versioned, deterministic Golden Course query dataset authored before the FTS implementation is tuned.
5. Measure ranking/coverage with explicit metrics and query-level evidence.
6. Verify every shadow hit against canonical `SourceIdentity` and requested section scope.
7. Produce deterministic evaluation evidence suitable for exact-HEAD review.
8. Keep public Search and QA behavior byte/shape/ordering compatible with the current Exact-only product contract.
9. Leave activation, fusion, score normalization, and production FTS persistence to a later explicit B4b design gate.

## 3. Non-goals / hard exclusions

H4a MUST NOT:

- install FTS5 as the `BookAppService` production `retrieval_factory`;
- change `/search` result ranking, score, order, response keys, or error mapping;
- change QA evidence candidate selection in the user-visible product path;
- combine Exact and FTS results into a fused list;
- reinterpret SQLite BM25 values as the existing Exact `1000/900/800/...` score scale;
- broaden or change the public Search/Source/QA DTO shapes;
- change `RetrievalHit.score` from its current Exact-oriented integer contract merely to accommodate shadow BM25 floats;
- create production Concept data or activate H3b;
- perform B4b public FTS/fusion/ranking activation;
- perform B5 work;
- migrate StudyRecord to book-version identity;
- write generated search state into `books/functional-analysis/**` or any other canonical book/course input;
- make a machine-specific benchmark time a correctness gate;
- auto-authorize a later activation proposal based only on H4a metrics.

`H3b`, `B4b`, `B5`, and StudyRecord book-version migration remain separate Human Gates.

## 4. Existing H2 boundary and H4a placement

H2 currently provides:

```text
BookAppService / QARuntime
        ↓
RetrievalEngine
        ↓
Retriever Protocol
        ↓
CanonicalExactRetriever
        ↓
SearchRuntime
```

The production factory remains:

```python
RetrievalEngine.exact
```

H4a MUST NOT create a second production retrieval boundary. Instead it adds an evaluation-only shadow subsystem adjacent to the H2 seam:

```text
canonical search_index.jsonl
        │
        ├── RetrievalEngine.exact(course)
        │       ↓
        │   Exact baseline hits
        │
        └── H4a shadow corpus builder
                ↓
          SQLite :memory:
          metadata + FTS5 tables
                ↓
          unicode61 / trigram
                ↓
              bm25()
                ↓
           ShadowHit records
                │
                └── canonical SourceIdentity re-validation

Exact baseline + ShadowHit records
                ↓
        deterministic evaluator
                ↓
        stable JSON evidence report
```

The key boundary rule is:

- `RetrievalEngine.exact` remains the only production retrieval engine during H4a.
- The evaluator consumes the H2 Exact baseline and uses the same canonical Course/Book/Source identity model.
- Shadow-specific BM25 scores live in evaluation-only types, not in the existing public or production Exact score contract.
- If H4a later supports a B4b proposal, B4b must separately design how an FTS retriever would implement the production `Retriever` contract and how scores/fusion would work.

This avoids prematurely changing H2 just to make an experiment fit a production type.

## 5. Shadow corpus authority and candidate eligibility

The H4a corpus is derived data. It is never authority.

Authoritative inputs remain:

- `CourseRuntime` / canonical course identity;
- the enabled primary Book selected by the current Course contract;
- the canonical primary Book `search_index.jsonl`;
- `SourceResolver` and current internal provenance helpers.

The shadow builder MUST preserve the existing Exact candidate boundary rather than inventing a broader corpus.

Candidate eligibility is deterministic:

1. A search-index row with no `id`/`unit_id` is non-indexable and is skipped.
2. A row whose source ID is not a supported current canonical object/figure source is non-indexable and is skipped, matching the existing Exact candidate boundary rather than turning unrelated rows into an error.
3. A row that claims to identify an indexable canonical object/figure but cannot be resolved consistently, has a book/source identity mismatch, or cannot prove canonical provenance fails the shadow build closed.
4. Only rows that pass the source trust check may receive a shadow `rowid` and enter FTS5.

The builder MUST NOT silently repair malformed canonical data merely to increase FTS coverage.

The shadow builder MUST NOT mutate, normalize in place, rewrite, repair, or promote canonical book files.

For the Golden Course the canonical facts remain:

```text
course_id = functional_analysis_course
book_id = stein_shakarchi_functional_analysis_2011
8 chapters
132 sections
1493 search records
442 PDF pages
final printed page 423
```

## 6. SQLite storage model

H4a uses an ephemeral in-memory SQLite connection by default:

```text
sqlite3.connect(":memory:")
```

The evaluation index is rebuilt from canonical inputs for each evaluator construction. There is no durable production FTS database in H4a.

### 6.1 Metadata table

One ordinary metadata table maps SQLite row identity to canonical source identity and scope. Conceptually:

```text
shadow_documents
- rowid INTEGER PRIMARY KEY
- source_kind TEXT NOT NULL
- source_id TEXT NOT NULL
- section_id TEXT
- object_type TEXT
- number TEXT
- title_zh TEXT
- title_en TEXT
- formula TEXT
- concepts_zh TEXT
- snippet TEXT
```

`rowid` assignment MUST be deterministic and follow canonical search-index order among eligible rows.

The metadata table is the only place where rowid-to-source mapping is interpreted. FTS internal shadow tables such as `_data`, `_idx`, `_docsize`, `_content`, and `_config` are SQLite implementation detail and never provenance authority.

### 6.2 FTS tables

Each profile uses a separate FTS5 virtual table over the same deterministic metadata rows.

Profile 1:

```text
fts_unicode61_bm25_v1
```

- tokenizer: SQLite FTS5 `unicode61` default behavior;
- intended role: token/phrase-oriented baseline for Unicode text;
- BM25: built-in `bm25(table)` with no tuned per-column weights in H4a v1.

Profile 2:

```text
fts_trigram_bm25_v1
```

- tokenizer: SQLite FTS5 `trigram`, default case-insensitive mode;
- intended role: substring-oriented comparison, especially useful where current Exact behavior can match title/formula substrings;
- BM25: built-in `bm25(table)` with no tuned per-column weights in H4a v1.

H4a deliberately avoids weight tuning. Weight tuning after seeing the evaluation set would make the first comparison less trustworthy and belongs to a later versioned experiment if needed.

### 6.3 Indexed text projection

The initial H4a profiles index the same bounded textual fields:

```text
title_zh
title_en
concepts_zh
formula
number
object_type
snippet
```

Projection from a canonical search-index row is deterministic:

- scalar text fields use their existing canonical text value after the same non-semantic whitespace trimming used by current Runtime helpers;
- missing/`None` scalar values become the empty string for FTS storage;
- `initial_concepts_zh`, when it is a list, is projected to `concepts_zh` by preserving source list order and joining non-empty string members with `\n`;
- no sorting, stemming, synonym injection, translation, AI expansion, or query-derived text is added during H4a;
- `snippet` uses the same bounded canonical projection logic already used by current search diagnostics, not generated prose.

Canonical source identity fields are not treated as relevance text. `source_kind`, `source_id`, and `section_id` remain metadata/filter/provenance fields.

## 7. Query compilation and safety

User/evaluation query text MUST NOT be concatenated into SQL or treated as raw FTS5 query language.

The H4a query compiler MUST:

1. reuse the existing Retrieval request validation for blank query, integer `limit`, and section-id shape where applicable;
2. trim but not semantically rewrite the human query;
3. escape embedded quote characters according to FTS5 string rules;
4. compile the user text as a quoted FTS phrase rather than allowing arbitrary `AND`, `OR`, `NOT`, `NEAR`, column filters, or future FTS syntax to execute from user text;
5. bind the resulting MATCH expression as a SQL parameter;
6. apply section scope using metadata predicates, never by trusting text matches;
7. order by `bm25(...) ASC`, then deterministic `rowid ASC` for ties.

SQLite FTS5 defines lower BM25 values as better matches. H4a MUST preserve this meaning inside `ShadowHit.bm25_score`; it MUST NOT negate, rescale, or pretend the value is comparable to Exact scores.

The trigram profile has an explicit known boundary: full-text substrings shorter than 3 Unicode characters do not match. Such a query is a legitimate evaluation outcome, not an infrastructure failure.

## 8. Evaluation-only result types

H4a introduces separate evaluation types rather than modifying the production `RetrievalHit` contract.

Conceptually:

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

@dataclass(frozen=True)
class ShadowQueryResult:
    query_id: str
    profile_id: str
    hits: tuple[ShadowHit, ...]
```

The evaluator may attach canonical display metadata for diagnostics, but relevance metrics key on canonical source identity, not titles/snippets.

No `ShadowHit` or BM25 field is serialized through existing public Search/QA DTOs.

## 9. Deterministic evaluation dataset

H4a uses a versioned checked-in dataset, created before FTS implementation tuning:

```text
evaluation/h4a/functional_analysis_queries.v1.json
```

Suggested schema:

```json
{
  "schema_version": "h4a_query_set_v1",
  "dataset_id": "functional_analysis_h4a_v1",
  "course_id": "functional_analysis_course",
  "queries": [
    {
      "query_id": "...",
      "category": "...",
      "query": "...",
      "section_id": null,
      "expected_sources": [
        {"source_kind": "object", "source_id": "..."}
      ],
      "notes": "..."
    }
  ]
}
```

### 9.1 Dataset construction rules

The first dataset SHOULD contain 24–30 queries with minimum category coverage:

| Category | Minimum |
| --- | ---: |
| English exact/title terminology | 4 |
| English partial/natural wording | 4 |
| Chinese complete terminology | 4 |
| Chinese substring/partial wording | 4 |
| Formula/symbol-like queries | 4 |
| Section-scoped queries | 3 |
| Deliberate zero-result negatives | 2 |

One positive query may have multiple relevant canonical sources where the source material genuinely supports that judgment.

For positive categories, `expected_sources` MUST contain at least one canonical source. For the deliberate zero-result negative category, `expected_sources` MUST be an empty list.

### 9.2 Ground-truth rule

`expected_sources` MUST be curated from canonical source objects and `SourceResolver` evidence. It MUST NOT be generated by asking Exact or FTS which result should be considered correct.

Exact is a baseline retriever, not the ground-truth generator.

### 9.3 Anti-tuning rule

The query dataset is committed before the GREEN FTS implementation is tuned against it. Once the first real H4a shadow evaluation has been recorded in the PR history, corrections that change relevance judgments or query text require a new version such as `functional_analysis_queries.v2.json`; the previous version remains historical evidence.

H4a v1 is not called an unseen/frozen benchmark, but its first observed result must still remain historically traceable.

## 10. Metrics

Metrics are computed separately for:

- Exact baseline;
- `fts_unicode61_bm25_v1`;
- `fts_trigram_bm25_v1`;
- each positive query category;
- deliberate negative queries;
- overall positive-query aggregate.

### 10.1 Positive-query coverage / recall

For queries with one or more `expected_sources`:

- `hit_at_1`: whether at least one expected source appears at rank 1.
- `hit_at_5`: whether at least one expected source appears in top 5.
- `hit_at_10`: whether at least one expected source appears in top 10.
- `recall_at_10`: expected sources retrieved in top 10 / expected sources.

Aggregate `hit_at_k` values are reported as rates across positive queries.

### 10.2 Positive-query ranking

- `reciprocal_rank`: `1 / rank` of the first expected source, else 0.
- `MRR`: arithmetic mean of per-query reciprocal rank over positive queries only.

### 10.3 Comparative recovery/loss

For each positive query/profile:

- `fts_only_recovery_at_10`: expected source appears in FTS top 10 but not Exact top 10.
- `exact_only_recovery_at_10`: expected source appears in Exact top 10 but not FTS top 10.
- query-level delta table showing exact rank versus FTS rank for each expected source.

### 10.4 Negative-query behavior

Negative queries are not included in Recall/MRR denominators.

For each deliberate zero-result negative query/profile, report:

- `negative_clean_at_10`: true when the retriever returns zero top-10 candidates;
- `unexpected_hit_count_at_10`: number of returned candidates up to 10;
- returned canonical source identities for diagnosis when the count is non-zero.

These metrics reveal broad false-positive behavior without inventing a recall denominator of zero.

### 10.5 Correctness invariants

These are hard correctness gates:

- provenance validity: 100% of returned shadow hits resolve to the mounted Course/Book/source identity;
- section-scope validity: 100% of section-scoped shadow hits belong to the requested section;
- deterministic tie/order behavior: identical evaluator input in the same environment produces the same ordered source signature;
- public Exact contract equivalence: existing Search and QA Exact regression suite remains unchanged and passing;
- canonical Golden Course diff: zero changes under `books/functional-analysis/**`.

H4a stage completion does NOT require FTS metrics to beat Exact. A negative result is a valid completed evaluation.

## 11. Determinism and floating-point handling

BM25 is diagnostic evaluation data, not a package identity.

H4a MUST distinguish:

1. deterministic source/rank signature, which is a correctness requirement; and
2. raw BM25 floating-point values, which may vary slightly with SQLite library version.

The evaluator MUST record the SQLite version and FTS5 availability in the report environment section. It MUST NOT require byte-identical raw BM25 floats across different Python/SQLite versions.

Within one environment, repeated runs MUST produce identical ordered source signatures and aggregate metric values. Any report canonicalization that stores BM25 values must use a documented finite numeric representation and reject NaN/Inf.

## 12. Stable evaluation report

The evaluator writes generated evidence outside canonical content, for example:

```text
.build/evaluations/h4a/functional_analysis_course/report.json
```

The report is generated output and is not product authority.

Required logical fields:

```text
schema_version
stage = H4a
course identity
dataset id + content hash
profile definitions
sqlite version / FTS5 availability
per-query Exact results
per-query shadow results
positive-query relevance metrics
negative-query cleanliness metrics
aggregate metrics by profile/category
provenance gate
section-scope gate
determinism gate
public-contract regression evidence reference
canonical-tree integrity evidence reference
```

No timestamp, temp path, absolute machine path, random value, or current wall-clock time participates in dataset identity or deterministic evidence identity.

The evaluator MUST NOT output an automatic `ACTIVATE_FTS=true` flag. B4b remains an explicit future decision.

## 13. Failure semantics

H4a failures are shadow/evaluation failures only; they must never degrade the current product path.

### 13.1 FTS5 unavailable

Detect capability by attempting to create the required FTS5 virtual table in an isolated connection. If unavailable:

- mark the profile/run `SHADOW_UNAVAILABLE`;
- emit a stable diagnostic without Python traceback leakage from CLI-facing tools;
- fail the H4a evaluation command/check rather than silently substituting Exact and pretending FTS was evaluated;
- leave public Search/QA unaffected.

### 13.2 Corpus/provenance failure

If an eligible index row cannot resolve to a canonical source, book identity mismatches, or source scope is inconsistent:

- fail shadow index construction closed;
- do not emit metrics from a partially trusted index.

Rows that are explicitly non-indexable under the existing Exact candidate boundary are skipped, not misreported as provenance failures.

### 13.3 Query/dataset failure

Malformed dataset shape, duplicate query IDs, a positive query with no expected sources, a negative query with non-empty expected sources, a missing/unresolvable expected source, invalid section IDs, blank queries, invalid limits, or non-finite metric values are hard evaluation errors.

### 13.4 Profile-specific no-match

A valid query producing zero results is data, not infrastructure failure. This includes expected tokenizer limitations such as trigram queries shorter than 3 Unicode characters.

## 14. Testing strategy

Implementation MUST use TDD and record a real RED checkpoint before GREEN behavior.

### 14.1 Focused unit tests

At minimum:

- FTS5 capability detection;
- safe query quoting / operator-neutralization;
- parameterized MATCH execution;
- existing-candidate-boundary skip behavior;
- deterministic text projection, including ordered `initial_concepts_zh` joining;
- deterministic rowid assignment;
- unicode61 English/Unicode behavior fixture;
- trigram substring behavior fixture;
- trigram `<3 Unicode characters` no-match behavior;
- deterministic BM25 ordering with rowid tie-break;
- section filtering;
- canonical provenance re-validation;
- mismatched/unresolvable eligible source fail-closed;
- malformed dataset fail-closed;
- duplicate query IDs fail-closed;
- positive/negative expected-source shape validation;
- negative-query metrics exclude Recall/MRR denominators;
- zero-result is valid data;
- non-finite score rejection if encountered;
- stable report schema;
- repeat-run ordered signature determinism.

### 14.2 Golden Course evaluation tests

- committed v1 dataset validates independently;
- Exact baseline results are obtained through `RetrievalEngine.exact`;
- both FTS profiles execute over the Golden Course;
- positive query/category metrics are produced;
- negative-query cleanliness diagnostics are produced;
- all shadow hits prove canonical provenance;
- section-scoped queries never escape scope.

### 14.3 Public regression

The exact final H4a implementation HEAD MUST rerun the existing Search/QA contract suites that proved H2 equivalence, plus App API/Web/Chromium gates required by current CI.

No H4a completion claim may reuse old green runs from a different HEAD.

## 15. CI and exact-HEAD evidence

H4a should add the smallest focused CI coverage necessary to make the shadow evaluation reproducible without turning every ordinary test into a heavy benchmark.

Expected layering:

```text
FAST / focused
- dataset schema/identity tests
- shadow FTS unit tests
- H4a evaluator fixture tests

PR FULL Runtime matrix
- Python 3.11 / 3.12 / 3.13
- existing Retrieval/Search/QA regression
- Golden Course H4a evaluation command
- provenance/scope gates
- Golden canonical integrity

App UI
- existing App API
- Web tests
- typecheck/build
- real Chromium acceptance
```

If a Python matrix member lacks FTS5, that is an explicit environment failure for H4a evidence, not a reason to weaken the test or silently skip the profile.

## 16. Acceptance criteria

H4a is ready for review only when all of the following are true on one exact final HEAD:

1. The v1 evaluation dataset is versioned and independently validated.
2. Dataset relevance labels are canonical-source-derived, not retriever-generated.
3. Positive and deliberate negative query semantics are validated deterministically.
4. Both unicode61 and trigram shadow profiles build from canonical inputs without canonical writes.
5. Candidate eligibility matches the existing Exact source boundary; unsupported/non-indexable rows are skipped while inconsistent eligible sources fail closed.
6. Both profiles use safe parameterized FTS query compilation.
7. BM25 values remain evaluation-only and are not mixed with Exact scores.
8. All shadow hits pass canonical provenance checks.
9. All section-scoped shadow hits pass scope checks.
10. Repeat runs preserve ordered source signatures in the same environment.
11. Exact baseline uses the H2 `RetrievalEngine.exact` boundary.
12. Public Search/QA ranking, score, order, DTO, and error behavior remain Exact-only and regression-clean.
13. `books/functional-analysis/**` is unchanged.
14. The exact-head H4a report contains positive-query and negative-query evidence for Exact, unicode61, and trigram.
15. Required Runtime/App/Web/Chromium checks pass on the exact final HEAD.
16. External source-study provenance is recorded with fixed upstream commits/licenses; any required Drive source snapshots are archived or explicitly tracked as non-blocking `pending_sync` before the H4a checkpoint is declared fully reconciled.
17. No code path or report field automatically activates B4b.

## 17. Evidence interpretation after H4a

After implementation, the H4a review should classify evidence, not activate behavior. Suggested human-readable outcomes are:

- `FTS_EVIDENCE_PROMISING`: one or both profiles recover meaningful relevant sources or materially improve ranking without provenance/scope regressions;
- `FTS_EVIDENCE_MIXED`: gains and losses are material and a later experiment is needed;
- `FTS_EVIDENCE_NOT_PROMISING`: Exact is equal/better for the evaluated corpus or FTS limitations dominate;
- `FTS_EVALUATION_INVALID`: correctness/evidence gates failed.

These labels are review summaries, not automatic deployment gates.

Only a later explicitly approved B4b design may propose production FTS retrieval, score semantics, fusion, persistence, or public ranking changes.

## 18. External source study

H4a design was informed by source-level study and official FTS5 documentation. These references are advisory only and are not Book project authority.

### SQLite FTS5 official documentation

- URL: `https://www.sqlite.org/fts5.html`
- Relevant findings:
  - `unicode61` is the default built-in tokenizer;
  - `trigram` supports general substring matching;
  - trigram full-text substrings shorter than 3 Unicode characters do not match;
  - `bm25()` returns numerically smaller values for better matches;
  - FTS5 query strings have their own operators/syntax and therefore user text must not be treated as raw query language.

### `simonw/sqlite-utils`

- fixed commit: `56dd09702fdb9e899f577ffd51693c1f2176cb08`
- license: Apache-2.0
- studied area: FTS table creation/population and FTS query escaping patterns in `sqlite_utils/db.py`;
- adapted lesson: separate index lifecycle from application authority, and neutralize user query syntax rather than interpolating raw FTS expressions.

### `simonw/datasette`

- fixed commit: `0337fba234bf574629d56be631468ea060495fa0`
- license: Apache-2.0
- studied area: SQLite virtual/shadow table classification in `datasette/utils/sqlite.py`;
- adapted lesson: FTS5 internal shadow tables are implementation detail and must not be confused with application/domain tables or provenance authority.

No third-party source code is copied by this design. The references supply patterns and failure-awareness only.

Because these two repositories entered real source-level study, their exact-commit source snapshots should be archived under the existing Book `External_References/Snapshots` workflow or added to `governance/pending_sync.json` as non-blocking before the final H4a checkpoint is declared reconciled. This archival requirement does not block review of this design spec itself.

## 19. Implementation-shape expectation

Exact file boundaries are deferred to the implementation plan, but the design expects small isolated responsibilities rather than one large benchmark module. A likely decomposition is:

```text
runtime/
  retrieval.py                 # existing H2 production Exact seam; minimal/no change preferred
  shadow_fts.py                # evaluation-only FTS index/query primitives

evaluation/h4a/
  functional_analysis_queries.v1.json

book_core/ or evaluation helper
  h4a schema/validation/report logic

tools/
  evaluate_h4a_retrieval.py    # deterministic CLI orchestration

tests/
  focused shadow/evaluator tests
```

The implementation plan MUST verify the repository's existing patterns before freezing exact paths. It must avoid unrelated refactors.

## 20. Final design decision

H4a will use an **offline, ephemeral, shadow-only SQLite FTS5 evaluator** with two fixed tokenizer profiles (`unicode61` and `trigram`) and built-in unweighted BM25. It will compare those profiles to the existing H2 Exact baseline using a pre-authored deterministic Golden Course dataset, canonical source identities, section-scope checks, positive-query Recall@10/MRR/coverage/recovery metrics, explicit negative-query cleanliness metrics, and exact-HEAD regression evidence.

The experiment is intentionally unable to change public Search/QA behavior. Its purpose is to produce trustworthy evidence for or against a later B4b proposal, not to smuggle B4b activation into H4a.
