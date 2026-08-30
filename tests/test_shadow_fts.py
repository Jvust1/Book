from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from runtime.course_runtime import CourseRuntime
from runtime.search_runtime import SearchRuntime
from runtime.shadow_fts import (
    H4A_PROFILES,
    ShadowFtsIndex,
    ShadowFtsInvariantError,
    ShadowFtsQueryError,
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


class ShadowFtsSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.repo = make_repo(Path(self.tempdir.name))
        self.book_dir = self.repo / "books" / "fixture-book"
        self.course_dir = self.repo / "courses" / "fixture-course"

    def _object(
        self,
        source_id: str,
        section_id: str,
        page: int,
        *,
        object_type: str = "theorem",
    ) -> dict[str, object]:
        return {
            "type": object_type,
            "id": source_id,
            "section_id": section_id,
            "name_en": source_id,
            "anchor": {
                "pdf_page": page,
                "printed_page": page,
                "source_anchor": f"fixture_book:pdf:{page}:{source_id}",
            },
        }

    def _open_course(self) -> CourseRuntime:
        write_ready_book(
            self.book_dir,
            book_id="fixture_book",
            objects=[
                self._object("obj_first", "sec_a", 1),
                self._object("obj_second", "sec_b", 2),
                self._object("obj_literal", "sec_a", 1, object_type="definition"),
                self._object("obj_quote", "sec_a", 1, object_type="definition"),
                self._object("obj_zh", "sec_b", 2, object_type="definition"),
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
                    "id": "obj_first",
                    "book_id": "fixture_book",
                    "type": "theorem",
                    "title_en": "shared tie phrase Open mapping theorem",
                },
                {
                    "id": "obj_second",
                    "book_id": "fixture_book",
                    "type": "theorem",
                    "title_en": "shared tie phrase Open mapping theorem",
                },
                {
                    "id": "obj_literal",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "title_en": "AND OR NOT NEAR literal operator words",
                },
                {
                    "id": "obj_quote",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "title_en": "quoted \"operator\" phrase",
                },
                {
                    "id": "obj_zh",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "title_zh": "巴拿赫空间中的开映射定理",
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

    def _require_search(self, index: ShadowFtsIndex):
        search = getattr(index, "search", None)
        self.assertTrue(
            callable(search),
            "ShadowFtsIndex.search must exist before shadow query semantics can pass",
        )
        return search

    def test_rejects_blank_query(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        with self.assertRaises(ShadowFtsQueryError):
            search(H4A_PROFILES[0], "   ")

    def test_rejects_invalid_limit_values(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        for invalid in (0, -1, True, 1.5, "10"):
            with self.subTest(limit=invalid):
                with self.assertRaises(ShadowFtsQueryError):
                    search(H4A_PROFILES[0], "Open mapping theorem", limit=invalid)

    def test_rejects_blank_section_id(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        with self.assertRaises(ShadowFtsQueryError):
            search(H4A_PROFILES[0], "Open mapping theorem", section_id="  ")

    def test_rejects_unknown_profile_id(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        with self.assertRaises(ShadowFtsQueryError):
            search("unknown_profile", "Open mapping theorem")

    def test_operator_words_are_literal_user_text(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        hits = search(H4A_PROFILES[0], "AND OR NOT NEAR")
        self.assertEqual([hit.source_id for hit in hits], ["obj_literal"])

    def test_embedded_quotes_are_safe(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        hits = search(H4A_PROFILES[0], 'quoted "operator" phrase')
        self.assertEqual([hit.source_id for hit in hits], ["obj_quote"])

    def test_match_query_is_parameterized(self) -> None:
        index = self._build_index(self._open_course())
        search = self._require_search(index)
        hits = search(H4A_PROFILES[0], "x' UNION SELECT")
        self.assertEqual(hits, [])
        table_count = index.connection.execute(
            "SELECT COUNT(*) FROM shadow_documents"
        ).fetchone()[0]
        self.assertEqual(table_count, 5)

    def test_unicode61_returns_unicode_fixture_match(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        hits = search(H4A_PROFILES[0], "Open mapping theorem")
        self.assertEqual(
            [hit.source_id for hit in hits[:2]],
            ["obj_first", "obj_second"],
        )

    def test_trigram_returns_substring_fixture_match(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        hits = search(H4A_PROFILES[1], "映射定")
        self.assertEqual([hit.source_id for hit in hits], ["obj_zh"])

    def test_trigram_under_three_unicode_characters_is_valid_zero_match(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        self.assertEqual(search(H4A_PROFILES[1], "映射"), [])

    def test_bm25_is_sorted_ascending_then_rowid_for_ties(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        hits = search(H4A_PROFILES[0], "shared tie phrase")
        self.assertEqual([hit.source_id for hit in hits], ["obj_first", "obj_second"])
        self.assertEqual([hit.rank for hit in hits], [1, 2])
        self.assertTrue(all(math.isfinite(hit.bm25_score) for hit in hits))
        self.assertLessEqual(hits[0].bm25_score, hits[1].bm25_score)

    def test_section_scope_never_returns_other_section(self) -> None:
        search = self._require_search(self._build_index(self._open_course()))
        hits = search(
            H4A_PROFILES[0],
            "Open mapping theorem",
            section_id="sec_a",
        )
        self.assertEqual([hit.source_id for hit in hits], ["obj_first"])
        self.assertTrue(all(hit.section_id == "sec_a" for hit in hits))

    def test_shadow_hit_revalidates_canonical_identity(self) -> None:
        course = self._open_course()
        index = self._build_index(course)
        search = self._require_search(index)
        course.main_book().objects["obj_first"].id = "corrupted_identity"

        with self.assertRaises(ShadowFtsInvariantError):
            search(H4A_PROFILES[0], "Open mapping theorem")


if __name__ == "__main__":
    unittest.main()
