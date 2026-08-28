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

from course_package.validator import validate_course_package


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a generated Book Course Package.")
    parser.add_argument("package_dir", type=Path, help="Generated Course Package directory")
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=ROOT,
        help="Book repository root (default: repository containing this script)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    repository_root = args.repository_root.resolve()
    if not repository_root.is_dir():
        parser.error("repository root does not exist or is not a directory")

    package_dir = args.package_dir
    if not package_dir.is_absolute():
        package_dir = repository_root / package_dir
    package_dir = package_dir.resolve()
    if not package_dir.is_dir():
        parser.error("package directory does not exist or is not a directory")

    result = validate_course_package(package_dir, repository_root)
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
