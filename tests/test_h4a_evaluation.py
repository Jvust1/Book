from __future__ import annotations

from collections import Counter
import copy
import json
from pathlib import Path
import unittest

import evaluation.h4a_runtime as h4a_runtime
from evaluation.h4a_runtime import (
    H4A_QUERY_CATEGORIES,
    H4aDatasetError,
    canonical_query_set_json,
    parse_h4a_query_set,
    query_set_sha256,
)
from runtime.course_runtime import CourseRuntime
from runtime.source_resolver import SourceResolver


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_QUERY_SET_PATH = (
    ROOT / "evaluation" / "h4a" / "functional_analysis_queries.v1.json"
)
GOLDEN_COURSE_PATH = ROOT / "courses" / "functional-analysis"
CATEGORY_MINIMUMS = {
    "english_exact": 4,
    "english_partial": 4,
    "chinese_complete": 4,
    "chinese_partial": 4,
    "formula_symbol": 4,
    "section_scoped": 3,
    "negative_zero_result": 2,
}

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


class H4aGoldenDatasetTests(unittest.TestCase):
    def test_functional_analysis_v1_dataset_has_required_category_coverage(self) -> None:
        raw = json.loads(GOLDEN_QUERY_SET_PATH.read_text(encoding="utf-8"))
        query_set = parse_h4a_query_set(raw)

        self.assertEqual(query_set.course_id, "functional_analysis_course")
        self.assertEqual(query_set.dataset_id, "functional_analysis_h4a_v1")
        self.assertGreaterEqual(len(query_set.queries), 24)
        self.assertLessEqual(len(query_set.queries), 30)

        counts = Counter(query.category for query in query_set.queries)
        for category, minimum in CATEGORY_MINIMUMS.items():
            with self.subTest(category=category):
                self.assertGreaterEqual(counts[category], minimum)

        course = CourseRuntime.open(GOLDEN_COURSE_PATH)
        self.assertEqual(course.course_id, "functional_analysis_course")
        self.assertEqual(
            course.main_book().book_id,
            "stein_shakarchi_functional_analysis_2011",
        )
        resolver = SourceResolver(course)

        for query in query_set.queries:
            if query.category == "negative_zero_result":
                continue
            if query.category == "section_scoped":
                self.assertIsNotNone(query.section_id)

            for expected in query.expected_sources:
                with self.subTest(
                    query_id=query.query_id,
                    source_kind=expected.source_kind,
                    source_id=expected.source_id,
                ):
                    resolved = resolver.resolve(
                        expected.source_kind,
                        expected.source_id,
                    )
                    self.assertEqual(resolved.source_id, expected.source_id)
                    self.assertEqual(resolved.kind, expected.source_kind)
                    if query.category == "section_scoped":
                        self.assertEqual(resolved.section_id, query.section_id)


