# SymPy symbolic answer checking — 2026-09-30

Upstream: `sympy/sympy`  
Revision inspected: `2d283a82d15f2b46beff7be5399546c79613c445`  
License: BSD-3-Clause

Book uses SymPy only for narrow symbolic equivalence after an expected answer is already source-backed. It never fabricates an expected solution, and parse failures return `equivalent=None` rather than marking a student wrong.
