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

        for limit in (0, 101):
            with self.subTest(limit=limit):
                with self.assertRaises(SearchQueryError):
                    runtime.search("Banach", limit=limit)

    def test_no_match_is_normal_empty_result(self) -> None:
        runtime = SearchRuntime.from_course(self._open_course())
        self.assertEqual(runtime.search("definitely-no-such-text"), [])


if __name__ == "__main__":
    unittest.main()
