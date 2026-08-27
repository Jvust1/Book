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
        core_source_keys: dict[str, set[str]] = defaultdict(set)
        relation_fields = {
            "continued_from",
            "continues_in",
            "continuation_of",
            "completion_of",
            "completed_from",
            "same_as",
            "alias_of",
            "canonical_id",
            "supersedes",
            "replaces",
        }
        core_relations: dict[str, dict[str, Any]] = defaultdict(dict)

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
                    core_source_keys[rid].add(key)
                    for relation in relation_fields:
                        if raw.get(relation) not in (None, "", [], {}):
                            core_relations[rid][relation] = raw[relation]
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

        # Empirical policy check: from PDF 91 onward the historical delta files
        # are present. Any structure object there that never appears in the raw
        # delta is direct evidence of a non-search object / alias / continuation.
        post90_missing_from_delta = []
        post90_present_type_counts: Counter[str] = Counter()
        post90_missing_type_counts: Counter[str] = Counter()
        for rid, row in sorted(core_rows.items()):
            page = rebuild.first_page(row)
            if page is None or page < 91:
                continue
            row_type = str(row.get("type") or "")
            if rid in raw_delta_ids:
                post90_present_type_counts[row_type] += 1
                continue
            post90_missing_type_counts[row_type] += 1
            post90_missing_from_delta.append(
                {
                    "id": rid,
                    "type": row_type,
                    "pdf_page": page,
                    "number": row.get("number"),
                    "chunks": sorted(core_locations.get(rid, set())),
                    "source_keys": sorted(core_source_keys.get(rid, set())),
                    "relations": core_relations.get(rid, {}),
                }
            )

        early_relation_candidates = [
            {
                "id": rid,
                "type": str(core_rows[rid].get("type") or ""),
                "pdf_page": rebuild.first_page(core_rows[rid]),
                "chunks": sorted(core_locations.get(rid, set())),
                "source_keys": sorted(core_source_keys.get(rid, set())),
                "relations": core_relations[rid],
            }
            for rid in new_core_ids
            if core_relations.get(rid)
        ]

        # Compare new baseline-recovery objects against existing delta objects by
        # normalized title, allowing a one-page boundary shift and type variants.
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

        delta_by_text: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        for rid, row in base_records.items():
            key = text_key(row)
            if key:
                delta_by_text[key].append((rid, row))

        early_text_alias_candidates = []
        for rid in new_core_ids:
            row = core_rows[rid]
            key = text_key(row)
            if not key:
                continue
            page = rebuild.first_page(row)
            matches = []
            for candidate_id, candidate in delta_by_text.get(key, []):
                candidate_page = rebuild.first_page(candidate)
                if page is None or candidate_page is None or abs(page - candidate_page) <= 1:
                    matches.append(candidate_id)
            if matches:
                early_text_alias_candidates.append(
                    {
                        "id": rid,
                        "type": row.get("type"),
                        "pdf_page": page,
                        "matches": sorted(matches),
                    }
                )

        records_pre_tail, _ = rebuild.expand_v035_backmatter(delta_records, book_id=book_id)
        rebuild.merge_core_structure_records(records_pre_tail, root, book_id=book_id)
        pre_tail_count = len(records_pre_tail)

        diagnostic = {
            "final_pre_tail_unique_target": 1396,
            "recovered_pre_tail_count": pre_tail_count,
            "gap_to_final_pre_tail_target": pre_tail_count - 1396,
            "base_after_delta_expansion": len(base_records),
            "new_core_unique_count": len(new_core_ids),
            "new_core_type_counts": dict(sorted(new_type_counts.items())),
            "new_core_chunk_counts": dict(sorted(new_chunk_counts.items())),
            "complete_pairs": complete_pairs,
            "literal_complete_base_pairs": literal_complete_base_pairs,
            "post90_present_type_counts": dict(sorted(post90_present_type_counts.items())),
            "post90_missing_type_counts": dict(sorted(post90_missing_type_counts.items())),
            "post90_missing_from_delta": post90_missing_from_delta,
            "early_relation_candidates": early_relation_candidates,
            "early_text_alias_candidates": early_text_alias_candidates,
        }
        print("SEARCH_IDENTITY_DIAGNOSTIC=" + json.dumps(diagnostic, ensure_ascii=False, sort_keys=True))

        self.assertEqual(pre_tail_count, 1415)
        self.assertEqual(pre_tail_count - 1396, 19)
        self.assertEqual(len(complete_pairs), 11)


if __name__ == "__main__":
    unittest.main()
