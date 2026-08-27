"""HTTP contract tests for the Phase 1F textbook QA endpoint."""

from __future__ import annotations

import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from runtime import DeterministicFakeModelProvider, ModelResponse

from app.api.main import app, get_service
from app.api.service import BookAppService


REPO_ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = "functional_analysis_course"
SUFFICIENT_QA_QUESTION = "1/p + 1/q = 1"


class InvalidCitationProvider:
    def answer(self, request):
        del request
        return ModelResponse.from_mapping(
            {
                "answer": "非法引用回答",
                "evidence_ids": ["E999"],
                "insufficient_evidence": False,
                "answer_style": "brief",
            }
        )


class BookAppQAApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_service = BookAppService(
            REPO_ROOT,
            qa_provider=DeterministicFakeModelProvider(),
        )
        app.dependency_overrides[get_service] = lambda: self.fake_service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.client.close()

    def post(self, payload):
        return self.client.post(f"/api/courses/{COURSE_ID}/qa", json=payload)

    def test_valid_question_returns_generated_answer_with_canonical_citation(self) -> None:
        response = self.post({"question": SUFFICIENT_QA_QUESTION})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["course_id"], COURSE_ID)
        self.assertEqual(body["answer_kind"], "generated")
        self.assertEqual(body["evidence_status"], "sufficient")
        self.assertTrue(body["citations"])
        self.assertEqual(body["citations"][0]["source_kind"], "object")
        self.assertTrue(body["citations"][0]["source_id"])

    def test_insufficient_evidence_is_normal_200_system_notice(self) -> None:
        response = self.post({"question": "definitely-no-such-topic-92831"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["answer_kind"], "system_notice")
        self.assertEqual(body["evidence_status"], "insufficient_evidence")
        self.assertEqual(body["citations"], [])

    def test_blank_missing_and_malformed_json_are_stable_400_not_422(self) -> None:
        blank = self.post({"question": "   "})
        self.assertEqual(blank.status_code, 400)
        self.assertEqual(
            blank.json(),
            {"error": {"code": "invalid_qa_question", "message": "提问内容无效"}},
        )

        missing = self.client.post(f"/api/courses/{COURSE_ID}/qa", json={})
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(missing.json()["error"]["code"], "invalid_qa_question")

        malformed = self.client.post(
            f"/api/courses/{COURSE_ID}/qa",
            content="{broken",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(malformed.status_code, 400)
        self.assertEqual(malformed.json()["error"]["code"], "invalid_qa_question")
        self.assertNotIn("Traceback", malformed.text)

    def test_unknown_course_is_stable_404(self) -> None:
        response = self.client.post(
            "/api/courses/missing/qa",
            json={"question": "什么是巴拿赫空间？"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"error": {"code": "course_not_found", "message": "课程不存在"}},
        )

    def test_default_unavailable_provider_is_stable_503(self) -> None:
        app.dependency_overrides[get_service] = lambda: BookAppService(REPO_ROOT)

        response = self.post({"question": SUFFICIENT_QA_QUESTION})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"error": {"code": "qa_provider_unavailable", "message": "教材问答模型暂不可用"}},
        )

    def test_invalid_provider_response_is_stable_502_without_detail_leak(self) -> None:
        app.dependency_overrides[get_service] = lambda: BookAppService(
            REPO_ROOT,
            qa_provider=InvalidCitationProvider(),
        )

        response = self.post({"question": SUFFICIENT_QA_QUESTION})

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(),
            {"error": {"code": "qa_provider_invalid_response", "message": "教材问答结果校验失败"}},
        )
        self.assertNotIn("E999", response.text)
        self.assertNotIn("Traceback", response.text)

    def test_local_cors_preflight_allows_post_but_external_origin_remains_blocked(self) -> None:
        headers = {
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
        local = self.client.options(f"/api/courses/{COURSE_ID}/qa", headers=headers)
        self.assertEqual(local.status_code, 200)
        self.assertEqual(local.headers.get("access-control-allow-origin"), headers["Origin"])
        self.assertIn("POST", local.headers.get("access-control-allow-methods", ""))

        external_headers = {**headers, "Origin": "https://example.com"}
        external = self.client.options(
            f"/api/courses/{COURSE_ID}/qa",
            headers=external_headers,
        )
        self.assertNotEqual(external.headers.get("access-control-allow-origin"), "https://example.com")


if __name__ == "__main__":
    unittest.main()
