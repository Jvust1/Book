from __future__ import annotations

import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.errors import AppUnavailableError
from app.api.main import app, get_service
from app.api.service import BookAppService


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_SERVICE = BookAppService(REPO_ROOT)


class BookAppApiTests(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides[get_service] = lambda: REAL_SERVICE
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.client.close()

    def test_health_is_available_without_textbook_projection(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_cors_allows_only_local_vite_origins(self) -> None:
        for origin in ("http://127.0.0.1:5173", "http://localhost:5173"):
            with self.subTest(origin=origin):
                response = self.client.get("/api/health", headers={"Origin": origin})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers.get("access-control-allow-origin"), origin)

        response = self.client.get(
            "/api/health",
            headers={"Origin": "https://example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_library_and_course_return_real_audited_navigation(self) -> None:
        library_response = self.client.get("/api/library")
        self.assertEqual(library_response.status_code, 200)
        library = library_response.json()
        self.assertEqual(len(library["courses"]), 1)
        self.assertEqual(
            library["courses"][0]["name_zh"],
            "泛函分析：分析学进一步专题导论",
        )
        self.assertEqual(library["courses"][0]["chapter_count"], 8)
        self.assertEqual(library["courses"][0]["section_count"], 132)

        course_response = self.client.get("/api/courses/functional_analysis_course")
        self.assertEqual(course_response.status_code, 200)
        course = course_response.json()
        self.assertEqual(len(course["chapters"]), 8)
        self.assertEqual(course["section_count"], 132)

    def test_chapter_and_section_routes_open_real_data(self) -> None:
        chapter_response = self.client.get(
            "/api/courses/functional_analysis_course/chapters/chapter_01"
        )
        self.assertEqual(chapter_response.status_code, 200)
        self.assertEqual(chapter_response.json()["chapter"]["chapter_id"], "chapter_01")
        self.assertGreater(len(chapter_response.json()["sections"]), 0)

        section_response = self.client.get(
            "/api/courses/functional_analysis_course/sections/ch01_s01"
        )
        self.assertEqual(section_response.status_code, 200)
        section = section_response.json()
        self.assertEqual(section["course_id"], "functional_analysis_course")
        self.assertEqual(section["book_id"], "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(section["section"]["section_id"], "ch01_s01")

    def test_four_learning_routes_preserve_runtime_identity(self) -> None:
        for mode in ("preview", "learn", "review", "practice"):
            with self.subTest(mode=mode):
                response = self.client.get(
                    f"/api/courses/functional_analysis_course/sections/ch01_s01/{mode}"
                )
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["mode"], mode)
                self.assertEqual(payload["course_id"], "functional_analysis_course")
                self.assertEqual(
                    payload["book_id"],
                    "stein_shakarchi_functional_analysis_2011",
                )
                self.assertEqual(payload["section_id"], "ch01_s01")

    def test_search_route_returns_real_canonical_results(self) -> None:
        response = self.client.get(
            "/api/courses/functional_analysis_course/search",
            params={"q": "Hölder", "limit": 10},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["course_id"], "functional_analysis_course")
        self.assertEqual(payload["book_id"], "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(payload["query"], "Hölder")
        self.assertGreater(payload["result_count"], 0)
        self.assertEqual(payload["result_count"], len(payload["results"]))
        self.assertEqual(payload["results"][0]["source_kind"], "object")
        self.assertEqual(payload["results"][0]["object_type"], "theorem")

    def test_search_route_supports_chinese_and_normal_empty_results(self) -> None:
        chinese = self.client.get(
            "/api/courses/functional_analysis_course/search",
            params={"q": "巴拿赫空间"},
        )
        self.assertEqual(chinese.status_code, 200)
        self.assertGreater(chinese.json()["result_count"], 0)

        empty = self.client.get(
            "/api/courses/functional_analysis_course/search",
            params={"q": "definitely-no-such-text-92831"},
        )
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json()["result_count"], 0)
        self.assertEqual(empty.json()["results"], [])

    def test_search_invalid_query_is_stable_400(self) -> None:
        for query in ("", "   "):
            with self.subTest(query=query):
                response = self.client.get(
                    "/api/courses/functional_analysis_course/search",
                    params={"q": query},
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json(),
                    {"error": {"code": "invalid_search_query", "message": "搜索条件无效"}},
                )

        out_of_range = self.client.get(
            "/api/courses/functional_analysis_course/search",
            params={"q": "Banach", "limit": 101},
        )
        self.assertEqual(out_of_range.status_code, 400)
        self.assertEqual(out_of_range.json()["error"]["code"], "invalid_search_query")

    def test_search_unknown_course_is_stable_404(self) -> None:
        response = self.client.get("/api/courses/missing/search", params={"q": "Banach"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"error": {"code": "course_not_found", "message": "课程不存在"}},
        )

    def test_search_unavailable_is_stable_503_without_detail_leak(self) -> None:
        def unavailable_service() -> BookAppService:
            raise AppUnavailableError(
                code="search_unavailable",
                user_message="教材搜索暂不可用",
                detail="search internals must not leak",
            )

        app.dependency_overrides[get_service] = unavailable_service
        response = self.client.get(
            "/api/courses/functional_analysis_course/search",
            params={"q": "Banach"},
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"error": {"code": "search_unavailable", "message": "教材搜索暂不可用"}},
        )
        self.assertNotIn("search internals", response.text)
        self.assertNotIn("Traceback", response.text)

    def test_not_found_errors_have_stable_chinese_json_without_tracebacks(self) -> None:
        response = self.client.get("/api/courses/missing")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"error": {"code": "course_not_found", "message": "课程不存在"}},
        )
        self.assertNotIn("Traceback", response.text)

        source_response = self.client.get(
            "/api/courses/functional_analysis_course/sources/object/missing"
        )
        self.assertEqual(source_response.status_code, 404)
        self.assertEqual(
            source_response.json(),
            {"error": {"code": "source_not_found", "message": "教材来源不存在"}},
        )
        self.assertNotIn("Traceback", source_response.text)

    def test_service_initialization_failure_maps_to_503_without_import_crash(self) -> None:
        def unavailable_service() -> BookAppService:
            raise AppUnavailableError(
                code="library_unavailable",
                user_message="教材库暂不可用",
                detail="fixture failure that must not leak",
            )

        app.dependency_overrides[get_service] = unavailable_service
        response = self.client.get("/api/library")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"error": {"code": "library_unavailable", "message": "教材库暂不可用"}},
        )
        self.assertNotIn("fixture failure", response.text)
        self.assertNotIn("Traceback", response.text)


if __name__ == "__main__":
    unittest.main()
