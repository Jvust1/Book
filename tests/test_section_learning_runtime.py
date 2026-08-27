from __future__ import annotations

import unittest
from pathlib import Path

from runtime.book_runtime import (
    BookRuntimeError,
    RuntimeAnchor,
    RuntimeFigure,
    RuntimeObject,
    RuntimeSection,
)
from runtime.section_learning_runtime import (
    SectionLearningRuntime,
    SectionLearningSourceError,
)


class FakeBook:
    book_id = "fixture_book"

    def __init__(self) -> None:
        self.figures = {
            "fig_2": RuntimeFigure(
                id="fig_2",
                anchor=RuntimeAnchor(pdf_page=2, source_anchor="fig-a2"),
                source_batch="b2",
            ),
            "fig_out": RuntimeFigure(
                id="fig_out",
                anchor=RuntimeAnchor(pdf_page=9),
                source_batch="b9",
            ),
            "fig_1": RuntimeFigure(
                id="fig_1",
                anchor=RuntimeAnchor(pdf_page=1, source_anchor="fig-a1"),
                source_batch="b1",
            ),
        }
        self._objects = [
            RuntimeObject(
                id="def_1",
                type="definition",
                section_id="s1",
                name_en="Definition",
                anchor=RuntimeAnchor(
                    pdf_page=1,
                    printed_page=11,
                    source_anchor="obj-a1",
                ),
                source_batch="b1",
            ),
            RuntimeObject(
                id="thm_1",
                type=" Theorem ",
                section_id="s1",
                name_en="Theorem",
                anchor=RuntimeAnchor(pdf_page=1, printed_page=11),
                source_batch="b1",
            ),
            RuntimeObject(
                id="ex_1",
                type="exercise",
                section_id="s1",
                name_en="Exercise",
                anchor=RuntimeAnchor(pdf_page=2),
                source_batch="b2",
            ),
            RuntimeObject(
                id="prob_1",
                type="PROBLEM",
                section_id="s1",
                name_en="Problem",
                anchor=RuntimeAnchor(pdf_page=2),
                source_batch="b2",
            ),
            RuntimeObject(
                id="remark_1",
                type="remark",
                section_id="s1",
                name_en="Remark",
                anchor=RuntimeAnchor(pdf_page=2),
                source_batch="b2",
            ),
        ]

    def objects_for_section(self, section_id: str):
        if section_id != "s1":
            raise AssertionError(section_id)
        return list(self._objects)

    def page_map_row(self, pdf_page: int):
        return {"pdf_page": str(pdf_page), "printed_page": str(pdf_page + 10)}

    def translation_text(self, batch_id: str):
        return "translated" if batch_id == "b1" else None


class FakeCourse:
    course_id = "fixture_course"

    def __init__(self) -> None:
        self._book = FakeBook()
        self._section = RuntimeSection(
            id="s1",
            number="1.1",
            title_en="Section One",
            title_zh="第一节",
            chapter_id="chapter_01",
            pdf_page_start=1,
            pdf_page_end=2,
            printed_page_start=11,
            printed_page_end=12,
            source_batches=["b1", "b2", "b1"],
        )

    def main_book(self):
        return self._book

    def section(self, section_id: str):
        if section_id != "s1":
            raise BookRuntimeError(f"Unknown section: {section_id}")
        return self._section


