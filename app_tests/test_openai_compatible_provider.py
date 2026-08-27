"""Contract tests for the server-side OpenAI-compatible QA adapter."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import httpx

from runtime import (
    EvidenceItem,
    EvidencePack,
    ModelProviderInvalidResponseError,
    ModelProviderUnavailableError,
    ModelRequest,
    QAHistoryMessage,
)
from app.api.openai_compatible_provider import OpenAICompatibleModelProvider


COURSE_ID = "functional_analysis_course"
BOOK_ID = "stein_shakarchi_functional_analysis_2011"
API_KEY = "super-secret-test-key"
BASE_URL = "https://model.example.test/v1/"
MODEL = "example-model"


def model_request() -> ModelRequest:
    evidence = EvidenceItem(
        evidence_id="E1",
        source_kind="object",
        source_id="def_dual_exponents",
        object_type="definition",
        title_zh="共轭指数",
        title_en="Conjugate exponents",
        number=None,
        formula="1/p + 1/q = 1",
        content_zh="若 1 < p < ∞，则 q 由 1/p + 1/q = 1 定义。",
        source_anchor="anchor_dual_exponents",
        pdf_page=23,
        printed_page=4,
        search_score=1000,
        course_id=COURSE_ID,
        book_id=BOOK_ID,
        chapter_id="ch01",
        section_id="ch01_s01",
        type_zh="定义",
    )
    pack = EvidencePack(
        course_id=COURSE_ID,
        book_id=BOOK_ID,
        question="p 和 q 满足什么关系？",
        evidence=(evidence,),
        scope_requested="section_then_book",
        scope_used="section",
    )
    return ModelRequest.from_pack(
        pack,
        section_id="ch01_s01",
        history=(
            QAHistoryMessage(role="user", content="什么是共轭指数？"),
            QAHistoryMessage(role="assistant", content="前一轮已验证回答，仅用于理解指代。"),
        ),
    )


def upstream_content(
    *,
    answer: str = "教材回答",
    evidence_ids: list[str] | None = None,
    insufficient_evidence: bool = False,
    answer_style: str = "brief",
) -> str:
    return json.dumps(
        {
            "answer": answer,
            "evidence_ids": evidence_ids if evidence_ids is not None else ["E1"],
            "insufficient_evidence": insufficient_evidence,
            "answer_style": answer_style,
        },
        ensure_ascii=False,
    )


def upstream_response(content: str, *, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code,
        json={"choices": [{"message": {"content": content}}]},
    )


class OpenAICompatibleModelProviderTests(unittest.TestCase):
    def make_provider(self, handler, *, timeout_seconds: float = 12.5):
        transport = httpx.MockTransport(handler)
        client = httpx.Client(transport=transport)
        patcher = patch(
            "app.api.openai_compatible_provider.httpx.Client",
            return_value=client,
        )
        mocked_client = patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(client.close)
        provider = OpenAICompatibleModelProvider(
            base_url=BASE_URL,
            api_key=API_KEY,
            model=MODEL,
            timeout_seconds=timeout_seconds,
        )
        return provider, mocked_client

    def test_posts_bounded_textbook_only_request_and_parses_strict_response(self) -> None:
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return upstream_response(upstream_content())

        provider, mocked_client = self.make_provider(handler)
        result = provider.answer(model_request())

        self.assertEqual(result.answer, "教材回答")
        self.assertEqual(result.evidence_ids, ("E1",))
        self.assertFalse(result.insufficient_evidence)
        self.assertEqual(result.answer_style, "brief")
        self.assertEqual(len(captured), 1)

        outgoing = captured[0]
        self.assertEqual(str(outgoing.url), "https://model.example.test/v1/chat/completions")
        self.assertEqual(outgoing.headers["authorization"], f"Bearer {API_KEY}")
        self.assertEqual(outgoing.headers["content-type"], "application/json")

        body = json.loads(outgoing.content.decode("utf-8"))
        self.assertEqual(body["model"], MODEL)
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertEqual([row["role"] for row in body["messages"]], ["system", "user"])
        self.assertIn("只能依据", body["messages"][0]["content"])
        self.assertIn("evidence_id", body["messages"][0]["content"])

        user_payload = json.loads(body["messages"][1]["content"])
        self.assertEqual(user_payload["question"], "p 和 q 满足什么关系？")
        self.assertEqual(user_payload["section_id"], "ch01_s01")
        self.assertEqual(len(user_payload["history"]), 2)
        self.assertEqual(user_payload["evidence"][0]["evidence_id"], "E1")
        self.assertEqual(user_payload["evidence"][0]["formula"], "1/p + 1/q = 1")
        self.assertEqual(
            user_payload["allowed_answer_styles"],
            ["brief", "explain", "compare", "proof"],
        )
        serialized = json.dumps(user_payload, ensure_ascii=False)
        self.assertNotIn(API_KEY, serialized)
        self.assertNotIn("repository_root", serialized)
        self.assertNotIn("browser_state", serialized)
        self.assertNotIn("raw_response", serialized)
        self.assertNotIn("prompt", user_payload)

        mocked_client.assert_called_once()
        self.assertEqual(mocked_client.call_args.kwargs["timeout"], 12.5)

    def test_invalid_json_or_schema_gets_exactly_one_retry(self) -> None:
        scenarios = [
            "not-json",
            json.dumps(
                {
                    "answer": "missing evidence ids",
                    "insufficient_evidence": False,
                    "answer_style": "brief",
                }
            ),
        ]
        for invalid_content in scenarios:
            with self.subTest(invalid_content=invalid_content):
                calls = 0

                def handler(request: httpx.Request) -> httpx.Response:
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        return upstream_response(invalid_content)
                    return upstream_response(upstream_content(answer="第二次合法回答"))

                provider, _ = self.make_provider(handler)
                result = provider.answer(model_request())

                self.assertEqual(calls, 2)
                self.assertEqual(result.answer, "第二次合法回答")

    def test_second_invalid_response_fails_closed_without_raw_or_key_leak(self) -> None:
        calls = 0
        raw_marker = "RAW-UPSTREAM-SECRET-MARKER"

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return upstream_response(raw_marker)

        provider, _ = self.make_provider(handler)

        with self.assertRaises(ModelProviderInvalidResponseError) as ctx:
            provider.answer(model_request())

        self.assertEqual(calls, 2)
        public_message = str(ctx.exception)
        self.assertNotIn(raw_marker, public_message)
        self.assertNotIn(API_KEY, public_message)

    def test_transport_timeout_and_http_error_map_to_secret_safe_unavailable(self) -> None:
        def timeout_handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout body must not escape", request=request)

        timeout_provider, _ = self.make_provider(timeout_handler)
        with self.assertRaises(ModelProviderUnavailableError) as timeout_ctx:
            timeout_provider.answer(model_request())
        self.assertNotIn(API_KEY, str(timeout_ctx.exception))
        self.assertNotIn("timeout body must not escape", str(timeout_ctx.exception))

        raw_marker = "UPSTREAM-HTTP-BODY-MUST-NOT-ESCAPE"

        def http_error_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text=raw_marker, request=request)

        http_provider, _ = self.make_provider(http_error_handler)
        with self.assertRaises(ModelProviderUnavailableError) as http_ctx:
            http_provider.answer(model_request())
        self.assertNotIn(API_KEY, str(http_ctx.exception))
        self.assertNotIn(raw_marker, str(http_ctx.exception))


if __name__ == "__main__":
    unittest.main()
