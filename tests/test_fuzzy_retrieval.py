from runtime.book_runtime import RuntimeAnchor, RuntimeObject
from runtime.retrieval import FuzzyObjectRetriever, RetrievalRequest


class FakeIdentity:
    pass


class FakeBook:
    book_id = "book"

    def __init__(self):
        self.objects = {
            "def_banach": RuntimeObject(
                id="def_banach",
                type="definition",
                section_id="s1",
                number="1.2",
                name_zh="巴拿赫空间",
                name_en="Banach space",
                anchor=RuntimeAnchor(pdf_page=5),
            )
        }


class FakeCourse:
    course_id = "course"

    def __init__(self):
        self.book = FakeBook()

    def main_book(self):
        return self.book

    def main_book_identity(self):
        return object()


def test_fuzzy_retriever_uses_injected_score_and_keeps_object_identity(monkeypatch):
    monkeypatch.setattr("runtime.retrieval.source_identity_for", lambda *_args: FakeIdentity())
    retriever = FuzzyObjectRetriever(
        FakeCourse(),
        min_score=70,
        scorer=lambda query, candidate: 90 if "巴拿" in candidate else 0,
    )
    hits = retriever.search(RetrievalRequest("巴拿赫空間", limit=5))
    assert len(hits) == 1
    assert hits[0].source_kind == "object"
    assert hits[0].source_id == "def_banach"
    assert hits[0].score == 90
