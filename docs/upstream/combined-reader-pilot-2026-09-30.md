# Original chapter integration candidate

This candidate composes the reader stack from Draft PRs #58–#60 and #62–#65 with the independently based SymPy hardening in Draft PR #61. It preserves those review branches and does not merge or deploy `main`. The source heads are reader `c73e361a527c2832650c0e4eaba5c64ac74d3e36` and symbolic checker `69eb1bbe9858941bba5d4d23c3d4d3c0c33bfe26`, on main `805510f86546709b6f67c9e9079943f205c2c245`.

## One actual input-to-output pilot

`app_tests/synthetic_chapter.py` writes a wholly original one-chapter/one-section repository in a temporary directory. It includes a definition, an exercise, a source anchor, printed/physical page mapping and lexical search records. `app_tests/synthetic_pilot_server.py` is an explicit test-only FastAPI factory using the real BookAppService, Library/Course/Book runtimes, retrieval, source resolver, QA evidence gate and SQLite StudyRecord repository. It does not load the canonical textbook directory. Production startup remains unchanged.

The browser pilot uses the production build without HTTP response mocks:

1. Open the file-backed library, chapter and section; preview objects and study the rendered formulas.
2. Explicitly complete the study mode, then navigate to its real source DTO and check physical PDF page 2 versus printed page 1 and the exact source anchor.
3. Select an original two-page PDF generated in the test. PDF.js renders the page, then streams a selected-page text index into the actual Fuse worker. A misspelt query locates original text; nothing is uploaded or persisted and the file is still explicitly unverified.
4. Return to the section and ask a question. The deterministic provider receives real retrieved evidence; the actual API and Zod boundary validate the resulting citation. React Markdown/KaTeX render the answer. The citation returns to the same source, reusing TanStack's short-lived exact-identity cache without retaining the PDF or index.
5. Reveal the review content, then open the exercise. Real math.js worker output for the original `2+2` exercise is passed to the actual isolated SymPy diagnostic CLI with caller-supplied expected value `4`. Correct, incorrect and forbidden-input outcomes are checked. The CLI is invoked by the test harness, **not exposed as a browser grading endpoint**. Neither calculation nor diagnostic changes StudyRecord progress.
6. Leave and reenter practice to verify scratchpad cleanup. Desktop and 390px flows check console errors and unexpected external/writing requests. Screenshot artifacts contain only original test material.

Connected review also reproduced and repaired persisted-conversation identity gaps: each cached answer must match its preceding question, message IDs must be unique even after reload, and return routes stay inside the same course QA screen. The frozen session shape is preserved. A legacy selected source ID is only used when its citations resolve to one unambiguous book/kind/ID tuple; an object, figure or another book sharing the ID cannot inherit the wrong QA-return affordance. The browser pilot includes reload and follow-up with unique restored message IDs.

The existing 33 browser cases are retained, including cancelled PDF/Fuse/calculator work, invalid responses, stale-cache visibility and authorization failure recovery. The pilot adds two longer connected journeys; it does not replace individual safety tests.

## Reproduce

Install the existing App dependencies and the pinned optional checker:

```sh
python -m pip install -r app/api/requirements.txt
python -m pip install --require-hashes -r requirements-extras/symbolic.txt
npm --prefix app/web ci --no-audit
python -m unittest app_tests.test_synthetic_chapter -v
python -m uvicorn app_tests.synthetic_pilot_server:create_app --factory --host 127.0.0.1 --port 8000
```

In another shell, build and preview the app on its existing loopback port:

```sh
cd app/web
npm run build
npx vite preview --host 127.0.0.1 --port 5173 --strictPort
# Then, in another shell in app/web:
npm run e2e -- --config playwright.pilot.config.ts
```

The temporary fixture and study database are removed when the test server shuts down. Do not run this fixture server as a deployment. The standard `app.api.main:app` startup and frozen API contracts remain unchanged. Python/SymPy run only on the test host; no external model credentials are needed.

## Upstream provenance

Official repository metadata was rechecked at 2026-09-30 21:58 UTC. Versions, source tags/commits, package integrities, complete licenses and required notices remain pinned in the individual integration records and lockfiles.

| Runtime upstream | Stars | License | Exact package |
| --- | ---: | --- | --- |
| [KaTeX/KaTeX](https://github.com/KaTeX/KaTeX) | 20,414 | MIT | katex 0.18.10 |
| [mozilla/pdf.js](https://github.com/mozilla/pdf.js) | 53,965 | Apache-2.0 | pdfjs-dist 6.3.289 |
| [remarkjs/react-markdown](https://github.com/remarkjs/react-markdown) | 15,899 | MIT | react-markdown 10.1.0 |
| [josdejong/mathjs](https://github.com/josdejong/mathjs) | 15,079 | Apache-2.0 | mathjs 15.2.0 |
| [krisk/Fuse](https://github.com/krisk/Fuse) | 20,496 | Apache-2.0 | fuse.js 7.5.0 |
| [colinhacks/zod](https://github.com/colinhacks/zod) | 44,046 | MIT | zod 4.6.5 |
| [TanStack/query](https://github.com/TanStack/query) | 50,386 | MIT | @tanstack/react-query and query-core 5.104.0 |
| [sympy/sympy](https://github.com/sympy/sympy) | 14,981 | BSD-3-Clause core plus bundled notices | sympy 1.14.0 |

GitHub labels SymPy's aggregate license `NOASSERTION`; this is not presented as an SPDX-only license grant. Its full upstream LICENSE is preserved in `licenses/SymPy-1.14.0-LICENSE.txt`. SymPy was already present conceptually and its safety hardening is not counted as an eighth new upstream integration.

## Verification boundaries

Local combined checks: 350 Runtime tests, 101 App tests, 260 web tests, TypeScript and architecture fitness. Hosted exact-head CI is the production-browser/build gate; the local browser sandbox does not permit Chromium startup. The new browser journey is pending until that gate runs on this candidate. Existing branch CI is evidence for those branches, not a substitute for the candidate's exact head.

No canonical `books/`, `courses/` or `library/` content is changed. This is an original engineering pilot, not full-book content verification, proof correctness, file-edition authentication, a Windows release or a production deployment. QA generation is deterministic fake-provider coverage; no claim is made about live paid-model quality. Optional npm audit remains unrun because transmission of the dependency manifest was not approved; installations and CI explicitly use `--no-audit`.
