#!/usr/bin/env python3
"""Namespace reused local figure numbers in Functional Analysis structure data.

Some source chunks store figures with book-local display labels such as
``Figure 1`` rather than globally stable IDs.  Those labels legitimately repeat
in different chapters, but the runtime figure registry is book-wide.  This
migration only scopes a local ``Figure N`` label when the same label occurs on
more than one physical PDF page.  Same-page repeated references remain
unchanged, and explicit semantic IDs are never overwritten.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


LOCAL_FIGURE_RE = re.compile(r"^Figure\s+\d+$", re.IGNORECASE)
FIGURE_LIST_KEYS = ("figure_anchors", "figures")


def _structure_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*_structure.json") if path.is_file())


def _page(row: dict[str, Any]) -> int | None:
    anchor = row.get("anchor") if isinstance(row.get("anchor"), dict) else {}
    value = anchor.get("pdf_page") or row.get("pdf_page")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _effective_id(row: dict[str, Any]) -> str | None:
    value = row.get("id") or row.get("figure_id") or row.get("figure") or row.get("number")
    return str(value) if value not in (None, "") else None


def _local_display_label(row: dict[str, Any]) -> str | None:
    # An explicit id/figure_id is already a deliberate namespace decision.  Only
    # fall back to display fields when no explicit identity exists.
    if row.get("id") or row.get("figure_id"):
        return None
    value = row.get("figure") or row.get("number")
    if value in (None, ""):
        return None
    label = str(value)
    return label if LOCAL_FIGURE_RE.fullmatch(label) else None


def normalize_local_figure_ids(root: Path, *, write: bool = False) -> dict[str, Any]:
    files = _structure_files(root)
    parsed: dict[Path, dict[str, Any]] = {}
    label_pages: dict[str, set[int]] = defaultdict(set)

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        parsed[path] = data
        for key in FIGURE_LIST_KEYS:
            values = data.get(key)
            if not isinstance(values, list):
                continue
            for row in values:
                if not isinstance(row, dict):
                    continue
                label = _local_display_label(row)
                page = _page(row)
                if label and page is not None:
                    label_pages[label].add(page)

    conflicting = sorted(label for label, pages in label_pages.items() if len(pages) > 1)
    conflicting_set = set(conflicting)
    changes: list[dict[str, Any]] = []

    for path, data in parsed.items():
        changed_file = False
        for key in FIGURE_LIST_KEYS:
            values = data.get(key)
            if not isinstance(values, list):
                continue
            for row in values:
                if not isinstance(row, dict):
                    continue
                label = _local_display_label(row)
                if label not in conflicting_set:
                    continue
                page = _page(row)
                if page is None:
                    continue
                scoped_id = f"{label}@pdf:{page}"
                if row.get("id") == scoped_id:
                    continue
                changes.append(
                    {
                        "file": str(path.relative_to(root)),
                        "source_key": key,
                        "label": label,
                        "pdf_page": page,
                        "old_id": row.get("id"),
                        "new_id": scoped_id,
                    }
                )
                row["id"] = scoped_id
                changed_file = True
        if changed_file and write:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Evaluate the post-normalization identities in-memory.  A remaining same ID
    # on different pages is a real conflict and must not be hidden by this tool.
    id_pages: dict[str, set[int]] = defaultdict(set)
    for data in parsed.values():
        for key in FIGURE_LIST_KEYS:
            values = data.get(key)
            if not isinstance(values, list):
                continue
            for row in values:
                if not isinstance(row, dict):
                    continue
                figure_id = _effective_id(row)
                page = _page(row)
                if figure_id and page is not None:
                    id_pages[figure_id].add(page)

    remaining_cross_page_conflicts = {
        figure_id: sorted(pages)
        for figure_id, pages in sorted(id_pages.items())
        if len(pages) > 1
    }
    return {
        "status": "PASS" if not remaining_cross_page_conflicts else "FAIL",
        "write": write,
        "conflicting_local_labels": conflicting,
        "changed_occurrences": len(changes),
        "changes": changes,
        "remaining_cross_page_conflicts": remaining_cross_page_conflicts,
        "all_cross_page_figure_ids_unique": not remaining_cross_page_conflicts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("book_root", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    report = normalize_local_figure_ids(args.book_root, write=args.write)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["all_cross_page_figure_ids_unique"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
