from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import normalize_functional_analysis_figure_ids as normalizer


class FunctionalAnalysisFigureNormalizerTests(unittest.TestCase):
    def test_local_figure_numbers_are_scoped_only_when_reused_on_different_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "chunk_a_structure.json"
            second = root / "chunk_b_structure.json"
            third = root / "chunk_c_structure.json"
            first.write_text(
                json.dumps({"chunk_id": "chunk_a", "figures": [{"figure": "Figure 1", "pdf_page": 36}]}),
                encoding="utf-8",
            )
            second.write_text(
                json.dumps({"chunk_id": "chunk_b", "figures": [{"figure": "Figure 1", "pdf_page": 212}]}),
                encoding="utf-8",
            )
            third.write_text(
                json.dumps({"chunk_id": "chunk_c", "figures": [{"figure": "Figure 2", "pdf_page": 90}]}),
                encoding="utf-8",
            )

            report = normalizer.normalize_local_figure_ids(root, write=True)

            a = json.loads(first.read_text(encoding="utf-8"))["figures"][0]
            b = json.loads(second.read_text(encoding="utf-8"))["figures"][0]
            c = json.loads(third.read_text(encoding="utf-8"))["figures"][0]
            self.assertEqual(a["id"], "Figure 1@pdf:36")
            self.assertEqual(b["id"], "Figure 1@pdf:212")
            self.assertNotIn("id", c)
            self.assertEqual(report["conflicting_local_labels"], ["Figure 1"])
            self.assertEqual(report["changed_occurrences"], 2)
            self.assertTrue(report["all_cross_page_figure_ids_unique"])

    def test_same_local_figure_reference_on_same_page_is_not_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for chunk in ("a", "b"):
                (root / f"chunk_{chunk}_structure.json").write_text(
                    json.dumps(
                        {
                            "chunk_id": f"chunk_{chunk}",
                            "figure_anchors": [{"figure": "Figure 3", "pdf_page": 120}],
                        }
                    ),
                    encoding="utf-8",
                )

            report = normalizer.normalize_local_figure_ids(root, write=True)

            self.assertEqual(report["changed_occurrences"], 0)
            self.assertEqual(report["conflicting_local_labels"], [])


if __name__ == "__main__":
    unittest.main()
