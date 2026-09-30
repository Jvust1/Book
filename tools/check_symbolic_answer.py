"""Local diagnostic CLI; caller supplies the expected expression, never an invented solution."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.symbolic_answer import SymPyAnswerChecker


def main() -> int:
    try:
        raw = sys.stdin.read(16385)
        if len(raw) > 16384:
            raise ValueError("input_too_large")
        payload = json.loads(raw)
        if not isinstance(payload, dict) or set(payload) != {"student", "expected"}:
            raise ValueError("student_and_expected_required")
        result = SymPyAnswerChecker().check(payload["student"], payload["expected"])
        print(json.dumps({"schema_version": "symbolic_diagnostic_v1", "automatic_grade": False,
                          **asdict(result)}, ensure_ascii=True))
        return 0
    except (ValueError, TypeError, RuntimeError):
        print(json.dumps({"error": "invalid_input_or_optional_dependency_unavailable"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
