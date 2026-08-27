from __future__ import annotations

import unittest
from pathlib import Path

from runtime.book_runtime import (
    BookRuntime,
    BookRuntimeError,
    RuntimeAnchor,
    RuntimeBatch,
    RuntimeObject,
)


class RuntimeObjectMergeTests(unittest.TestCase):
    @staticmethod
    def _runtime_with(*objects: tuple[str, RuntimeObject]) -> BookRuntime:
        runtime = BookRuntime(Path("."))
        batches: dict[str, RuntimeBatch] = {}
        for batch_id, obj in objects:
            batch = batches.setdefault(
                batch_id,
                RuntimeBatch(
                    id=batch_id,
                    source_file=Path(f"{batch_id}_structure.json"),
                    translation_file=None,
                ),
            )
            batch.objects.append(obj)
        runtime.batches = list(batches.values())
        return runtime

    def test_same_stable_id_merges_when_canonical_identity_matches(self) -> None:
        first = RuntimeObject(
            id="thm_4_2",
            type="theorem",
            number="4.2",
            name_en="Holder regularity and roughness of Brownian paths",
            name_zh="Brownian 路径的 Hölder 正则性与粗糙性",
            anchor=RuntimeAnchor(pdf_page=270, printed_page=251),
            source_batch="chunk_a",
            raw={"continues_in": "chunk_b"},
        )
        second = RuntimeObject(
            id="thm_4_2",
            type="theorem",
            number="4.2",
            name_en="Holder regularity and roughness of Brownian paths",
            name_zh="Brownian 路径的 Hölder 正则性与粗糙性",
            anchor=RuntimeAnchor(pdf_page=271, printed_page=252),
            source_batch="chunk_b",
            raw={"continued_from": "chunk_a"},
        )
        runtime = self._runtime_with(("chunk_a", first), ("chunk_b", second))

        runtime._merge_objects()

        merged = runtime.objects["thm_4_2"]
        self.assertEqual(merged.id, "thm_4_2")
        self.assertEqual(merged.type, "theorem")
        self.assertEqual(merged.number, "4.2")
        self.assertEqual(merged.anchor.pdf_page, 270)

    def test_same_stable_id_rejects_identity_label_drift_even_across_continuation(self) -> None:
        first = RuntimeObject(
            id="ex_10",
            type="exercise",
            number="10",
            name_zh="后续练习（跨批次继续）",
            source_batch="chunk_a",
            raw={"continues_in": "chunk_b"},
        )
        second = RuntimeObject(
            id="ex_10",
            type="exercise",
            number="10",
            name_zh="Poisson 核卷积练习",
            source_batch="chunk_b",
            raw={"continued_from": "chunk_a"},
        )
        runtime = self._runtime_with(("chunk_a", first), ("chunk_b", second))

        with self.assertRaises(BookRuntimeError):
            runtime._merge_objects()

    def test_same_stable_id_still_rejects_true_identity_conflict(self) -> None:
        first = RuntimeObject(
            id="shared_id",
            type="theorem",
            number="1.1",
            name_en="First theorem",
            name_zh="第一个定理",
            source_batch="chunk_a",
            raw={},
        )
        second = RuntimeObject(
            id="shared_id",
            type="theorem",
            number="1.2",
            name_en="Different theorem",
            name_zh="另一个定理",
            source_batch="chunk_b",
            raw={},
        )
        runtime = self._runtime_with(("chunk_a", first), ("chunk_b", second))

        with self.assertRaises(BookRuntimeError):
            runtime._merge_objects()


if __name__ == "__main__":
    unittest.main()
