from __future__ import annotations

import unittest
from pathlib import Path

from tools import check_runtime_readiness as readiness_checker


class ContinuationIntegrityTests(unittest.TestCase):
    def test_functional_analysis_continuation_targets_resolve(self) -> None:
        root = Path(__file__).resolve().parents[1] / "books" / "functional-analysis"
        if not root.exists():
            self.skipTest("repository fixture not present")

        files = readiness_checker.find_structure_files(root)
        _, _, bad_continuations = readiness_checker.collect_structure_state(files)

        self.assertEqual(bad_continuations, [])


if __name__ == "__main__":
    unittest.main()
