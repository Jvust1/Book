#!/usr/bin/env python3
"""Validate whether a structured Book textbook is ready for Course OS runtime use.

This checker intentionally distinguishes STRUCTURED_COMPLETE from RUNTIME_READY.
It uses only the Python standard library so it can run on Windows, macOS, Linux,
CI, or a developer machine without installing dependencies.

Usage:
    python tools/check_runtime_readiness.py books/functional-analysis
    python tools/check_runtime_readiness.py books/functional-analysis --write

Exit codes:
    0 = READY
    1 = BLOCKED
    2 = invalid checker invocation / unreadable root
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


READY = "READY"
BLOCKED = "BLOCKED"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def add_check(checks: list[dict[str, str]], name: str, ok: bool, detail: str) -> None:
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})


def find_structure_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*_structure.json"):
        if path.name == "RUNTIME_READINESS.json":
            continue
        files.append(path)
    return sorted(files)


def collect_structure_state(files: list[Path]) -> tuple[list[str], list[str], list[str]]:
    stale: list[str] = []
    duplicate_ids: list[str] = []
    bad_continuations: list[str] = []
    seen_ids: dict[str, str] = {}
    batch_ids: set[str] = set()
    parsed: dict[str, dict[str, Any]] = {}

    for path in files:
        try:
            data = load_json(path)
        except Exception as exc:  # noqa: BLE001
            stale.append(f"{path}: unreadable JSON: {exc}")
            continue

        batch_id = str(data.get("chunk_id") or path.stem.removesuffix("_structure"))
        batch_ids.add(batch_id)
        parsed[batch_id] = data

        status = str(data.get("status", "")).lower()
        if "partial" in status:
            stale.append(f"{path}: status={data.get('status')}")

        for key in ("key_objects", "objects", "exercises", "problems"):
            values = data.get(key, [])
            if not isinstance(values, list):
                continue
            for item in values:
                if not isinstance(item, dict):
                    continue
                object_id = item.get("id") or item.get("object_id") or item.get("exercise_id") or item.get("problem_id")
                if not object_id:
                    continue
                object_id = str(object_id)
                source = str(path)
                previous = seen_ids.get(object_id)
                if previous and previous != source:
                    # Cross-batch repeats can be legitimate continuation references. The
                    # checker reports them for review instead of failing automatically.
                    duplicate_ids.append(f"{object_id}: {previous} | {source}")
                else:
                    seen_ids[object_id] = source

    for batch_id, data in parsed.items():
        targets: list[tuple[str, str]] = []
        for key in ("continues_in", "continued_from"):
            if data.get(key):
                targets.append((key, str(data[key])))
        for section in data.get("sections", []) if isinstance(data.get("sections"), list) else []:
            if not isinstance(section, dict):
                continue
            for key in ("continues_in", "continued_from"):
                if section.get(key):
                    targets.append((key, str(section[key])))
        for key, target in targets:
            if target not in batch_ids:
                bad_continuations.append(f"{batch_id}.{key} -> {target}")

    return stale, duplicate_ids, bad_continuations


def validate_page_map(path: Path, expected_pages: int) -> tuple[bool, str]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except Exception as exc:  # noqa: BLE001
        return False, f"cannot read CSV: {exc}"

    if len(rows) != expected_pages:
        return False, f"expected {expected_pages} rows, found {len(rows)}"

    page_key = None
    if rows:
        for candidate in ("pdf_page_index", "pdf_page", "physical_pdf_page"):
            if candidate in rows[0]:
                page_key = candidate
                break
    if not page_key:
        return False, "missing pdf page column (pdf_page_index/pdf_page/physical_pdf_page)"

    values: list[int] = []
    try:
        values = [int(row[page_key]) for row in rows]
    except Exception as exc:  # noqa: BLE001
        return False, f"invalid PDF page value: {exc}"

    if len(values) != len(set(values)):
        return False, "duplicate PDF page values"

    ordered = sorted(values)
    zero_based = list(range(0, expected_pages))
    one_based = list(range(1, expected_pages + 1))
    if ordered not in (zero_based, one_based):
        return False, "PDF page values are not a continuous 0-based or 1-based range"

    return True, f"{len(rows)} page-map rows; PDF page sequence is continuous"


def validate_search_index(path: Path, expected_book_id: str, expected_records: int | None) -> tuple[bool, str]:
    ids: set[str] = set()
    rows = 0
    missing_anchor = 0
    wrong_book = 0
    duplicate_ids = 0

    try:
        with path.open("r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                rows += 1
                object_id = row.get("object_id") or row.get("id")
                if not object_id:
                    return False, f"line {line_no}: missing object_id/id"
                object_id = str(object_id)
                if object_id in ids:
                    duplicate_ids += 1
                ids.add(object_id)
                if row.get("book_id") not in (None, expected_book_id):
                    wrong_book += 1
                if not row.get("source_anchor"):
                    missing_anchor += 1
    except Exception as exc:  # noqa: BLE001
        return False, f"cannot parse JSONL: {exc}"

    problems: list[str] = []
    if duplicate_ids:
        problems.append(f"duplicate IDs={duplicate_ids}")
    if wrong_book:
        problems.append(f"book_id mismatches={wrong_book}")
    if missing_anchor:
        problems.append(f"missing source_anchor={missing_anchor}")
    if expected_records is not None and rows != expected_records:
        problems.append(f"expected records={expected_records}, found={rows}")

    if problems:
        return False, "; ".join(problems)
    return True, f"{rows} unique indexed objects with source anchors"


def validate(root: Path) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    missing: list[str] = []
    stale: list[str] = []
    identity_mismatches: list[str] = []

    completion_path = root / "STRUCTURED_COMPLETE.json"
    metadata_path = root / "book_metadata.json"

    if not completion_path.exists():
        add_check(checks, "structured_complete_marker", False, "STRUCTURED_COMPLETE.json missing")
        missing.append("STRUCTURED_COMPLETE.json")
        completion: dict[str, Any] = {}
    else:
        try:
            completion = load_json(completion_path)
            ok = completion.get("status") == "STRUCTURED_COMPLETE" and completion.get("audit_fail_count") == 0
            add_check(checks, "structured_complete_marker", ok, f"status={completion.get('status')}; audit_fail_count={completion.get('audit_fail_count')}")
        except Exception as exc:  # noqa: BLE001
            completion = {}
            add_check(checks, "structured_complete_marker", False, f"invalid JSON: {exc}")

    if not metadata_path.exists():
        add_check(checks, "book_metadata", False, "book_metadata.json missing")
        missing.append("book_metadata.json")
        metadata: dict[str, Any] = {}
    else:
        try:
            metadata = load_json(metadata_path)
            add_check(checks, "book_metadata", True, "book_metadata.json parsed")
        except Exception as exc:  # noqa: BLE001
            metadata = {}
            add_check(checks, "book_metadata", False, f"invalid JSON: {exc}")

    canonical_book_id = str(metadata.get("book_id") or completion.get("book_id") or "")
    expected_pages = int(metadata.get("pdf_total_pages") or completion.get("pdf_pages") or 0)

    if completion and metadata:
        if completion.get("book_id") != metadata.get("book_id"):
            identity_mismatches.append("STRUCTURED_COMPLETE.book_id != book_metadata.book_id")
        if completion.get("pdf_pages") != metadata.get("pdf_total_pages"):
            identity_mismatches.append("STRUCTURED_COMPLETE.pdf_pages != book_metadata.pdf_total_pages")
    add_check(checks, "completion_metadata_identity", not identity_mismatches, "; ".join(identity_mismatches) if identity_mismatches else "completion and metadata identities agree")

    audit_name = completion.get("audit_report", "BOOK_AUDIT_REPORT.md")
    audit_path = root / str(audit_name)
    if audit_path.exists():
        text = audit_path.read_text(encoding="utf-8", errors="replace")
        ok = "FAIL = 0" in text or "FAIL: 0" in text
        add_check(checks, "audit_report", ok, f"{audit_name} exists; zero-failure marker={'present' if ok else 'absent'}")
    else:
        missing.append(str(audit_name))
        add_check(checks, "audit_report", False, f"{audit_name} missing")

    toc_name = str(metadata.get("toc_file") or "toc_bilingual.json")
    toc_path = root / toc_name
    if toc_path.exists():
        try:
            load_json(toc_path)
            add_check(checks, "bilingual_toc", True, f"{toc_name} parsed")
        except Exception as exc:  # noqa: BLE001
            add_check(checks, "bilingual_toc", False, f"{toc_name} invalid JSON: {exc}")
    else:
        missing.append(toc_name)
        add_check(checks, "bilingual_toc", False, f"{toc_name} missing")

    page_map_name = str(metadata.get("page_map_file") or "page_map.csv")
    page_map_path = root / page_map_name
    if page_map_path.exists():
        ok, detail = validate_page_map(page_map_path, expected_pages)
        add_check(checks, "page_map", ok, detail)
    else:
        missing.append(page_map_name)
        add_check(checks, "page_map", False, f"{page_map_name} missing")

    qa_path = root / "qa_retrieval_policy.json"
    if qa_path.exists():
        try:
            qa = load_json(qa_path)
            ok = qa.get("book_id") == canonical_book_id
            if not ok:
                identity_mismatches.append("qa_retrieval_policy.book_id != canonical book_id")
            add_check(checks, "qa_policy_identity", ok, f"book_id={qa.get('book_id')}")
        except Exception as exc:  # noqa: BLE001
            add_check(checks, "qa_policy_identity", False, f"invalid JSON: {exc}")
    else:
        missing.append("qa_retrieval_policy.json")
        add_check(checks, "qa_policy_identity", False, "qa_retrieval_policy.json missing")

    search_name = completion.get("search_index")
    if not search_name:
        add_check(checks, "final_search_index", False, "STRUCTURED_COMPLETE.search_index missing")
    else:
        search_path = root / str(search_name)
        if search_path.exists():
            expected_records = 1493 if str(completion.get("version")) == "v0.36" and canonical_book_id == "stein_shakarchi_functional_analysis_2011" else None
            ok, detail = validate_search_index(search_path, canonical_book_id, expected_records)
            add_check(checks, "final_search_index", ok, detail)
        else:
            missing.append(str(search_name))
            add_check(checks, "final_search_index", False, f"{search_name} missing")

    structure_files = find_structure_files(root)
    stale_structure, duplicate_ids, bad_continuations = collect_structure_state(structure_files)
    stale.extend(stale_structure)
    add_check(checks, "structure_files", bool(structure_files), f"found {len(structure_files)} structure JSON files")
    add_check(checks, "continuation_targets", not bad_continuations, "; ".join(bad_continuations[:10]) if bad_continuations else "all observed continuation targets resolve")
    # Duplicate IDs are informational because legitimate continuation references can repeat.
    add_check(checks, "stable_id_scan", True, f"cross-file repeated IDs for review={len(duplicate_ids)}")

    partial_files = sorted(str(path.relative_to(root)) for path in root.rglob("*partial*"))
    if partial_files:
        stale.extend(partial_files)
        add_check(checks, "no_partial_deliverables", False, ", ".join(partial_files))
    else:
        add_check(checks, "no_partial_deliverables", True, "no partial-named deliverables found")

    failures = [check for check in checks if check["status"] == "FAIL"]
    status = READY if not failures and not missing and not stale and not identity_mismatches else BLOCKED

    return {
        "status": status,
        "book_id": canonical_book_id or None,
        "structured_status": completion.get("status"),
        "structured_version": completion.get("version"),
        "audit_fail_count": completion.get("audit_fail_count"),
        "checks": checks,
        "missing_required_files": sorted(set(missing)),
        "stale_files": sorted(set(stale)),
        "identity_mismatches": sorted(set(identity_mismatches)),
        "diagnostics": {
            "structure_file_count": len(structure_files),
            "cross_file_repeated_ids_for_review": len(duplicate_ids),
            "bad_continuation_targets": bad_continuations,
        },
        "next_action": (
            "Runtime assets satisfy the import gate; proceed with the Course -> Book -> Chapter -> Section loader."
            if status == READY
            else "Restore/fix failed runtime assets, then rerun this checker until status becomes READY."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("book_root", type=Path)
    parser.add_argument("--write", action="store_true", help="write RUNTIME_READINESS.json into book_root")
    args = parser.parse_args()

    root: Path = args.book_root
    if not root.is_dir():
        print(json.dumps({"status": "ERROR", "detail": f"not a directory: {root}"}, ensure_ascii=False, indent=2))
        return 2

    result = validate(root)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(output, end="")

    if args.write:
        (root / "RUNTIME_READINESS.json").write_text(output, encoding="utf-8")

    return 0 if result["status"] == READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
