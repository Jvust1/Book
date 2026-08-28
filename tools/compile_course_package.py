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

from course_package.compiler import PackageCompileError, compile_course_package
from course_package.validator import validate_compiled_package


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile and validate a Book Course Package.")
    parser.add_argument("course_dir", type=Path, help="Course directory inside the repository")
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=ROOT,
        help="Book repository root (default: repository containing this script)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(".build/course-packages"),
        help="Generated package root inside the repository",
    )
    return parser


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _resolve_inputs(parser: argparse.ArgumentParser, args: argparse.Namespace) -> tuple[Path, Path, Path]:
    repository_root = args.repository_root.resolve()
    if not repository_root.is_dir():
        parser.error("repository root does not exist or is not a directory")

    course_dir = args.course_dir
    if not course_dir.is_absolute():
        course_dir = repository_root / course_dir
    course_dir = course_dir.resolve()
    if not course_dir.is_dir() or not _inside(course_dir, repository_root):
        parser.error("course directory must be an existing directory inside repository root")

    output_root = args.output_root
    if not output_root.is_absolute():
        output_root = repository_root / output_root
    output_root = output_root.resolve()
    if not _inside(output_root, repository_root):
        parser.error("output root must remain inside repository root")

    return repository_root, course_dir, output_root


def _print_failure(code: str, detail: str) -> None:
    print(
        json.dumps(
            {
                "status": "FAIL",
                "diagnostics": [
                    {
                        "code": code,
                        "severity": "FAIL",
                        "detail": detail,
                        "relative_path": None,
                    }
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    repository_root, course_dir, output_root = _resolve_inputs(parser, args)

    try:
        package = compile_course_package(repository_root, course_dir)
    except (PackageCompileError, OSError, ValueError):
        _print_failure("compile_error", "Course Package compilation failed.")
        return 1

    validation = validate_compiled_package(package, repository_root)
    if validation.status == "FAIL":
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "diagnostics": [asdict(item) for item in validation.diagnostics],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1

    try:
        package_dir = package.write(output_root)
        relative_package_dir = package_dir.resolve().relative_to(repository_root).as_posix()
    except (PackageCompileError, OSError, ValueError):
        _print_failure("package_write_error", "Generated Course Package could not be written safely.")
        return 1

    print(
        json.dumps(
            {
                "status": validation.status,
                "course_id": package.course_id,
                "package_identity": package.package_identity,
                "package_dir": relative_package_dir,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
