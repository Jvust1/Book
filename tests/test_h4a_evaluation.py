from __future__ import annotations

import copy
import json
import unittest

from evaluation.h4a_runtime import (
    H4A_QUERY_CATEGORIES,
    H4aDatasetError,
    canonical_query_set_json,
    parse_h4a_query_set,
    query_set_sha256,
)


VALID = {
    "schema_version": "h4a_query_set_v1",
    "dataset_id": "synthetic_h4a_v1",
    "course_id": "functional_analysis_course",
    "queries": [
        {
            "query_id": "q-positive",
            "category": "english_exact",
            "query": "Banach space",
            "section_id": None,
            "expected_sources": [
                {
                    "source_kind": "object",
                    "source_id": "definition.banach-space",
                }
            ],
            "notes": "synthetic positive query",
        },
        {
            "query_id": "q-negative",
            "category": "negative_zero_result",
            "query": "definitely absent synthetic phrase",
            "section_id": None,
            "expected_sources": [],
            "notes": None,
        },
    ],
}


class H4aQuerySetValidationTests(unittest.TestCase):
    def test_accepts_positive_and_negative_queries(self) -> None:
        query_set = parse_h4a_query_set(copy.deepcopy(VALID))

        self.assertEqual(query_set.schema_version, "h4a_query_set_v1")
        self.assertEqual(query_set.dataset_id, "synthetic_h4a_v1")
        self.assertEqual(query_set.course_id, "functional_analysis_course")
        self.assertEqual(len(query_set.queries), 2)
        self.assertEqual(
            H4A_QUERY_CATEGORIES,
            frozenset(
                {
                    "english_exact",
                    "english_partial",
                    "chinese_complete",
                    "chinese_partial",
                    "formula_symbol",
                    "section_scoped",
                    "negative_zero_result",
                }
            ),
        )

    def test_rejects_unknown_top_level_field(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["unexpected"] = True

        with self.assertRaises(H4aDatasetError):
            parse_h4a_query_set(raw)

    def test_rejects_duplicate_query_ids(self) -> None:
        raw = copy.deepcopy(VALID)
        duplicate = copy.deepcopy(raw["queries"][0])
        raw["queries"].append(duplicate)

        with self.assertRaises(H4aDatasetError):
            parse_h4a_query_set(raw)

    def test_rejects_blank_query(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["queries"][0]["query"] = " \t\n"

        with self.assertRaises(H4aDatasetError):
            parse_h4a_query_set(raw)

    def test_positive_query_requires_expected_source(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["queries"][0]["expected_sources"] = []

        with self.assertRaises(H4aDatasetError):
            parse_h4a_query_set(raw)

    def test_negative_query_requires_empty_expected_sources(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["queries"][1]["expected_sources"] = [
            {"source_kind": "object", "source_id": "unexpected.object"}
        ]

        with self.assertRaises(H4aDatasetError):
            parse_h4a_query_set(raw)

    def test_rejects_duplicate_expected_source_identity(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["queries"][0]["expected_sources"].append(
            copy.deepcopy(raw["queries"][0]["expected_sources"][0])
        )

        with self.assertRaises(H4aDatasetError):
            parse_h4a_query_set(raw)

    def test_rejects_invalid_source_kind(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["queries"][0]["expected_sources"][0]["source_kind"] = "page"

        with self.assertRaises(H4aDatasetError):
            parse_h4a_query_set(raw)

    def test_rejects_blank_section_id(self) -> None:
        raw = copy.deepcopy(VALID)
        raw["queries"][0]["section_id"] = "  "

        with self.assertRaises(H4aDatasetError):
            parse_h4a_query_set(raw)

    def test_canonical_json_hash_is_deterministic(self) -> None:
        forward = parse_h4a_query_set(copy.deepcopy(VALID))
        reordered = json.loads(
            json.dumps(VALID, ensure_ascii=False, sort_keys=True)
        )
        backward = parse_h4a_query_set(reordered)

        self.assertEqual(
            canonical_query_set_json(forward),
            canonical_query_set_json(backward),
        )
        self.assertEqual(query_set_sha256(forward), query_set_sha256(backward))


if __name__ == "__main__":
    unittest.main()
