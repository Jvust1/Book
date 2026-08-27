from __future__ import annotations

import unittest
from pathlib import Path

from app.api.service import BookAppService


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

    def test_course_and_section_keep_real_navigation_identity(self) -> None:
        course = self.service.course("functional_analysis_course")
        self.assertEqual(course.course.course_id, "functional_analysis_course")
        self.assertEqual(len(course.chapters), 8)
        self.assertEqual(course.section_count, 132)

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


if __name__ == "__main__":
    unittest.main()
