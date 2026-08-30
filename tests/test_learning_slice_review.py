from __future__ import annotations

import unittest

from runtime.learning_slice_runtime import LearningSliceRuntime
from runtime.section_learning_runtime import SectionLearningRuntime
from tests.test_learning_slice_runtime import FakeCourse, collect_source_refs


EXPECTED_REVIEW_IDS = [
    "def_1",
    "thm_1",
    "formula_1",
    "prop_1",
    "def_2",
    "lemma_1",
    "cor_1",
]


class LearningSliceReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.learning = SectionLearningRuntime.from_course(FakeCourse(), "s1")
        self.runtime = LearningSliceRuntime(self.learning)

    def _preset(self, preset_id: str) -> dict[str, object]:
        presets = self.runtime.review().payload["presets"]
        return next(row for row in presets if row["id"] == preset_id)

    def test_full_preset_is_all_review_candidates_in_source_order(self) -> None:
        refs = self._preset("full")["source_refs"]
        self.assertEqual([row["source_id"] for row in refs], EXPECTED_REVIEW_IDS)

    def test_one_minute_seeds_definition_theorem_family_formula_then_fills_to_three(self) -> None:
        refs = self._preset("one_minute")["source_refs"]
        self.assertEqual(
            [row["source_id"] for row in refs],
            ["def_1", "thm_1", "formula_1"],
        )

    def test_five_minute_uses_same_diversity_seed_then_fills_to_five(self) -> None:
        refs = self._preset("five_minute")["source_refs"]
        self.assertEqual(
            [row["source_id"] for row in refs],
            ["def_1", "thm_1", "formula_1", "prop_1", "def_2"],
        )

    def test_presets_never_duplicate_source_refs(self) -> None:
        for preset in self.runtime.review().payload["presets"]:
            refs = [(row["kind"], row["source_id"]) for row in preset["source_refs"]]
            with self.subTest(preset=preset["id"]):
                self.assertEqual(len(refs), len(set(refs)))

    def test_review_prompts_use_only_fixed_templates(self) -> None:
        prompts = self.runtime.review().payload["prompts"]
        self.assertEqual(
            [row["text"] for row in prompts],
            [
                "先回忆「定义一」的定义，再显示教材内容。",
                "先回忆「定理一」的条件和结论，再显示教材内容。",
                "先尝试写出「公式一」，再显示教材公式。",
                "先回忆「命题一」的条件和结论，再显示教材内容。",
                "先回忆「定义二」的定义，再显示教材内容。",
                "先回忆「引理一」的条件和结论，再显示教材内容。",
                "先回忆「推论一」的条件和结论，再显示教材内容。",
            ],
        )
        self.assertEqual(
            [row["source_ref"]["source_id"] for row in prompts],
            EXPECTED_REVIEW_IDS,
        )
        self.assertTrue(
            all(row["derivation"] == "deterministic_template" for row in prompts)
        )

    def test_empty_review_is_valid_and_all_presets_are_empty(self) -> None:
        course = FakeCourse()
        course._book._objects = [
            row for row in course._book._objects if row.type.strip().casefold() == "remark"
        ]
        runtime = LearningSliceRuntime(SectionLearningRuntime.from_course(course, "s1"))
        payload = runtime.review().payload
        self.assertEqual(
            [(row["id"], row["label"]) for row in payload["presets"]],
            [
                ("one_minute", "1 分钟"),
                ("five_minute", "5 分钟"),
                ("full", "完整复习"),
            ],
        )
        self.assertTrue(all(row["source_refs"] == [] for row in payload["presets"]))
        self.assertEqual(payload["prompts"], [])

    def test_review_projection_refs_are_closed_over_review_mode_candidates(self) -> None:
        projection = self.runtime.review()
        nested_refs = collect_source_refs(projection.payload)
        expected = {("object", source_id) for source_id in EXPECTED_REVIEW_IDS}
        self.assertEqual(set(projection.source_refs), nested_refs)
        self.assertEqual(nested_refs, expected)


if __name__ == "__main__":
    unittest.main()
