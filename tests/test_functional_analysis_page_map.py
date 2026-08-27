from __future__ import annotations

import unittest
from pathlib import Path

from tools import recover_functional_analysis_page_map as page_map_recovery


class FunctionalAnalysisPageMapRecoveryTests(unittest.TestCase):
    def test_reconstructed_page_map_matches_audited_book_anchors(self) -> None:
        root = Path(__file__).resolve().parents[1] / "books" / "functional-analysis"
        if not root.exists():
            self.skipTest("repository fixture not present")

        rows, report = page_map_recovery.build_page_map(root)

        self.assertEqual(len(rows), 442)
        self.assertEqual([row["pdf_page_index"] for row in rows], list(range(1, 443)))

        by_pdf = {row["pdf_page_index"]: row for row in rows}
        self.assertEqual(by_pdf[1]["page_label"], "Cover")
        self.assertEqual(by_pdf[1]["printed_page"], "")
        self.assertEqual(by_pdf[2]["page_label"], "i")
        self.assertEqual(by_pdf[8]["page_label"], "vii")
        self.assertEqual(by_pdf[12]["page_label"], "xi")
        self.assertEqual(by_pdf[18]["page_label"], "xvii")
        self.assertEqual(by_pdf[19]["page_label"], "xviii")
        self.assertEqual(by_pdf[20]["page_label"], "1")
        self.assertEqual(by_pdf[20]["printed_page"], "1")
        self.assertEqual(by_pdf[442]["page_label"], "423")
        self.assertEqual(by_pdf[442]["printed_page"], "423")

        self.assertTrue(report["anchor_checks_pass"])
        self.assertEqual(report["row_count"], 442)
        self.assertEqual(report["frontmatter_roman_count"], 18)
        self.assertEqual(report["main_text_count"], 423)
        self.assertEqual(report["main_text_pdf_range"], [20, 442])
        self.assertEqual(report["main_text_printed_range"], [1, 423])


if __name__ == "__main__":
    unittest.main()
