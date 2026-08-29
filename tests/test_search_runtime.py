from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime import (
    CourseRuntime,
    SearchIndexUnavailableError,
    SearchQueryError,
    SearchRuntime,
)
from tests.runtime_fixture_factory import main_book_entry, make_repo, write_course, write_ready_book


REPO_ROOT = Path(__file__).resolve().parents[1]


class SearchRuntimeFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.repo = make_repo(Path(self.tempdir.name))
        self.book_dir = self.repo / "books" / "fixture-book"
        self.course_dir = self.repo / "courses" / "fixture-course"

    def _open_course(
        self,
        *,
        search_records: list[dict[str, object]] | None = None,
    ) -> CourseRuntime:
        write_ready_book(
            self.book_dir,
            book_id="fixture_book",
            objects=[
                {
                    "type": "definition",
                    "id": "def_banach",
                    "name_zh": "巴拿赫空间",
                    "name_en": "Banach space",
                    "number": "1.1",
                    "formula": "||x|| < infinity",
                    "anchor": {
                        "pdf_page": 1,
                        "printed_page": 1,
                        "source_anchor": "fixture_book:pdf:1:def_banach",
                    },
                },
                {
                    "type": "definition",
                    "id": "def_banach_algebra",
                    "name_zh": "巴拿赫代数",
                    "name_en": "Banach algebra",
                    "number": "1.2",
                    "anchor": {"pdf_page": 2, "printed_page": 2},
                },
            ],
            figures=[
                {
                    "id": "fig_fixture",
                    "title_zh": "测试图",
                    "title_en": "Fixture figure",
                    "anchor": {"pdf_page": 2, "printed_page": 2},
                }
            ],
            sections=[
                {
                    "id": "sec_a",
                    "number": "1",
                    "title_en": "Section A",
                    "title_zh": "A 节",
                    "pdf_pages": [1, 1],
                    "printed_pages": [1, 1],
                },
                {
                    "id": "sec_b",
                    "number": "2",
                    "title_en": "Section B",
                    "title_zh": "B 节",
                    "pdf_pages": [2, 2],
                    "printed_pages": [2, 2],
                },
            ],
            search_records=search_records
            if search_records is not None
            else [
                {
                    "id": "def_banach",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "name_zh": "巴拿赫空间",
                    "name_en": "Banach space",
                    "number": "1.1",
                    "formula": "||x|| < infinity",
                    "pdf_page": 1,
                    "printed_page": 1,
                    "source_anchor": "fixture_book:pdf:1:def_banach",
                },
                {
                    "id": "def_banach_algebra",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "name_zh": "巴拿赫代数",
                    "name_en": "Banach algebra",
                    "number": "1.2",
                    "pdf_page": 2,
                    "printed_page": 2,
                },
                {
                    "id": "fig_fixture",
                    "book_id": "fixture_book",
                    "type": "figure",
                    "title_zh": "测试图",
                    "title_en": "Fixture figure",
                    "pdf_page": 2,
                    "printed_page": 2,
                },
                {
                    "id": "section_ch01_s01",
                    "book_id": "fixture_book",
                    "type": "section",
                    "title_zh": "不可直接跳转的小节索引",
                },
            ],
        )
        write_course(
            self.course_dir,
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
        )
        return CourseRuntime.open(self.course_dir)

    def test_loads_index_and_only_exposes_resolvable_candidates(self) -> None:
        course = self._open_course()
        runtime = SearchRuntime.from_course(course)

        self.assertEqual(runtime.index_record_count, 4)
        self.assertEqual(runtime.searchable_candidate_count, 3)

        hits = runtime.search("巴拿赫空间")
        self.assertEqual(hits[0].source_kind, "object")
        self.assertEqual(hits[0].source_id, "def_banach")
        self.assertEqual(hits[0].object_type, "definition")
        self.assertEqual(hits[0].book_id, "fixture_book")
        self.assertEqual(hits[0].course_id, "fixture_course")
        self.assertEqual(hits[0].source_anchor, "fixture_book:pdf:1:def_banach")

    def test_scoring_is_exact_and_deterministic(self) -> None:
        runtime = SearchRuntime.from_course(self._open_course())

        exact_title = runtime.search("巴拿赫空间")
        self.assertEqual(exact_title[0].score, 1000)

        exact_id = runtime.search("def_banach")
        self.assertEqual(exact_id[0].score, 900)

        prefix = runtime.search("bAnAcH")
        self.assertEqual([hit.source_id for hit in prefix[:2]], ["def_banach", "def_banach_algebra"])
        self.assertEqual([hit.score for hit in prefix[:2]], [800, 800])
        self.assertEqual([hit.rank for hit in prefix[:2]], [1, 2])

        title_substring = runtime.search("space")
        self.assertEqual(title_substring[0].score, 700)

        formula = runtime.search("||x|| < infinity")
        self.assertEqual(formula[0].score, 600)

        formula_substring = runtime.search("infinity")
        self.assertEqual(formula_substring[0].score, 500)

        by_type = runtime.search("definition")
        self.assertEqual(by_type[0].score, 300)

    def test_initial_concept_match_uses_fixed_weight(self) -> None:
        course = self._open_course(
            search_records=[
                {
                    "id": "def_banach",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "name_zh": "巴拿赫空间",
                    "initial_concepts_zh": ["完备空间", "范数"],
                }
            ]
        )
        runtime = SearchRuntime.from_course(course)
        self.assertEqual(runtime.search("完备空间")[0].score, 400)
        self.assertEqual(runtime.search("完备")[0].score, 350)

    def test_limit_is_applied_before_continuous_rank_assignment(self) -> None:
        runtime = SearchRuntime.from_course(self._open_course())
        hits = runtime.search("Banach", limit=1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].rank, 1)

    def test_section_filter_is_applied_before_limit(self) -> None:
        runtime = SearchRuntime.from_course(self._open_course())
        try:
            hits = runtime.search("Banach", limit=1, section_id="sec_b")
        except TypeError as exc:
            self.fail(f"section-scoped search is not implemented: {exc}")
        self.assertEqual([hit.source_id for hit in hits], ["def_banach_algebra"])

    def test_omitting_section_filter_preserves_existing_result_order(self) -> None:
        runtime = SearchRuntime.from_course(self._open_course())
        baseline = runtime.search("Banach", limit=20)
        try:
            explicit_none = runtime.search("Banach", limit=20, section_id=None)
        except TypeError as exc:
            self.fail(f"section-scoped search is not implemented: {exc}")
        self.assertEqual(baseline, explicit_none)

    def test_blank_supplied_section_filter_is_rejected(self) -> None:
        runtime = SearchRuntime.from_course(self._open_course())
        try:
            with self.assertRaises(SearchQueryError):
                runtime.search("Banach", section_id="   ")
        except TypeError as exc:
            self.fail(f"section-scoped search is not implemented: {exc}")

    def test_missing_index_file_is_unavailable(self) -> None:
        course = self._open_course()
        (self.book_dir / "search_index_v1.jsonl").unlink()

        with self.assertRaises(SearchIndexUnavailableError):
            SearchRuntime.from_course(course)

    def test_malformed_jsonl_fails_closed(self) -> None:
        course = self._open_course()
        (self.book_dir / "search_index_v1.jsonl").write_text(
            '{"id":"def_banach","book_id":"fixture_book"}\n{broken\n',
            encoding="utf-8",
        )

        with self.assertRaises(SearchIndexUnavailableError):
            SearchRuntime.from_course(course)

    def test_book_identity_mismatch_fails_closed(self) -> None:
        course = self._open_course(
            search_records=[
                {
                    "id": "def_banach",
                    "book_id": "wrong_book",
                    "type": "definition",
                    "name_zh": "巴拿赫空间",
                }
            ]
        )

        with self.assertRaises(SearchIndexUnavailableError):
            SearchRuntime.from_course(course)

    def test_blank_query_and_invalid_limit_are_rejected(self) -> None:
        runtime = SearchRuntime.from_course(self._open_course())

        for query in ("", "   ", "\t\n"):
            with self.subTest(query=query):
                with self.assertRaises(SearchQueryError):
                    runtime.search(query)

        for limit in (-1, 0, 101, True, 1.5):
            with self.subTest(limit=limit):
                with self.assertRaises(SearchQueryError):
                    runtime.search("Banach", limit=limit)

    def test_no_match_is_normal_empty_result(self) -> None:
        runtime = SearchRuntime.from_course(self._open_course())
        self.assertEqual(runtime.search("definitely-no-such-text"), [])


class RealFunctionalAnalysisSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        course = CourseRuntime.open(REPO_ROOT / "courses" / "functional-analysis")
        cls.runtime = SearchRuntime.from_course(course)

    def test_real_index_count_and_searchable_candidates(self) -> None:
        self.assertEqual(self.runtime.index_record_count, 1493)
        self.assertGreater(self.runtime.searchable_candidate_count, 0)

    def test_real_chinese_english_and_holder_queries_resolve_to_objects(self) -> None:
        chinese = self.runtime.search("巴拿赫空间")
        self.assertTrue(chinese)
        self.assertTrue(any(hit.source_kind == "object" for hit in chinese))

        english = self.runtime.search("infinite Bernoulli space")
        self.assertTrue(english)
        self.assertTrue(any(hit.source_id == "def_ch5_infinite_bernoulli_space" for hit in english))

        holder = self.runtime.search("Hölder")
        self.assertTrue(holder)
        self.assertEqual(holder[0].source_kind, "object")
        self.assertEqual(holder[0].object_type, "theorem")

    def test_real_formula_and_practice_types_are_searchable(self) -> None:
        formula = self.runtime.search("1/p + 1/q = 1")
        self.assertTrue(formula)
        self.assertTrue(any(hit.source_id == "def_dual_exponents" for hit in formula))

        exercises = self.runtime.search("exercise", limit=100)
        self.assertTrue(any(hit.object_type == "exercise" for hit in exercises))

        problems = self.runtime.search("problem", limit=100)
        self.assertTrue(any(hit.object_type == "problem" for hit in problems))


if __name__ == "__main__":
    unittest.main()
