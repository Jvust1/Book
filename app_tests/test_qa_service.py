"""BookAppService v2 QA projection and stable-error tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime import (
    CourseRuntime,
    DeterministicFakeModelProvider,
    ModelProviderUnavailableError,
    ModelResponse,
    QAHistoryMessage,
)
from runtime.retrieval import RetrievalEngine

from app.api.errors import (
    AppNotFoundError,
    AppUnavailableError,
    InvalidQAQuestionError,
    QAProviderInvalidResponseError,
)
from app.api.service import BookAppService
from tests.runtime_fixture_factory import (
    dump_json,
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = "functional_analysis_course"
BOOK_ID = "stein_shakarchi_functional_analysis_2011"
SUFFICIENT_QA_QUESTION = "1/p + 1/q = 1"
INSUFFICIENT_MESSAGE = "根据当前教材中检索到的内容，暂时无法可靠回答这个问题。"


class InvalidCitationProvider:
    def answer(self, request):
        del request
        return ModelResponse.from_mapping(
            {
                "answer": "非法来源回答",
                "evidence_ids": ["E999"],
                "insufficient_evidence": False,
                "answer_style": "brief",
            }
        )


class UpstreamUnavailableProvider:
    def answer(self, request):
        del request
        raise ModelProviderUnavailableError(
            "upstream https://secret-provider.example/v1 failed with key secret-key"
        )


class SpyRetrievalFactory:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, course: CourseRuntime) -> RetrievalEngine:
        self.calls.append(course.course_id)
        return RetrievalEngine.exact(course)


class BookAppQAServiceTests(unittest.TestCase):
    def test_same_retrieval_factory_serves_search_and_qa(self) -> None:
        spy = SpyRetrievalFactory()
        service = BookAppService(
            REPO_ROOT,
            qa_provider=DeterministicFakeModelProvider(),
            retrieval_factory=spy,
        )

        search = service.search(COURSE_ID, "Hölder")
        after_search = len(spy.calls)
        qa = service.ask(COURSE_ID, SUFFICIENT_QA_QUESTION)

        self.assertGreater(search.result_count, 0)
        self.assertEqual(after_search, 1)
        self.assertGreater(len(spy.calls), after_search)
        self.assertTrue(all(course_id == COURSE_ID for course_id in spy.calls))
        self.assertEqual(qa.answer_kind, "generated")
        self.assertTrue(qa.citations)

    def test_scoped_history_projects_v2_response_and_canonical_citations(self) -> None:
        service = BookAppService(
            REPO_ROOT,
            qa_provider=DeterministicFakeModelProvider(),
        )

        payload = service.ask(
            COURSE_ID,
            SUFFICIENT_QA_QUESTION,
            section_id="ch01_s01",
            history=(
                QAHistoryMessage(role="user", content="什么是共轭指数？"),
                QAHistoryMessage(role="assistant", content="上一轮回答只用于理解追问。"),
            ),
        )

        self.assertEqual(payload.course_id, COURSE_ID)
        self.assertEqual(payload.book_id, BOOK_ID)
        self.assertEqual(payload.question, SUFFICIENT_QA_QUESTION)
        self.assertEqual(payload.answer_kind, "generated")
        self.assertEqual(payload.answer_style, "brief")
        self.assertEqual(payload.scope_requested, "section_then_book")
        self.assertIn(payload.scope_used, ("section", "book"))
        self.assertFalse(payload.insufficient_evidence)
        self.assertIsNone(payload.message)
        self.assertIsInstance(payload.answer, str)
        self.assertTrue(payload.citations)
        first = payload.citations[0]
        self.assertEqual(first.source_kind, "object")
        self.assertTrue(first.source_id)
        self.assertTrue(first.evidence_id.startswith("E"))
        self.assertIsNotNone(first.chapter_id)
        self.assertIsNotNone(first.section_id)
        self.assertTrue(first.type_zh)
        self.assertFalse(hasattr(first, "citation_id"))

    def test_default_service_provider_is_distinctly_unconfigured(self) -> None:
        service = BookAppService(REPO_ROOT)

        with self.assertRaises(AppUnavailableError) as ctx:
            service.ask(COURSE_ID, SUFFICIENT_QA_QUESTION)

        self.assertEqual(ctx.exception.code, "qa_provider_unconfigured")
        self.assertEqual(ctx.exception.user_message, "教材问答模型未配置")

    def test_upstream_provider_failure_is_distinctly_unavailable(self) -> None:
        service = BookAppService(REPO_ROOT, qa_provider=UpstreamUnavailableProvider())

        with self.assertRaises(AppUnavailableError) as ctx:
            service.ask(COURSE_ID, SUFFICIENT_QA_QUESTION)

        self.assertEqual(ctx.exception.code, "qa_provider_unavailable")
        self.assertEqual(ctx.exception.user_message, "教材问答模型暂不可用")

    def test_blank_question_and_malformed_history_map_to_invalid_qa_question(self) -> None:
        service = BookAppService(
            REPO_ROOT,
            qa_provider=DeterministicFakeModelProvider(),
        )

        cases = (
            lambda: service.ask(COURSE_ID, "   "),
            lambda: service.ask(
                COURSE_ID,
                SUFFICIENT_QA_QUESTION,
                history=({"role": "system", "content": "bad role"},),  # type: ignore[arg-type]
            ),
        )
        for call in cases:
            with self.subTest(call=call):
                with self.assertRaises(InvalidQAQuestionError) as ctx:
                    call()
                self.assertEqual(ctx.exception.code, "invalid_qa_question")
                self.assertEqual(ctx.exception.user_message, "提问内容无效")

    def test_unknown_section_maps_to_stable_section_not_found(self) -> None:
        service = BookAppService(
            REPO_ROOT,
            qa_provider=DeterministicFakeModelProvider(),
        )

        with self.assertRaises(AppNotFoundError) as ctx:
            service.ask(
                COURSE_ID,
                SUFFICIENT_QA_QUESTION,
                section_id="missing_section",
            )

        self.assertEqual(ctx.exception.code, "section_not_found")
        self.assertEqual(ctx.exception.user_message, "小节不存在")

    def test_invalid_provider_citation_maps_to_distinct_gateway_error(self) -> None:
        service = BookAppService(REPO_ROOT, qa_provider=InvalidCitationProvider())

        with self.assertRaises(QAProviderInvalidResponseError) as ctx:
            service.ask(COURSE_ID, SUFFICIENT_QA_QUESTION)

        self.assertEqual(ctx.exception.code, "qa_provider_invalid_response")
        self.assertEqual(ctx.exception.user_message, "教材问答结果校验失败")

    def test_insufficient_evidence_is_normal_v2_system_notice(self) -> None:
        service = BookAppService(
            REPO_ROOT,
            qa_provider=DeterministicFakeModelProvider(),
        )

        payload = service.ask(COURSE_ID, "definitely-no-such-topic-92831")

        self.assertEqual(payload.answer_kind, "system_notice")
        self.assertIsNone(payload.answer)
        self.assertIsNone(payload.answer_style)
        self.assertEqual(payload.scope_requested, "book")
        self.assertEqual(payload.scope_used, "book")
        self.assertTrue(payload.insufficient_evidence)
        self.assertEqual(payload.message, INSUFFICIENT_MESSAGE)
        self.assertEqual(payload.citations, [])


class BookAppQAEvidenceUnavailableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        repo = make_repo(Path(self.tempdir.name))
        book_dir = repo / "books" / "fixture-book"
        write_ready_book(
            book_dir,
            book_id="fixture_book",
            objects=[
                {
                    "type": "definition",
                    "id": "def_fixture",
                    "name_zh": "测试定义",
                    "content_zh": "这是可回答的测试定义内容。",
                    "anchor": {"pdf_page": 1, "printed_page": 1},
                }
            ],
            search_records=[
                {
                    "id": "def_fixture",
                    "book_id": "fixture_book",
                    "type": "definition",
                    "name_zh": "测试定义",
                }
            ],
        )
        write_course(
            repo / "courses" / "fixture-course",
            course_id="fixture_course",
            main_book_id="fixture_book",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
        )
        dump_json(
            repo / "library" / "library.json",
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
        self.service = BookAppService(
            repo,
            qa_provider=DeterministicFakeModelProvider(),
        )
        (book_dir / "search_index_v1.jsonl").write_text("{broken\n", encoding="utf-8")

    def test_broken_trusted_evidence_path_maps_to_qa_unavailable(self) -> None:
        with self.assertRaises(AppUnavailableError) as ctx:
            self.service.ask("fixture_course", "测试定义是什么？")

        self.assertEqual(ctx.exception.code, "qa_unavailable")
        self.assertEqual(ctx.exception.user_message, "教材问答暂不可用")


if __name__ == "__main__":
    unittest.main()
