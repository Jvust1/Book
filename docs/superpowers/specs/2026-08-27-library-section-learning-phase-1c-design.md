# Phase 1C Design: App Library + Section Learning Runtime

Date: 2026-08-27  
Status: proposed  
Target branch: `feature/library-section-learning-phase-1c`

## 1. Product clarification

Book is **one application containing multiple independent textbook courses**.

```text
Book App
├── Functional Analysis course
│   └── one Functional Analysis textbook
├── Real Analysis course
│   └── one Real Analysis textbook
├── Complex Analysis course
│   └── one Complex Analysis textbook
└── ...
```

A new textbook such as Real Analysis is added as a **new independent course inside the same app**, not as a supplementary/reference book under Functional Analysis.

Phase 1B `CourseRuntime` keeps its generic multi-book capability for compatibility and possible future use, but the Book App product profile introduced here admits only courses with exactly one enabled main book.

Current MVP product rules:

- one App → many independent courses;
- one admitted course → exactly one enabled textbook;
- books/courses do not merge chapter trees;
- books/courses do not share Section-level user state;
- no cross-course search or knowledge-tree merge in Phase 1C.

## 2. Goals

Phase 1C introduces two runtime layers before UI work:

1. `LibraryRuntime`: the Book App course catalog.
2. `SectionLearningRuntime`: a deterministic, source-backed learning view for one Section.

First real end-to-end fixture:

```text
Book App
→ functional_analysis_course
→ chapter_01
→ ch01_s01
→ Preview / Learn / Review / Practice
```

The implementation must preserve all Phase 1A/1B runtime gates and must not duplicate parsing already owned by `BookRuntime` or `CourseRuntime`.

## 3. Non-goals

Phase 1C does **not** implement:

- graphical/mobile/web UI;
- Real Analysis or any second real textbook import;
- user accounts;
- progress persistence or a database;
- notes, mistakes, lectures, exams, mastery, or study history;
- AI-generated explanations, summaries, objectives, questions, or answers;
- semantic CourseKnowledgeTree construction;
- cross-course search or QA;
- cross-course concept alignment;
- textbook replacement/migration workflows;
- generated static learning JSON for all 132 sections.

## 4. Architecture

```text
library/library.json
        ↓
LibraryRuntime
        ↓
CourseRuntime
        ↓
BookRuntime
        ↓
SectionLearningSource
        ↓
SectionLearningRuntime
        ↓
Preview / Learn / Review / Practice
```

Responsibilities:

- `LibraryRuntime` owns which independent courses appear in the App.
- `CourseRuntime` validates/opens one course.
- `BookRuntime` remains the sole parser/normalizer for structured textbook assets.
- `SectionLearningSource` is a deterministic projection of one real Section and its source-backed objects.
- `SectionLearningRuntime` exposes four learning-mode views over that source without inventing content.

No new layer may re-read raw structure JSON merely to recreate information already exposed by a lower runtime.

## 5. Library manifest

Add:

```text
library/library.json
```

Schema version:

```text
library_manifest_v1
```

Initial real manifest:

```json
{
  "schema_version": "library_manifest_v1",
  "library_id": "book_app_library",
  "name": "Book",
  "courses": [
    {
      "course_id": "functional_analysis_course",
      "name": "Functional Analysis",
      "path": "../courses/functional-analysis",
      "enabled": true,
      "order": 10
    }
  ]
}
```

Required top-level fields:

- `schema_version`
- `library_id`
- `name`
- `courses`

Required course-entry fields:

- `course_id`
- `name`
- `path`
- `enabled`
- `order`

### 5.1 Library validation

`LibraryRuntime.open()` rejects:

- unsupported `schema_version`;
- missing/empty `library_id`;
- missing/empty `name`;
- non-list or empty `courses`;
- zero enabled courses;
- malformed course entries;
- duplicate enabled `course_id` values;
- non-integer `order` values (`bool` is not accepted as an integer order);
- enabled course paths that are missing;
- enabled course paths escaping the repository root;
- enabled course manifest `course_id` that does not match the library entry;
- enabled courses that cannot open through normal `CourseRuntime.open()`;
- enabled courses that violate the Phase 1C single-book product profile.

Disabled entries are catalog metadata only and are not opened, so an incomplete future course may be registered with `enabled=false` while its textbook is being prepared. At least one other course must remain enabled.

### 5.2 Single-book product profile