class SectionLearningSourceTests(unittest.TestCase):
    def test_known_section_builds_source_with_canonical_identity(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual(
            (source.course_id, source.book_id, source.chapter_id, source.section_id),
            ("fixture_course", "fixture_book", "chapter_01", "s1"),
        )

    def test_unknown_section_fails_explicitly(self) -> None:
        with self.assertRaises(SectionLearningSourceError):
            SectionLearningRuntime.from_course(FakeCourse(), "missing")

    def test_source_objects_preserve_book_runtime_order(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual(
            [row["id"] for row in source.objects],
            ["def_1", "thm_1", "ex_1", "prob_1", "remark_1"],
        )

    def test_figures_include_only_in_range_and_sort_by_page_then_id(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual([row["id"] for row in source.figures], ["fig_1", "fig_2"])

    def test_page_map_boundaries_are_preserved(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual(source.page_map_start["printed_page"], "11")
        self.assertEqual(source.page_map_end["printed_page"], "12")

    def test_missing_optional_anchor_is_not_fabricated(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        theorem = next(row for row in source.objects if row["id"] == "thm_1")
        self.assertIsNone(theorem["source_anchor"])

    def test_translation_availability_is_stable_deduplicated_and_contains_no_sliced_text(self) -> None:
        source = SectionLearningRuntime.from_course(FakeCourse(), "s1").source()
        self.assertEqual(
            source.translation_sources,
            [
                {"batch_id": "b1", "available": True},
                {"batch_id": "b2", "available": False},
            ],
        )
        self.assertTrue(
            all(set(row) == {"batch_id", "available"} for row in source.translation_sources)
        )


class SectionLearningModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.learning = SectionLearningRuntime.from_course(FakeCourse(), "s1")

    def test_preview_preserves_identity_and_compact_source_metadata(self) -> None:
        payload = self.learning.preview()
        self.assertEqual(payload["mode"], "preview")
        self.assertEqual(
            (
                payload["course_id"],
                payload["book_id"],
                payload["chapter_id"],
                payload["section_id"],
            ),
            ("fixture_course", "fixture_book", "chapter_01", "s1"),
        )
        object_item = next(
            row
            for row in payload["items"]
            if row["kind"] == "object" and row["source_id"] == "def_1"
        )
        translation_item = next(
            row
            for row in payload["items"]
            if row["kind"] == "translation" and row["source_id"] == "b1"
        )
        self.assertEqual(object_item["object_type"], "definition")
        self.assertIs(translation_item["available"], True)

    def test_learn_references_all_source_objects_figures_and_translations_in_order(self) -> None:
        source = self.learning.source()
        payload = self.learning.learn()
        expected = (
            [("object", row["id"]) for row in source.objects]
            + [("figure", row["id"]) for row in source.figures]
            + [("translation", row["batch_id"]) for row in source.translation_sources]
        )
        self.assertEqual(
            [(row["kind"], row["source_id"]) for row in payload["items"]],
            expected,
        )

    def test_review_uses_exact_normalized_policy_and_preserves_source_type(self) -> None:
        payload = self.learning.review()
        source = self.learning.source()
        by_id = {row["id"]: row for row in source.objects}
        self.assertEqual(
            [row["source_id"] for row in payload["items"]],
            ["def_1", "thm_1"],
        )
        self.assertEqual(by_id["thm_1"]["type"], " Theorem ")

    def test_practice_uses_only_exact_exercise_problem_policy(self) -> None:
        payload = self.learning.practice()
        self.assertEqual(
            [row["source_id"] for row in payload["items"]],
            ["ex_1", "prob_1"],
        )

    def test_empty_review_and_practice_subsets_are_valid(self) -> None:
        course = FakeCourse()
        course._book._objects = [
            RuntimeObject(id="remark_only", type="remark", section_id="s1")
        ]
        learning = SectionLearningRuntime.from_course(course, "s1")
        self.assertEqual(learning.review()["items"], [])
        self.assertEqual(learning.practice()["items"], [])

    def test_every_mode_item_maps_to_source_by_kind_and_source_id(self) -> None:
        source = self.learning.source()
        source_keys = (
            {("object", row["id"]) for row in source.objects}
            | {("figure", row["id"]) for row in source.figures}
            | {
                ("translation", row["batch_id"])
                for row in source.translation_sources
            }
        )
        for payload in (
            self.learning.preview(),
            self.learning.learn(),
            self.learning.review(),
            self.learning.practice(),
        ):
            for item in payload["items"]:
                self.assertIn((item["kind"], item["source_id"]), source_keys)
            self.assertEqual(
                payload["source_refs"],
                [
                    {"kind": item["kind"], "source_id": item["source_id"]}
                    for item in payload["items"]
                ],
            )

    def test_modes_have_no_ordering_lock(self) -> None:
        fresh = SectionLearningRuntime.from_course(FakeCourse(), "s1")
        self.assertEqual(
            [
                fresh.practice()["mode"],
                fresh.preview()["mode"],
                fresh.review()["mode"],
                fresh.learn()["mode"],
            ],
            ["practice", "preview", "review", "learn"],
        )


class RealSectionLearningFixtureTests(unittest.TestCase):
    def test_real_ch01_s01_builds_all_modes(self) -> None:
        from runtime import LibraryRuntime

        repo = Path(__file__).resolve().parents[1]
        if not (repo / "books" / "functional-analysis").exists():
            self.skipTest("repository Functional Analysis fixture not present")
        course = LibraryRuntime.open(repo / "library").course(
            "functional_analysis_course"
        )
        learning = SectionLearningRuntime.from_course(course, "ch01_s01")
        source = learning.source()
        self.assertEqual(source.course_id, "functional_analysis_course")
        self.assertEqual(source.book_id, "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(source.section_id, "ch01_s01")
        for payload in (
            learning.preview(),
            learning.learn(),
            learning.review(),
            learning.practice(),
        ):
            self.assertEqual(payload["course_id"], source.course_id)
            self.assertEqual(payload["book_id"], source.book_id)
            self.assertEqual(payload["chapter_id"], source.chapter_id)
            self.assertEqual(payload["section_id"], source.section_id)

    def test_runtime_package_exports_section_learning_runtime(self) -> None:
        from runtime import SectionLearningRuntime as ExportedSectionLearningRuntime

        self.assertIs(ExportedSectionLearningRuntime, SectionLearningRuntime)


if __name__ == "__main__":
    unittest.main()
