# KaTeX math reader integration

## Upstream identity and selection

- Official repository: https://github.com/KaTeX/KaTeX
- GitHub REST observation: **20,412 stars**, checked 2026-09-30 18:13 UTC via https://api.github.com/repos/KaTeX/KaTeX
- Version: **0.18.10**, exact npm dependency and lockfile integrity
- Tag / npm `gitHead`: **411da7029f5c095943c2805ce6db16c2be5f214d** (`v0.18.10`)
- License: MIT. The unmodified upstream license is included in `app/web/public/licenses/KaTeX-LICENSE.txt` and copied into production builds.
- Inspected implementation: `contrib/auto-render/auto-render.ts`, `contrib/auto-render/splitAtDelimiters.ts`, public TypeScript options, and the published runtime/CSS package.
- Security references: https://katex.org/docs/security and https://katex.org/docs/options

The current main-line React/PWA showed raw LaTeX in learning, source and search cards. KaTeX supplies the actual typesetter, MathML output and delimiter parser; Book supplies a bounded React adapter and source-preserving UI. This is runtime dependency integration, not a reference-only tree or reimplementation of an upstream parser.

The separate unmerged Windows reader line has its own MathJax implementation and artifact source. This change does not replace or claim to rebuild that Windows application.

## User-visible runtime path

`LearningObjectCard`, `SourcePage`, `SearchPage` → `MathContent` → `katex.render` / upstream `renderMathInElement`.

- Dedicated formula fields render in display mode, with an expandable exact source view.
- Chinese prose supports `\(...\)`, `\[...\]`, and `$$...$$` through the upstream parser.
- Single dollar signs remain prose because Book also includes financial material; currency is not guessed to be math.
- Original unsupported or invalid formulas remain visible with a concise notice. Rendering is presentation, not mathematical correctness certification.
- HTML is always supplied as a text node, not parsed as source HTML. `trust: false`, strict parsing, maximum expansion/size/input limits and per-field macro state prevent active links, external image loads, oversized expansions and cross-card macro leakage.
- Existing source IDs, page numbers, source anchors, exact retrieval, API DTOs and server-owned StudyRecord are preserved.
- Font/CSS assets and attribution ship locally. The service worker precaches WOFF2 fonts; course data and StudyRecord still require the local API.

## Validation scope

- 68 web unit/integration tests passed, including 14 new tests using real KaTeX.
- TypeScript and production build passed.
- 334 Runtime tests and 99 App tests passed locally.
- Added real-browser synthetic chapter coverage for preview/learn/review/practice, source round trip, reload, original formula text, narrow layout and unsafe markup.
- Local Chromium launch could not start because the managed environment denied process sockets; the cloud browser also blocked localhost. Browser acceptance must come from exact-head CI, recorded in the PR, and is not claimed by these local unit results.
- Canonical content files are not included in this change. The existing Runtime suite rewrites a diagnostic report while testing; that incidental generated file is restored before publication.
- No whole-book proofreading, independent mathematical acceptance, Windows/Android host acceptance or new executable is claimed.

## Reproduce

From `app/web`: `npm ci`, `npm test`, `npm run typecheck`, `npm run build`.
The existing `Book App UI tests` workflow runs the real Chromium acceptance suite, including `e2e/math-reader.spec.ts`, against the branch's exact head. It uses a deterministic provider and isolated study storage; no paid API calls are needed.
