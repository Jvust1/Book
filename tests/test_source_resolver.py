from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.course_runtime import CourseRuntime
from runtime.source_resolver import SourceResolutionError, SourceResolver
from tests.runtime_fixture_factory import (
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


class SourceResolverTests(unittest.TestCase):
    def _open_course(self, objects: list[dict[str, object]]) -> CourseRuntime:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        repo = make_repo(Path(self.tempdir.name))
        book_dir = repo / "books" / "fixture-book"
        write_ready_book(book_dir, book_id="fixture_book", objects=objects)
        course_dir = repo / "courses" / "fixture-course"
        write_course(
            course_dir,
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
        )
        return CourseRuntime.open(course_dir)

    def test_resolves_real_object_fields_without_synthesis(self) -> None:
        course = self._open_course(
            [
                {
                    "type": "theorem",
                    "id": "thm_fixture",
                    "number": "1.1",
                    "name_en": "Fixture theorem",
                    "name_zh": "测试定理",
                    "content_zh": "这是测试定理的中文内容。",
                    "anchor": {
                        "pdf_page": 1,
                        "printed_page": 1,
                        "source_anchor": "fixture:p1:thm_fixture",
                    },
                }
            ]
        )

        source = SourceResolver(course).resolve("object", "thm_fixture")

        self.assertEqual(source.kind, "object")
        self.assertEqual(source.source_id, "thm_fixture")
        self.assertEqual(source.type, "theorem")
        self.assertEqual(source.type_zh, "定理")
        self.assertEqual(source.title_zh, "测试定理")
        self.assertEqual(source.title_en, "Fixture theorem")
        self.assertEqual(source.content_zh, "这是测试定理的中文内容。")
        self.assertEqual(source.pdf_page, 1)
        self.assertEqual(source.printed_page, 1)
        self.assertEqual(source.source_anchor, "fixture:p1:thm_fixture")
        self.assertTrue(source.translation_available)

    def test_missing_optional_content_and_anchor_remain_none(self) -> None:
        course = self._open_course(
            [
                {
                    "type": "definition",
                    "id": "def_missing_optional",
                    "name_zh": "缺失字段定义",
                    "anchor": {"pdf_page": 1, "printed_page": 1},
                }
            ]
        )

        source = SourceResolver(course).resolve("object", "def_missing_optional")

        self.assertIsNone(source.content_zh)
        self.assertIsNone(source.source_anchor)
        self.assertTrue(source.translation_available)

    def test_unknown_source_and_kind_fail_closed(self) -> None:
        course = self._open_course(
            [
                {
                    "type": "theorem",
                    "id": "thm_fixture",
                    "name_zh": "测试定理",
                    "anchor": {"pdf_page": 1, "printed_page": 1},
                }
            ]
        )
        resolver = SourceResolver(course)

        with self.assertRaises(SourceResolutionError):
            resolver.resolve("object", "missing")
        with self.assertRaises(SourceResolutionError):
            resolver.resolve("bogus", "thm_fixture")


if __name__ == "__main__":
    unittest.main()
