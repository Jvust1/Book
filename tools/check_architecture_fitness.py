#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from course_package.fitness import run_architecture_fitness


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Book Foundation architecture fitness gates.")
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=ROOT,
        help="Book repository root (default: repository containing this script)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = run_architecture_fitness(args.repository_root)
    print(
        json.dumps(
            {
                "status": result.status,
                "diagnostics": [asdict(item) for item in result.diagnostics],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 1 if result.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
