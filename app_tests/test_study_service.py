from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.api.errors import AppNotFoundError, AppUnavailableError, InvalidModeError
from app.api.service import BookAppService
from app.study.repository import StudyRecordRepository, StudyRecordRepositoryError
from app.study.service import StudyRecordService


REPO_ROOT = Path(__file__).resolve().parents[1]


class _FailingTouchRepository(StudyRecordRepository):
    def touch_record(self, course_id, book_id, section_id, mode):
        raise StudyRecordRepositoryError("private sqlite detail: /tmp/private.sqlite3")


class _UnexpectedListRepository(StudyRecordRepository):
    def list_course_records(self, course_id):
        raise AssertionError("repository must not be queried before course validation")


class StudyRecordServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.book_service = BookAppService(REPO_ROOT)

    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = StudyRecordRepository(Path(self.temp.name) / "study.sqlite3")
        self.service = StudyRecordService(self.book_service, self.repo)

    def test_valid_touch_stores_canonical_book_identity(self) -> None:
        record = self.service.touch(
            "functional_analysis_course",
            "ch01_s01",
            "learn",
        )

        self.assertEqual(record.course_id, "functional_analysis_course")
        self.assertEqual(record.section_id, "ch01_s01")
        self.assertEqual(record.mode, "learn")
        self.assertEqual(record.book_id, "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(record.profile_id, self.repo.get_profile_id())

    def test_mode_is_normalized_before_persistence(self) -> None:
        record = self.service.touch(
            "functional_analysis_course",
            "ch01_s01",
            "  LEARN  ",
        )

        self.assertEqual(record.mode, "learn")
        self.assertIsNotNone(
            self.repo.get_record("functional_analysis_course", "ch01_s01", "learn")
        )

    def test_unknown_course_fails_without_mutation(self) -> None:
        with self.assertRaises(AppNotFoundError) as ctx:
            self.service.touch("missing_course", "ch01_s01", "learn")

        self.assertEqual(ctx.exception.code, "course_not_found")
        self.assertIsNone(self.repo.get_recent_record())

    def test_unknown_section_fails_without_mutation(self) -> None:
        with self.assertRaises(AppNotFoundError) as ctx:
            self.service.touch("functional_analysis_course", "missing", "learn")

        self.assertEqual(ctx.exception.code, "section_not_found")
        self.assertIsNone(self.repo.get_recent_record())

    def test_invalid_mode_fails_without_mutation(self) -> None:
        with self.assertRaises(InvalidModeError) as ctx:
            self.service.touch("functional_analysis_course", "ch01_s01", "watch")

        self.assertEqual(ctx.exception.code, "invalid_mode")
        self.assertEqual(ctx.exception.user_message, "学习模式无效")
        self.assertIsNone(self.repo.get_recent_record())

    def test_complete_uses_same_canonical_validation(self) -> None:
        record = self.service.complete(
            "functional_analysis_course",
            "ch01_s01",
            "practice",
        )

        self.assertEqual(record.book_id, "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(record.status, "completed")
        self.assertEqual(record.progress, 100)

    def test_browser_facing_methods_do_not_accept_book_or_profile_identity(self) -> None:
        for method_name in ("touch", "complete"):
            parameters = inspect.signature(
                getattr(StudyRecordService, method_name)
            ).parameters
            self.assertNotIn("book_id", parameters)
            self.assertNotIn("profile_id", parameters)

    def test_list_course_validates_course_before_repository_query(self) -> None:
        guarded = _UnexpectedListRepository(Path(self.temp.name) / "guarded.sqlite3")
        service = StudyRecordService(self.book_service, guarded)

        with self.assertRaises(AppNotFoundError) as ctx:
            service.list_course("missing_course")

        self.assertEqual(ctx.exception.code, "course_not_found")

    def test_list_course_returns_only_valid_course_records(self) -> None:
        touched = self.service.touch(
            "functional_analysis_course",
            "ch01_s01",
            "preview",
        )

        records = self.service.list_course("functional_analysis_course")

        self.assertEqual(records, (touched,))

    def test_recent_returns_none_then_latest_durable_record(self) -> None:
        self.assertIsNone(self.service.recent())
        latest = self.service.touch(
            "functional_analysis_course",
            "ch01_s02",
            "review",
        )

        self.assertEqual(self.service.recent(), latest)

    def test_repository_failure_maps_to_stable_unavailable_error(self) -> None:
        failing = _FailingTouchRepository(Path(self.temp.name) / "failing.sqlite3")
        service = StudyRecordService(self.book_service, failing)

        with self.assertRaises(AppUnavailableError) as ctx:
            service.touch("functional_analysis_course", "ch01_s01", "learn")

        self.assertEqual(ctx.exception.code, "study_store_unavailable")
        self.assertEqual(ctx.exception.user_message, "学习进度暂无法保存")
        self.assertIn("private sqlite detail", ctx.exception.detail or "")


if __name__ == "__main__":
    unittest.main()
