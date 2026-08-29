from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.course_runtime import CourseRuntime
from runtime.search_runtime import SearchRuntime
from runtime.shadow_fts import (
    H4A_PROFILES,
    ShadowFtsIndex,
    ShadowFtsInvariantError,
    fts5_available,
)
from tests.runtime_fixture_factory import (
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class ShadowFtsCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.repo = make_repo(Path(self.tempdir.name))
        self.book_dir = self.repo / "books" / "fixture-book"
        self.course_dir = self.repo / "courses" / "fixture-course"

    def _open_course(self) -> CourseRuntime:
        write_ready_book(
            self.book_dir,
            book_id="fixture_book",
            objects=[
                {
                    "type": "definition",
                    "id": "def_first",
                    "section_id": "sec_a",
                    "name_zh": "第一定义",
                    "name_en": "First definition",
                    "number": "1.1",
                    "anchor": {
                        "pdf_page": 1,
                        "printed_page": 1,
                        "source_anchor": "fixture_book:pdf:1:def_first",
                    },
                },
                {
                    "type": "theorem",
                    "id": "thm_second",
                    "section_id": "sec_b",
                    "name_zh": "第二定理",
                    "name_en": "Second theorem",
                    "number": "2.1",
                    "anchor": {
                        "pdf_page": 2,
                        "printed_page": 2,
                        "source_anchor": "fixture_book:pdf:2:thm_second",
                    },
                },
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
            search_records=[
                {
                    "id": "thm_second",
                    "book_id": "fixture_book",
                    "type": "theorem",
                },
                {
                    "id": "section_sec_a",
                    "book_id": "fixture_book",
                    "type": "section",
                    "title_zh": "不属于 Exact 候选边界",
                },
                {
                    "id": "def_first",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "title_zh": " 第一定义 ",
                    "title_en": " First definition ",
                    "number": " 1.1 ",
                    "formula": None,
                    "initial_concepts_zh": ["第二概念", "第一概念", "  ", 7],
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

    def _build_index(self, course: CourseRuntime) -> ShadowFtsIndex:
        index = ShadowFtsIndex.from_course(course)
        self.addCleanup(index.close)
        return index

    def test_detects_fts5_by_creating_virtual_table(self) -> None:
        self.assertTrue(fts5_available())

    def test_builds_in_memory_index_only(self) -> None:
        index = self._build_index(self._open_course())

        database_rows = index.connection.execute("PRAGMA database_list").fetchall()
        self.assertTrue(database_rows)
        self.assertTrue(all(row[2] == "" for row in database_rows))

        table_names = {
            row[0]
            for row in index.connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            )
        }
        self.assertIn("shadow_documents", table_names)
        self.assertTrue(set(H4A_PROFILES).issubset(table_names))

    def test_skips_rows_outside_existing_exact_candidate_boundary(self) -> None:
        index = self._build_index(self._open_course())

        self.assertEqual(
            [document.source_id for document in index.documents],
            ["thm_second", "def_first"],
        )

    def test_preserves_canonical_search_index_order_in_rowids(self) -> None:
        index = self._build_index(self._open_course())

        self.assertEqual(
            [(document.rowid, document.source_id) for document in index.documents],
            [(1, "thm_second"), (2, "def_first")],
        )

    def test_projects_concepts_in_source_list_order(self) -> None:
        index = self._build_index(self._open_course())
        document = next(
            row for row in index.documents if row.source_id == "def_first"
        )

        self.assertEqual(document.concepts_zh, "第二概念\n第一概念")
        self.assertEqual(document.title_zh, "第一定义")
        self.assertEqual(document.title_en, "First definition")
        self.assertEqual(document.number, "1.1")

    def test_missing_text_projects_to_empty_string(self) -> None:
        index = self._build_index(self._open_course())
        document = next(
            row for row in index.documents if row.source_id == "thm_second"
        )

        self.assertEqual(document.number, "")
        self.assertEqual(document.title_zh, "")
        self.assertEqual(document.title_en, "")
        self.assertEqual(document.formula, "")
        self.assertEqual(document.concepts_zh, "")
        self.assertEqual(document.snippet, "")

    def test_eligible_provenance_mismatch_fails_closed(self) -> None:
        course = self._open_course()
        course.main_book().objects["def_first"].id = "def_corrupted_identity"

        with self.assertRaises(ShadowFtsInvariantError):
            ShadowFtsIndex.from_course(course)

    def test_document_count_matches_search_runtime_candidate_count(self) -> None:
        course = CourseRuntime.open(REPO_ROOT / "courses" / "functional-analysis")
        exact = SearchRuntime.from_course(course)
        index = self._build_index(course)

        self.assertEqual(index.document_count, exact.searchable_candidate_count)


if __name__ == "__main__":
    unittest.main()
