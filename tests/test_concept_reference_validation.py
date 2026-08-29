from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from book_core.concepts import (
    ConceptAlignment,
    ConceptGraph,
    concept_graph_to_canonical_json,
    parse_concept_graph,
)
from runtime.concept_validation import (
    ConceptReferenceValidationError,
    ConceptReferenceValidator,
)
from runtime.course_runtime import CourseRuntime
from tests.runtime_fixture_factory import (
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


class ConceptReferenceValidationTests(unittest.TestCase):
    def _open_course(self) -> CourseRuntime:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        repo = make_repo(Path(self.tempdir.name))

        write_ready_book(
            repo / "books" / "fixture-book",
            book_id="fixture_book",
            objects=[
                {
                    "type": "theorem",
                    "id": "thm_fixture",
                    "number": "1.1",
                    "name_en": "Fixture theorem",
                    "name_zh": "测试定理",
                    "anchor": {
                        "pdf_page": 1,
                        "printed_page": 1,
                        "source_anchor": "fixture:p1:thm_fixture",
                    },
                }
            ],
        )
        write_ready_book(
            repo / "books" / "supp-book",
            book_id="supp_book",
            objects=[
                {
                    "type": "theorem",
                    "id": "supp_thm",
                    "name_en": "Supplement theorem",
                    "anchor": {"pdf_page": 1, "printed_page": 1},
                }
            ],
        )

        course_dir = repo / "courses" / "fixture-course"
        write_course(
            course_dir,
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[
                main_book_entry("fixture_book", "../../books/fixture-book"),
                {
                    "book_id": "supp_book",
                    "role": "supplementary",
                    "path": "../../books/supp-book",
                    "required": False,
                    "enabled": True,
                },
            ],
        )
        return CourseRuntime.open(course_dir)

    @staticmethod
    def _graph(
        *,
        book_version_id: str = "fixture_book@v1",
        section_id: str | None = "ch01_s01",
        source_kind: str | None = "object",
        source_id: str | None = "thm_fixture",
    ) -> ConceptGraph:
        return parse_concept_graph(
            {
                "schema_version": "concept_graph_v1",
                "concepts": [
                    {
                        "concept_id": "concept.fixture",
                        "title": "Fixture concept",
                        "aliases": [],
                        "prerequisite_concept_ids": [],
                        "revision": "r1",
                        "provenance": "synthetic-test",
                    }
                ],
                "alignments": [
                    {
                        "alignment_id": "align.fixture",
                        "concept_id": "concept.fixture",
                        "book_version_id": book_version_id,
                        "section_id": section_id,
                        "source_kind": source_kind,
                        "source_id": source_id,
                        "relation": "explains",
                        "confidence": 1.0,
                        "revision": "r1",
                        "provenance": "synthetic-test",
                    }
                ],
            }
        )

    def test_valid_main_book_section_and_object_source_pass(self) -> None:
        course = self._open_course()
        graph = self._graph()

        ConceptReferenceValidator(course).validate(graph)

    def test_unknown_book_version_is_rejected(self) -> None:
        course = self._open_course()
        graph = self._graph(book_version_id="missing_book@v1")

        with self.assertRaises(ConceptReferenceValidationError):
            ConceptReferenceValidator(course).validate(graph)

    def test_unknown_main_book_section_is_rejected(self) -> None:
        course = self._open_course()
        graph = self._graph(section_id="missing_section")

        with self.assertRaises(ConceptReferenceValidationError):
            ConceptReferenceValidator(course).validate(graph)

    def test_unknown_non_main_book_section_is_rejected(self) -> None:
        course = self._open_course()
        graph = self._graph(
            book_version_id="supp_book@v1",
            section_id="missing_section",
            source_kind=None,
            source_id=None,
        )

        with self.assertRaises(ConceptReferenceValidationError):
            ConceptReferenceValidator(course).validate(graph)

    def test_unknown_source_id_is_rejected(self) -> None:
        course = self._open_course()
        graph = self._graph(source_id="missing_source")

        with self.assertRaises(ConceptReferenceValidationError):
            ConceptReferenceValidator(course).validate(graph)

    def test_unsupported_source_kind_is_rejected(self) -> None:
        course = self._open_course()
        graph = self._graph(source_kind="bogus")

        with self.assertRaises(ConceptReferenceValidationError):
            ConceptReferenceValidator(course).validate(graph)

    def test_explicit_section_must_match_resolved_source_section(self) -> None:
        course = self._open_course()
        graph = self._graph(section_id="chapter_01")

        with self.assertRaises(ConceptReferenceValidationError):
            ConceptReferenceValidator(course).validate(graph)

    def test_source_bearing_non_main_alignment_is_rejected(self) -> None:
        course = self._open_course()
        graph = self._graph(
            book_version_id="supp_book@v1",
            section_id=None,
            source_kind="object",
            source_id="supp_thm",
        )

        with self.assertRaises(ConceptReferenceValidationError):
            ConceptReferenceValidator(course).validate(graph)

    def test_locationless_alignment_for_mounted_non_main_book_passes(self) -> None:
        course = self._open_course()
        graph = self._graph(
            book_version_id="supp_book@v1",
            section_id=None,
            source_kind=None,
            source_id=None,
        )

        ConceptReferenceValidator(course).validate(graph)

    def test_validator_rejects_unparsed_partial_source_pairs(self) -> None:
        course = self._open_course()
        for source_kind, source_id in (("object", None), (None, "thm_fixture")):
            with self.subTest(source_kind=source_kind, source_id=source_id):
                graph = ConceptGraph(
                    schema_version="concept_graph_v1",
                    concepts=(),
                    alignments=(
                        ConceptAlignment(
                            alignment_id="align.unparsed",
                            concept_id="concept.fixture",
                            book_version_id="fixture_book@v1",
                            relation="explains",
                            section_id=None,
                            source_kind=source_kind,
                            source_id=source_id,
                            revision="r1",
                            provenance="synthetic-test",
                        ),
                    ),
                )
                with self.assertRaises(ConceptReferenceValidationError):
                    ConceptReferenceValidator(course).validate(graph)

    def test_validation_does_not_mutate_graph(self) -> None:
        course = self._open_course()
        graph = self._graph()
        before = concept_graph_to_canonical_json(graph)

        ConceptReferenceValidator(course).validate(graph)

        self.assertEqual(concept_graph_to_canonical_json(graph), before)


if __name__ == "__main__":
    unittest.main()
