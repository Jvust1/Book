from __future__ import annotations

import json
import unittest

from runtime.learning_slice_runtime import LearningSliceRuntime
from runtime.section_learning_runtime import SectionLearningRuntime
from tests.test_learning_slice_runtime import FakeCourse


PRACTICE_TYPES = {"exercise", "problem"}


def make_practice_runtime(*enabled_types: str) -> tuple[SectionLearningRuntime, LearningSliceRuntime]:
    course = FakeCourse()
    enabled = {value.strip().casefold() for value in enabled_types}
    kept = []
    for obj in course._book._objects:
        normalized = str(obj.type or "").strip().casefold()
        if normalized in PRACTICE_TYPES:
            obj.raw["content_zh"] = "solution 解析 sentinel that must never affect presentation"
            if normalized not in enabled:
                continue
        kept.append(obj)
    course._book._objects = kept
    learning = SectionLearningRuntime.from_course(course, "s1")
    return learning, LearningSliceRuntime(learning)


class LearningSlicePracticeTests(unittest.TestCase):
    def test_all_filter_always_exists_and_preserves_candidate_order(self) -> None:
        _, runtime = make_practice_runtime("exercise", "problem")
        filters = runtime.practice().payload["filters"]
        self.assertEqual(
            filters[0],
            {
                "id": "all",
                "label": "全部",
                "source_refs": [
                    {"kind": "object", "source_id": "ex_1"},
                    {"kind": "object", "source_id": "prob_1"},
                ],
            },
        )

    def test_exercise_filter_exists_only_when_exercise_candidate_exists(self) -> None:
        _, with_exercise = make_practice_runtime("exercise", "problem")
        self.assertEqual(
            next(row for row in with_exercise.practice().payload["filters"] if row["id"] == "exercise"),
            {
                "id": "exercise",
                "label": "练习",
                "source_refs": [{"kind": "object", "source_id": "ex_1"}],
            },
        )

        _, without_exercise = make_practice_runtime("problem")
        self.assertNotIn(
            "exercise",
            [row["id"] for row in without_exercise.practice().payload["filters"]],
        )

    def test_problem_filter_exists_only_when_problem_candidate_exists(self) -> None:
        _, with_problem = make_practice_runtime("exercise", "problem")
        self.assertEqual(
            next(row for row in with_problem.practice().payload["filters"] if row["id"] == "problem"),
            {
                "id": "problem",
                "label": "习题",
                "source_refs": [{"kind": "object", "source_id": "prob_1"}],
            },
        )

        _, without_problem = make_practice_runtime("exercise")
        self.assertNotIn(
            "problem",
            [row["id"] for row in without_problem.practice().payload["filters"]],
        )

    def test_every_practice_item_has_explicit_unavailable_solution_status(self) -> None:
        _, runtime = make_practice_runtime("exercise", "problem")
        self.assertEqual(
            runtime.practice().payload["items"],
            [
                {
                    "source_ref": {"kind": "object", "source_id": "ex_1"},
                    "solution_status": "unavailable",
                },
                {
                    "source_ref": {"kind": "object", "source_id": "prob_1"},
                    "solution_status": "unavailable",
                },
            ],
        )

    def test_practice_does_not_parse_body_text_for_solution_detection(self) -> None:
        _, runtime = make_practice_runtime("exercise", "problem")
        payload = runtime.practice().payload
        self.assertTrue(all(row["solution_status"] == "unavailable" for row in payload["items"]))
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("solution", serialized)
        self.assertNotIn("解析", serialized)
        self.assertNotIn("sentinel", serialized)

    def test_empty_practice_is_valid_with_only_empty_all_filter(self) -> None:
        _, runtime = make_practice_runtime()
        payload = runtime.practice().payload
        self.assertEqual(
            payload["filters"],
            [{"id": "all", "label": "全部", "source_refs": []}],
        )
        self.assertEqual(payload["items"], [])

    def test_practice_projection_refs_are_closed_over_practice_candidates(self) -> None:
        learning, runtime = make_practice_runtime("exercise", "problem")
        projection = runtime.practice()
        allowed = {
            (str(row["kind"]), str(row["source_id"]))
            for row in learning.practice()["items"]
        }
        self.assertEqual(
            projection.source_refs,
            (("object", "ex_1"), ("object", "prob_1")),
        )
        self.assertTrue(set(projection.source_refs).issubset(allowed))


if __name__ == "__main__":
    unittest.main()
