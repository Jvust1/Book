from __future__ import annotations

import json
import unittest

from runtime.learning_slice_runtime import LearningSliceRuntime
from runtime.section_learning_runtime import SectionLearningRuntime
from tests.test_learning_slice_runtime import FakeCourse


EXPECTED_GROUPS = [
    {
        "id": "definitions",
        "label": "定义 / 概念入口",
        "source_refs": [
            {"kind": "object", "source_id": "def_1"},
            {"kind": "object", "source_id": "def_2"},
        ],
    },
    {
        "id": "theorem_family",
        "label": "定理与命题",
        "source_refs": [
            {"kind": "object", "source_id": "thm_1"},
            {"kind": "object", "source_id": "prop_1"},
            {"kind": "object", "source_id": "lemma_1"},
            {"kind": "object", "source_id": "cor_1"},
        ],
    },
    {
        "id": "formulas",
        "label": "公式",
        "source_refs": [{"kind": "object", "source_id": "formula_1"}],
    },
    {
        "id": "examples",
        "label": "例题",
        "source_refs": [{"kind": "object", "source_id": "example_1"}],
    },
    {
        "id": "other_objects",
        "label": "其他教材对象",
        "source_refs": [
            {"kind": "object", "source_id": "ex_1"},
            {"kind": "object", "source_id": "prob_1"},
            {"kind": "object", "source_id": "remark_1"},
        ],
    },
    {
        "id": "figures",
        "label": "教材图示",
        "source_refs": [{"kind": "figure", "source_id": "fig_in"}],
    },
    {
        "id": "translations",
        "label": "中文学习层",
        "source_refs": [
            {"kind": "translation", "source_id": "b1"},
            {"kind": "translation", "source_id": "b2"},
        ],
    },
]


class LearningSliceLearnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.learning = SectionLearningRuntime.from_course(FakeCourse(), "s1")
        self.runtime = LearningSliceRuntime(self.learning)

    def test_learn_groups_are_mutually_exclusive_for_objects(self) -> None:
        groups = self.runtime.learn().payload["groups"]
        object_refs = [
            ref["source_id"]
            for group in groups
            for ref in group["source_refs"]
            if ref["kind"] == "object"
        ]
        self.assertEqual(len(object_refs), len(set(object_refs)))
        self.assertEqual(
            set(object_refs),
            {row["source_id"] for row in self.learning.learn()["items"] if row["kind"] == "object"},
        )

    def test_learn_groups_preserve_source_order_within_each_group(self) -> None:
        self.assertEqual(self.runtime.learn().payload["groups"], EXPECTED_GROUPS)

    def test_learn_omits_empty_groups(self) -> None:
        course = FakeCourse()
        course._book._objects = [course._book._objects[0]]
        course._book.figures = {}
        course._section.source_batches = []
        runtime = LearningSliceRuntime(SectionLearningRuntime.from_course(course, "s1"))
        self.assertEqual(
            runtime.learn().payload["groups"],
            [
                {
                    "id": "definitions",
                    "label": "定义 / 概念入口",
                    "source_refs": [{"kind": "object", "source_id": "def_1"}],
                }
            ],
        )

    def test_formula_bearing_theorem_remains_theorem_family_not_duplicate_formula_group(self) -> None:
        groups = {row["id"]: row["source_refs"] for row in self.runtime.learn().payload["groups"]}
        theorem_ref = {"kind": "object", "source_id": "thm_1"}
        formula_definition_ref = {"kind": "object", "source_id": "def_1"}
        self.assertIn(theorem_ref, groups["theorem_family"])
        self.assertNotIn(theorem_ref, groups["formulas"])
        self.assertIn(formula_definition_ref, groups["definitions"])
        self.assertNotIn(formula_definition_ref, groups["formulas"])

    def test_figures_and_translations_keep_existing_runtime_order(self) -> None:
        groups = {row["id"]: row["source_refs"] for row in self.runtime.learn().payload["groups"]}
        self.assertEqual(groups["figures"], [{"kind": "figure", "source_id": "fig_in"}])
        self.assertEqual(
            groups["translations"],
            [
                {"kind": "translation", "source_id": "b1"},
                {"kind": "translation", "source_id": "b2"},
            ],
        )

    def test_supplementary_and_lecture_extensions_are_explicitly_unavailable(self) -> None:
        self.assertEqual(
            self.runtime.learn().payload["extensions"],
            {
                "supplementary": {"status": "unavailable"},
                "lecture": {"status": "unavailable"},
            },
        )

    def test_learn_projection_contains_no_body_text(self) -> None:
        serialized = json.dumps(self.runtime.learn().payload, ensure_ascii=False)
        self.assertNotIn("CANONICAL_BODY_SENTINEL", serialized)
        self.assertNotIn("content_zh", serialized)
        self.assertNotIn("T(x) = x", serialized)
        self.assertNotIn("f(x) = x", serialized)

    def test_learn_projection_refs_are_closed_over_learn_candidates(self) -> None:
        projection = self.runtime.learn()
        allowed = {
            (str(row["kind"]), str(row["source_id"]))
            for row in self.learning.learn()["items"]
        }
        self.assertTrue(set(projection.source_refs).issubset(allowed))
        self.assertEqual(set(projection.source_refs), allowed)


if __name__ == "__main__":
    unittest.main()
