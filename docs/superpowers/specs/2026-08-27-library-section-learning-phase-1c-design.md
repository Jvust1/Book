# Phase 1C Design: App Library + Section Learning Runtime

Date: 2026-08-27  
Status: proposed  
Target branch: `feature/library-section-learning-phase-1c`

## 1. Product clarification

Book is **one application containing multiple independent textbook courses**.

The product model for the current app is:

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

Phase 1B `CourseRuntime` retains its generic multi-book capability for backward compatibility and possible future use, but the Book App product profile introduced in Phase 1C admits only courses with exactly one enabled main book.

This product rule is authoritative for the current MVP:

- one App → many independent courses;
- one admitted course → exactly one enabled textbook;
- books/courses do not merge chapter trees;
- books/courses do not share learning records;
- no cross-course search or knowledge-tree merge in Phase 1C.

## 2. Goals

Phase 1C introduces the two runtime layers required before UI work:

1. `LibraryRuntime`: the Book App course catalog.
2. `SectionLearningRuntime`: a deterministic, source-backed learning view for one Section.

The first real end-to-end fixture remains:

```text
Book App
→ functional_analysis_course
→ chapter_01
→ ch01_s01
→ Preview / Learn / Review / Practice
```

The implementation must preserve all existing Phase 1A/1B runtime gates and must not duplicate parsing already owned by `BookRuntime` or `CourseRuntime`.

## 3. Non-goals

Phase 1C does **not** implement:

- graphical/mobile/web UI;
- Real Analysis or any second real textbook import;
- user accounts;
- progress persistence or a database;
- notes, mistakes, lectures, exams, mastery, or study history;
- AI-generated explanations, summaries, objectives, questions, or answers;
- semantic CourseKnowledgeTree construction;
- cross-course search;
- cross-course question answering;
- cross-course concept alignment;
- textbook replacement/migration workflows;
- generated static learning JSON for all 132 sections.

These remain later milestones.

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

Responsibilities stay isolated:

- `LibraryRuntime` knows which independent courses belong to the App.
- `CourseRuntime` continues to validate/open a course and its book runtime(s).
- `BookRuntime` remains the sole parser/normalizer for structured textbook assets.
- `SectionLearningSource` is a deterministic projection of one real Section and its source-backed objects.
- `SectionLearningRuntime` exposes four learning-mode views over that source without inventing content.

No layer may re-read raw structure JSON merely to recreate information that an existing lower runtime already exposes.

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
- malformed course entries;
- duplicate enabled `course_id` values;
- unsupported/non-integer `order` values;
- enabled course paths that are missing;
- enabled course paths escaping the repository root;
- enabled course manifest `course_id` that does not match the library entry;
- enabled courses that cannot open through normal `CourseRuntime.open()`;
- enabled courses that violate the Phase 1C single-book product profile.

Disabled entries are catalog metadata only and are not opened, so an incomplete future course may be registered with `enabled=false` while its textbook is being prepared.

### 5.2 Single-book product profile

An enabled course admitted by `LibraryRuntime` must satisfy all of the following:

1. `CourseRuntime.open()` succeeds normally.
2. `len(course.book_ids()) == 1`.
3. that one book is `course.main_book()`.
4. the mounted book is already `RUNTIME_READY` because CourseRuntime/BookRuntime enforce that gate.

`CourseRuntime` itself is **not** narrowed or rewritten in Phase 1C. Its generic multi-book capability remains available below the product layer; `LibraryRuntime` is where the Book App profile is enforced.

## 6. LibraryRuntime public API

Suggested API:

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

Rules:

- enabled courses are returned in deterministic `(order, manifest position)` order;
- `course(course_id)` returns an already-mounted `CourseRuntime`;
- unknown/disabled course IDs raise a library runtime error;
- no implicit filesystem discovery is used;
- adding a future textbook means adding a new `courses/<slug>/course.json` and a new catalog entry.

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
2. infer repository root only from the standard `<repo_root>/library` layout, or accept an explicit repository root if the API later requires isolated test fixtures;
3. resolve course paths relative to the library directory;
4. canonicalize resolved course paths;
5. require each enabled course path to remain below the repository root;
6. open it through `CourseRuntime.open()`;
7. verify canonical `course_id` equality.

