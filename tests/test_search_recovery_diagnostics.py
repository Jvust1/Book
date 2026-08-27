from __future__ import annotations

import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools import rebuild_runtime_artifacts as rebuild


class SearchRecoveryDiagnostics(unittest.TestCase):
    def test_report_identity_gap_without_guessing(self) -> None:
        root = Path(__file__).resolve().parents[1] / "books" / "functional-analysis"
        if not root.exists():
            self.skipTest("repository fixture not present")

        metadata = rebuild.load_json(root / "book_metadata.json")
        book_id = str(metadata.get("book_id") or "")
        delta_records = rebuild.load_delta_records(root)
        base_records, _ = rebuild.expand_v035_backmatter(delta_records, book_id=book_id)
        base_ids = set(base_records)
        raw_delta_ids = set(delta_records)
        base_type_counts = Counter(str(row.get("type") or "") for row in base_records.values())

        core_rows: dict[str, dict[str, Any]] = {}
        core_locations: dict[str, set[str]] = defaultdict(set)
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
                    rid = str(row["id"])
                    core_locations[rid].add(chunk_id)
                    previous = core_rows.get(rid, {})
                    merged = dict(previous)
                    merged.update({k: v for k, v in row.items() if v not in (None, "", [], {})})
                    core_rows[rid] = merged

        new_core_ids = sorted(set(core_rows) - base_ids)
        new_type_counts = Counter(str(core_rows[rid].get("type") or "") for rid in new_core_ids)
        new_chunk_counts = Counter(
            chunk
            for rid in new_core_ids
            for chunk in core_locations.get(rid, set())
        )
        new_types_absent_from_base = {
            row_type: count
            for row_type, count in sorted(new_type_counts.items())
            if base_type_counts.get(row_type, 0) == 0
        }
        new_ids_for_absent_types = {
            row_type: [
                rid
                for rid in new_core_ids
                if str(core_rows[rid].get("type") or "") == row_type
            ]
            for row_type in new_types_absent_from_base
        }

        all_ids = base_ids | set(core_rows)
        complete_pairs = []
        literal_complete_base_pairs: list[str] = []
        for rid in sorted(all_ids):
            if not rid.endswith("_complete"):
                continue
            base = rid[: -len("_complete")]
            base_exists = base in all_ids
            complete_row = core_rows.get(rid) or base_records.get(rid) or {}
            base_row = core_rows.get(base) or base_records.get(base) or {}
            complete_pairs.append(
                {
                    "complete_id": rid,
                    "base_id": base,
                    "base_exists": base_exists,
                    "complete_in_raw_delta": rid in raw_delta_ids,
                    "base_in_raw_delta": base in raw_delta_ids,
                    "complete_in_expanded_delta": rid in base_ids,
                    "base_in_expanded_delta": base in base_ids,
                    "complete_type": complete_row.get("type"),
                    "base_type": base_row.get("type"),
                    "complete_pdf_page": rebuild.first_page(complete_row),
                    "base_pdf_page": rebuild.first_page(base_row),
                    "complete_number": complete_row.get("number"),
                    "base_number": base_row.get("number"),
                    "complete_chunks": sorted(core_locations.get(rid, set())),
                    "base_chunks": sorted(core_locations.get(base, set())),
                }
            )
            if base_exists:
                literal_complete_base_pairs.append(rid)

        # Compare newly introduced structure IDs against the pre-structure index.
        # This is diagnostic only: matches are candidates for audit, not automatic merges.
        def text_key(row: dict[str, Any]) -> str:
            for key in (
                "name_en",
                "title_en",
                "name_zh",
                "title_zh",
                "name",
                "title",
                "statement",
            ):
                if row.get(key):
                    return rebuild.normalized_text(row.get(key))
            return ""

        base_semantic: dict[tuple[str, int | None, str], list[str]] = defaultdict(list)
        for rid, row in base_records.items():
            key = (str(row.get("type") or ""), rebuild.first_page(row), text_key(row))
            if key[2]:
                base_semantic[key].append(rid)

        semantic_alias_candidates = []
        for rid in new_core_ids:
            row = core_rows[rid]
            key = (str(row.get("type") or ""), rebuild.first_page(row), text_key(row))
            matches = [candidate for candidate in base_semantic.get(key, []) if candidate != rid]
            if matches:
                semantic_alias_candidates.append(
                    {
                        "new_id": rid,
                        "type": key[0],
                        "pdf_page": key[1],
                        "matches": sorted(matches),
                        "chunks": sorted(core_locations.get(rid, set())),
                    }
                )

        # Also report same type + theorem/lemma/proposition number + page collisions,
        # because some boundary objects use sparse titles but preserve numbering.
        number_groups: dict[tuple[str, int | None, str], set[str]] = defaultdict(set)
        combined = dict(base_records)
        combined.update(core_rows)
        for rid, row in combined.items():
            row_type = str(row.get("type") or "").lower()
            number = rebuild.normalized_text(row.get("number"))
            if row_type not in {"theorem", "lemma", "proposition", "corollary"} or not number:
                continue
            number_groups[(row_type, rebuild.first_page(row), number)].add(rid)
        numbered_collision_groups = [
            {
                "type": key[0],
                "pdf_page": key[1],
                "number": key[2],
                "ids": sorted(ids),
            }
            for key, ids in sorted(number_groups.items(), key=lambda item: str(item[0]))
            if len(ids) > 1
        ]

        records_pre_tail, _ = rebuild.expand_v035_backmatter(delta_records, book_id=book_id)
        rebuild.merge_core_structure_records(records_pre_tail, root, book_id=book_id)
        pre_tail_count = len(records_pre_tail)

        diagnostic = {
            "v035_historical_row_count": 1404,
            "final_pre_tail_unique_target": 1396,
            "recovered_pre_tail_count": pre_tail_count,
            "gap_to_final_pre_tail_target": pre_tail_count - 1396,
            "base_after_delta_expansion": len(base_records),
            "base_type_counts": dict(sorted(base_type_counts.items())),
            "new_core_unique_count": len(new_core_ids),
            "new_core_type_counts": dict(sorted(new_type_counts.items())),
            "new_core_chunk_counts": dict(sorted(new_chunk_counts.items())),
            "new_types_absent_from_base": new_types_absent_from_base,
            "new_ids_for_absent_types": new_ids_for_absent_types,
            "complete_pairs": complete_pairs,
            "literal_complete_base_pairs": literal_complete_base_pairs,
            "semantic_alias_candidates": semantic_alias_candidates,
            "numbered_collision_groups": numbered_collision_groups,
        }
        print("SEARCH_IDENTITY_DIAGNOSTIC=" + json.dumps(diagnostic, ensure_ascii=False, sort_keys=True))

        self.assertEqual(pre_tail_count, 1415)
        self.assertEqual(pre_tail_count - 1396, 19)
        self.assertEqual(len(complete_pairs), 11)


if __name__ == "__main__":
    unittest.main()
