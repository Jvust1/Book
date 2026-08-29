from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from runtime.course_runtime import CourseRuntime
from runtime.provenance import RuntimeProvenanceError, source_identity_for
from tests.runtime_fixture_factory import (
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


class RuntimeProvenanceTests(unittest.TestCase):
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
                    "name_zh": "测试定理",
                    "anchor": {
                        "pdf_page": 1,
                        "printed_page": 1,
                        "source_anchor": "fixture:p1:thm_fixture",
                    },
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

    def test_projects_resolved_source_to_internal_identity(self) -> None:
        identity = source_identity_for(self._open_course(), "object", "thm_fixture")

        self.assertEqual(identity.course_id, "fixture_course")
        self.assertEqual(identity.book.book_id, "fixture_book")
        self.assertEqual(identity.book.book_version_id, "fixture_book@v1")
        self.assertEqual(identity.source_kind, "object")
        self.assertEqual(identity.source_id, "thm_fixture")
        self.assertEqual(
            identity.collision_key,
            ("fixture_book@v1", "object", "thm_fixture"),
        )

    def test_unknown_source_fails_as_runtime_provenance_error(self) -> None:
        with self.assertRaises(RuntimeProvenanceError):
            source_identity_for(self._open_course(), "object", "missing")

    def test_resolved_course_or_book_identity_mismatch_fails_closed(self) -> None:
        course = self._open_course()
        for course_id, book_id in [
            ("wrong_course", "fixture_book"),
            ("fixture_course", "wrong_book"),
        ]:
            with self.subTest(course_id=course_id, book_id=book_id):
                resolver = Mock()
                resolver.resolve.return_value = SimpleNamespace(
                    course_id=course_id,
                    book_id=book_id,
                    kind="object",
                    source_id="thm_fixture",
                )
                with patch("runtime.provenance.SourceResolver", return_value=resolver):
                    with self.assertRaises(RuntimeProvenanceError):
                        source_identity_for(course, "object", "thm_fixture")

    def test_collision_key_changes_when_book_version_changes(self) -> None:
        course = self._open_course()
        first = source_identity_for(course, "object", "thm_fixture")
        course.main_book().completion["version"] = "v2"
        second = source_identity_for(course, "object", "thm_fixture")

        self.assertNotEqual(first.collision_key, second.collision_key)
        self.assertEqual(second.collision_key, ("fixture_book@v2", "object", "thm_fixture"))


if __name__ == "__main__":
    unittest.main()
