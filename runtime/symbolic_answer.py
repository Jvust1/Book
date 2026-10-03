"""Bounded, optional symbolic comparison of an already source-backed expected answer.

SymPy 1.14.0 (sympy/sympy, BSD core with notices): production input is converted
from a restricted AST into constructors, never passed to sympify/parse_expr/eval.
This does not invent solutions, establish source authority, or grade proofs.
"""
from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._symbolic_safe_parser import UnsafeExpression, validate_expression


@dataclass(frozen=True)
class SymbolicCheckResult:
    equivalent: bool | None
    normalized_student: str
    normalized_expected: str
    reason: str


class SymPyAnswerChecker:
    def __init__(self, *, sympify: Any | None = None, simplify: Any | None = None,
                 timeout_seconds: float = 5.0) -> None:
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or not math.isfinite(timeout_seconds) or not 0.05 <= timeout_seconds <= 10:
            raise ValueError("timeout_seconds must be between 0.05 and 10")
        # Retain the legacy deterministic testing seam, never used by production.
        if (sympify is None) != (simplify is None):
            raise TypeError("both trusted test callables must be supplied together")
        if sympify is not None and (not callable(sympify) or not callable(simplify)):
            raise TypeError("sympify and simplify must be callable")
        if sympify is None and importlib.util.find_spec("sympy") is None:
            raise RuntimeError("SymPy is optional; install requirements-extras/symbolic.txt before enabling symbolic answer checking")
        self._sympify = sympify
        self._simplify = simplify
        self._timeout = float(timeout_seconds)

    def check(self, student: str, expected: str) -> SymbolicCheckResult:
        if not isinstance(student, str) or not isinstance(expected, str):
            raise TypeError("expressions must be strings")
        if not student.strip() or not expected.strip():
            raise ValueError("student and expected expressions cannot be empty")

        def unknown(reason: str) -> SymbolicCheckResult:
            return SymbolicCheckResult(None, student.strip()[:4096], expected.strip()[:4096], reason)

        try:
            left, right = validate_expression(student), validate_expression(expected)
        except UnsafeExpression as exc:
            return unknown(f"unsupported_expression:{exc}")
        if left.domain_unverified or right.domain_unverified:
            return unknown("domain_unverified")

        if self._sympify is not None:
            try:
                lhs, rhs = self._sympify(student), self._sympify(expected)
                difference = self._simplify(lhs - rhs)
                equivalent = bool(difference == 0)
                return SymbolicCheckResult(equivalent, str(lhs), str(rhs),
                    "symbolic_difference_zero" if equivalent else "symbolic_difference_nonzero")
            except Exception as exc:
                return unknown(f"parse_or_simplify_failed:{type(exc).__name__}")

        worker = Path(__file__).with_name("_symbolic_worker.py")
        try:
            completed = subprocess.run([sys.executable, str(worker)],
                input=json.dumps({"student": student, "expected": expected}),
                text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=self._timeout, check=False)
        except subprocess.TimeoutExpired:
            return unknown("symbolic_timeout")
        except OSError:
            return unknown("symbolic_worker_unavailable")
        if completed.returncode != 0 or len(completed.stdout) > 32768:
            return unknown("symbolic_worker_failed")
        try:
            result = json.loads(completed.stdout)
            if not isinstance(result, dict) or type(result.get("equivalent")) not in (bool, type(None)):
                raise ValueError("invalid result")
            if result.get("engine_version") != "1.14.0":
                return unknown("symbolic_engine_version_mismatch")
            reason = result.get("reason")
            if not isinstance(reason, str) or len(reason) > 200:
                raise ValueError("invalid reason")
            if result["equivalent"] is True and reason != "symbolic_difference_zero":
                raise ValueError("inconsistent positive result")
            if result["equivalent"] is False and reason != "symbolic_difference_nonzero":
                raise ValueError("inconsistent negative result")
            normalized_student = result.get("normalized_student", student.strip())
            normalized_expected = result.get("normalized_expected", expected.strip())
            if not all(isinstance(value, str) and len(value) <= 4096 for value in (normalized_student, normalized_expected)):
                raise ValueError("invalid normalization")
            return SymbolicCheckResult(result["equivalent"], normalized_student, normalized_expected, reason)
        except (ValueError, TypeError, KeyError):
            return unknown("symbolic_worker_invalid_result")
