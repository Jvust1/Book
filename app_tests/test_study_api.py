from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.api.main import app, get_service, get_study_repository
from app.api.service import BookAppService
from app.study.repository import StudyRecordRepository, StudyRecordRepositoryError


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_SERVICE = BookAppService(REPO_ROOT)


class _FailingStudyRepository(StudyRecordRepository):
    def touch_record(self, course_id, book_id, section_id, mode):
        raise StudyRecordRepositoryError(
            "private sqlite detail: /tmp/never-expose-study.sqlite3"
        )


class StudyRecordApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repository = StudyRecordRepository(
            Path(self.temp.name) / "book-app.sqlite3"
        )
        app.dependency_overrides[get_service] = lambda: REAL_SERVICE
        app.dependency_overrides[get_study_repository] = lambda: self.repository
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.client.close()

    @staticmethod
    def touch_path(
        *,
        course_id: str = "functional_analysis_course",
        section_id: str = "ch01_s01",
        mode: str = "learn",
    ) -> str:
        return (
            f"/api/courses/{course_id}/sections/{section_id}"
            f"/study/{mode}/touch"
        )

    @staticmethod
    def complete_path(
        *,
        course_id: str = "functional_analysis_course",
        section_id: str = "ch01_s01",
        mode: str = "learn",
    ) -> str:
        return (
            f"/api/courses/{course_id}/sections/{section_id}"
            f"/study/{mode}/complete"
        )

    def test_touch_returns_product_facing_in_progress_record(self) -> None:
        response = self.client.post(self.touch_path())

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["course_id"], "functional_analysis_course")
        self.assertEqual(
            payload["book_id"], "stein_shakarchi_functional_analysis_2011"
        )
        self.assertEqual(payload["section_id"], "ch01_s01")
        self.assertEqual(payload["mode"], "learn")
        self.assertEqual(payload["status"], "in_progress")
        self.assertEqual(payload["progress"], 0)
        self.assertIsNone(payload["completed_at"])
        self.assertEqual(
            set(payload),
            {
                "course_id",
                "book_id",
                "section_id",
                "mode",
                "status",
                "progress",
                "started_at",
                "last_studied_at",
                "completed_at",
                "updated_at",
            },
        )
        for internal_field in (
            "profile_id",
            "sync_status",
            "deleted_at",
            "study_record_id",
            "revision",
        ):
            self.assertNotIn(internal_field, payload)

    def test_complete_returns_completed_record(self) -> None:
        response = self.client.post(self.complete_path(mode="practice"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode"], "practice")
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["progress"], 100)
        self.assertIsNotNone(payload["completed_at"])

    def test_course_list_returns_only_product_records(self) -> None:
        self.client.post(self.touch_path(mode="preview"))
        self.client.post(self.complete_path(mode="learn"))

        response = self.client.get(
            "/api/courses/functional_analysis_course/study-records"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["course_id"], "functional_analysis_course")
        self.assertEqual(len(payload["records"]), 2)
        self.assertEqual(
            {row["mode"] for row in payload["records"]}, {"preview", "learn"}
        )
        self.assertTrue(
            all("profile_id" not in row for row in payload["records"])
        )

    def test_recent_is_null_on_fresh_store_then_latest_record(self) -> None:
        fresh = self.client.get("/api/study/recent")
        self.assertEqual(fresh.status_code, 200)
        self.assertIsNone(fresh.json())

        self.client.post(self.touch_path(section_id="ch01_s01", mode="preview"))
        self.client.post(self.touch_path(section_id="ch01_s02", mode="review"))

        recent = self.client.get("/api/study/recent")
        self.assertEqual(recent.status_code, 200)
        self.assertEqual(recent.json()["section_id"], "ch01_s02")
        self.assertEqual(recent.json()["mode"], "review")

    def test_invalid_mode_is_stable_400(self) -> None:
        response = self.client.post(self.touch_path(mode="watch"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"error": {"code": "invalid_mode", "message": "学习模式无效"}},
        )
        self.assertIsNone(self.repository.get_recent_record())

    def test_unknown_course_and_section_are_stable_404_without_mutation(self) -> None:
        unknown_course = self.client.post(self.touch_path(course_id="missing"))
        self.assertEqual(unknown_course.status_code, 404)
        self.assertEqual(
            unknown_course.json(),
            {"error": {"code": "course_not_found", "message": "课程不存在"}},
        )

        unknown_section = self.client.post(self.touch_path(section_id="missing"))
        self.assertEqual(unknown_section.status_code, 404)
        self.assertEqual(
            unknown_section.json(),
            {"error": {"code": "section_not_found", "message": "小节不存在"}},
        )
        self.assertIsNone(self.repository.get_recent_record())

    def test_storage_failure_is_stable_503_without_detail_leak(self) -> None:
        failing = _FailingStudyRepository(
            Path(self.temp.name) / "failing.sqlite3"
        )
        app.dependency_overrides[get_study_repository] = lambda: failing

        response = self.client.post(self.touch_path())

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "study_store_unavailable",
                    "message": "学习进度暂无法保存",
                }
            },
        )
        self.assertNotIn("sqlite", response.text.casefold())
        self.assertNotIn("/tmp/", response.text)

    def test_post_routes_have_no_browser_identity_body_contract(self) -> None:
        response = self.client.post(
            self.touch_path(),
            json={
                "profile_id": "browser-controlled-profile",
                "book_id": "browser-controlled-book",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            payload["book_id"], "stein_shakarchi_functional_analysis_2011"
        )
        self.assertNotIn("profile_id", payload)
        persisted = self.repository.get_recent_record()
        self.assertIsNotNone(persisted)
        self.assertNotEqual(persisted.profile_id, "browser-controlled-profile")
        self.assertNotEqual(persisted.book_id, "browser-controlled-book")

    def test_manual_export_import_merges_newer_records(self) -> None:
        self.client.post(self.complete_path(mode="learn"))
        exported = self.client.get("/api/study/export")
        self.assertEqual(exported.status_code, 200)
        payload = exported.json()
        self.assertEqual(payload["schema_version"], "book_study_sync_v1")
        self.assertEqual(len(payload["records"]), 1)
        self.assertNotIn("profile_id", payload["records"][0])

        destination = StudyRecordRepository(Path(self.temp.name) / "destination.sqlite3")
        app.dependency_overrides[get_study_repository] = lambda: destination
        imported = self.client.post("/api/study/import", json=payload)
        self.assertEqual(imported.status_code, 200)
        self.assertEqual(imported.json()["imported_count"], 1)
        self.assertEqual(destination.get_recent_record().status, "completed")

        repeated = self.client.post("/api/study/import", json=payload)
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(repeated.json()["imported_count"], 0)

    def test_manual_import_rejects_invalid_package_without_mutation(self) -> None:
        response = self.client.post("/api/study/import", json={"schema_version": "wrong", "records": []})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_study_sync")
        self.assertIsNone(self.repository.get_recent_record())


if __name__ == "__main__":
    unittest.main()
