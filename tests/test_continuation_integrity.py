from __future__ import annotations

import json
import unittest
from collections import defaultdict
from pathlib import Path

from tools import check_runtime_readiness as readiness_checker


class ContinuationIntegrityTests(unittest.TestCase):
    def test_functional_analysis_continuation_targets_and_repeated_identities_are_consistent(self) -> None:
        root = Path(__file__).resolve().parents[1] / "books" / "functional-analysis"
        if not root.exists():
            self.skipTest("repository fixture not present")

        files = readiness_checker.find_structure_files(root)
        _, repeated_ids, bad_continuations = readiness_checker.collect_structure_state(files)
        repeated_names = {item.split(":", 1)[0] for item in repeated_ids}

        identities: dict[str, list[tuple[object, object, object, object]]] = defaultdict(list)
        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            for key in ("key_objects", "objects", "exercises", "problems"):
                values = data.get(key, [])
                if not isinstance(values, list):
                    continue
                for row in values:
                    if not isinstance(row, dict):
                        continue
                    object_id = row.get("id") or row.get("object_id") or row.get("exercise_id") or row.get("problem_id")
                    object_id = str(object_id) if object_id else ""
                    if object_id not in repeated_names:
                        continue
                    identities[object_id].append(
                        (
                            row.get("type") or ("exercise" if key == "exercises" else "problem" if key == "problems" else None),
                            str(row.get("number")) if row.get("number") is not None else None,
                            row.get("name_en") or row.get("title_en"),
                            row.get("name_zh") or row.get("title_zh"),
                        )
                    )

        identity_conflicts = {
            object_id: rows
            for object_id, rows in identities.items()
            if len(set(rows)) > 1
        }

        self.assertEqual(bad_continuations, [])
        self.assertEqual(identity_conflicts, {})


if __name__ == "__main__":
    unittest.main()