An enabled course admitted by `LibraryRuntime` must satisfy all of the following:

1. `CourseRuntime.open()` succeeds normally.
2. `len(course.book_ids()) == 1`.
3. that single mounted book is `course.main_book()`.
4. the mounted book is already `RUNTIME_READY` because CourseRuntime/BookRuntime enforce that gate.

`CourseRuntime` itself is **not** narrowed or rewritten in Phase 1C. The Book App profile is enforced only by `LibraryRuntime`.

## 6. LibraryRuntime public API

Required Phase 1C API:

```python
from runtime import LibraryRuntime

library = LibraryRuntime.open("library")

library.library_id
library.name
library.course_ids()
library.courses()
library.course("functional_analysis_course")
library.summary()
```

For isolated tests, the API also accepts an explicit root:

```python
library = LibraryRuntime.open(library_dir, repository_root=repo_root)
```

Rules:

- enabled courses are returned in deterministic `(order, manifest_position)` order;
- `course(course_id)` returns an already-mounted `CourseRuntime`;
- unknown/disabled course IDs raise a library runtime error;
- no implicit filesystem discovery of courses is used;
- adding a future textbook means adding a new `courses/<slug>/course.json` and a new enabled catalog entry once that course is ready.

Suggested errors:

```text
LibraryRuntimeError
├── LibraryManifestError
├── LibraryCourseResolutionError
└── LibraryRuntimeBlockedError
```

## 7. Repository root and path trust

`LibraryRuntime` follows the same fail-closed trust model as CourseRuntime.

Resolution rules:

1. canonicalize the supplied library directory;
2. if `repository_root` is supplied, canonicalize and use it;
3. otherwise require the standard `<repo_root>/library` layout and infer the root as the parent of `library`;
4. require the resolved library directory itself to lie under the repository root;
5. resolve course paths relative to the library directory;
6. canonicalize each enabled course path;
7. require each enabled course path to remain below the repository root;
8. open it through `CourseRuntime.open()`;
9. verify canonical `course_id` equality.

If the library is in a nonstandard layout and no explicit `repository_root` is supplied, loading fails rather than guessing.

The manifest cannot inject imports, URLs, shell commands, or external filesystem paths.

## 8. SectionLearningSource

`SectionLearningSource` is the stable evidence layer used by all four learning modes.

It is generated at runtime from already-loaded `CourseRuntime` / `BookRuntime` objects and is not stored as one static JSON file per Section.

Suggested fields:

```text
course_id
book_id
chapter_id
section_id
number
title_en
title_zh
pdf_page_start
pdf_page_end
printed_page_start
printed_page_end
source_batches
page_map_start
page_map_end
objects[]
figures[]
translation_sources[]
```

Object projection:

```text
kind = "object"
id
type
number
name_en
name_zh
formula
pdf_page
printed_page
source_anchor
source_batch
```

Figure projection:

```text
kind = "figure"
id
title_en
title_zh
pdf_page
printed_page
source_anchor
source_batch
```

Translation-source projection:

```text
batch_id
available
```

Phase 1C does not slice batch-level translation Markdown into invented Section paragraphs.

### 8.1 Source selection

For one Section:

- Section identity/metadata comes from `CourseRuntime.section()`.
- Objects come from `BookRuntime.objects_for_section(section_id)`.
- Figures are included only when their anchored PDF page lies inside the Section PDF page range.
- PageMap boundary rows come from `BookRuntime.page_map_row()`.
- Translation availability comes from the Section's `source_batches` and whether `BookRuntime.translation_text(batch_id)` returns text.

Source ordering is deterministic:

- objects preserve the order returned by `BookRuntime.objects_for_section()`;
- figures sort by `(pdf_page, id)`, with missing pages ordered last;
- source batches sort by their order in `RuntimeSection.source_batches` after stable de-duplication.

The source layer never fabricates missing anchors or fills missing textbook facts from model knowledge.

## 9. SectionLearningRuntime

Required Phase 1C API:

```python
from runtime import LibraryRuntime, SectionLearningRuntime

library = LibraryRuntime.open("library")
course = library.course("functional_analysis_course")
learning = SectionLearningRuntime.from_course(course, "ch01_s01")

source = learning.source()
preview = learning.preview()
learn = learning.learn()
review = learning.review()
practice = learning.practice()
```

