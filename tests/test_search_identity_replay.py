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

        # Preserve line-level evidence before load_delta_records() collapses rows
        # with the same stable ID.
        raw_occurrences: dict[str, list[str]] = defaultdict(list)
        raw_line_count = 0
        for path in sorted(root.glob("search_index_delta_v*.jsonl"), key=rebuild.delta_version):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):
                    continue
                rid = row.get("id") or row.get("object_id")
                if not rid:
                    continue
                raw_line_count += 1
                raw_occurrences[str(rid)].append(path.name)

        duplicate_delta_ids = {
            rid: files
            for rid, files in sorted(raw_occurrences.items())
            if len(files) > 1
        }

        delta_records = rebuild.load_delta_records(root)
        records, _ = rebuild.expand_v035_backmatter(delta_records, book_id=book_id)
        raw_delta_ids = set(delta_records)

        # v0.5 was the full-search baseline through PDF 90. Later delta files
        # therefore must not be backfilled with structure-only objects after 90.
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
                    records[rid] = rebuild.anchor_record(merged, book_id=book_id, rid=rid)

        # The seven early frontmatter/search units are part of the v0.5 baseline.
        chunk001 = rebuild.load_json(root / "chunks" / "chunk_001_structure.json")
        content_unit_ids: list[str] = []
        for raw in chunk001.get("content_units", []):
            if not isinstance(raw, dict) or not raw.get("unit_id"):
                continue
            rid = str(raw["unit_id"])
            content_unit_ids.append(rid)
            row = dict(raw)
            row["id"] = rid
            row["chunk_id"] = "chunk_001"
            records[rid] = rebuild.anchor_record(row, book_id=book_id, rid=rid)

        self.assertEqual(len(early_core_added), 157)
        self.assertEqual(len(content_unit_ids), 7)
        self.assertEqual(len(records), 1404)

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
            canonical[target] = rebuild.anchor_record(merged, book_id=book_id, rid=target)

        suffix_collisions = {
            target: sources
            for target, sources in sorted(canonical_sources.items())
            if len(sources) > 1
        }

        diagnostic = {
            "v035_replay_count": len(records),
            "early_core_added": len(early_core_added),
            "content_unit_ids": content_unit_ids,
            "raw_delta_line_count": raw_line_count,
            "raw_delta_unique_count": len(raw_delta_ids),
            "duplicate_delta_id_count": len(duplicate_delta_ids),
            "duplicate_delta_ids": duplicate_delta_ids,
            "legacy_complete_ids": legacy_complete_ids,
            "legacy_complete_count": len(legacy_complete_ids),
            "count_after_suffix_normalization": len(canonical),
            "suffix_collisions": suffix_collisions,
            "remaining_gap_to_pre_tail_target_1396": len(canonical) - 1396,
        }
        print("SEARCH_V035_REPLAY_DIAGNOSTIC=" + json.dumps(diagnostic, ensure_ascii=False, sort_keys=True))

        self.assertEqual(len(legacy_complete_ids), 7)


if __name__ == "__main__":
    unittest.main()
