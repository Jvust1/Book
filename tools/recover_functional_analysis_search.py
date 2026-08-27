#!/usr/bin/env python3
"""Recover the audited Functional Analysis v0.36 search index.

This module is intentionally book-specific. The historical search pipeline used a
full v0.5 baseline through PDF 90 and delta files from v0.6 onward. The v0.5
full export is no longer present, so recovery must reconstruct only that missing
baseline portion from structure files instead of indiscriminately adding every
structure-only object created later.

The final v0.36 audit also normalized seven legacy ``*_complete`` IDs back to
their original stable IDs and appended Index ordinals 135-231 from PDF 441-442.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import rebuild_runtime_artifacts as base

V05_LAST_PDF_PAGE = 90
NON_SEARCH_FRONTMATTER_TYPES = {"copyright", "series_info"}


def _merge_row(
    records: OrderedDict[str, dict[str, Any]],
    row: dict[str, Any],
    *,
    book_id: str,
    prefer_existing_identity: bool = False,
) -> None:
    rid = str(row["id"])
    previous = records.get(rid)
    if previous is None:
        records[rid] = base.anchor_record(row, book_id=book_id, rid=rid)
        return

    if prefer_existing_identity:
        merged = dict(row)
        merged.update({k: v for k, v in previous.items() if v not in (None, "", [], {})})
    else:
        merged = dict(previous)
        merged.update({k: v for k, v in row.items() if v not in (None, "", [], {})})
    records[rid] = base.anchor_record(merged, book_id=book_id, rid=rid)


def merge_v05_baseline_structure(
    records: OrderedDict[str, dict[str, Any]],
    root: Path,
    *,
    book_id: str,
) -> dict[str, Any]:
    """Reconstruct only the missing v0.5 baseline through physical PDF 90.

    Existing IDs may be enriched from later structure JSON, but a structure row
    absent from the historical delta stream is introduced only when its source
    page belongs to the v0.5 baseline range. This is the key distinction from
    the earlier over-broad recovery that produced 1512 records.
    """

    stats: dict[str, Any] = {
        "core_rows_seen": 0,
        "core_existing_ids_merged": 0,
        "v05_core_new_unique_ids": 0,
        "post_v05_structure_only_skipped": 0,
        "v05_frontmatter_added": 0,
        "v05_frontmatter_excluded": [],
    }

    for path in base.structure_files(root):
        data = base.load_json(path)
        if not isinstance(data, dict):
            continue
        chunk_id = str(data.get("chunk_id") or path.stem.replace("_structure", ""))
        sources: Iterable[tuple[str, str | None]] = (
            ("key_objects", None),
            ("objects", None),
            ("exercises", "exercise"),
            ("problems", "problem"),
        )
        for key, forced_type in sources:
            values = data.get(key)
            if not isinstance(values, list):
                continue
            for raw in values:
                if not isinstance(raw, dict):
                    continue
                row = base.enrich_core_record(
                    raw,
                    book_id=book_id,
                    chunk_id=chunk_id,
                    forced_type=forced_type,
                )
                if not row:
                    continue
                stats["core_rows_seen"] += 1
                rid = str(row["id"])
                if rid in records:
                    stats["core_existing_ids_merged"] += 1
                    _merge_row(records, row, book_id=book_id)
                    continue

                page = base.first_page(row)
                if page is not None and page <= V05_LAST_PDF_PAGE:
                    stats["v05_core_new_unique_ids"] += 1
                    _merge_row(records, row, book_id=book_id)
                else:
                    stats["post_v05_structure_only_skipped"] += 1

    chunk001_path = root / "chunks" / "chunk_001_structure.json"
    if chunk001_path.exists():
        chunk001 = base.load_json(chunk001_path)
        units = chunk001.get("content_units") if isinstance(chunk001, dict) else None
        for raw in units if isinstance(units, list) else []:
            if not isinstance(raw, dict):
                continue
            rid = base.object_id(raw)
            if not rid:
                continue
            row_type = str(raw.get("type") or "frontmatter")
            if raw.get("metadata_only") is True or row_type in NON_SEARCH_FRONTMATTER_TYPES:
                stats["v05_frontmatter_excluded"].append(rid)
                continue
            # Search results need a meaningful label. This excludes storage-only
            # frontmatter metadata while keeping cover, foreword, TOC, preface,
            # and the Chapter 1 opening as navigable book nodes.
            if not (raw.get("title_en") or raw.get("title_zh") or raw.get("chapter_id")):
                stats["v05_frontmatter_excluded"].append(rid)
                continue
            row = dict(raw)
            row["id"] = rid
            row.setdefault("chunk_id", "chunk_001")
            row.setdefault("type", row_type)
            _merge_row(records, row, book_id=book_id)
            stats["v05_frontmatter_added"] += 1

    return stats


def normalize_legacy_complete_ids(
    records: OrderedDict[str, dict[str, Any]],
    *,
    book_id: str,
    legacy_complete_ids: set[str],
) -> dict[str, Any]:
    """Normalize only legacy complete IDs that actually occur in delta history."""

    normalized: list[dict[str, Any]] = []
    collision_count = 0

    for complete_id in sorted(legacy_complete_ids):
        if not complete_id.endswith("_complete") or complete_id not in records:
            continue
        stable_id = complete_id[: -len("_complete")]
        completed = records.pop(complete_id)
        existing = records.get(stable_id)

        if existing is not None:
            collision_count += 1
            # Preserve the original stable object's identity/page while filling
            # any fields that existed only on the completion row.
            merged = dict(completed)
            merged.update({k: v for k, v in existing.items() if v not in (None, "", [], {})})
        else:
            merged = dict(completed)

        merged.pop("source_anchor", None)
        merged.pop("jump_target", None)
        merged["id"] = stable_id
        records[stable_id] = base.anchor_record(merged, book_id=book_id, rid=stable_id)
        normalized.append(
            {
                "from": complete_id,
                "to": stable_id,
                "collided_with_existing": existing is not None,
            }
        )

    return {
        "legacy_complete_normalized_count": len(normalized),
        "legacy_complete_collision_count": collision_count,
        "legacy_complete_normalizations": normalized,
    }


def recover_search_index(root: Path, *, promote_safe: bool = False) -> tuple[Path, dict[str, Any]]:
    metadata = base.load_json(root / "book_metadata.json")
    book_id = str(metadata.get("book_id") or "")
    if book_id != base.EXPECTED_FA_BOOK_ID:
        raise RuntimeError(f"This recovery is only valid for {base.EXPECTED_FA_BOOK_ID}; got {book_id!r}")

    delta_records = base.load_delta_records(root)
    legacy_complete_ids = {rid for rid in delta_records if rid.endswith("_complete")}
    records, expansion = base.expand_v035_backmatter(delta_records, book_id=book_id)

    baseline_stats = merge_v05_baseline_structure(records, root, book_id=book_id)
    normalization_stats = normalize_legacy_complete_ids(
        records,
        book_id=book_id,
        legacy_complete_ids=legacy_complete_ids,
    )
    pre_tail_count = len(records)
    base.append_v036_index_tail(records, root, book_id=book_id, stats=expansion)

    final_rows: list[dict[str, Any]] = []
    without_anchor: list[str] = []
    duplicate_ids: list[str] = []
    seen: set[str] = set()
    for rid, raw in records.items():
        if rid in seen:
            duplicate_ids.append(rid)
        seen.add(rid)
        row = base.anchor_record(raw, book_id=book_id, rid=rid)
        if not row.get("source_anchor"):
            without_anchor.append(rid)
        final_rows.append(row)

    final_rows.sort(
        key=lambda row: (
            base.first_page(row) if base.first_page(row) is not None else 10**9,
            str(row.get("type") or ""),
            str(row.get("number") or row.get("ordinal") or ""),
            str(row.get("id") or ""),
        )
    )

    out = root / "search_index_v0_36.jsonl.candidate"
    with out.open("w", encoding="utf-8") as fh:
        for row in final_rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    report: dict[str, Any] = {
        "book_id": book_id,
        "recovery_model": "v0.5 baseline through PDF 90 + v0.6-v0.35 deltas + v0.36 index tail",
        "raw_delta_unique_count": len(delta_records),
        **expansion,
        **baseline_stats,
        **normalization_stats,
        "pre_tail_unique_count": pre_tail_count,
        "record_count": len(final_rows),
        "expected_record_count": base.EXPECTED_FA_SEARCH_RECORDS,
        "all_unique": not duplicate_ids and len(seen) == len(final_rows),
        "duplicate_ids": duplicate_ids,
        "without_source_anchor": without_anchor,
        "candidate": out.name,
    }
    report["promotable_by_count_and_anchor"] = (
        report["record_count"] == base.EXPECTED_FA_SEARCH_RECORDS
        and report["all_unique"]
        and not without_anchor
        and report["legacy_complete_normalized_count"] == 7
    )
    base.write_json(root / "search_index_v0_36.rebuild_report.json", report)

    if promote_safe and report["promotable_by_count_and_anchor"]:
        shutil.copyfile(out, root / "search_index_v0_36.jsonl")
        report["promoted"] = True
        base.write_json(root / "search_index_v0_36.rebuild_report.json", report)

    return out, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("book_root", type=Path)
    parser.add_argument("--promote-safe", action="store_true")
    args = parser.parse_args()

    candidate, report = recover_search_index(args.book_root, promote_safe=args.promote_safe)
    print(json.dumps({"candidate": str(candidate), "report": report}, ensure_ascii=False, indent=2))
    return 0 if report["promotable_by_count_and_anchor"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
