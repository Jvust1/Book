from __future__ import annotations

import json
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Any

from tools import rebuild_runtime_artifacts as rebuild


class SearchIdentityReplayDiagnostics(unittest.TestCase):
    def test_replay_v035_baseline_and_report_final_identity_candidates(self) -> None:
        root = Path(__file__).resolve().parents[1] / "books" / "functional-analysis"
        if not root.exists():
            self.skipTest("repository fixture not present")

        metadata = rebuild.load_json(root / "book_metadata.json")
        book_id = str(metadata.get("book_id") or "")
        delta_records = rebuild.load_delta_records(root)
        records, _ = rebuild.expand_v035_backmatter(delta_records, book_id=book_id)
        raw_delta_ids = set(delta_records)

        early_core_added: list[str] = []
        for path in rebuild.structure_files(root):
            data = rebuild.load_json(path)
            if not isinstance(data, dict):
                continue
            chunk_id = str(data.get("chunk_id") or path.stem.replace("_structure", ""))
            for key, forced_type in (
                ("key_objects", None),
                ("objects", None),
                ("exercises", "exercise"),
                ("problems", "problem"),
            ):
                values = data.get(key)
                if not isinstance(values, list):
                    continue
                for raw in values:
                    if not isinstance(raw, dict):
                        continue
                    row = rebuild.enrich_core_record(
                        raw,
                        book_id=book_id,
                        chunk_id=chunk_id,
                        forced_type=forced_type,
                    )
                    if not row:
                        continue
                    page = rebuild.first_page(row)
                    if page is None or page > 90:
                        continue
                    rid = str(row["id"])
                    if rid not in records:
                        early_core_added.append(rid)
                    previous = records.get(rid, {})
                    merged = dict(previous)
                    merged.update({k: v for k, v in row.items() if v not in (None, "", [], {})})
                    records[rid] = rebuild.normalize_search_row(merged, book_id=book_id)

        chunk001 = rebuild.load_json(root / "chunks" / "chunk_001_structure.json")
        content_unit_ids: list[str] = []
        for raw in chunk001.get("content_units", []):
            if not isinstance(raw, dict) or not raw.get("unit_id"):
                continue
            rid = str(raw["unit_id"])
            content_unit_ids.append(rid)
            pdf_page = raw.get("pdf_page")
            if pdf_page is None and isinstance(raw.get("pdf_pages"), list) and raw["pdf_pages"]:
                pdf_page = raw["pdf_pages"][0]
            printed_page = raw.get("printed_page")
            row: dict[str, Any] = {
                "id": rid,
                "book_id": book_id,
                "chunk_id": "chunk_001",
                "type": raw.get("type") or "frontmatter",
                "title_en": raw.get("title_en"),
                "title_zh": raw.get("title_zh"),
                "pdf_page": pdf_page,
                "printed_page": printed_page,
                "source_anchor": rebuild.canonical_source_anchor(
                    book_id,
                    rid,
                    pdf_page,
                    printed_page,
                ),
            }
            records[rid] = rebuild.normalize_search_row(row, book_id=book_id)

        self.assertEqual(len(early_core_added), 157)
        self.assertEqual(len(content_unit_ids), 7)
        self.assertEqual(len(records), 1404)

        # Reproduce the audit's explicit rule: all seven legacy *_complete IDs
        # came from historical deltas and are normalized by removing the suffix.
        legacy_complete_ids = sorted(
            rid for rid in raw_delta_ids if rid.endswith("_complete")
        )
        canonical: dict[str, dict[str, Any]] = {}
        canonical_sources: dict[str, list[str]] = defaultdict(list)
        for rid, row in records.items():
            target = rid[:-len("_complete")] if rid in legacy_complete_ids else rid
            canonical_sources[target].append(rid)
            previous = canonical.get(target, {})
            merged = dict(previous)
            merged.update({k: v for k, v in row.items() if v not in (None, "", [], {})})
            merged["id"] = target
            canonical[target] = rebuild.normalize_search_row(merged, book_id=book_id)

        suffix_collisions = {
            target: sources
            for target, sources in sorted(canonical_sources.items())
            if len(sources) > 1
        }

        def title_key(row: dict[str, Any]) -> str:
            return rebuild.normalized_text(
                row.get("title_en")
                or row.get("name_en")
                or row.get("title_zh")
                or row.get("name_zh")
                or ""
            )

        by_title: dict[tuple[str, str], list[str]] = defaultdict(list)
        by_number: dict[tuple[str, str], list[str]] = defaultdict(list)
        for rid, row in canonical.items():
            row_type = str(row.get("type") or "")
            key = title_key(row)
            if key:
                by_title[(row_type, key)].append(rid)
            number = str(row.get("number") or "").strip()
            if number:
                by_number[(row_type, number)].append(rid)

        title_candidates = []
        for (row_type, key), ids in sorted(by_title.items()):
            if len(ids) < 2:
                continue
            pages = [rebuild.first_page(canonical[rid]) for rid in ids]
            numeric_pages = [page for page in pages if page is not None]
            if numeric_pages and max(numeric_pages) - min(numeric_pages) <= 8:
                title_candidates.append(
                    {"type": row_type, "title_key": key, "ids": ids, "pages": pages}
                )

        number_candidates = []
        for (row_type, number), ids in sorted(by_number.items()):
            if len(ids) < 2:
                continue
            pages = [rebuild.first_page(canonical[rid]) for rid in ids]
            numeric_pages = [page for page in pages if page is not None]
            if numeric_pages and max(numeric_pages) - min(numeric_pages) <= 8:
                number_candidates.append(
                    {"type": row_type, "number": number, "ids": ids, "pages": pages}
                )

        diagnostic = {
            "v035_replay_count": len(records),
            "early_core_added": len(early_core_added),
            "content_unit_ids": content_unit_ids,
            "legacy_complete_ids": legacy_complete_ids,
            "legacy_complete_count": len(legacy_complete_ids),
            "count_after_suffix_normalization": len(canonical),
            "suffix_collisions": suffix_collisions,
            "nearby_exact_title_candidates": title_candidates,
            "nearby_same_type_number_candidates": number_candidates,
            "remaining_gap_to_pre_tail_target_1396": len(canonical) - 1396,
        }
        print("SEARCH_V035_REPLAY_DIAGNOSTIC=" + json.dumps(diagnostic, ensure_ascii=False, sort_keys=True))

        self.assertEqual(len(legacy_complete_ids), 7)


if __name__ == "__main__":
    unittest.main()
