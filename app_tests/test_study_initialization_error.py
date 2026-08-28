from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.api.main import app, get_study_repository
from app.study import StudyRecordRepositoryError


class StudyRecordInitializationErrorTests(unittest.TestCase):
    def setUp(self) -> None:
        def fail_repository_initialization():
            raise StudyRecordRepositoryError(
                "private sqlite detail: /tmp/never-expose-init.sqlite3"
            )

        app.dependency_overrides[get_study_repository] = fail_repository_initialization
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.client.close()

    def test_repository_dependency_failure_is_stable_503_without_detail_leak(self) -> None:
        response = self.client.get("/api/study/recent")

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


if __name__ == "__main__":
    unittest.main()
