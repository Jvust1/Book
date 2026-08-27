#!/usr/bin/env python3
"""Recover Functional Analysis v0.36 PageMap from audited repository evidence.

The original 442-page binary with its embedded PDF page-label dictionary is no
longer present in the repository.  Recovery therefore does *not* claim to have
re-read that binary.  Instead it materializes the page-label sequence already
recorded by the final structured assets:

* book_metadata.json: PDF 20-442 == printed 1-423 and the source PDF used
  embedded page labels;
* chunks/chunk_001_structure.json: PDF 1 == Cover, PDF 8 == vii,
  PDF 12 == xi, PDF 18 == xvii, PDF 20 == printed 1;
* the frontmatter occupies the 18 roman-numbered pages immediately before
  printed page 1.

The generated CSV is a runtime fact file, so clients never need to apply an
implicit offset formula themselves.  A rebuild report records the evidence and
anchor checks used to materialize it.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

EXPECTED_BOOK_ID = "stein_shakarchi_functional_analysis_2011"
EXPECTED_PDF_PAGES = 442
EXPECTED_PRINTED_FINAL = 423
MAIN_TEXT_PDF_START = 20
ROMAN_FRONTMATTER_COUNT = 18


ROMAN_1_TO_18 = [
    "i",
    "ii",
    "iii",
    "iv",
    "v",
    "vi",
    "vii",
    "viii",
    "ix",
    "x",
    "xi",
    "xii",
    "xiii",
    "xiv",
    "xv",
    "xvi",
    "xvii",
    "xviii",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return data


def parse_range(value: Any, *, field: str) -> tuple[int, int]:
    if not isinstance(value, str):
        raise RuntimeError(f"{field} must be a string range, got {value!r}")
    match = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", value)
    if not match:
        raise RuntimeError(f"Cannot parse {field}: {value!r}")
    return int(match.group(1)), int(match.group(2))


def _structure_anchor_expectations(chunk001: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    page_labels = chunk001.get("page_labels")
    pdf_pages = chunk001.get("pdf_pages")
    if isinstance(page_labels, list) and len(page_labels) >= 2 and isinstance(pdf_pages, list) and len(pdf_pages) >= 2:
        checks.append(
            {
                "name": "chunk_001_range_labels",
                "pdf_page": int(pdf_pages[0]),
                "expected_page_label": str(page_labels[0]),
            }
        )
        checks.append(
            {
                "name": "chunk_001_end_label",
                "pdf_page": int(pdf_pages[-1]),
                "expected_page_label": str(page_labels[-1]),
            }
        )

    for unit in chunk001.get("content_units", []) if isinstance(chunk001.get("content_units"), list) else []:
        if not isinstance(unit, dict):
            continue
        unit_id = str(unit.get("unit_id") or unit.get("id") or "content_unit")

        if unit.get("pdf_page") is not None and unit.get("page_label") is not None:
            checks.append(
                {
                    "name": unit_id,
                    "pdf_page": int(unit["pdf_page"]),
                    "expected_page_label": str(unit["page_label"]),
                }
            )
        if unit.get("pdf_page") is not None and unit.get("printed_page") is not None:
            checks.append(
                {
                    "name": unit_id + "_printed",
                    "pdf_page": int(unit["pdf_page"]),
                    "expected_printed_page": str(unit["printed_page"]),
                }
            )

        unit_pdf_pages = unit.get("pdf_pages")
        unit_page_labels = unit.get("page_labels")
        if (
            isinstance(unit_pdf_pages, list)
            and len(unit_pdf_pages) >= 2
            and isinstance(unit_page_labels, list)
            and len(unit_page_labels) >= 2
        ):
            checks.append(
                {
                    "name": unit_id + "_start",
                    "pdf_page": int(unit_pdf_pages[0]),
                    "expected_page_label": str(unit_page_labels[0]),
                }
            )
            checks.append(
                {
                    "name": unit_id + "_end",
                    "pdf_page": int(unit_pdf_pages[-1]),
                    "expected_page_label": str(unit_page_labels[-1]),
                }
            )

    return checks


def build_page_map(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metadata = load_json(root / "book_metadata.json")
    book_id = str(metadata.get("book_id") or "")
    if book_id != EXPECTED_BOOK_ID:
        raise RuntimeError(f"PageMap recovery only supports {EXPECTED_BOOK_ID}; got {book_id!r}")

    pdf_total = int(metadata.get("pdf_total_pages") or 0)
    if pdf_total != EXPECTED_PDF_PAGES:
        raise RuntimeError(f"Expected {EXPECTED_PDF_PAGES} PDF pages, got {pdf_total}")

    main_pdf_start, main_pdf_end = parse_range(metadata.get("main_text_pdf_pages"), field="main_text_pdf_pages")
    printed_start, printed_end = parse_range(metadata.get("main_text_printed_pages"), field="main_text_printed_pages")
    if (main_pdf_start, main_pdf_end) != (MAIN_TEXT_PDF_START, EXPECTED_PDF_PAGES):
        raise RuntimeError(f"Unexpected main-text PDF range: {(main_pdf_start, main_pdf_end)}")
    if (printed_start, printed_end) != (1, EXPECTED_PRINTED_FINAL):
        raise RuntimeError(f"Unexpected printed range: {(printed_start, printed_end)}")
    if (main_pdf_end - main_pdf_start) != (printed_end - printed_start):
        raise RuntimeError("Main-text PDF and printed ranges have incompatible lengths")

    rows: list[dict[str, Any]] = [
        {
            "pdf_page_index": 1,
            "printed_page": "",
            "page_label": "Cover",
            "mapping_basis": "chunk_001_structure",
        }
    ]

    for offset, roman in enumerate(ROMAN_1_TO_18, start=2):
        rows.append(
            {
                "pdf_page_index": offset,
                "printed_page": "",
                "page_label": roman,
                "mapping_basis": "frontmatter_sequence+chunk_001_anchors",
            }
        )

    for pdf_page in range(main_pdf_start, main_pdf_end + 1):
        printed_page = pdf_page - main_pdf_start + printed_start
        rows.append(
            {
                "pdf_page_index": pdf_page,
                "printed_page": str(printed_page),
                "page_label": str(printed_page),
                "mapping_basis": "book_metadata.main_text_ranges",
            }
        )

    if len(rows) != pdf_total:
        raise RuntimeError(f"Generated {len(rows)} PageMap rows, expected {pdf_total}")

    by_pdf = {int(row["pdf_page_index"]): row for row in rows}
    if len(by_pdf) != len(rows):
        raise RuntimeError("Generated duplicate physical PDF page indices")
    if sorted(by_pdf) != list(range(1, pdf_total + 1)):
        raise RuntimeError("Generated physical PDF page indices are not continuous")

    chunk001 = load_json(root / "chunks" / "chunk_001_structure.json")
    anchor_results: list[dict[str, Any]] = []
    for expectation in _structure_anchor_expectations(chunk001):
        pdf_page = int(expectation["pdf_page"])
        row = by_pdf.get(pdf_page)
        if row is None:
            anchor_results.append({**expectation, "status": "FAIL", "actual": None})
            continue

        expected_label = expectation.get("expected_page_label")
        expected_printed = expectation.get("expected_printed_page")
        ok = True
        actual: dict[str, Any] = {
            "page_label": row.get("page_label"),
            "printed_page": row.get("printed_page"),
        }
        if expected_label is not None and row.get("page_label") != expected_label:
            ok = False
        if expected_printed is not None and row.get("printed_page") != expected_printed:
            ok = False
        anchor_results.append({**expectation, "status": "PASS" if ok else "FAIL", "actual": actual})

    # Explicit final anchors protect the materialized PageMap from accidental
    # shifts even if metadata is later edited incorrectly.
    final_expectations = {
        1: ("Cover", ""),
        2: ("i", ""),
        8: ("vii", ""),
        12: ("xi", ""),
        18: ("xvii", ""),
        19: ("xviii", ""),
        20: ("1", "1"),
        442: ("423", "423"),
    }
    for pdf_page, (label, printed) in final_expectations.items():
        row = by_pdf[pdf_page]
        ok = row["page_label"] == label and row["printed_page"] == printed
        anchor_results.append(
            {
                "name": f"final_anchor_pdf_{pdf_page}",
                "pdf_page": pdf_page,
                "expected_page_label": label,
                "expected_printed_page": printed,
                "status": "PASS" if ok else "FAIL",
                "actual": {"page_label": row["page_label"], "printed_page": row["printed_page"]},
            }
        )

    anchor_checks_pass = all(item["status"] == "PASS" for item in anchor_results)
    report: dict[str, Any] = {
        "book_id": book_id,
        "status": "PASS_CANDIDATE" if anchor_checks_pass else "FAIL",
        "recovery_kind": "materialized_from_audited_repository_evidence",
        "original_pdf_binary_re_read": False,
        "evidence": [
            "book_metadata.json: pdf_total_pages=442",
            "book_metadata.json: main_text_pdf_pages=20-442",
            "book_metadata.json: main_text_printed_pages=1-423",
            "book_metadata.json: source PDF used embedded page labels",
            "chunks/chunk_001_structure.json: stored Cover/vii/xi/xvii/printed-1 anchors",
            "frontmatter sequence: Cover + i-xviii before printed page 1",
        ],
        "row_count": len(rows),
        "frontmatter_cover_count": 1,
        "frontmatter_roman_count": ROMAN_FRONTMATTER_COUNT,
        "main_text_count": printed_end - printed_start + 1,
        "main_text_pdf_range": [main_pdf_start, main_pdf_end],
        "main_text_printed_range": [printed_start, printed_end],
        "anchor_checks_pass": anchor_checks_pass,
        "anchor_checks": anchor_results,
        "candidate": "page_map.csv.candidate",
    }
    return rows, report


def write_page_map(root: Path, *, promote_safe: bool = False) -> tuple[Path, dict[str, Any]]:
    rows, report = build_page_map(root)
    candidate = root / "page_map.csv.candidate"
    fieldnames = ["pdf_page_index", "printed_page", "page_label", "mapping_basis"]
    with candidate.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    report_path = root / "page_map.rebuild_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if promote_safe and report["anchor_checks_pass"] and report["row_count"] == EXPECTED_PDF_PAGES:
        final_path = root / "page_map.csv"
        final_path.write_bytes(candidate.read_bytes())
        report["promoted"] = True
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return candidate, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("book_root", type=Path)
    parser.add_argument("--promote-safe", action="store_true")
    args = parser.parse_args()

    candidate, report = write_page_map(args.book_root, promote_safe=args.promote_safe)
    print(json.dumps({"candidate": str(candidate), "report": report}, ensure_ascii=False, indent=2))
    return 0 if report["anchor_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
