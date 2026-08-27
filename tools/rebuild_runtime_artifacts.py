#!/usr/bin/env python3
"""Conservatively rebuild recoverable Course OS runtime artifacts.

Candidates are written as ``*.candidate`` by default.  Nothing is promoted unless
hard objective checks pass.  Page labels are never guessed: rebuilding PageMap
requires the original PDF and pypdf so labels come from the source PDF itself.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable

EXPECTED_FA_BOOK_ID = "stein_shakarchi_functional_analysis_2011"
EXPECTED_FA_PAGES = 442
EXPECTED_FA_CHAPTERS = 8
EXPECTED_FA_SEARCH_RECORDS = 1493
EXPECTED_FA_CORE_RECORDS = 1520


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


def chapter_number(chapter_id: str) -> int | None:
    match = re.search(r"(?:chapter_|ch)0*(\d+)", chapter_id, flags=re.I)
    return int(match.group(1)) if match else None


def canonical_chapter_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    n = chapter_number(text)
    return f"chapter_{n:02d}" if n is not None else None


def infer_chapter_id(section_id: str) -> str | None:
    return canonical_chapter_id(section_id)


def chapter_sort_key(chapter_id: str) -> tuple[int, str]:
    n = chapter_number(chapter_id)
    return (n if n is not None else 10**9, chapter_id)


def section_number_key(number: str | None) -> tuple[Any, ...]:
    if not number:
        return (10**9,)
    parts: list[Any] = []
    for part in re.split(r"[.\-]", str(number)):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(part)
    return tuple(parts)


def new_chapter(cid: str) -> dict[str, Any]:
    n = chapter_number(cid)
    return {
        "id": cid,
        "number": str(n) if n is not None else None,
        "title_en": None,
        "title_zh": None,
        "pdf_page_start": None,
        "printed_page_start": None,
        "source_batches": [],
        "sections": [],
    }


def update_chapter(
    chapter: dict[str, Any],
    *,
    batch_id: str,
    title_en: Any = None,
    title_zh: Any = None,
    pdf_page: Any = None,
    printed_page: Any = None,
) -> None:
    if title_en and not chapter.get("title_en"):
        chapter["title_en"] = title_en
    if title_zh and not chapter.get("title_zh"):
        chapter["title_zh"] = title_zh
    page = as_int(pdf_page)
    if page is not None:
        old = as_int(chapter.get("pdf_page_start"))
        chapter["pdf_page_start"] = page if old is None else min(old, page)
    printed = as_int(printed_page)
    if printed is not None:
        old = as_int(chapter.get("printed_page_start"))
        chapter["printed_page_start"] = printed if old is None else min(old, printed)
    chapter["source_batches"] = sorted(set((chapter.get("source_batches") or []) + [batch_id]))


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
    chapter_marker_rows = 0

    for path in structure_files(root):
        data = load_json(path)
        if not isinstance(data, dict):
            continue
        batch_id = str(data.get("chunk_id") or path.stem.replace("_structure", ""))

        declared: list[str] = []
        if data.get("chapter_id"):
            cid = canonical_chapter_id(data.get("chapter_id")) or str(data["chapter_id"])
            declared.append(cid)
        if isinstance(data.get("chapter_ids"), list):
            for value in data["chapter_ids"]:
                cid = canonical_chapter_id(value) or str(value)
                if cid not in declared:
                    declared.append(cid)

        for cid in declared:
            chapter = chapters.setdefault(cid, new_chapter(cid))
            update_chapter(
                chapter,
                batch_id=batch_id,
                title_en=data.get("chapter_title_en") if len(declared) == 1 else None,
                title_zh=data.get("chapter_title_zh") if len(declared) == 1 else None,
            )

        units = data.get("content_units") if isinstance(data.get("content_units"), list) else []
        for unit in units:
            if not isinstance(unit, dict):
                continue
            cid = canonical_chapter_id(unit.get("chapter_id"))
            if not cid:
                continue
            chapter = chapters.setdefault(cid, new_chapter(cid))
            is_opening = unit.get("type") == "chapter_opening"
            update_chapter(
                chapter,
                batch_id=batch_id,
                title_en=unit.get("title_en") if is_opening else None,
                title_zh=unit.get("title_zh") if is_opening else None,
                pdf_page=unit.get("pdf_page") if is_opening else None,
                printed_page=unit.get("printed_page") if is_opening else None,
            )

        raw_sections = data.get("sections") if isinstance(data.get("sections"), list) else []
        for raw in raw_sections:
            if not isinstance(raw, dict) or not raw.get("id"):
                continue
            sid = str(raw["id"])
            inferred = infer_chapter_id(sid)
            cid = canonical_chapter_id(raw.get("chapter_id")) or inferred
            if not cid and len(declared) == 1:
                cid = declared[0]

            pdf_start, pdf_end = pair(raw.get("batch_coverage") or raw.get("pdf_pages") or raw.get("pdf_page"))
            printed_start, printed_end = pair(raw.get("printed_pages") or raw.get("printed_page"))

            # Later batches encode a chapter start as a row inside sections, e.g.
            # id=chapter_05.  Chapter 8 uses ch08_intro for the same purpose.
            is_explicit_chapter_marker = bool(re.fullmatch(r"chapter_0*\d+", sid, flags=re.I))
            is_intro_marker = bool(re.fullmatch(r"ch0*\d+_intro", sid, flags=re.I))
            if cid and (is_explicit_chapter_marker or is_intro_marker):
                chapter = chapters.setdefault(cid, new_chapter(cid))
                update_chapter(
                    chapter,
                    batch_id=batch_id,
                    title_en=raw.get("title_en"),
                    title_zh=raw.get("title_zh"),
                    pdf_page=pdf_start,
                    printed_page=printed_start,
                )
                chapter_marker_rows += 1
                continue

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
                chapter = chapters.setdefault(cid, new_chapter(cid))
                update_chapter(
                    chapter,
                    batch_id=batch_id,
                    pdf_page=pdf_start,
                    printed_page=printed_start,
                )

    for section in sections.values():
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
        "chapter_marker_rows_folded": chapter_marker_rows,
        "chapters": output_chapters,
    }
    path = root / "toc_bilingual.json.candidate"
    write_json(path, result)
    return path, result


def delta_version(path: Path) -> tuple[int, ...]:
    match = re.search(r"search_index_delta_v(\d+)(?:_(\d+))?", path.name)
    if not match:
        return (10**9,)
    return tuple(int(x) for x in match.groups() if x is not None)


def load_delta_records(root: Path) -> OrderedDict[str, dict[str, Any]]:
    records: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for path in sorted(root.glob("search_index_delta_v*.jsonl"), key=delta_version):
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
    for key in ("pdf_page", "page", "p"):
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
    if isinstance(anchor, dict) and anchor.get("printed_page") is not None:
        return anchor.get("printed_page")
    page = first_page(record)
    if page is not None and 20 <= page <= EXPECTED_FA_PAGES:
        return page - 19
    return None


def object_id(record: dict[str, Any]) -> str | None:
    for key in ("id", "object_id", "exercise_id", "problem_id", "unit_id", "figure_id"):
        if record.get(key):
            return str(record[key])
    return None


def anchor_record(row: dict[str, Any], *, book_id: str, rid: str) -> dict[str, Any]:
    row = dict(row)
    row["id"] = rid
    row["book_id"] = book_id
    page = first_page(row)
    printed = printed_page(row)
    if page is not None:
        row["pdf_page"] = page
    if printed is not None:
        row["printed_page"] = printed
    if page is not None:
        row.setdefault("source_anchor", f"{book_id}:pdf:{page}:{rid}")
        row.setdefault(
            "jump_target",
            {"book_id": book_id, "pdf_page": page, "printed_page": printed, "object_id": rid},
        )
    return row


def enrich_record(
    record: dict[str, Any], *, book_id: str, chunk_id: str | None, forced_type: str | None = None
) -> dict[str, Any] | None:
    rid = object_id(record)
    if not rid:
        return None
    row = dict(record)
    if chunk_id:
        row.setdefault("chunk_id", chunk_id)
    if forced_type:
        row.setdefault("type", forced_type)
    row.setdefault("type", "object")
    return anchor_record(row, book_id=book_id, rid=rid)


def normalized_term(text: Any) -> str:
    value = unicodedata.normalize("NFKC", str(text or "")).casefold().strip()
    value = re.sub(r"\s+", " ", value)
    value = value.replace("–", "-").replace("—", "-")
    return value


def stable_text_id(prefix: str, text: Any) -> str:
    normalized = normalized_term(text)
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")[:48]
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{ascii_slug}_{digest}" if ascii_slug else f"{prefix}_{digest}"


def expand_backmatter_groups(
    records: OrderedDict[str, dict[str, Any]], *, book_id: str
) -> tuple[OrderedDict[str, dict[str, Any]], dict[str, int]]:
    out: OrderedDict[str, dict[str, Any]] = OrderedDict()
    stats = {
        "group_rows_removed": 0,
        "expanded_bibliography_count": 0,
        "expanded_symbol_count": 0,
        "expanded_index_item_count": 0,
        "index_duplicate_terms_merged": 0,
    }
    index_rows: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def add_index(term: Any, page: Any, chunk_id: str | None) -> None:
        normalized = normalized_term(term)
        if not normalized:
            return
        rid = stable_text_id("index", normalized)
        p = as_int(page)
        if rid in index_rows:
            stats["index_duplicate_terms_merged"] += 1
            existing = index_rows[rid]
            pages = set(existing.get("pdf_pages") or ([existing.get("pdf_page")] if existing.get("pdf_page") else []))
            if p is not None:
                pages.add(p)
            existing["pdf_pages"] = sorted(int(x) for x in pages if x is not None)
            return
        row = {
            "id": rid,
            "type": "index_entry",
            "term": str(term),
            "pdf_page": p,
            "printed_page": (p - 19) if p is not None and p >= 20 else None,
            "chunk_id": chunk_id,
            "terms": [str(term)],
        }
        index_rows[rid] = anchor_record(row, book_id=book_id, rid=rid)

    for rid, row in records.items():
        row_type = str(row.get("type") or "")
        if row_type == "bibliography_group" and isinstance(row.get("entries"), list):
            stats["group_rows_removed"] += 1
            for entry in row["entries"]:
                if not isinstance(entry, dict):
                    continue
                n = str(entry.get("n") or "").strip()
                entry_id = f"bibliography_{int(n):03d}" if n.isdigit() else stable_text_id("bibliography", entry.get("citation"))
                p = as_int(entry.get("p"))
                item = {
                    "id": entry_id,
                    "type": "bibliography",
                    "number": n or None,
                    "citation": entry.get("citation"),
                    "pdf_page": p,
                    "printed_page": (p - 19) if p is not None and p >= 20 else None,
                    "chunk_id": row.get("chunk_id"),
                }
                out[entry_id] = anchor_record(item, book_id=book_id, rid=entry_id)
                stats["expanded_bibliography_count"] += 1
            continue

        if row_type == "symbol_glossary_group" and isinstance(row.get("symbols"), list):
            stats["group_rows_removed"] += 1
            for symbol in row["symbols"]:
                if not isinstance(symbol, dict):
                    continue
                symbol_text = symbol.get("symbol")
                symbol_id = stable_text_id("symbol", symbol_text)
                p = as_int(symbol.get("p"))
                item = {
                    "id": symbol_id,
                    "type": "symbol_glossary",
                    "symbol": symbol_text,
                    "first_printed_page": symbol.get("first"),
                    "meaning": symbol.get("meaning"),
                    "pdf_page": p,
                    "printed_page": (p - 19) if p is not None and p >= 20 else None,
                    "chunk_id": row.get("chunk_id"),
                }
                out[symbol_id] = anchor_record(item, book_id=book_id, rid=symbol_id)
                stats["expanded_symbol_count"] += 1
            continue

        if row_type == "index_group" and isinstance(row.get("terms"), list):
            stats["group_rows_removed"] += 1
            for item in row["terms"]:
                if isinstance(item, dict):
                    add_index(item.get("term"), item.get("p"), str(row.get("chunk_id") or "") or None)
                    stats["expanded_index_item_count"] += 1
            continue

        out[rid] = row

    # v0.36 appended the final 97 Index rows in chunk_023a, stored as
    # [term, pdf_page] pairs rather than dict objects.
    # They share the same stable key with the v0.35 Index group, so repeated
    # terms merge rather than acquiring a second identity.
    for row in index_rows.values():
        out[row["id"]] = row

    return out, stats


def append_final_index_from_structure(
    records: OrderedDict[str, dict[str, Any]], root: Path, *, book_id: str, stats: dict[str, int]
) -> None:
    # Preserve one stable row per normalized index term across PDF 438-442.
    by_term: dict[str, str] = {}
    for rid, row in records.items():
        if row.get("type") == "index_entry" and row.get("term"):
            by_term[normalized_term(row["term"])] = rid

    for path in structure_files(root):
        data = load_json(path)
        if not isinstance(data, dict) or not isinstance(data.get("index_entries"), list):
            continue
        chunk_id = str(data.get("chunk_id") or path.stem.replace("_structure", ""))
        for raw in data["index_entries"]:
            term: Any = None
            page: Any = None
            if isinstance(raw, (list, tuple)) and len(raw) >= 2:
                term, page = raw[0], raw[1]
            elif isinstance(raw, dict):
                term = raw.get("term") or raw.get("name")
                page = raw.get("p") or raw.get("pdf_page")
            else:
                continue
            normalized = normalized_term(term)
            if not normalized:
                continue
            stats["expanded_index_item_count"] += 1
            p = as_int(page)
            if normalized in by_term:
                stats["index_duplicate_terms_merged"] += 1
                rid = by_term[normalized]
                existing = records[rid]
                pages = set(existing.get("pdf_pages") or ([existing.get("pdf_page")] if existing.get("pdf_page") else []))
                if p is not None:
                    pages.add(p)
                existing["pdf_pages"] = sorted(int(x) for x in pages if x is not None)
                continue
            rid = stable_text_id("index", normalized)
            row = {
                "id": rid,
                "type": "index_entry",
                "term": str(term),
                "terms": [str(term)],
                "pdf_page": p,
                "printed_page": (p - 19) if p is not None and p >= 20 else None,
                "chunk_id": chunk_id,
            }
            records[rid] = anchor_record(row, book_id=book_id, rid=rid)
            by_term[normalized] = rid


def merge_structure_records(
    records: OrderedDict[str, dict[str, Any]], root: Path, *, book_id: str
) -> None:
    # Preserve all historical ordinary records while filling any objects that were
    # emitted into structure JSON but omitted from an old delta.
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
                row = enrich_record(
                    raw,
                    book_id=book_id,
                    chunk_id=chunk_id,
                    forced_type=str(raw.get("type") or "content_unit"),
                )
                if not row:
                    continue
                previous = records.get(row["id"], {})
                merged = dict(previous)
                merged.update({k: v for k, v in row.items() if v not in (None, "", [], {})})
                records[row["id"]] = merged


def rebuild_search_index(root: Path) -> tuple[Path, dict[str, Any]]:
    metadata = load_json(root / "book_metadata.json")
    book_id = str(metadata.get("book_id") or "")
    delta_records = load_delta_records(root)
    raw_delta_unique_count = len(delta_records)

    records, stats = expand_backmatter_groups(delta_records, book_id=book_id)
    append_final_index_from_structure(records, root, book_id=book_id, stats=stats)
    merge_structure_records(records, root, book_id=book_id)

    final_rows: list[dict[str, Any]] = []
    without_anchor: list[str] = []
    wrong_book: list[str] = []
    for rid, raw in records.items():
        row = anchor_record(raw, book_id=book_id, rid=rid)
        if raw.get("book_id") not in (None, book_id):
            wrong_book.append(rid)
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
        "raw_delta_unique_count": raw_delta_unique_count,
        **stats,
        "expanded_backmatter_raw_count": (
            stats["expanded_bibliography_count"]
            + stats["expanded_symbol_count"]
            + stats["expanded_index_item_count"]
        ),
        "record_count": len(final_rows),
        "expected_record_count": EXPECTED_FA_SEARCH_RECORDS if book_id == EXPECTED_FA_BOOK_ID else None,
        "expected_core_record_count_before_stable_dedupe": EXPECTED_FA_CORE_RECORDS if book_id == EXPECTED_FA_BOOK_ID else None,
        "all_unique": len({row["id"] for row in final_rows}) == len(final_rows),
        "without_source_anchor": without_anchor,
        "wrong_book_id_before_normalization": wrong_book,
        "candidate": str(out.name),
        "promotable_by_count_and_anchor": (
            book_id == EXPECTED_FA_BOOK_ID
            and len(final_rows) == EXPECTED_FA_SEARCH_RECORDS
            and not without_anchor
            and len({row["id"] for row in final_rows}) == len(final_rows)
        ),
    }
    write_json(root / "search_index_v0_36.rebuild_report.json", report)
    return out, report


def rebuild_page_map(root: Path, source_pdf: Path) -> tuple[Path, dict[str, Any]]:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PageMap rebuild requires pypdf. Install with: python -m pip install pypdf") from exc

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
        rows.append({"pdf_page": index, "page_label": label_text, "printed_page": printed if printed is not None else ""})

    out = root / "page_map.csv.candidate"
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["pdf_page", "page_label", "printed_page"])
        writer.writeheader()
        writer.writerows(rows)

    main_mapping_ok = all(
        str(rows[p - 1]["page_label"]) == str(p - 19) and rows[p - 1]["printed_page"] == p - 19
        for p in range(20, total + 1)
    ) if total >= 20 else False
    report = {
        "source_pdf": str(source_pdf),
        "pdf_pages": total,
        "page_labels": len(labels),
        "expected_pages": EXPECTED_FA_PAGES if total == EXPECTED_FA_PAGES else None,
        "main_mapping_pdf20_442_ok": main_mapping_ok,
        "candidate": str(out.name),
        "promotable_by_page_count_and_labels": total == EXPECTED_FA_PAGES and main_mapping_ok,
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
        help="promote only candidates satisfying hard objective checks",
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
                "reason": "--source-pdf is required; embedded page labels will not be guessed",
            }
        else:
            path, report = rebuild_page_map(root, args.source_pdf)
            summary["outputs"]["page_map"] = report
            if args.promote_safe and report.get("promotable_by_page_count_and_labels"):
                promote_candidate(path, root / "page_map.csv")
                summary["outputs"]["page_map"]["promoted"] = True

    summary["remaining_gate"] = [
        "Validate TOC chapter_count == 8",
        "Validate final search index == 1493 unique IDs and zero missing anchors",
        "Rebuild PageMap from original PDF embedded labels",
        "Run tools/check_runtime_readiness.py <book_root> --write",
    ]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
