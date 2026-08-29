from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from runtime.course_runtime import CourseBookEntry, CourseRuntime, CourseRuntimeError


class CourseRuntimeIdentityTests(unittest.TestCase):
    def _course(self) -> CourseRuntime:
        course = CourseRuntime(
            Path("."),
            {
                "course_id": "fixture_course",
                "name": "Fixture Course",
                "main_book_id": "fixture_main",
            },
        )
        course.course_id = "fixture_course"
        course.main_book_id = "fixture_main"
        course.entries = (
            CourseBookEntry(
                book_id="fixture_main",
                role="main",
                path=Path("books/main"),
                required=True,
                enabled=True,
            ),
            CourseBookEntry(
                book_id="fixture_supplementary",
                role="supplementary",
                path=Path("books/supplementary"),
                required=False,
                enabled=True,
            ),
        )
        course.books = {
            "fixture_main": SimpleNamespace(
                book_id="fixture_main",
                structured_version="v1",
            ),
            "fixture_supplementary": SimpleNamespace(
                book_id="fixture_supplementary",
                structured_version="v2",
            ),
        }
        return course

    def test_main_book_identity_projects_canonical_identity(self) -> None:
        identity = self._course().main_book_identity()
        self.assertEqual(identity.book_id, "fixture_main")
        self.assertEqual(identity.logical_book_id, "fixture_main")
        self.assertEqual(identity.book_version_id, "fixture_main@v1")
        self.assertEqual(identity.role, "primary")

    def test_supplementary_identity_preserves_legacy_role_api(self) -> None:
        course = self._course()
        identity = course.book_identity("fixture_supplementary")
        self.assertEqual(identity.book_id, "fixture_supplementary")
        self.assertEqual(identity.logical_book_id, "fixture_supplementary")
        self.assertEqual(identity.book_version_id, "fixture_supplementary@v2")
        self.assertEqual(identity.role, "supplementary")
        self.assertEqual(
            [(entry.book_id, entry.role) for entry in course.entries],
            [("fixture_main", "main"), ("fixture_supplementary", "supplementary")],
        )

    def test_blank_structured_version_fails_closed_on_projection(self) -> None:
        course = self._course()
        course.books["fixture_main"].structured_version = ""
        with self.assertRaises(CourseRuntimeError):
            course.main_book_identity()


if __name__ == "__main__":
    unittest.main()
