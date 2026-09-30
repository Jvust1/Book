# Safe SymPy integration boundary

This improves the existing optional SymPy adapter. It is **not** counted as a newly added upstream project.

## Upstream evidence and license

- Repository: https://github.com/sympy/sympy
- Official REST observation: **14,981 stars** on 2026-09-30 19:08 UTC, https://api.github.com/repos/sympy/sympy.
- Official PyPI wheel/sdist SHA-256 identities are pinned in the requirements file and were checked by a `pip download --require-hashes` run.
- Pinned runtime: SymPy **1.14.0**, release tag `sympy-1.14.0`, peeled commit **16fa855354eb7bcabd3fe10993841e03b1382692**; mpmath **1.3.0**.
- The core is BSD-3-Clause, and the upstream LICENSE includes additional component notices. GitHub reports the aggregate as `NOASSERTION`; the complete exact-release LICENSE is retained in `docs/upstream/licenses/SymPy-1.14.0-LICENSE.txt` rather than flattening those notices.
- Official `sympify` documentation explicitly warns that it uses eval on string input: https://docs.sympy.org/latest/modules/core.html#module-sympy.core.sympify.

## Gap found

The previous helper passed both student and expected strings directly into `sympify`. Its three tests used injected fake arithmetic and did not exercise real SymPy parsing. The helper is currently exported by Runtime but not exposed through an App API route; this change does not claim an externally reachable App exploit or add a grading endpoint.

## Actual runtime change

`SymPyAnswerChecker.check` now validates both strings with a small arithmetic AST grammar, then invokes an isolated-lifetime local worker that constructs explicit SymPy nodes. Production strings are never sent to `sympify`, `parse_expr`, Python eval or exec. The worker runs the real pinned engine and returns a bounded typed result.

- Allowed: numeric literals, up to eight named symbols, constants pi/E/I, arithmetic, bounded integer powers, and a narrow single-argument function allowlist.
- Disallowed: attributes, indexing, imports, file calls, assignments, comprehensions, containers, keywords, splats, arbitrary function calls and unsupported syntax.
- Length/node/depth/weight/degree/numeric-growth budgets reject explosive expressions before SymPy construction.
- Default parent wall timeout: 5 seconds. The POSIX worker additionally attempts per-worker CPU and 512 MiB address-space limits where supported. If those calls are unavailable/rejected, parent timeout and structural budgets still apply. Windows has those portable bounds, **not an equivalent hard memory limit**. This is input isolation and resource bounding, not a general OS security sandbox.
- Runtime engine version is checked before accepting any equivalence result; a version mismatch remains unknown.
- Parent sends expressions through stdin, uses no shell, validates worker output and treats timeout, worker failure, unsupported input and indeterminate results as `equivalent=None`, never an incorrect answer.
- Numeric undefined operands are simplified and checked before subtraction so two undefined expressions cannot cancel into a correct result.
- Symbolic denominators, negative powers and branch/domain-sensitive functions require domain information the current API does not have; those comparisons conservatively remain unknown. The checker does not invent assumptions.
- Legacy injected callables remain a trusted deterministic test seam behind the same syntax/domain gate. Supplying one callback without the other now raises TypeError.

## Reproducible use

Install `requirements-extras/symbolic.txt`. Pipe a JSON object containing exactly `student` and `expected` to `python tools/check_symbolic_answer.py`.

Example input:

    {"student":"(x+1)^2","expected":"x^2+2*x+1"}

The diagnostic returns schema `symbolic_diagnostic_v1`, normalized expressions, a three-valued equivalence result and `automatic_grade=false`. The caller is responsible for obtaining a source-backed expected answer; this CLI does not establish source provenance, manufacture textbook solutions or grade proofs.

## Verification

- The original three fake-arithmetic tests remain, plus focused adversarial boundary, worker-protocol, real polynomial/trigonometric/exact-decimal, undefined/domain and CLI tests.
- Dedicated exact-head CI installs the pinned engine and exercises the real default worker on Ubuntu/Python 3.13 and Windows/Python 3.11, alongside existing repository CI.
- Test-method counts and final pass/fail outcomes are reported with the PR/CI run; subcases are not inflated into extra independent tests.
- No canonical textbook assets, source records, online provider calls, new secrets, automatic grades or native release artifacts are introduced.