class H4aMetricTests(unittest.TestCase):
    def _api(self, name: str):
        value = getattr(h4a_runtime, name, None)
        self.assertIsNotNone(value, f"evaluation.h4a_runtime.{name} must exist")
        return value

    def _source(self, source_id: str, rank: int):
        ranked_source = self._api("RankedSource")
        return ranked_source(source_kind="object", source_id=source_id, rank=rank)

    def _positive_query(self, *source_ids: str):
        expected_source = h4a_runtime.ExpectedSource
        return h4a_runtime.H4aQuery(
            query_id="metric-positive",
            category="english_exact",
            query="synthetic metric query",
            section_id=None,
            expected_sources=tuple(
                expected_source(source_kind="object", source_id=source_id)
                for source_id in source_ids
            ),
            notes=None,
        )

    def _negative_query(self):
        return h4a_runtime.H4aQuery(
            query_id="metric-negative",
            category="negative_zero_result",
            query="synthetic absent phrase",
            section_id=None,
            expected_sources=(),
            notes=None,
        )

    def test_positive_hit_at_1_5_10_and_recall_at_10(self) -> None:
        compute = self._api("compute_query_metrics")
        metrics = compute(
            self._positive_query("a", "b", "c"),
            (self._source("a", 1), self._source("b", 5), self._source("c", 11)),
        )

        self.assertTrue(metrics.hit_at_1)
        self.assertTrue(metrics.hit_at_5)
        self.assertTrue(metrics.hit_at_10)
        self.assertAlmostEqual(metrics.recall_at_10, 2 / 3)
        self.assertIsNone(metrics.negative_clean_at_10)
        self.assertIsNone(metrics.unexpected_hit_count_at_10)

    def test_reciprocal_rank_and_mrr(self) -> None:
        compute = self._api("compute_query_metrics")
        aggregate = self._api("aggregate_query_metrics")
        first = compute(
            self._positive_query("a"),
            (self._source("a", 1),),
        )
        fourth = compute(
            self._positive_query("b"),
            (self._source("other", 1), self._source("b", 4)),
        )
        summary = aggregate((first, fourth))

        self.assertEqual(first.reciprocal_rank, 1.0)
        self.assertEqual(fourth.reciprocal_rank, 0.25)
        self.assertEqual(summary["positive_query_count"], 2)
        self.assertAlmostEqual(summary["mrr"], 0.625)

    def test_multiple_expected_sources_recall(self) -> None:
        compute = self._api("compute_query_metrics")
        metrics = compute(
            self._positive_query("a", "b", "c"),
            (self._source("c", 2), self._source("a", 9)),
        )

        self.assertAlmostEqual(metrics.recall_at_10, 2 / 3)
        self.assertEqual(metrics.reciprocal_rank, 0.5)

    def test_fts_only_and_exact_only_recovery(self) -> None:
        compare = self._api("comparative_recovery_at_10")
        recovery = compare(
            self._positive_query("a", "b", "c"),
            exact_ranked=(self._source("a", 1), self._source("b", 3)),
            candidate_ranked=(self._source("b", 1), self._source("c", 2)),
        )

        self.assertEqual(
            [(item.source_kind, item.source_id) for item in recovery.fts_only_recovery_at_10],
            [("object", "c")],
        )
        self.assertEqual(
            [(item.source_kind, item.source_id) for item in recovery.exact_only_recovery_at_10],
            [("object", "a")],
        )

    def test_negative_queries_are_excluded_from_recall_and_mrr(self) -> None:
        compute = self._api("compute_query_metrics")
        aggregate = self._api("aggregate_query_metrics")
        positive = compute(
            self._positive_query("a"),
            (self._source("a", 1),),
        )
        negative = compute(
            self._negative_query(),
            (self._source("unexpected", 1),),
        )
        summary = aggregate((positive, negative))

        self.assertIsNone(negative.hit_at_1)
        self.assertIsNone(negative.hit_at_5)
        self.assertIsNone(negative.hit_at_10)
        self.assertIsNone(negative.recall_at_10)
        self.assertIsNone(negative.reciprocal_rank)
        self.assertEqual(summary["positive_query_count"], 1)
        self.assertEqual(summary["negative_query_count"], 1)
        self.assertEqual(summary["mrr"], 1.0)
        self.assertEqual(summary["recall_at_10"], 1.0)

    def test_negative_clean_and_unexpected_hit_count(self) -> None:
        compute = self._api("compute_query_metrics")
        clean = compute(self._negative_query(), ())
        dirty = compute(
            self._negative_query(),
            (self._source("u1", 1), self._source("u2", 10), self._source("u3", 11)),
        )

        self.assertTrue(clean.negative_clean_at_10)
        self.assertEqual(clean.unexpected_hit_count_at_10, 0)
        self.assertFalse(dirty.negative_clean_at_10)
        self.assertEqual(dirty.unexpected_hit_count_at_10, 2)

    def test_non_finite_metric_input_fails_closed(self) -> None:
        query_metrics = self._api("QueryMetrics")
        aggregate = self._api("aggregate_query_metrics")
        invalid = query_metrics(
            hit_at_1=True,
            hit_at_5=True,
            hit_at_10=True,
            recall_at_10=float("nan"),
            reciprocal_rank=1.0,
            negative_clean_at_10=None,
            unexpected_hit_count_at_10=None,
        )

        with self.assertRaises(h4a_runtime.H4aEvaluationError):
            aggregate((invalid,))

    def test_aggregate_metrics_are_deterministic(self) -> None:
        compute = self._api("compute_query_metrics")
        aggregate = self._api("aggregate_query_metrics")
        positive = compute(
            self._positive_query("a"),
            (self._source("a", 2),),
        )
        negative = compute(self._negative_query(), ())

        forward = aggregate((positive, negative))
        reverse = aggregate((negative, positive))
        self.assertEqual(forward, reverse)
        self.assertEqual(
            json.dumps(forward, sort_keys=True, separators=(",", ":")),
            json.dumps(reverse, sort_keys=True, separators=(",", ":")),
        )


