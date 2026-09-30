"""Optional symbolic-equivalence checker for math practice.

Upstream: sympy/sympy @
2d283a82d15f2b46beff7be5399546c79613c445 (BSD-3-Clause).

This checker is intentionally narrow: it compares already-extracted symbolic
answers. It does not invent an expected answer and does not replace proof
grading or source-backed solutions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SymbolicCheckResult:
    equivalent: bool | None
    normalized_student: str
    normalized_expected: str
    reason: str


class SymPyAnswerChecker:
    def __init__(self, *, sympify: Any | None = None, simplify: Any | None = None) -> None:
        if sympify is None or simplify is None:
            try:
                from sympy import simplify as sympy_simplify
                from sympy import sympify as sympy_sympify
            except ImportError as exc:
                raise RuntimeError(
                    "SymPy is optional; install sympy before enabling symbolic answer checking"
                ) from exc
            sympify = sympify or sympy_sympify
            simplify = simplify or sympy_simplify
        if not callable(sympify) or not callable(simplify):
            raise TypeError("sympify and simplify must be callable")
        self._sympify = sympify
        self._simplify = simplify

    def check(self, student: str, expected: str) -> SymbolicCheckResult:
        if not str(student).strip() or not str(expected).strip():
            raise ValueError("student and expected expressions cannot be empty")
        try:
            left = self._sympify(str(student))
            right = self._sympify(str(expected))
            difference = self._simplify(left - right)
        except Exception as exc:
            return SymbolicCheckResult(
                equivalent=None,
                normalized_student=str(student).strip(),
                normalized_expected=str(expected).strip(),
                reason=f"parse_or_simplify_failed:{exc.__class__.__name__}",
            )
        equivalent = bool(difference == 0)
        return SymbolicCheckResult(
            equivalent=equivalent,
            normalized_student=str(left),
            normalized_expected=str(right),
            reason="symbolic_difference_zero" if equivalent else "symbolic_difference_nonzero",
        )