`SectionLearningRuntime` accepts a selected `CourseRuntime`; therefore an app-level Section ID is never used without a course namespace.

Unknown Sections fail explicitly. There is no fallback to another course or book.

Suggested errors:

```text
SectionLearningRuntimeError
├── SectionLearningSourceError
└── SectionLearningModeError
```

## 10. Four learning modes

The four modes are parallel and independently callable. None unlocks another.

Phase 1C modes are deterministic projections, not AI-authored lessons.

### 10.1 Preview

Purpose: orient the learner before reading.

Contains only source-supported information:

- Section number/title;
- chapter/section IDs;
- textbook page range;
- compact index of object types and source IDs;
- figure source IDs;
- translation-source batch IDs and availability.

It does not invent learning objectives or prerequisites.

### 10.2 Learn

Purpose: expose the complete source-backed material available to the runtime.

Contains references to:

- all Section objects in deterministic textbook order;
- all in-range figures in deterministic order;
- formulas already embedded in source objects;
- source anchor/page provenance;
- translation-source references.

Phase 1C does not generate explanatory prose beyond structured source data.

### 10.3 Review

Purpose: provide a compact source-backed review subset.

Object `type` is normalized with `strip().casefold()` only for policy comparison. The exact Phase 1C review type set is:

```text
definition
theorem
proposition
lemma
corollary
formula
```

The original source `type` value is preserved in output. Unknown object types are not reclassified.

If none of these types exists in the Section, Review returns a valid empty `items[]` while the full source remains available.

No AI summary is generated.

### 10.4 Practice

Purpose: expose textbook practice material already assigned to the Section.

Object `type` is normalized with `strip().casefold()` for policy comparison. The exact Phase 1C practice type set is:

```text
exercise
problem
```

The original source `type` value is preserved in output.

If the Section has no such object, Practice returns a valid empty `items[]`. Phase 1C never invents questions.

## 11. Mode payload contract and traceability

All four modes return a common envelope:

```text
mode
course_id
book_id
chapter_id
section_id
source_status
items[]
source_refs[]
```

`source_status` reports source availability, not learner progress.

Every mode item is a reference, not a copied independent fact record:

```text
kind       // object | figure | translation
source_id  // object/figure id, or batch_id for translation
```

Traceability key is therefore:

```text
(kind, source_id)
```

not `source_id` alone. This prevents an object ID and figure ID from becoming ambiguous if they happen to use the same string.

Rules:

- every `(kind, source_id)` in a mode payload must exist in its `SectionLearningSource`;
- mode payloads may add presentation metadata such as labels/counts, but may not alter source identity or source facts;
- the same canonical `course_id`, `book_id`, `chapter_id`, and `section_id` are preserved across source and all four modes.

## 12. Course isolation

Phase 1C establishes the isolation key later persistent features must follow:

```text
course_id + section_id
```

A future Real Analysis course may contain a Section ID resembling one in Functional Analysis. Records remain independent because the course namespace differs.

No Phase 1C library-level API accepts an unqualified Section ID. A Section is always reached through a selected `CourseRuntime`.

## 13. Minimum repository layout

Expected focused implementation files:

```text
library/library.json
runtime/library_runtime.py
runtime/section_learning_runtime.py
runtime/__init__.py
tests/test_library_runtime.py
tests/test_section_learning_runtime.py
runtime/README.md
README.md
.github/workflows/runtime-reference-tests.yml
```

Test helpers may add files under `tests/fixtures/` if needed.

No Functional Analysis structured textbook source file is expected to change in Phase 1C.

## 14. TDD test design

### 14.1 Library manifest tests

At minimum:

1. valid library opens;
2. unsupported schema version fails;
3. missing library ID fails;
4. empty courses fails;
5. zero enabled courses fails;
6. duplicate enabled course ID fails;
7. malformed course entry fails;
8. missing enabled course path fails;
9. course path escape fails;
10. nonstandard layout without explicit repository root fails;
11. explicit repository root supports isolated fixture layout;
12. canonical course ID mismatch fails;
13. blocked enabled course fails;
14. disabled incomplete course is ignored when another enabled course exists;
15. deterministic course ordering works;
16. multi-book CourseRuntime is rejected by the Book App single-book profile;
17. exactly-one-main-book course is accepted.

### 14.2 Section source tests

At minimum:

