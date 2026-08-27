from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.api.errors import AppNotFoundError, InvalidModeError
from app.api.service import BookAppService
from tests.runtime_fixture_factory import (
    dump_json,
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class BookAppServiceRealLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = BookAppService(REPO_ROOT)

    def test_library_projects_real_functional_analysis_course(self) -> None:
        library = self.service.library()

        self.assertEqual(len(library.courses), 1)
        card = library.courses[0]
        self.assertEqual(card.course_id, "functional_analysis_course")
        self.assertEqual(card.name_zh, "泛函分析：分析学进一步专题导论")
        self.assertEqual(card.book_id, "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(card.chapter_count, 8)
        self.assertEqual(card.section_count, 132)
        self.assertEqual(card.runtime_status, "READY")

    def test_course_chapter_and_section_keep_real_navigation_identity(self) -> None:
        course = self.service.course("functional_analysis_course")
        self.assertEqual(course.course.course_id, "functional_analysis_course")
        self.assertEqual(len(course.chapters), 8)
        self.assertEqual(course.section_count, 132)

        chapter = self.service.chapter("functional_analysis_course", "chapter_01")
        self.assertEqual(chapter.course_id, "functional_analysis_course")
        self.assertEqual(chapter.book_id, "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(chapter.chapter.chapter_id, "chapter_01")
        self.assertGreater(len(chapter.sections), 0)

        section = self.service.section("functional_analysis_course", "ch01_s01")
        self.assertEqual(section.course_id, "functional_analysis_course")
        self.assertEqual(section.book_id, "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(section.section.section_id, "ch01_s01")
        self.assertIsNotNone(section.section.pdf_page_start)
        self.assertIsNotNone(section.section.pdf_page_end)

    def test_four_modes_preserve_runtime_identity_and_source_order(self) -> None:
        expected_modes = ("preview", "learn", "review", "practice")
        for mode in expected_modes:
            payload = self.service.mode("functional_analysis_course", "ch01_s01", mode)
            self.assertEqual(payload.mode, mode)
            self.assertEqual(payload.course_id, "functional_analysis_course")
            self.assertEqual(payload.book_id, "stein_shakarchi_functional_analysis_2011")
            self.assertEqual(payload.section_id, "ch01_s01")
            self.assertEqual(
                [(ref.kind, ref.source_id) for ref in payload.source_refs],
                [(item.kind, item.source_id) for item in payload.items],
            )

    def test_missing_entities_and_invalid_mode_raise_stable_app_errors(self) -> None:
        cases = (
            (lambda: self.service.course("missing"), AppNotFoundError, "course_not_found", "课程不存在"),
            (
                lambda: self.service.chapter("functional_analysis_course", "missing"),
                AppNotFoundError,
                "chapter_not_found",
                "章节不存在",
            ),
            (
                lambda: self.service.section("functional_analysis_course", "missing"),
                AppNotFoundError,
                "section_not_found",
                "小节不存在",
            ),
            (
                lambda: self.service.source("functional_analysis_course", "object", "missing"),
                AppNotFoundError,
                "source_not_found",
                "教材来源不存在",
            ),
            (
                lambda: self.service.mode("functional_analysis_course", "ch01_s01", "bogus"),
                InvalidModeError,
                "invalid_mode",
                "学习模式无效",
            ),
        )
        for call, error_type, code, message in cases:
            with self.subTest(code=code):
                with self.assertRaises(error_type) as ctx:
                    call()
                self.assertEqual(ctx.exception.code, code)
                self.assertEqual(ctx.exception.user_message, message)


class BookAppServiceEmptyModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        repo = make_repo(Path(self.tempdir.name))
        write_ready_book(
            repo / "books" / "fixture-book",
            book_id="fixture_book",
            objects=[
                {
                    "type": "concept",
                    "id": "concept_fixture",
                    "name_zh": "普通概念",
                    "anchor": {"pdf_page": 1, "printed_page": 1},
                }
            ],
        )
        write_course(
            repo / "courses" / "fixture-course",
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
        )
        library_dir = repo / "library"
        dump_json(
            library_dir / "library.json",
            {
                "schema_version": "library_manifest_v1",
                "library_id": "fixture_library",
                "name": "测试书架",
                "courses": [
                    {
                        "course_id": "fixture_course",
                        "name": "测试课程",
                        "path": "../courses/fixture-course",
                        "enabled": True,
                        "order": 10,
                    }
                ],
            },
        )
        self.service = BookAppService(repo)

    def test_review_and_practice_empty_lists_are_valid(self) -> None:
        review = self.service.mode("fixture_course", "ch01_s01", "review")
        practice = self.service.mode("fixture_course", "ch01_s01", "practice")

        self.assertEqual(review.items, [])
        self.assertEqual(review.source_refs, [])
        self.assertEqual(practice.items, [])
        self.assertEqual(practice.source_refs, [])


if __name__ == "__main__":
    unittest.main()
