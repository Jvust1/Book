from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Callable, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.h4a_runtime import (  # noqa: E402
    H4aDatasetError,
    H4aEvaluationError,
    canonical_h4a_report_json,
    evaluate_h4a_course,
)
from runtime.shadow_fts import (  # noqa: E402
    ShadowFtsError,
    ShadowFtsUnavailableError,
)


Evaluator = Callable[[Path, Path], dict[str, object]]


def _json_line(payload: Mapping[str, object]) -> str:
    return json.dumps(
        dict(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _emit(payload: Mapping[str, object]) -> None:
    print(_json_line(payload))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the evaluation-only H4a Exact vs shadow FTS5 comparison."
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=ROOT,
        help="Book repository root (default: current checkout root).",
    )
    parser.add_argument(
        "--query-set",
        type=Path,
        default=None,
        help="Frozen H4a query-set path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Report path; must remain under <repository>/.build.",
    )
    return parser


def _resolve_output(root: Path, output: Path | None) -> Path:
    build_root = (root / ".build").resolve()
    candidate = (
        output
        if output is not None
        else build_root
        / "evaluations"
        / "h4a"
        / "functional_analysis_course"
        / "report.json"
    ).resolve()
    if not candidate.is_relative_to(build_root):
        raise ValueError("H4a report output must remain under repository .build")
    return candidate


def main(
    argv: list[str] | None = None,
    *,
    evaluator: Evaluator | None = None,
) -> int:
    args = _parser().parse_args(argv)
    root = args.repository_root.resolve()

    try:
        output_path = _resolve_output(root, args.output)
    except ValueError as exc:
        _emit(
            {
                "status": "ERROR",
                "stage": "H4a",
                "error_kind": "output_path",
                "message": str(exc),
            }
        )
        return 2

    query_set_path = (
        args.query_set.resolve()
        if args.query_set is not None
        else root / "evaluation" / "h4a" / "functional_analysis_queries.v1.json"
    )
    run_evaluator = evaluator or evaluate_h4a_course

    try:
        report = run_evaluator(root, query_set_path)
        canonical = canonical_h4a_report_json(report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(canonical, encoding="utf-8")
    except H4aDatasetError as exc:
        _emit(
            {
                "status": "ERROR",
                "stage": "H4a",
                "error_kind": "dataset",
                "message": str(exc),
            }
        )
        return 2
    except (ShadowFtsUnavailableError, ShadowFtsError) as exc:
        _emit(
            {
                "status": "ERROR",
                "stage": "H4a",
                "error_kind": "shadow_fts",
                "message": str(exc),
            }
        )
        return 3
    except H4aEvaluationError as exc:
        _emit(
            {
                "status": "ERROR",
                "stage": "H4a",
                "error_kind": "evaluation",
                "message": str(exc),
            }
        )
        return 4
    except OSError as exc:
        _emit(
            {
                "status": "ERROR",
                "stage": "H4a",
                "error_kind": "io",
                "message": str(exc),
            }
        )
        return 5

    relative_output = output_path.relative_to(root).as_posix()
    _emit(
        {
            "status": "PASS",
            "stage": "H4a",
            "dataset_id": report["dataset"]["dataset_id"],
            "report_path": relative_output,
            "report_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
