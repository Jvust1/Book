"""HTTP contract tests for the Phase 1F v2 textbook QA endpoint."""

from __future__ import annotations

import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from runtime import (
    DeterministicFakeModelProvider,
    ModelProviderUnavailableError,
    ModelResponse,
)

from app.api.errors import AppUnavailableError
from app.api.main import app, default_service, get_service
from app.api.service import BookAppService


REPO_ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = "functional_analysis_course"
SUFFICIENT_QA_QUESTION = "1/p + 1/q = 1"
INSUFFICIENT_MESSAGE = "根据当前教材中检索到的内容，暂时无法可靠回答这个问题。"
SECRET_KEY = "secret-api-key-must-not-leak"
SECRET_BASE_URL = "https://secret-provider.example/v1"


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


class UpstreamUnavailableProvider:
    def answer(self, request):
        del request
        raise ModelProviderUnavailableError(
            f"upstream failed at {SECRET_BASE_URL} with key {SECRET_KEY}"
        )


class QAEvidenceUnavailableService:
    def ask(self, course_id, question, *, section_id=None, history=()):
        del course_id, question, section_id, history
        raise AppUnavailableError(
            code="qa_unavailable",
            user_message="教材问答暂不可用",
            detail=f"broken evidence path {SECRET_BASE_URL} {SECRET_KEY}",
        )


class BookAppQAApiTests(unittest.TestCase):
    def setUp(self) -> None:
        default_service.cache_clear()
        self.fake_service = BookAppService(
            REPO_ROOT,
            qa_provider=DeterministicFakeModelProvider(),
        )
        app.dependency_overrides[get_service] = lambda: self.fake_service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        default_service.cache_clear()
        self.client.close()

    def post(self, payload):
        return self.client.post(f"/api/courses/{COURSE_ID}/qa", json=payload)

    def test_scoped_history_returns_exact_v2_response_and_canonical_citation(self) -> None:
        response = self.post(
            {
                "question": SUFFICIENT_QA_QUESTION,
                "section_id": "ch01_s01",
                "history": [
                    {"role": "user", "content": "什么是共轭指数？"},
                    {"role": "assistant", "content": "上一轮回答只用于理解追问。"},
                ],
            }
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            set(body),
            {
                "course_id",
                "book_id",
                "question",
                "answer",
                "answer_kind",
                "answer_style",
                "scope_requested",
                "scope_used",
                "insufficient_evidence",
                "message",
                "citations",
            },
        )
        self.assertEqual(body["course_id"], COURSE_ID)
        self.assertEqual(body["answer_kind"], "generated")
        self.assertEqual(body["answer_style"], "brief")
        self.assertEqual(body["scope_requested"], "section_then_book")
        self.assertIn(body["scope_used"], ("section", "book"))
        self.assertFalse(body["insufficient_evidence"])
        self.assertIsNone(body["message"])
        self.assertTrue(body["citations"])
        citation = body["citations"][0]
        self.assertEqual(
            set(citation),
            {
                "evidence_id",
                "source_kind",
                "source_id",
                "chapter_id",
                "section_id",
                "object_type",
                "type_zh",
                "number",
                "title_zh",
                "title_en",
                "printed_page",
                "pdf_page",
                "source_anchor",
            },
        )
        self.assertEqual(citation["source_kind"], "object")
        self.assertTrue(citation["source_id"])
        self.assertIsNotNone(citation["chapter_id"])
        self.assertIsNotNone(citation["section_id"])
        self.assertTrue(citation["type_zh"])

    def test_insufficient_evidence_is_normal_200_v2_system_notice(self) -> None:
        response = self.post({"question": "definitely-no-such-topic-92831"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["answer_kind"], "system_notice")
        self.assertIsNone(body["answer"])
        self.assertIsNone(body["answer_style"])
        self.assertEqual(body["scope_requested"], "book")
        self.assertEqual(body["scope_used"], "book")
        self.assertTrue(body["insufficient_evidence"])
        self.assertEqual(body["message"], INSUFFICIENT_MESSAGE)
        self.assertEqual(body["citations"], [])

    def test_blank_missing_malformed_json_and_malformed_history_are_stable_400(self) -> None:
        cases = [
            self.post([["question", SUFFICIENT_QA_QUESTION]]),
            self.post({"question": 42}),
            self.post({"question": SUFFICIENT_QA_QUESTION, "section_id": 42}),
            self.post({
                "question": SUFFICIENT_QA_QUESTION,
                "history": [[["role", "user"], ["content", "text"]]],
            }),
            self.post({"question": "   "}),
            self.client.post(f"/api/courses/{COURSE_ID}/qa", json={}),
            self.post(
                {
                    "question": SUFFICIENT_QA_QUESTION,
                    "history": [{"role": "system", "content": "bad role"}],
                }
            ),
            self.post(
                {
                    "question": SUFFICIENT_QA_QUESTION,
                    "history": [{"role": "user", "content": 42}],
                }
            ),
        ]
        malformed = self.client.post(
            f"/api/courses/{COURSE_ID}/qa",
            content="{broken",
            headers={"Content-Type": "application/json"},
        )
        cases.append(malformed)

        for response in cases:
            with self.subTest(response=response):
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json(),
                    {"error": {"code": "invalid_qa_question", "message": "提问内容无效"}},
                )
                self.assertNotIn("Traceback", response.text)

    def test_unknown_course_and_section_are_stable_404(self) -> None:
        course = self.client.post(
            "/api/courses/missing/qa",
            json={"question": "什么是巴拿赫空间？"},
        )
        self.assertEqual(course.status_code, 404)
        self.assertEqual(
            course.json(),
            {"error": {"code": "course_not_found", "message": "课程不存在"}},
        )

        section = self.post(
            {"question": SUFFICIENT_QA_QUESTION, "section_id": "missing_section"}
        )
        self.assertEqual(section.status_code, 404)
        self.assertEqual(
            section.json(),
            {"error": {"code": "section_not_found", "message": "小节不存在"}},
        )

    def test_unconfigured_provider_is_stable_503(self) -> None:
        app.dependency_overrides[get_service] = lambda: BookAppService(REPO_ROOT)

        response = self.post({"question": SUFFICIENT_QA_QUESTION})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"error": {"code": "qa_provider_unconfigured", "message": "教材问答模型未配置"}},
        )

    def test_unavailable_provider_is_stable_503_without_secret_leak(self) -> None:
        app.dependency_overrides[get_service] = lambda: BookAppService(
            REPO_ROOT,
            qa_provider=UpstreamUnavailableProvider(),
        )

        response = self.post({"question": SUFFICIENT_QA_QUESTION})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"error": {"code": "qa_provider_unavailable", "message": "教材问答模型暂不可用"}},
        )
        self.assertNotIn(SECRET_KEY, response.text)
        self.assertNotIn(SECRET_BASE_URL, response.text)

    def test_qa_evidence_unavailable_is_stable_503_without_secret_leak(self) -> None:
        app.dependency_overrides[get_service] = lambda: QAEvidenceUnavailableService()

        response = self.post({"question": SUFFICIENT_QA_QUESTION})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"error": {"code": "qa_unavailable", "message": "教材问答暂不可用"}},
        )
        self.assertNotIn(SECRET_KEY, response.text)
        self.assertNotIn(SECRET_BASE_URL, response.text)

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
