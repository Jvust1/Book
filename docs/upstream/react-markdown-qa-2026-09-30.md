# Structured QA answer rendering

## Upstream identity

- Primary upstream: https://github.com/remarkjs/react-markdown
- Official GitHub REST observation: **15,898 stars**, 2026-09-30 18:47 UTC, https://api.github.com/repos/remarkjs/react-markdown
- Exact dependency: **react-markdown 10.1.0**, official tag/npm gitHead **44d2e4a44b37461ab7778d6870c1a9eb36393ad2**, MIT.
- Supporting parser extensions (not counted as separate 10,000-star projects): remark-gfm **4.0.1**, gitHead **109972e8a773bf5dac1d6d2da0776557f36971aa**; remark-math **6.0.0**, gitHead **d5d0660b150810a535bbb07eac6cc96a4510aa24**; both MIT.
- Upstream license notices are preserved under `app/web/public/licenses/`. The remark-math npm package omits the license file, so its notice was retrieved from the exact upstream commit at https://github.com/remarkjs/remark-math/blob/d5d0660b150810a535bbb07eac6cc96a4510aa24/license.
- Inspected implementation: react-markdown `lib/index.js` processor, raw-HTML filtering and URL transformation; remark-math parser registration; mdast-util-math's display/inline AST contract.

## Functional integration

`QAPage` generated answer → memoized `QAAnswerContent` → real react-markdown/unified parser → React elements. Display/inline math AST nodes call the existing pinned KaTeX renderer. This replaces flattening structured explanations into plain text.

- Headings, ordered/unordered lists, emphasis, fenced code, GFM tables and inert checklist symbols are supported.
- Double-dollar inline/block math is typeset; single-dollar currency stays prose. Other math notations remain available in the exact answer-original view; no universal LaTeX compatibility is claimed.
- Complete original answers remain available without modifying API payloads, persisted conversation content or follow-up history.
- User questions and evidence-insufficient notices retain plain-text rendering.
- Existing server-verified citation cards, source identity and source/QA round-trip remain the sole active source-navigation controls.

## Untrusted-output safeguards

Raw HTML is disabled, element types are allowlisted and no raw-HTML plugin is installed. Model-authored links become inert labeled text; images become alt-text placeholders with no fetch. Code is displayed, never executed. Math uses the existing no-trust, bounded KaTeX adapter with fresh macro scope, safe error fallback and inline semantic markup. Oversized Markdown falls back to the complete plain answer rather than truncation or expensive parsing.

The renderer does not create/verify citations or make a model answer authoritative. It does not add any model/provider calls, keys, external resource loading, textbook content or canonical-data changes.

## Verification scope

- Local web: **97/97 tests passed** (7 new real-parser/renderer tests), TypeScript and production build passed.
- npm production dependency audit returned **0 known vulnerabilities** at this checkpoint; that registry result is not a guarantee of security.
- Two new synthetic real-browser cases check rendered heading/list/table/code/math, unchanged user-question text, inert unverified links/images, exact original answer, source citation/return with no repeated QA request, and desktop/390px layout.
- The existing real-runtime acceptance test now inspects the explicit answer-original control for byte-equivalent answer text, while new browser assertions verify the formatted presentation. No citation/history assertions are weakened.
- Exact-head GitHub CI is the browser gate; the managed local environment still cannot launch Chromium or browse localhost. No local browser acceptance is claimed.

Stacked on the PDF.js source-viewer branch (#59), itself based on the KaTeX reader (#58). These are React/PWA changes, not a new Windows/Android executable, all-book learning-content completion or mathematical correctness certification.