class H4aReportTests(unittest.TestCase):
    def _api(self, name: str):
        value = getattr(h4a_runtime, name, None)
        self.assertIsNotNone(value, f"evaluation.h4a_runtime.{name} must exist")
        return value

    def _report(self):
        build = self._api("build_h4a_report")
        query_set = parse_h4a_query_set(copy.deepcopy(VALID))
        return build(
            query_set=query_set,
            course_identity={
                "course_id": "functional_analysis_course",
                "book_id": "stein_shakarchi_functional_analysis_2011",
                "book_version_id": "functional-analysis-2011-structured-v0.36",
            },
            profile_definitions=(
                {"profile_id": "exact_v1", "kind": "exact"},
                {
                    "profile_id": "fts_unicode61_bm25_v1",
                    "kind": "shadow_fts5",
                    "tokenizer": "unicode61",
                },
                {
                    "profile_id": "fts_trigram_bm25_v1",
                    "kind": "shadow_fts5",
                    "tokenizer": "trigram",
                },
            ),
            sqlite_version="3.synthetic",
            fts5_available=True,
            query_results=(),
            aggregate_metrics={},
            gates={
                "provenance": "PASS",
                "section_scope": "PASS",
                "determinism": "PASS",
            },
            evidence={
                "public_contract_regression": "pending-task6",
                "canonical_tree_integrity": "pending-task6",
            },
        )

    def test_report_has_closed_top_level_shape(self) -> None:
        report = self._report()
        self.assertEqual(
            set(report),
            {
                "schema_version",
                "stage",
                "course",
                "dataset",
                "profiles",
                "environment",
                "queries",
                "aggregates",
                "gates",
                "evidence",
            },
        )
        self.assertEqual(report["schema_version"], "h4a_report_v1")
        self.assertEqual(report["stage"], "H4a")

    def test_report_records_sqlite_version_and_profile_ids(self) -> None:
        report = self._report()
        self.assertEqual(
            report["environment"],
            {"sqlite_version": "3.synthetic", "fts5_available": True},
        )
        self.assertEqual(
            [profile["profile_id"] for profile in report["profiles"]],
            ["exact_v1", "fts_unicode61_bm25_v1", "fts_trigram_bm25_v1"],
        )

    def test_report_omits_wall_clock_and_absolute_paths(self) -> None:
        canonical = self._api("canonical_h4a_report_json")(self._report())
        lowered = canonical.lower()
        self.assertNotIn("timestamp", lowered)
        self.assertNotIn("wall_clock", lowered)
        self.assertNotIn("/tmp/", canonical)
        self.assertNotIn("c:\\\\", lowered)

    def test_report_has_no_activation_flag(self) -> None:
        canonical = self._api("canonical_h4a_report_json")(self._report())
        self.assertNotIn("activate_fts", canonical.lower())
        self.assertNotIn("activation", canonical.lower())

    def test_report_canonical_json_is_repeatable(self) -> None:
        canonical = self._api("canonical_h4a_report_json")
        first = canonical(self._report())
        second = canonical(self._report())
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), json.loads(second))


if __name__ == "__main__":
    unittest.main()
