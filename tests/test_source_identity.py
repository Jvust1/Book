from __future__ import annotations

import unittest

from book_core.identity import BookIdentity
from book_core.provenance import SourceIdentity


class SourceIdentityTests(unittest.TestCase):
    def test_collision_key_includes_book_version(self) -> None:
        source_a = SourceIdentity(
            course_id="course",
            book=BookIdentity("book", "book", "book@v1", "primary"),
            source_kind="object",
            source_id="thm_1",
        )
        source_b = SourceIdentity(
            course_id="course",
            book=BookIdentity("book", "book", "book@v2", "primary"),
            source_kind="object",
            source_id="thm_1",
        )
        self.assertNotEqual(source_a.collision_key, source_b.collision_key)
        self.assertEqual(source_a.collision_key, ("book@v1", "object", "thm_1"))

    def test_blank_course_id_fails_closed(self) -> None:
        book = BookIdentity("book", "book", "book@v1", "primary")
        with self.assertRaises(ValueError):
            SourceIdentity("", book, "object", "thm_1")

    def test_blank_source_parts_fail_closed(self) -> None:
        book = BookIdentity("book", "book", "book@v1", "primary")
        with self.assertRaises(ValueError):
            SourceIdentity("course", book, "", "thm_1")
        with self.assertRaises(ValueError):
            SourceIdentity("course", book, "object", "")


if __name__ == "__main__":
    unittest.main()
