from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from book_core.concepts import (
    ALIGNMENT_RELATIONS,
    CONCEPT_GRAPH_SCHEMA_VERSION,
    ConceptGraphValidationError,
    concept_graph_to_canonical_json,
    find_prerequisite_cycles,
    parse_concept_graph,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "concept-graph" / "v1" / "concept-graph.schema.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "concept-graph" / "valid-minimal.json"

VALID = {
    "schema_version": "concept_graph_v1",
    "concepts": [
        {
            "concept_id": "concept.lp-space",
            "title": "L^p space",
            "aliases": ["Lp space"],
            "prerequisite_concept_ids": [],
            "revision": "r1",
            "provenance": "synthetic-test",
        },
        {
            "concept_id": "concept.holder",
            "title": "Hölder inequality",
            "aliases": [],
            "prerequisite_concept_ids": ["concept.lp-space"],
            "revision": "r1",
            "provenance": "synthetic-test",
        },
    ],
    "alignments": [
        {
            "alignment_id": "align.holder.definition",
            "concept_id": "concept.holder",
            "book_version_id": "fixture_book@v1",
            "section_id": "ch01_s01",
            "source_kind": "object",
            "source_id": "thm_holder",
            "relation": "explains",
            "confidence": 1.0,
            "revision": "r1",
            "provenance": "synthetic-test",
        }
    ],
}


class ConceptGraphContractTests(unittest.TestCase):
    def test_version_and_relation_constants_are_frozen(self) -> None:
        self.assertEqual(CONCEPT_GRAPH_SCHEMA_VERSION, "concept_graph_v1")
        self.assertEqual(
            ALIGNMENT_RELATIONS,
            frozenset(
                {
                    "defines",
                    "explains",
                    "proves",
                    "examples",
                    "exercises",
                    "extends",
                    "contrasts",
                }
            ),
        )

    def test_same_logical_data_serializes_identically_regardless_of_input_order(self) -> None:
        forward = copy.deepcopy(VALID)
        reversed_input = copy.deepcopy(VALID)
        reversed_input["concepts"] = list(reversed(reversed_input["concepts"]))

        first = concept_graph_to_canonical_json(parse_concept_graph(forward))
        second = concept_graph_to_canonical_json(parse_concept_graph(reversed_input))

        self.assertEqual(first, second)
        parsed = json.loads(first)
        self.assertEqual(
            [item["concept_id"] for item in parsed["concepts"]],
            ["concept.holder", "concept.lp-space"],
        )

    def test_duplicate_concept_id_is_rejected(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["concepts"].append(copy.deepcopy(raw["concepts"][0]))
        with self.assertRaises(ConceptGraphValidationError):
            parse_concept_graph(raw)

    def test_duplicate_alignment_id_is_rejected(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["alignments"].append(copy.deepcopy(raw["alignments"][0]))
        with self.assertRaises(ConceptGraphValidationError):
            parse_concept_graph(raw)

    def test_dangling_prerequisite_is_rejected(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["concepts"][1]["prerequisite_concept_ids"] = ["concept.missing"]
        with self.assertRaises(ConceptGraphValidationError):
            parse_concept_graph(raw)

    def test_self_loop_is_rejected(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["concepts"][1]["prerequisite_concept_ids"] = ["concept.holder"]
        with self.assertRaises(ConceptGraphValidationError):
            parse_concept_graph(raw)

    def test_duplicate_prerequisite_edge_is_rejected(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["concepts"][1]["prerequisite_concept_ids"] = [
            "concept.lp-space",
            "concept.lp-space",
        ]
        with self.assertRaises(ConceptGraphValidationError):
            parse_concept_graph(raw)

    def test_illegal_alignment_relation_is_rejected(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["alignments"][0]["relation"] = "related_to"
        with self.assertRaises(ConceptGraphValidationError):
            parse_concept_graph(raw)

    def test_source_kind_and_source_id_must_be_supplied_together_in_contract(self) -> None:
        for missing_field in ("source_kind", "source_id"):
            with self.subTest(missing_field=missing_field):
                raw = copy.deepcopy(VALID)
                raw["alignments"][0].pop(missing_field)
                with self.assertRaises(ConceptGraphValidationError):
                    parse_concept_graph(raw)

    def test_confidence_must_be_real_number_within_closed_unit_interval(self) -> None:
        for invalid in (-0.01, 1.01, True):
            with self.subTest(invalid=invalid):
                raw = copy.deepcopy(VALID)
                raw["alignments"][0]["confidence"] = invalid
                with self.assertRaises(ConceptGraphValidationError):
                    parse_concept_graph(raw)

    def test_blank_required_strings_are_rejected(self) -> None:
        mutations = (
            ("concept_id", " "),
            ("title", ""),
            ("revision", "\t"),
            ("provenance", "\n"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                raw = copy.deepcopy(VALID)
                raw["concepts"][0][field] = value
                with self.assertRaises(ConceptGraphValidationError):
                    parse_concept_graph(raw)

        alignment_mutations = (
            ("alignment_id", " "),
            ("concept_id", ""),
            ("book_version_id", "\t"),
            ("relation", "\n"),
            ("revision", " "),
            ("provenance", ""),
        )
        for field, value in alignment_mutations:
            with self.subTest(alignment_field=field):
                raw = copy.deepcopy(VALID)
                raw["alignments"][0][field] = value
                with self.assertRaises(ConceptGraphValidationError):
                    parse_concept_graph(raw)

    def test_cycles_are_reported_deterministically_but_not_rejected_in_h3a(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["concepts"][0]["prerequisite_concept_ids"] = ["concept.holder"]

        graph = parse_concept_graph(raw)
        cycles = find_prerequisite_cycles(graph)

        self.assertEqual(cycles, (("concept.holder", "concept.lp-space"),))

    def test_published_schema_mirrors_version_relations_and_strict_fields(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        alignment_schema = schema["$defs"]["alignment"]

        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            CONCEPT_GRAPH_SCHEMA_VERSION,
        )
        self.assertEqual(
            set(alignment_schema["properties"]["relation"]["enum"]),
            set(ALIGNMENT_RELATIONS),
        )
        self.assertEqual(
            alignment_schema.get("dependentRequired"),
            {
                "source_kind": ["source_id"],
                "source_id": ["source_kind"],
            },
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["$defs"]["concept"]["additionalProperties"])
        self.assertFalse(alignment_schema["additionalProperties"])

    def test_synthetic_fixture_round_trips_without_production_authority(self) -> None:
        raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        graph = parse_concept_graph(raw)

        self.assertEqual(
            concept_graph_to_canonical_json(graph),
            concept_graph_to_canonical_json(parse_concept_graph(VALID)),
        )
        self.assertTrue(
            all(concept.provenance == "synthetic-test" for concept in graph.concepts)
        )
        self.assertTrue(
            all(
                alignment.provenance == "synthetic-test"
                and alignment.book_version_id == "fixture_book@v1"
                for alignment in graph.alignments
            )
        )


if __name__ == "__main__":
    unittest.main()