18. known Section builds a source;
19. unknown Section fails;
20. source identity matches course/book/section;
21. source objects come from `objects_for_section()`;
22. source object order is deterministic;
23. figure inclusion respects Section page range;
24. figure order is deterministic;
25. PageMap boundaries are preserved when available;
26. missing optional anchor remains missing rather than fabricated;
27. translation-source availability is represented without slicing invented text.

### 14.3 Four-mode tests

At minimum:

28. Preview preserves canonical Section identity;
29. Learn references all source objects and in-range figures;
30. Review returns only the exact review-policy types;
31. Practice returns only the exact practice-policy types;
32. empty Review subset is valid;
33. empty Practice subset is valid;
34. every mode `(kind, source_id)` maps back to the source;
35. four modes are independently callable with no ordering lock.

### 14.4 Real Functional Analysis fixture

At minimum:

36. `LibraryRuntime.open("library")` succeeds on a clean checkout;
37. library exposes exactly `functional_analysis_course` in Phase 1C;
38. the course exposes exactly one book;
39. canonical book ID is `stein_shakarchi_functional_analysis_2011`;
40. existing 8-Chapter / 132-Section navigation remains intact;
41. `ch01_s01` resolves through the selected course;
42. `SectionLearningSource` builds for `ch01_s01`;
43. Preview/Learn/Review/Practice all build for `ch01_s01`;
44. existing 442-row PageMap and 1493-record search-index readiness checks remain unchanged.

## 15. CI

Extend the existing `Runtime reference tests` workflow rather than creating another overlapping workflow.

CI must:

- watch `library/**` in addition to existing runtime/course paths;
- compile `runtime/library_runtime.py` and `runtime/section_learning_runtime.py`;
- run existing BookRuntime and CourseRuntime tests unchanged;
- run LibraryRuntime and SectionLearningRuntime tests;
- retain Python 3.11 / 3.12 / 3.13 coverage;
- retain the Python 3.13 real Functional Analysis rebuild/readiness gate;
- add a real Library → Course → SectionLearning acceptance check.

No CI step may automatically commit generated runtime files to `main`.

## 16. Documentation changes during implementation

The current root README still presents "one course supports multiple textbooks" as a product principle. Phase 1C implementation must update it to the confirmed product rule:

```text
one App → multiple independent textbook courses
one current product course → one textbook
```

The generic multi-book capability of `CourseRuntime` may be documented separately as a lower-level compatibility capability, not as the Book App's current product model.

`runtime/README.md` must document LibraryRuntime and SectionLearningRuntime usage and retain the distinction between `STRUCTURED_COMPLETE` and `RUNTIME_READY`.

The broader future data model (`CourseKnowledgeTree`, cross-book concepts, lectures, etc.) may remain documented as future architecture. Phase 1C does not implement or delete it.

## 17. Acceptance criteria

Phase 1C is complete only when all are true:

1. `LibraryRuntime.open("library")` succeeds on a clean checkout.
2. The library contains Functional Analysis as an enabled independent course.
3. The admitted course has exactly one enabled main textbook.
4. Canonical book ID remains `stein_shakarchi_functional_analysis_2011`.
5. Functional Analysis still exposes 8 Chapters and 132 Sections.
6. `SectionLearningRuntime.from_course(course, "ch01_s01")` succeeds.
7. Preview, Learn, Review, and Practice preserve canonical course/book/chapter/section identity.
8. Every mode item maps to its source by `(kind, source_id)`; Phase 1C invents no textbook facts, questions, or anchors.
9. Disabled/incomplete future courses do not block the library if at least one valid course is enabled; invalid enabled courses do block it.
10. Repository path containment is enforced for catalog course paths.
11. Existing BookRuntime and CourseRuntime tests remain green.
12. New LibraryRuntime and SectionLearningRuntime tests are green on Python 3.11 / 3.12 / 3.13.
13. The real Functional Analysis readiness/rebuild gate remains green.
14. Root/runtime documentation reflects the one-App/many-independent-courses product model.
15. No Phase 1C change modifies Functional Analysis structured textbook source assets.

## 18. Follow-on milestone

After this runtime contract is merged, the next milestone can build the App UI shell:

```text
Library screen
→ Course screen
→ Chapter screen
→ Section screen
   ├── Preview
   ├── Learn
   ├── Review
   └── Practice
```

Progress persistence, notes/mistakes, AI explanations, AI question generation, and additional textbooks should be layered only after this first real Section path is stable and accepted.
