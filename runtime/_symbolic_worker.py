"""One-shot local SymPy worker. Reads a bounded JSON payload from stdin only."""
from __future__ import annotations

import json
import sys


def main() -> None:
    # POSIX gets additional process limits. Other OSes still have parent wall timeout
    # plus the same structural input budgets; this is not an OS security sandbox.
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (3, 4))
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    except (ImportError, AttributeError, OSError, ValueError):
        pass
    engine_version = None
    try:
        from _symbolic_safe_parser import validate_expression, to_sympy
        import sympy as sp
        engine_version = sp.__version__
        if engine_version != "1.14.0":
            raise RuntimeError("unsupported symbolic engine version")
        payload = json.loads(sys.stdin.read(16385))
        left_input = validate_expression(payload["student"])
        right_input = validate_expression(payload["expected"])
        if left_input.domain_unverified or right_input.domain_unverified:
            result = {"equivalent": None, "reason": "domain_unverified"}
        else:
            left, right = sp.simplify(to_sympy(left_input)), sp.simplify(to_sympy(right_input))
            if left.has(sp.nan, sp.oo, -sp.oo, sp.zoo) or right.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
                result = {"equivalent": None, "reason": "undefined_expression"}
            else:
                difference = sp.simplify(left - right)
                if difference.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
                    equivalent, reason = None, "undefined_expression"
                elif difference.is_zero is True:
                    equivalent, reason = True, "symbolic_difference_zero"
                elif difference.is_zero is False:
                    equivalent, reason = False, "symbolic_difference_nonzero"
                else:
                    equivalent, reason = None, "symbolic_result_undetermined"
                result = {"equivalent": equivalent, "reason": reason,
                          "normalized_student": str(left)[:4096], "normalized_expected": str(right)[:4096]}
    except Exception as exc:
        result = {"equivalent": None, "reason": f"parse_or_simplify_failed:{type(exc).__name__}"}
    result["engine_version"] = engine_version
    sys.stdout.write(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
