from __future__ import annotations

import json
import unittest
from collections import defaultdict
from pathlib import Path

from tools import check_runtime_readiness as readiness_checker


class ContinuationIntegrityTests(unittest.TestCase):
    def test_functional_analysis_continuation_targets_resolve(self) -> None:
        root = Path(__file__).resolve().parents[1] / "books" / "functional-analysis"
        if not root.exists():
            self.skipTest("repository fixture not present")

        files = readiness_checker.find_structure_files(root)
        _, repeated_ids, bad_continuations = readiness_checker.collect_structure_state(files)
        repeated_names = {item.split(":", 1)[0] for item in repeated_ids}

        details: dict[str, list[dict[str, object]]] = defaultdict(list)
        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            chunk_id = str(data.get("chunk_id") or path.stem.removesuffix("_structure"))
            for key in ("key_objects", "objects", "exercises", "problems"):
                values = data.get(key, [])
                if not isinstance(values, list):
                    continue
                for row in values:
                    if not isinstance(row, dict):
                        continue
                    object_id = row.get("id") or row.get("object_id") or row.get("exercise_id") or row.get("problem_id")
                    if str(object_id) not in repeated_names:
                        continue
                    anchor = row.get("anchor") if isinstance(row.get("anchor"), dict) else {}
                    details[str(object_id)].append(
                        {
                            "chunk_id": chunk_id,
                            "source_key": key,
                            "type": row.get("type") or ("exercise" if key == "exercises" else "problem" if key == "problems" else None),
                            "number": row.get("number"),
                            "name_en": row.get("name_en") or row.get("title_en"),
                            "name_zh": row.get("name_zh") or row.get("title_zh"),
                            "pdf_page": anchor.get("pdf_page") or row.get("pdf_page"),
                            "printed_page": anchor.get("printed_page") or row.get("printed_page"),
                            "continued_from": row.get("continued_from"),
                            "continues_in": row.get("continues_in"),
                            "completed_in": row.get("completed_in"),
                            "summary_zh": row.get("summary_zh"),
                        }
                    )

        print("STRUCTURE_REPEATED_DETAILS=" + json.dumps(details, ensure_ascii=False, sort_keys=True))
        self.assertEqual(bad_continuations, [])


if __name__ == "__main__":
    unittest.main()
