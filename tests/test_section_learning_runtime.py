from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
