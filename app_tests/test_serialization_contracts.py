from __future__ import annotations

import unittest

from app.api.models import (
    QACitationItem,
    QAResponse,
    SearchResponse,
    SearchResultItem,
    SourceResponse,
)


FORBIDDEN_INTERNAL_KEYS = {
    "book_version_id",
    "logical_book_id",
    "provenance",
    "identity",
    "retriever_id",
}
SEARCH_RESPONSE_KEYS = {
    "course_id",
    "book_id",
    "query",
    "result_count",
    "results",
}
SEARCH_RESULT_KEYS = {
    "rank",
    "score",
    "source_kind",
    "source_id",
    "object_type",
    "number",
    "title_zh",
    "title_en",
    "formula",
    "pdf_page",
    "printed_page",
    "source_anchor",
    "snippet",
}
SOURCE_KEYS = {
    "course_id",
    "book_id",
    "section_id",
    "kind",
    "source_id",
    "type",
    "type_zh",
    "number",
    "title_zh",
    "title_en",
    "content_zh",
    "formula",
    "printed_page",
    "pdf_page",
    "source_anchor",
    "source_batch",
    "translation_available",
    "context_before",
    "context_after",
}
QA_RESPONSE_KEYS = {
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
}
QA_CITATION_KEYS = {
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
}


class SerializationContractTests(unittest.TestCase):
    def test_internal_provenance_keys_are_forbidden_from_all_frozen_dtos(self) -> None:
        for keys in (
            SEARCH_RESPONSE_KEYS,
            SEARCH_RESULT_KEYS,
            SOURCE_KEYS,
            QA_RESPONSE_KEYS,
            QA_CITATION_KEYS,
        ):
            self.assertTrue(FORBIDDEN_INTERNAL_KEYS.isdisjoint(keys))

    def test_search_response_and_result_keys_are_frozen(self) -> None:
        item = SearchResultItem(
            rank=1,
            score=7,
            source_kind="object",
            source_id="thm_1",
            object_type="theorem",
            number="1.1",
            title_zh="定理",
            title_en="Theorem",
            formula="x=x",
            pdf_page=20,
            printed_page=1,
            source_anchor="anchor",
            snippet="snippet",
        )
        response = SearchResponse(
            course_id="course",
            book_id="book",
            query="query",
            result_count=1,
            results=[item],
        )
        dumped = response.model_dump()
        self.assertEqual(set(dumped.keys()), SEARCH_RESPONSE_KEYS)
        self.assertEqual(set(dumped["results"][0].keys()), SEARCH_RESULT_KEYS)

    def test_source_response_keys_are_frozen(self) -> None:
        source = SourceResponse(
            course_id="course",
            book_id="book",
            section_id="section",
            kind="object",
            source_id="thm_1",
            type="theorem",
            type_zh="定理",
            number="1.1",
            title_zh="定理",
            title_en="Theorem",
            content_zh="内容",
            formula="x=x",
            printed_page=1,
            pdf_page=20,
            source_anchor="anchor",
            source_batch="chunk_001",
            translation_available=False,
            context_before=[],
            context_after=[],
        )
        self.assertEqual(set(source.model_dump().keys()), SOURCE_KEYS)

    def test_qa_response_and_citation_keys_are_frozen(self) -> None:
        citation = QACitationItem(
            evidence_id="ev_1",
            source_kind="object",
            source_id="thm_1",
            chapter_id="ch01",
            section_id="ch01_s01",
            object_type="theorem",
            type_zh="定理",
            number="1.1",
            title_zh="定理",
            title_en="Theorem",
            printed_page=1,
            pdf_page=20,
            source_anchor="anchor",
        )
        response = QAResponse(
            course_id="course",
            book_id="book",
            question="问题",
            answer="回答",
            answer_kind="generated",
            answer_style="brief",
            scope_requested="book",
            scope_used="book",
            insufficient_evidence=False,
            message=None,
            citations=[citation],
        )
        dumped = response.model_dump()
        self.assertEqual(set(dumped.keys()), QA_RESPONSE_KEYS)
        self.assertEqual(set(dumped["citations"][0].keys()), QA_CITATION_KEYS)


if __name__ == "__main__":
    unittest.main()
