from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import normalize_functional_analysis_runtime_identities as normalizer


class FunctionalAnalysisIdentityNormalizerTests(unittest.TestCase):
    def test_known_cross_batch_identity_is_canonicalized_without_changing_stable_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "chunk_006a_structure.json"
            second = root / "chunk_006b_structure.json"
            first.write_text(
                json.dumps(
                    {
                        "chunk_id": "chunk_006a",
                        "key_objects": [
                            {
                                "type": "exercise",
                                "id": "ex_ch2_7_10",
                                "number": "10",
                                "name_zh": "L^p(R) 上的后续练习（跨批次继续）",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            second.write_text(
                json.dumps(
                    {
                        "chunk_id": "chunk_006b",
                        "key_objects": [
                            {
                                "type": "exercise",
                                "id": "ex_ch2_7_10",
                                "number": "10",
                                "name_zh": "Poisson 核卷积在 L^p 中的压缩性与近似恒等性",
                                "continued_from": "chunk_006a",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = normalizer.normalize_known_identities(root, write=True)

            left = json.loads(first.read_text(encoding="utf-8"))["key_objects"][0]
            right = json.loads(second.read_text(encoding="utf-8"))["key_objects"][0]
            self.assertEqual(left["id"], "ex_ch2_7_10")
            self.assertEqual(right["id"], "ex_ch2_7_10")
            self.assertEqual(left["name_zh"], right["name_zh"])
            self.assertEqual(
                left["name_zh"],
                "Poisson 核卷积在 L^p 中的压缩性与近似恒等性",
            )
            self.assertEqual(report["changed_occurrences"], 1)
            self.assertTrue(report["all_known_identities_consistent"])


if __name__ == "__main__":
    unittest.main()
