from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime import CourseRuntime, DeterministicFakeModelProvider, QARuntime
from runtime.retrieval import RetrievalEngine
from tests.runtime_fixture_factory import (
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SHADOW_FIELDS = {
    "bm25_score",
    "profile_id",
    "shadow",
    "fts",
    "retriever_id",
    "identity",
    "book_version_id",
}


def _class_fields(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.target.id
                for child in node.body
                if isinstance(child, ast.AnnAssign)
                and isinstance(child.target, ast.Name)
            }
    raise AssertionError(f"Missing class {class_name!r} in {path}")


def _book_app_default_retrieval_assignment() -> ast.AST:
    path = REPO_ROOT / "app" / "api" / "service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "BookAppService":
            continue
        for child in node.body:
            if not isinstance(child, ast.FunctionDef) or child.name != "__init__":
                continue
            for statement in ast.walk(child):
                if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                    continue
                target = statement.targets[0]
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                    and target.attr == "_retrieval_factory"
                ):
                    return statement.value
    raise AssertionError("BookAppService default retrieval assignment is missing")


class H4aIsolationTests(unittest.TestCase):
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
                    "content_zh": "Fixture theorem content",
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

    def test_book_app_service_default_retrieval_remains_exact(self) -> None:
        value = _book_app_default_retrieval_assignment()

        self.assertIsInstance(value, ast.BoolOp)
        self.assertIsInstance(value.op, ast.Or)
        self.assertEqual(len(value.values), 2)
        self.assertIsInstance(value.values[0], ast.Name)
        self.assertEqual(value.values[0].id, "retrieval_factory")
        self.assertIsInstance(value.values[1], ast.Attribute)
        self.assertEqual(value.values[1].attr, "exact")
        self.assertIsInstance(value.values[1].value, ast.Name)
        self.assertEqual(value.values[1].value.id, "RetrievalEngine")

        tree = ast.parse(
            (REPO_ROOT / "app" / "api" / "service.py").read_text(encoding="utf-8")
        )
        self.assertFalse(
            any(
                isinstance(node, ast.Name) and node.id == "ShadowFtsIndex"
                for node in ast.walk(tree)
            )
        )

    def test_qa_runtime_default_retrieval_remains_exact(self) -> None:
        course = self._open_course()
        original_exact = RetrievalEngine.exact
        exact_calls: list[str] = []

        def exact_spy(selected_course: CourseRuntime) -> RetrievalEngine:
            exact_calls.append(selected_course.course_id)
            return original_exact(selected_course)

        with (
            patch(
                "runtime.qa_evidence.RetrievalEngine.exact",
                side_effect=exact_spy,
            ),
            patch(
                "runtime.shadow_fts.ShadowFtsIndex.from_course",
                side_effect=AssertionError("production QA must not instantiate shadow FTS"),
            ),
        ):
            result = QARuntime.from_course(
                course,
                provider=DeterministicFakeModelProvider(),
            ).answer("Fixture theorem")

        self.assertEqual(exact_calls, ["fixture_course"])
        self.assertFalse(result.insufficient_evidence)
        self.assertTrue(result.citations)

    def test_shadow_types_are_not_present_in_public_search_dto(self) -> None:
        models = REPO_ROOT / "app" / "api" / "models.py"
        search_fields = _class_fields(models, "SearchResultItem") | _class_fields(
            models, "SearchResponse"
        )

        self.assertTrue(FORBIDDEN_SHADOW_FIELDS.isdisjoint(search_fields))
        self.assertEqual(
            _class_fields(models, "SearchResultItem"),
            {
                "rank",
                "score",
                "source_kind",
                "source_id",
                "object_type",
                "number",
                "title_zh",
                "title_en",
                "formula",
                "pdf_page",
                "printed_page",
                "source_anchor",
                "snippet",
            },
        )

    def test_shadow_types_are_not_present_in_public_qa_dto(self) -> None:
        models = REPO_ROOT / "app" / "api" / "models.py"
        qa_fields = _class_fields(models, "QAResponse") | _class_fields(
            models, "QACitationItem"
        )

        self.assertTrue(FORBIDDEN_SHADOW_FIELDS.isdisjoint(qa_fields))
        self.assertEqual(
            _class_fields(models, "QAResponse"),
            {
                "course_id",
                "book_id",
                "question",
                "answer",
                "answer_kind",
                "answer_style",
                "scope_requested",
                "scope_used",
                "insufficient_evidence",
                "message",
                "citations",
            },
        )

    def test_public_exact_search_signature_matches_pre_h4a_contract(self) -> None:
        course = self._open_course()
        hits = RetrievalEngine.exact(course).search("Fixture theorem", limit=10)

        self.assertEqual(
            [
                (hit.rank, hit.score, hit.source_kind, hit.source_id)
                for hit in hits
            ],
            [(1, 1000, "object", "thm_fixture")],
        )
        self.assertTrue(all(isinstance(hit.score, int) for hit in hits))


if __name__ == "__main__":
    unittest.main()
