from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import runtime
from runtime.course_runtime import CourseRuntime
from runtime.source_resolver import SourceResolutionError, SourceResolver
from tests.runtime_fixture_factory import (
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


class SourceResolverTests(unittest.TestCase):
    def _open_course(
        self,
        objects: list[dict[str, object]] | None = None,
        figures: list[dict[str, object]] | None = None,
    ) -> CourseRuntime:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        repo = make_repo(Path(self.tempdir.name))
        book_dir = repo / "books" / "fixture-book"
        write_ready_book(
            book_dir,
            book_id="fixture_book",
            objects=objects,
            figures=figures,
        )
        course_dir = repo / "courses" / "fixture-course"
        write_course(
            course_dir,
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
        )
        return CourseRuntime.open(course_dir)

    def test_runtime_package_exports_source_resolver_contract(self) -> None:
        self.assertIs(runtime.SourceResolver, SourceResolver)
        self.assertIs(runtime.SourceResolutionError, SourceResolutionError)
        self.assertIs(runtime.ResolvedSource, SourceResolver(self._open_course()).resolve("translation", "chunk_001a").__class__)
        self.assertEqual(runtime.TYPE_LABELS_ZH["theorem"], "定理")

    def test_resolves_real_object_fields_without_synthesis(self) -> None:
        course = self._open_course(
            objects=[
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

    def test_resolves_figure_metadata_without_inventing_content(self) -> None:
        course = self._open_course(
            figures=[
                {
                    "id": "figure_fixture",
                    "title_en": "Fixture figure",
                    "title_zh": "测试图片",
                    "pdf_page": 2,
                    "printed_page": 2,
                    "source_anchor": "fixture:p2:figure_fixture",
                }
            ]
        )

        source = SourceResolver(course).resolve("figure", "figure_fixture")

        self.assertEqual(source.kind, "figure")
        self.assertEqual(source.source_id, "figure_fixture")
        self.assertEqual(source.type, "figure")
        self.assertEqual(source.type_zh, "图")
        self.assertEqual(source.title_zh, "测试图片")
        self.assertEqual(source.title_en, "Fixture figure")
        self.assertIsNone(source.content_zh)
        self.assertEqual(source.pdf_page, 2)
        self.assertEqual(source.printed_page, 2)
        self.assertEqual(source.source_anchor, "fixture:p2:figure_fixture")
        self.assertTrue(source.translation_available)

    def test_resolves_translation_batch_as_exact_chinese_learning_layer(self) -> None:
        course = self._open_course()

        source = SourceResolver(course).resolve("translation", "chunk_001a")

        self.assertEqual(source.kind, "translation")
        self.assertEqual(source.source_id, "chunk_001a")
        self.assertEqual(source.type, "translation")
        self.assertEqual(source.type_zh, "中文学习层")
        self.assertEqual(source.title_zh, "中文学习层")
        self.assertEqual(source.content_zh, "# 测试学习层\n")
        self.assertEqual(source.pdf_page, 1)
        self.assertEqual(source.printed_page, 1)
        self.assertIsNone(source.source_anchor)
        self.assertEqual(source.source_batch, "chunk_001a")
        self.assertTrue(source.translation_available)

    def test_missing_optional_content_and_anchor_remain_none(self) -> None:
        course = self._open_course(
            objects=[
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
            objects=[
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
