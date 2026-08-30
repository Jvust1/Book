from __future__ import annotations

import copy
import json
import unittest

from runtime.book_runtime import (
    RuntimeAnchor,
    RuntimeFigure,
    RuntimeObject,
    RuntimeSection,
)
from runtime.learning_slice_runtime import (
    LEARNING_SLICE_SCHEMA_VERSION,
    LearningSliceModeError,
    LearningSliceRuntime,
)
from runtime.section_learning_runtime import SectionLearningRuntime


class FakeBook:
    book_id = "fixture_book"

    def __init__(self) -> None:
        self.figures = {
            "fig_in": RuntimeFigure(
                id="fig_in",
                title_en="In-range figure",
                title_zh="节内图",
                anchor=RuntimeAnchor(pdf_page=2, printed_page=12, source_anchor="fig:in"),
                source_batch="b2",
            ),
            "fig_out": RuntimeFigure(
                id="fig_out",
                title_en="Out-of-range figure",
                title_zh="节外图",
                anchor=RuntimeAnchor(pdf_page=9, printed_page=19, source_anchor="fig:out"),
                source_batch="b9",
            ),
        }
        self._objects = [
            RuntimeObject(
                id="def_1",
                type="definition",
                section_id="s1",
                name_zh="定义一",
                formula="a = 1",
                anchor=RuntimeAnchor(pdf_page=1, printed_page=11),
                source_batch="b1",
                raw={"content_zh": "CANONICAL_BODY_SENTINEL"},
            ),
            RuntimeObject(
                id="thm_1",
                type=" Theorem ",
                section_id="s1",
                name_zh="定理一",
                formula="T(x) = x",
                anchor=RuntimeAnchor(pdf_page=1, printed_page=11),
                source_batch="b1",
            ),
            RuntimeObject(
                id="formula_1",
                type="formula",
                section_id="s1",
                number="(1)",
                name_zh="公式一",
                formula="f(x) = x",
                anchor=RuntimeAnchor(pdf_page=1, printed_page=11),
                source_batch="b1",
            ),
            RuntimeObject(
                id="prop_1",
                type="proposition",
                section_id="s1",
                name_zh="命题一",
                anchor=RuntimeAnchor(pdf_page=1, printed_page=11),
                source_batch="b1",
            ),
            RuntimeObject(
                id="example_1",
                type="example",
                section_id="s1",
                name_zh="例题一",
                anchor=RuntimeAnchor(pdf_page=2, printed_page=12),
                source_batch="b2",
            ),
            RuntimeObject(
                id="ex_1",
                type="exercise",
                section_id="s1",
                name_zh="练习一",
                anchor=RuntimeAnchor(pdf_page=2, printed_page=12),
                source_batch="b2",
            ),
            RuntimeObject(
                id="prob_1",
                type="PROBLEM",
                section_id="s1",
                name_zh="问题一",
                anchor=RuntimeAnchor(pdf_page=2, printed_page=12),
                source_batch="b2",
            ),
            RuntimeObject(
                id="remark_1",
                type="remark",
                section_id="s1",
                name_zh="备注一",
                anchor=RuntimeAnchor(pdf_page=2, printed_page=12),
                source_batch="b2",
            ),
            RuntimeObject(
                id="def_2",
                type="definition",
                section_id="s1",
                name_zh="定义二",
                anchor=RuntimeAnchor(pdf_page=2, printed_page=12),
                source_batch="b2",
            ),
            RuntimeObject(
                id="lemma_1",
                type="lemma",
                section_id="s1",
                name_zh="引理一",
                anchor=RuntimeAnchor(pdf_page=2, printed_page=12),
                source_batch="b2",
            ),
            RuntimeObject(
                id="cor_1",
                type="corollary",
                section_id="s1",
                name_zh="推论一",
                anchor=RuntimeAnchor(pdf_page=2, printed_page=12),
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
            raise AssertionError(section_id)
        return self._section


def collect_source_refs(value: object) -> set[tuple[str, str]]:
    refs: set[tuple[str, str]] = set()
    if isinstance(value, dict):
        if set(value) >= {"kind", "source_id"}:
            refs.add((str(value["kind"]), str(value["source_id"])))
        for nested in value.values():
            refs.update(collect_source_refs(nested))
    elif isinstance(value, list):
        for nested in value:
            refs.update(collect_source_refs(nested))
    return refs


class LearningSlicePreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.learning = SectionLearningRuntime.from_course(FakeCourse(), "s1")
        self.runtime = LearningSliceRuntime(self.learning)

    def test_preview_uses_learning_slice_v1_and_mode_discriminator(self) -> None:
        projection = self.runtime.preview()
        self.assertEqual(LEARNING_SLICE_SCHEMA_VERSION, "learning_slice_v1")
        self.assertEqual(projection.payload["schema_version"], "learning_slice_v1")
        self.assertEqual(projection.payload["mode"], "preview")

    def test_preview_overview_matches_source_counts_without_copying_body_text(self) -> None:
        source = self.learning.source()
        payload = self.runtime.preview().payload
        self.assertEqual(
            payload["overview"],
            {
                "object_count": len(source.objects),
                "figure_count": len(source.figures),
                "translation_available": True,
            },
        )
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("CANONICAL_BODY_SENTINEL", serialized)
        self.assertNotIn("content_zh", serialized)

    def test_preview_object_counts_preserve_first_seen_type_order(self) -> None:
        payload = self.runtime.preview().payload
        self.assertEqual(
            payload["object_counts"],
            [
                {"object_type": "definition", "count": 2},
                {"object_type": "theorem", "count": 1},
                {"object_type": "formula", "count": 1},
                {"object_type": "proposition", "count": 1},
                {"object_type": "example", "count": 1},
                {"object_type": "exercise", "count": 1},
                {"object_type": "problem", "count": 1},
                {"object_type": "remark", "count": 1},
                {"object_type": "lemma", "count": 1},
                {"object_type": "corollary", "count": 1},
            ],
        )

    def test_preview_objectives_are_deterministic_diversity_first_and_capped_at_eight(self) -> None:
        first = self.runtime.preview().payload["objectives"]
        second = self.runtime.preview().payload["objectives"]
        self.assertEqual(first, second)
        self.assertEqual(len(first), 8)
        self.assertEqual(
            [row["source_ref"]["source_id"] for row in first],
            ["def_1", "thm_1", "formula_1", "example_1", "ex_1", "prop_1", "prob_1", "def_2"],
        )

    def test_preview_objectives_use_only_fixed_templates_and_source_refs(self) -> None:
        objectives = self.runtime.preview().payload["objectives"]
        self.assertEqual(
            [(row["text"], row["derivation"]) for row in objectives[:5]],
            [
                ("理解并能复述：定义一", "deterministic_template"),
                ("理解并能说明结论与条件：定理一", "deterministic_template"),
                ("识别并能写出：公式一", "deterministic_template"),
                ("能够跟随教材例题：例题一", "deterministic_template"),
                ("尝试教材练习：练习一", "deterministic_template"),
            ],
        )
        self.assertTrue(
            all(set(row) == {"text", "derivation", "source_ref"} for row in objectives)
        )

    def test_preview_prerequisites_are_explicitly_unavailable(self) -> None:
        self.assertEqual(
            self.runtime.preview().payload["prerequisites"],
            {"status": "unavailable", "items": []},
        )

    def test_preview_core_definitions_preserve_source_order(self) -> None:
        refs = self.runtime.preview().payload["core_definitions"]
        self.assertEqual(
            [row["source_id"] for row in refs],
            ["def_1", "def_2"],
        )

    def test_preview_core_formulas_include_formula_type_and_formula_bearing_objects_once(self) -> None:
        refs = self.runtime.preview().payload["core_formulas"]
        self.assertEqual(
            [(row["kind"], row["source_id"]) for row in refs],
            [("object", "def_1"), ("object", "thm_1"), ("object", "formula_1")],
        )

    def test_preview_key_figures_use_only_in_range_section_figures(self) -> None:
        source = self.learning.source()
        self.assertEqual([row["id"] for row in source.figures], ["fig_in"])
        refs = self.runtime.preview().payload["key_figures"]
        self.assertEqual(refs, [{"kind": "figure", "source_id": "fig_in"}])

    def test_preview_quick_checks_are_deterministic_and_capped_at_six(self) -> None:
        checks = self.runtime.preview().payload["quick_checks"]
        self.assertEqual(len(checks), 6)
        self.assertEqual(
            [row["source_ref"]["source_id"] for row in checks],
            ["def_1", "thm_1", "formula_1", "prop_1", "def_2", "lemma_1"],
        )
        self.assertEqual(
            [row["text"] for row in checks[:3]],
            [
                "你能说出「定义一」的定义吗？",
                "你能说明「定理一」的条件和结论吗？",
                "你能不看教材写出「公式一」吗？",
            ],
        )

    def test_preview_projection_reports_every_nested_source_ref_for_closure_validation(self) -> None:
        projection = self.runtime.preview()
        nested_refs = collect_source_refs(projection.payload)
        self.assertEqual(set(projection.source_refs), nested_refs)

    def test_preview_does_not_mutate_section_learning_source(self) -> None:
        before = copy.deepcopy(self.learning.source())
        self.runtime.preview()
        self.assertEqual(self.learning.source(), before)

    def test_dispatch_rejects_unsupported_mode(self) -> None:
        with self.assertRaises(LearningSliceModeError):
            self.runtime.presentation("unknown")


if __name__ == "__main__":
    unittest.main()
