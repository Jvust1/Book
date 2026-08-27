#!/usr/bin/env python3
"""Rebuild recoverable Book runtime artifacts from canonical source data.

The script is intentionally conservative:

- It writes ``*.candidate`` outputs by default.
- It never invents PDF page labels.  PageMap rebuilding requires the original PDF
  and ``pypdf`` so embedded page labels can be read from the source itself.
- It can reconstruct a bilingual TOC candidate from stable structure batches.
- It can reconstruct a search-index candidate from existing deltas + structured
  objects, add canonical source anchors, deduplicate by stable ID, and report the
  resulting record count.
- It does NOT silently promote a candidate to the final v0.36 artifact.  Promotion
  is allowed only when explicit validation conditions pass.

Example:

    python tools/rebuild_runtime_artifacts.py books/functional-analysis \
        --source-pdf "Functional Analysis.pdf" --all

Install the optional PDF dependency only when rebuilding PageMap:

    python -m pip install pypdf
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable


EXPECTED_FA_BOOK_ID = "stein_shakarchi_functional_analysis_2011"
EXPECTED_FA_PAGES = 442
EXPECTED_FA_CHAPTERS = 8
EXPECTED_FA_SEARCH_RECORDS = 1493


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def structure_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*_structure.json"), key=lambda p: str(p.relative_to(root)))


def pair(value: Any) -> tuple[Any, Any]:
    if isinstance(value, list) and value:
        return value[0], value[1] if len(value) > 1 else value[0]
    if value is not None:
        return value, value
    return None, None


def as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def chapter_sort_key(chapter_id: str) -> tuple[int, str]:
    match = re.search(r"(\d+)$", chapter_id)
    return (int(match.group(1)) if match else 10**9, chapter_id)


def section_number_key(number: str | None) -> tuple:
    if not number:
        return (10**9,)
    parts: list[Any] = []
    for part in re.split(r"[.\-]", str(number)):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(part)
    return tuple(parts)


def merge_section(existing: dict[str, Any], incoming: dict[str, Any]) -> None:
    for key in ("number", "title_en", "title_zh", "chapter_id"):
        if not existing.get(key) and incoming.get(key):
            existing[key] = incoming[key]

    for start_key, end_key in (("pdf_page_start", "pdf_page_end"), ("printed_page_start", "printed_page_end")):
        old_start = as_int(existing.get(start_key))
        new_start = as_int(incoming.get(start_key))
        old_end = as_int(existing.get(end_key))
        new_end = as_int(incoming.get(end_key))
        if new_start is not None:
            existing[start_key] = new_start if old_start is None else min(old_start, new_start)
        if new_end is not None:
            existing[end_key] = new_end if old_end is None else max(old_end, new_end)

    sources = set(existing.get("source_batches") or [])
    sources.update(incoming.get("source_batches") or [])
    existing["source_batches"] = sorted(sources)


def rebuild_toc(root: Path) -> tuple[Path, dict[str, Any]]:
    metadata = load_json(root / "book_metadata.json")
    chapters: dict[str, dict[str, Any]] = {}
    sections: dict[str, dict[str, Any]] = {}

    for path in structure_files(root):
        data = load_json(path)
        if not isinstance(data, dict):
            continue
        batch_id = str(data.get("chunk_id") or path.stem.replace("_structure", ""))
        batch_chapter_id = data.get("chapter_id")

        if batch_chapter_id:
            cid = str(batch_chapter_id)
            chapter = chapters.setdefault(
                cid,
                {
                    "id": cid,
                    "number": re.sub(r"^chapter_0*", "", cid) or None,
                    "title_en": None,
                    "title_zh": None,
                    "pdf_page_start": None,
                    "printed_page_start": None,
                    "source_batches": [],
                    "sections": [],
                },
            )
            chapter["title_en"] = chapter.get("title_en") or data.get("chapter_title_en")
            chapter["title_zh"] = chapter.get("title_zh") or data.get("chapter_title_zh")
            chapter["source_batches"] = sorted(set(chapter["source_batches"] + [batch_id]))

        units = data.get("content_units") if isinstance(data.get("content_units"), list) else []
        for unit in units:
            if not isinstance(unit, dict):
                continue
            cid = unit.get("chapter_id")
            if not cid:
                continue
            cid = str(cid)
            chapter = chapters.setdefault(
                cid,
                {
                    "id": cid,
                    "number": re.sub(r"^chapter_0*", "", cid) or None,
                    "title_en": None,
                    "title_zh": None,
                    "pdf_page_start": None,
                    "printed_page_start": None,
                    "source_batches": [],
                    "sections": [],
                },
            )
            if unit.get("type") == "chapter_opening":
                chapter["title_en"] = chapter.get("title_en") or unit.get("title_en")
                chapter["title_zh"] = chapter.get("title_zh") or unit.get("title_zh")
                chapter["pdf_page_start"] = chapter.get("pdf_page_start") or as_int(unit.get("pdf_page"))
                chapter["printed_page_start"] = chapter.get("printed_page_start") or as_int(unit.get("printed_page"))
            chapter["source_batches"] = sorted(set(chapter["source_batches"] + [batch_id]))

        raw_sections = data.get("sections") if isinstance(data.get("sections"), list) else []
        for raw in raw_sections:
            if not isinstance(raw, dict) or not raw.get("id"):
                continue
            sid = str(raw["id"])
            cid = str(raw.get("chapter_id") or batch_chapter_id or "") or None
            pdf_start, pdf_end = pair(raw.get("pdf_pages") or raw.get("pdf_page"))
            printed_start, printed_end = pair(raw.get("printed_pages") or raw.get("printed_page"))
            row = {
                "id": sid,
                "chapter_id": cid,
                "number": str(raw.get("number")) if raw.get("number") is not None else None,
                "title_en": raw.get("title_en"),
                "title_zh": raw.get("title_zh"),
                "pdf_page_start": as_int(pdf_start),
                "pdf_page_end": as_int(pdf_end),
                "printed_page_start": as_int(printed_start),
                "printed_page_end": as_int(printed_end),
                "source_batches": [batch_id],
            }
            if sid in sections:
                merge_section(sections[sid], row)
            else:
                sections[sid] = row

            if cid:
                chapter = chapters.setdefault(
                    cid,
                    {
                        "id": cid,
                        "number": re.sub(r"^chapter_0*", "", cid) or None,
                        "title_en": None,
                        "title_zh": None,
                        "pdf_page_start": None,
                        "printed_page_start": None,
                        "source_batches": [],
                        "sections": [],
                    },
                )
                chapter["source_batches"] = sorted(set(chapter["source_batches"] + [batch_id]))
                starts = [p for p in (chapter.get("pdf_page_start"), as_int(pdf_start)) if p is not None]
                if starts:
                    chapter["pdf_page_start"] = min(starts)
                printed_starts = [p for p in (chapter.get("printed_page_start"), as_int(printed_start)) if p is not None]
                if printed_starts:
                    chapter["printed_page_start"] = min(printed_starts)

    for sid, section in sections.items():
        cid = section.get("chapter_id")
        if cid and cid in chapters:
            chapters[cid]["sections"].append(section)

    output_chapters: list[dict[str, Any]] = []
    for cid in sorted(chapters, key=chapter_sort_key):
        chapter = chapters[cid]
        chapter["sections"] = sorted(
            chapter["sections"],
            key=lambda row: (
                row.get("pdf_page_start") if row.get("pdf_page_start") is not None else 10**9,
                section_number_key(row.get("number")),
                row["id"],
            ),
        )
        output_chapters.append(chapter)

    result = {
        "schema": "book.toc_bilingual.v1",
        "book_id": metadata.get("book_id"),
        "generated_from": "*_structure.json",
        "chapter_count": len(output_chapters),
        "section_count": len(sections),
        "chapters": output_chapters,
    }
    path = root / "toc_bilingual.json.candidate"
    write_json(path, result)
    return path, result


def load_delta_records(root: Path) -> OrderedDict[str, dict[str, Any]]:
    records: OrderedDict[str, dict[str, Any]] = OrderedDict()
    delta_files = sorted(root.glob("search_index_delta_v*.jsonl"))
    for path in delta_files:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):
                    continue
                rid = row.get("id") or row.get("object_id")
                if rid:
                    records[str(rid)] = row
    return records


def first_page(record: dict[str, Any]) -> int | None:
    for key in ("pdf_page", "page"):
        if record.get(key) is not None:
            return as_int(record.get(key))
    value = record.get("pdf_pages")
    if isinstance(value, list) and value:
        return as_int(value[0])
    anchor = record.get("anchor")
    if isinstance(anchor, dict):
        return as_int(anchor.get("pdf_page"))
    return None


def printed_page(record: dict[str, Any]) -> Any:
    if record.get("printed_page") is not None:
        return record.get("printed_page")
    value = record.get("printed_pages")
    if isinstance(value, list) and value:
        return value[0]
    anchor = record.get("anchor")
    if isinstance(anchor, dict):
        return anchor.get("printed_page")
    return None


def object_id(record: dict[str, Any]) -> str | None:
    for key in ("id", "object_id", "exercise_id", "problem_id", "unit_id", "figure_id"):
        if record.get(key):
            return str(record[key])
    return None


def enrich_record(record: dict[str, Any], *, book_id: str, chunk_id: str | None, forced_type: str | None = None) -> dict[str, Any] | None:
    rid = object_id(record)
    if not rid:
        return None
    row = dict(record)
    row["id"] = rid
    row.setdefault("book_id", book_id)
    if chunk_id:
        row.setdefault("chunk_id", chunk_id)
    if forced_type:
        row.setdefault("type", forced_type)
    row.setdefault("type", "object")

    page = first_page(row)
    printed = printed_page(row)
    if page is not None:
        row["pdf_page"] = page
    if printed is not None:
        row["printed_page"] = printed

    if page is not None and not row.get("source_anchor"):
        row["source_anchor"] = f"{book_id}:pdf:{page}:{rid}"
    if page is not None and not row.get("jump_target"):
        row["jump_target"] = {
            "book_id": book_id,
            "pdf_page": page,
            "printed_page": printed,
            "object_id": rid,
        }
    return row


def rebuild_search_index(root: Path) -> tuple[Path, dict[str, Any]]:
    metadata = load_json(root / "book_metadata.json")
    book_id = str(metadata.get("book_id") or "")
    records = load_delta_records(root)

    for path in structure_files(root):
        data = load_json(path)
        if not isinstance(data, dict):
            continue
        chunk_id = str(data.get("chunk_id") or path.stem.replace("_structure", ""))

        sources: Iterable[tuple[str, str | None]] = (
            ("key_objects", None),
            ("objects", None),
            ("exercises", "exercise"),
            ("problems", "problem"),
            ("figures", "figure"),
            ("figure_anchors", "figure"),
            ("index_entries", "index_entry"),
        )
        for key, forced_type in sources:
            values = data.get(key)
            if not isinstance(values, list):
                continue
            for raw in values:
                if not isinstance(raw, dict):
                    continue
                row = enrich_record(raw, book_id=book_id, chunk_id=chunk_id, forced_type=forced_type)
                if not row:
                    continue
                previous = records.get(row["id"], {})
                merged = dict(previous)
                merged.update({k: v for k, v in row.items() if v not in (None, "", [], {})})
                records[row["id"]] = merged

        units = data.get("content_units")
        if isinstance(units, list):
            for raw in units:
                if not isinstance(raw, dict):
                    continue
                row = enrich_record(raw, book_id=book_id, chunk_id=chunk_id, forced_type=str(raw.get("type") or "content_unit"))
                if not row:
                    continue
                previous = records.get(row["id"], {})
                merged = dict(previous)
                merged.update({k: v for k, v in row.items() if v not in (None, "", [], {})})
                records[row["id"]] = merged

    final_rows: list[dict[str, Any]] = []
    without_anchor: list[str] = []
    wrong_book: list[str] = []
    for rid, row in records.items():
        row["id"] = rid
        if row.get("book_id") not in (None, book_id):
            wrong_book.append(rid)
        row["book_id"] = book_id
        page = first_page(row)
        if page is not None and not row.get("source_anchor"):
            row["source_anchor"] = f"{book_id}:pdf:{page}:{rid}"
        if not row.get("source_anchor"):
            without_anchor.append(rid)
        final_rows.append(row)

    final_rows.sort(
        key=lambda row: (
            first_page(row) if first_page(row) is not None else 10**9,
            str(row.get("type") or ""),
            str(row.get("number") or ""),
            str(row.get("id") or ""),
        )
    )

    out = root / "search_index_v0_36.jsonl.candidate"
    with out.open("w", encoding="utf-8") as fh:
        for row in final_rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    report = {
        "book_id": book_id,
        "record_count": len(final_rows),
        "expected_record_count": EXPECTED_FA_SEARCH_RECORDS if book_id == EXPECTED_FA_BOOK_ID else None,
        "all_unique": len({row["id"] for row in final_rows}) == len(final_rows),
        "without_source_anchor": without_anchor,
        "wrong_book_id_before_normalization": wrong_book,
        "candidate": str(out.name),
        "promotable_by_count_and_anchor": (
            book_id == EXPECTED_FA_BOOK_ID
            and len(final_rows) == EXPECTED_FA_SEARCH_RECORDS
            and not without_anchor
        ),
    }
    write_json(root / "search_index_v0_36.rebuild_report.json", report)
    return out, report


def rebuild_page_map(root: Path, source_pdf: Path) -> tuple[Path, dict[str, Any]]:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PageMap rebuild requires pypdf. Install with: python -m pip install pypdf"
        ) from exc

    reader = PdfReader(str(source_pdf))
    labels = list(reader.page_labels)
    total = len(reader.pages)
    if len(labels) != total:
        raise RuntimeError(f"pypdf returned {len(labels)} labels for {total} pages")

    rows: list[dict[str, Any]] = []
    for index, label in enumerate(labels, start=1):
        label_text = "" if label is None else str(label)
        printed: int | None = None
        if index >= 20 and label_text.isdigit():
            printed = int(label_text)
        rows.append(
            {
                "pdf_page": index,
                "page_label": label_text,
                "printed_page": printed if printed is not None else "",
            }
        )

    out = root / "page_map.csv.candidate"
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["pdf_page", "page_label", "printed_page"])
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "source_pdf": str(source_pdf),
        "pdf_pages": total,
        "page_labels": len(labels),
        "expected_pages": EXPECTED_FA_PAGES if total == EXPECTED_FA_PAGES else None,
        "main_mapping_pdf20": rows[19] if total >= 20 else None,
        "candidate": str(out.name),
        "promotable_by_page_count": total == EXPECTED_FA_PAGES,
    }
    write_json(root / "page_map.rebuild_report.json", report)
    return out, report


def promote_candidate(candidate: Path, final_path: Path) -> None:
    shutil.copyfile(candidate, final_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("book_root", type=Path)
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--toc", action="store_true")
    parser.add_argument("--search-index", action="store_true")
    parser.add_argument("--page-map", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument(
        "--promote-safe",
        action="store_true",
        help="promote only candidates that satisfy hard objective checks; never repairs chunk_002 automatically",
    )
    args = parser.parse_args()

    root: Path = args.book_root
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 2

    run_toc = args.all or args.toc
    run_search = args.all or args.search_index
    run_page = args.all or args.page_map
    if not any((run_toc, run_search, run_page)):
        parser.error("choose --all, --toc, --search-index, or --page-map")

    summary: dict[str, Any] = {"book_root": str(root), "outputs": {}}

    if run_toc:
        path, report = rebuild_toc(root)
        summary["outputs"]["toc"] = report
        if args.promote_safe and report.get("chapter_count") == EXPECTED_FA_CHAPTERS:
            promote_candidate(path, root / "toc_bilingual.json")
            summary["outputs"]["toc"]["promoted"] = True

    if run_search:
        path, report = rebuild_search_index(root)
        summary["outputs"]["search_index"] = report
        if args.promote_safe and report.get("promotable_by_count_and_anchor"):
            promote_candidate(path, root / "search_index_v0_36.jsonl")
            summary["outputs"]["search_index"]["promoted"] = True

    if run_page:
        if not args.source_pdf:
            summary["outputs"]["page_map"] = {
                "status": "SKIPPED",
                "reason": "--source-pdf is required; page labels will not be guessed",
            }
        else:
            path, report = rebuild_page_map(root, args.source_pdf)
            summary["outputs"]["page_map"] = report
            if args.promote_safe and report.get("promotable_by_page_count"):
                promote_candidate(path, root / "page_map.csv")
                summary["outputs"]["page_map"]["promoted"] = True

    summary["remaining_manual_gate"] = [
        "Restore/complete chunks/chunk_002_translation_zh.md",
        "Repair stale chunks/chunk_002_structure.json continuation/status",
        "Remove/archive chunks/chunk_002_translation_zh_partial.md",
        "Run tools/check_runtime_readiness.py <book_root> --write",
    ]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