The manifest cannot inject imports, URLs, shell commands, or external filesystem paths.

## 8. SectionLearningSource

`SectionLearningSource` is the stable evidence layer used by all four learning modes.

It is generated at runtime from already-loaded `CourseRuntime` / `BookRuntime` objects and is not stored as one static JSON file per section.

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

Each object projection preserves source identity and provenance where available:

```text
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

Each figure projection preserves:

```text
id
title_en
title_zh
pdf_page
printed_page
source_anchor
source_batch
```

`translation_sources[]` contains references to relevant source batches and whether a non-partial translation layer is available. Phase 1C does not attempt fragile free-text slicing of a batch-level translation Markdown file into invented section paragraphs.

### 8.1 Source selection

For one Section:

- Section identity/metadata comes from `CourseRuntime.section()`.
- Objects come from `BookRuntime.objects_for_section(section_id)`.
- Figures are included only when their anchored PDF page lies inside the Section PDF page range.
- PageMap boundary rows come from `BookRuntime.page_map_row()`.
- Translation availability comes from the Section's `source_batches` and `BookRuntime.translation_text(batch_id)` availability, but source text is not rewritten or summarized in Phase 1C.

The source layer never fabricates missing anchors or fills missing textbook facts from model knowledge.

## 9. SectionLearningRuntime

Suggested API:

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

`SectionLearningRuntime` only accepts a Section belonging to the course's single admitted main book.

Suggested errors:

```text
SectionLearningRuntimeError
├── SectionLearningSourceError
└── SectionLearningModeError
```

Unknown Sections fail explicitly; there is no fallback to a different course or book.

## 10. Four learning modes

The four modes are parallel and independent. None unlocks another.

Phase 1C modes are deterministic projections, not AI-authored lessons.

### 10.1 Preview

Purpose: orient the learner before reading.

Contains only source-supported information:

- Section number/title;
- chapter/section IDs;
- textbook page range;
- compact index of source object types and identifiers;
- available figure identifiers;
- available translation-source batch identifiers.

It does not invent learning objectives or prerequisites.

### 10.2 Learn

Purpose: expose the complete source-backed learning material available to the runtime.

Contains:

- all Section objects in deterministic textbook order;
- formulas embedded in those objects;
- in-range figure references;
- source anchors/page provenance;
- translation-source references.

Phase 1C does not generate explanatory prose beyond what is already present in structured assets.

### 10.3 Review

Purpose: provide a compact source-backed review view.

The runtime selects review-worthy structured objects by deterministic type policy, including known mathematical statement/formula categories such as definitions, theorems, propositions, lemmas, corollaries, and formulas when those categories exist in the source.

Unknown object types are not silently reclassified. The source payload remains accessible even if the review subset is empty.

No AI summary is generated in Phase 1C.

### 10.4 Practice

Purpose: expose textbook practice material already present in the Section.

Includes only existing structured practice objects such as `exercise` / `problem` categories that are already assigned to the Section by BookRuntime.

If the Section has no such object, `practice()` returns a valid empty practice payload. Phase 1C does not invent questions to avoid presenting fabricated textbook content as source material.

AI-generated variants can be a later layer with explicit provenance distinct from textbook questions.

## 11. Mode payload contract

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

Every `items[]` entry must be traceable to an ID from `SectionLearningSource`.

The same `section_id` and canonical `book_id` must be preserved across all four mode payloads.

## 12. Course isolation

Phase 1C establishes the isolation rule that later persistent features must follow:

```text
course_id + section_id
```

is the minimum namespace for Section-level user state.

A future Real Analysis course may contain a Section ID that resembles one in Functional Analysis; records must still remain independent because the course namespace differs.

No Phase 1C API accepts an unqualified Section ID at the app/library level. A Section is always reached through a selected `CourseRuntime`.

## 13. Minimum repository layout

Phase 1C implementation is expected to add or modify only focused files such as:

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

The exact test fixture helpers may add files under `tests/fixtures/` if needed.

No textbook structure files are expected to change for Phase 1C.

## 14. TDD test design

### 14.1 Library manifest tests

At minimum:

1. valid library opens;
2. unsupported schema version fails;
3. missing library ID fails;
4. empty courses fails;
5. duplicate enabled course ID fails;
6. malformed course entry fails;
7. missing enabled course path fails;
8. course path escape fails;
9. canonical course ID mismatch fails;
10. blocked enabled course fails;
11. disabled incomplete course is ignored;
12. deterministic course ordering works;
13. multi-book CourseRuntime is rejected by the Book App single-book profile;
14. exactly-one-main-book real course is accepted.

### 14.2 Section source tests

At minimum:

15. known Section builds a source;
16. unknown Section fails;
17. source identity matches course/book/section;
18. source objects come from `objects_for_section()`;
19. source object order is deterministic;
20. figure inclusion respects Section page range;
21. PageMap boundaries are preserved when available;
22. missing optional anchor remains missing rather than fabricated;
23. translation-source availability is represented without slicing invented text.

### 14.3 Four-mode tests

At minimum:

24. Preview returns the same canonical Section identity;
25. Learn exposes all source objects;
26. Review returns only deterministic review-policy object types;
27. Practice returns only existing practice object types;
28. empty practice material returns a valid empty payload;
29. every mode item maps back to a source item;
30. four modes are independently callable with no ordering lock.

### 14.4 Real Functional Analysis fixture

At minimum:

31. `LibraryRuntime.open("library")` succeeds on a clean checkout;
32. library exposes exactly `functional_analysis_course` in Phase 1C;
33. the course exposes exactly one book;
34. canonical book ID is `stein_shakarchi_functional_analysis_2011`;
35. the existing 8-Chapter / 132-Section course navigation remains intact;
36. `ch01_s01` resolves through the library-selected course;
37. `SectionLearningSource` builds for `ch01_s01`;
38. Preview/Learn/Review/Practice all build for `ch01_s01`;
39. existing 442-row PageMap and 1493-record search-index readiness checks remain unchanged.

## 15. CI

Extend the existing `Runtime reference tests` workflow rather than creating a second overlapping workflow.

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

The current root README still presents "one course supports multiple textbooks" as a product principle. Phase 1C implementation must update that wording to the newly confirmed product rule:

```text
one App → multiple independent textbook courses
one current product course → one textbook
```

The generic multi-book capability of `CourseRuntime` may be documented separately as a lower-level compatibility capability, not as the Book App's current product model.

`runtime/README.md` must document LibraryRuntime and SectionLearningRuntime usage and retain the distinction between `STRUCTURED_COMPLETE` and `RUNTIME_READY`.

The broader future data model (`CourseKnowledgeTree`, cross-book concepts, lectures, etc.) may remain documented as future architecture; Phase 1C does not implement or delete it.

## 17. Acceptance criteria

Phase 1C is complete only when all are true:

1. `LibraryRuntime.open("library")` succeeds on a clean checkout.
2. The library contains the Functional Analysis course as an enabled independent course.
3. The admitted course has exactly one enabled main textbook.
4. The canonical book ID remains `stein_shakarchi_functional_analysis_2011`.
5. Functional Analysis still exposes 8 Chapters and 132 Sections.
6. `SectionLearningRuntime.from_course(course, "ch01_s01")` succeeds.
7. Preview, Learn, Review, and Practice payloads all preserve canonical course/book/section identity.
8. Every mode item is source-traceable; Phase 1C invents no textbook facts, questions, or anchors.
9. Disabled/incomplete future courses do not block the library; invalid enabled courses do block it.
10. Repository path containment is enforced for catalog course paths.
11. Existing BookRuntime and CourseRuntime tests remain green.
12. New LibraryRuntime and SectionLearningRuntime tests are green on Python 3.11 / 3.12 / 3.13.
13. The real Functional Analysis readiness/rebuild gate remains green.
14. Root/runtime documentation reflects the one-App/many-independent-courses product model.
15. No Phase 1C change modifies Functional Analysis structured textbook source assets.

## 18. Follow-on milestone

After this runtime contract is merged, the next milestone can build the actual App UI shell:

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

Progress persistence, notes/mistakes, AI explanations, question generation, and additional textbooks should be layered only after this first real Section path is stable and accepted.
