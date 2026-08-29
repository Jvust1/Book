from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.course_runtime import CourseRuntime
from runtime.provenance import RuntimeProvenanceError
from runtime.retrieval import (
    CanonicalExactRetriever,
    RetrievalEngine,
    RetrievalInvariantError,
    RetrievalQueryError,
    RetrievalRequest,
    RetrievalUnavailableError,
)
from runtime.search_runtime import SearchRuntime
from tests.runtime_fixture_factory import (
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _search_signature(hits: list[object]) -> list[tuple[int, int, str, str]]:
    return [
        (hit.rank, hit.score, hit.source_kind, hit.source_id)
        for hit in hits
    ]


class RetrievalTests(unittest.TestCase):
    def _open_course(self) -> CourseRuntime:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        repo = make_repo(Path(tempdir.name))
        book_dir = repo / "books" / "fixture-book"
        write_ready_book(
            book_dir,
            book_id="fixture_book",
            objects=[
                {
                    "type": "theorem",
                    "id": "thm_fixture",
                    "name_en": "Fixture theorem",
                    "number": "1.1",
                    "formula": "x = y",
                    "anchor": {
                        "pdf_page": 1,
                        "printed_page": 1,
                        "source_anchor": "fixture:p1:thm_fixture",
                    },
                }
            ],
            search_records=[
                {
                    "id": "thm_fixture",
                    "book_id": "fixture_book",
                    "type": "theorem",
                    "name_en": "Fixture theorem",
                    "number": "1.1",
                    "formula": "x = y",
                    "pdf_page": 1,
                    "printed_page": 1,
                    "source_anchor": "fixture:p1:thm_fixture",
                }
            ],
        )
        course_dir = repo / "courses" / "fixture-course"
        write_course(
            course_dir,
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
        )
        return CourseRuntime.open(course_dir)

    def test_request_contract_is_stable(self) -> None:
        request = RetrievalRequest(query="Hölder", limit=10, section_id=None)
        self.assertEqual(request.query, "Hölder")
        self.assertEqual(request.limit, 10)
        self.assertIsNone(request.section_id)

    def test_canonical_exact_retriever_preserves_search_runtime_order_and_scores(self) -> None:
        course = self._open_course()
        search_hits = SearchRuntime.from_course(course).search("fixture", limit=10)
        retrieval_hits = CanonicalExactRetriever.from_course(course).search(
            RetrievalRequest("fixture", limit=10)
        )

        self.assertEqual(_search_signature(retrieval_hits), _search_signature(search_hits))
        self.assertTrue(retrieval_hits)
        for hit in retrieval_hits:
            self.assertEqual(hit.identity.course_id, course.course_id)
            self.assertEqual(hit.identity.book, course.main_book_identity())
            self.assertEqual(hit.identity.source_kind, hit.source_kind)
            self.assertEqual(hit.identity.source_id, hit.source_id)

    def test_engine_exact_is_a_thin_equivalent_seam(self) -> None:
        course = self._open_course()
        expected = SearchRuntime.from_course(course).search("fixture", limit=10)
        actual = RetrievalEngine.exact(course).search("fixture", limit=10)
        self.assertEqual(_search_signature(actual), _search_signature(expected))

    def test_query_error_is_translated(self) -> None:
        retriever = CanonicalExactRetriever.from_course(self._open_course())
        with self.assertRaises(RetrievalQueryError):
            retriever.search(RetrievalRequest("   "))

    def test_missing_search_index_is_translated_as_unavailable(self) -> None:
        course = self._open_course()
        search_path = course.main_book().search_index_path
        self.assertIsNotNone(search_path)
        Path(search_path).unlink()

        with self.assertRaises(RetrievalUnavailableError):
            CanonicalExactRetriever.from_course(course)

    def test_source_identity_failure_is_translated_as_invariant_error(self) -> None:
        retriever = CanonicalExactRetriever.from_course(self._open_course())
        with patch(
            "runtime.retrieval.source_identity_for",
            side_effect=RuntimeProvenanceError("fixture identity mismatch"),
        ):
            with self.assertRaises(RetrievalInvariantError):
                retriever.search(RetrievalRequest("fixture"))


class RealFunctionalAnalysisRetrievalEquivalenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.course = CourseRuntime.open(REPO_ROOT / "courses" / "functional-analysis")
        cls.search = SearchRuntime.from_course(cls.course)
        cls.retrieval = RetrievalEngine.exact(cls.course)

    def test_golden_queries_match_exact_search_rank_score_and_identity(self) -> None:
        queries = (
            "Hölder",
            "巴拿赫空间",
            "1/p + 1/q = 1",
            "definitely-no-such-text-92831",
        )
        for query in queries:
            with self.subTest(query=query):
                expected = self.search.search(query)
                actual = self.retrieval.search(query)
                self.assertEqual(_search_signature(actual), _search_signature(expected))

    def test_section_scoped_golden_query_matches_exact_search(self) -> None:
        query = "1/p + 1/q = 1"
        expected = self.search.search(query, section_id="ch01_s01")
        actual = self.retrieval.search(query, section_id="ch01_s01")
        self.assertEqual(_search_signature(actual), _search_signature(expected))


if __name__ == "__main__":
    unittest.main()
