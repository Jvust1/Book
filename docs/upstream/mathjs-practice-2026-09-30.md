# math.js practice scratchpad

## Upstream identity and actual code use

- Official repository: https://github.com/josdejong/mathjs
- Official REST observation: **15,079 stars**, rechecked 2026-09-30 19:51 UTC via https://api.github.com/repos/josdejong/mathjs.
- Exact package: **mathjs 15.2.0**, official `v15.2.0` tag/npm gitHead **fee4561840043a7473962367bbae6f15bbb3cebb**.
- License: **Apache-2.0**. Both the unmodified LICENSE and NOTICE are included in `app/web/public/licenses/` and the production build.
- Inspected upstream: expression `FunctionNode` safe-property compilation, parsed Node shapes, numeric/matrix execution, and https://mathjs.org/docs/expressions/security.html.

`SectionPage` Practice mode → `PracticeScratchpad` → cancellable Worker → actual math.js `parse` / AST `compile().evaluate` / `format` → typed numeric output.

The application previously exposed textbook exercise source objects without an interactive calculation aid. This adds explicit user-triggered arithmetic, complex-number and small-matrix calculations while preserving source/answer distinctions. No textbook solution is generated or silently supplied.

## User-facing capability

- Explicit Calculate action and Cancel/Clear controls; presets for trigonometry, determinant and inverse matrix only fill the input.
- Numeric and complex values, vectors and small matrices; radians are explicitly stated.
- Double-precision approximate output with engine identity. It is calculation assistance, not proof checking, a textbook answer or an automatic grade.
- No input/results are sent to an API, provider, browser durable storage or StudyRecord. The existing reading-mode touch/completion behavior is unchanged.
- Leaving Practice, changing section, clearing or unmounting stops active work and discards temporary calculator state.

## Restricted execution and lifecycle

- Only numeric constants, pi/e/i, arithmetic, bounded literal powers and an explicit small function set are allowed.
- Assignments, property/index access, custom functions, imports, expression re-parsing, object/string literals, ranges, allocation helpers and random functions are rejected.
- Upstream dangerous namespace operations are disabled as a second boundary after capturing the trusted parser.
- Limits: 2,048 input characters, 128 AST nodes, depth 20, two array levels with eight elements each, literal exponent magnitude at most 128 and bounded finite numeric output.
- Production evaluation runs in a fresh Web Worker. Five-second timeout, cancellation, errors and completion all terminate it and remove callbacks/timers. This protects main-thread responsiveness; it is not a hard browser memory sandbox or a guarantee against unknown engine defects.
- Only matching request ID, expression, engine version and bounded result shape are accepted. Late results cannot restore cleared or abandoned work.
- No CDN is configured. The production math worker is a separately built local asset, included in static precache.

## Verification

- Local: **156/156 web tests passed** after the parenthesized-exponent correction. The initial implementation passed local TypeScript and production build. Later build reruns encountered the shared environment memory limit; exact-head CI separately runs both gates.
- New tests use real math.js for arithmetic, matrices, complex values and negative capability cases; worker transport/lifecycle and UI state tests cover timeout, cancellation, duplicate submit, clearing and unmount.
- Local verification used bounded Node heap and two Vitest workers to fit the shared execution environment; test cases/assertions were not removed.
- Three new browser cases exercise real workers at desktop/390px, preserve the existing missing-solution notice, check no new API POST or browser-storage writes, reject an unsafe expression, and recover after interrupted worker startup/cancellation.
- Exact-head GitHub CI has 21 browser cases including inherited reader coverage. Final browser results and synthetic screenshots are checked after publication; local browser execution is unavailable in this managed environment.

This branch is stacked on the structured QA reader (#60). It does not include or supersede the independent SymPy safety PR (#61). No canonical assets, private PDFs, model calls, automatic grading, native release, merge or deployment is introduced.

### Built-worker acceptance

The first exact-head browser run passed after one cold development-module startup retry. Acceptance now builds and serves production assets, including the emitted math.js worker, with the same five-second bound and all existing assertions. The interrupted-startup case explicitly waits for the worker network request before cancellation; only this deliberate network-interception case blocks service workers. Final rerun status is tracked against the follow-up commit.

A read-only independent review found no high-impact grammar, capability or cancellation bug. Its reproduced usability gap (`2^(-2)` and `2^(2)`) is fixed by bounded parenthesis unwrapping, with positive and over-limit regression tests. No expression evaluation or exponent limit is relaxed.
