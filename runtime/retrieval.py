"""Internal Exact-only retrieval seam over the canonical SearchRuntime."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Callable, Protocol

from book_core.provenance import SourceIdentity

from .course_runtime import CourseRuntime
from .provenance import RuntimeProvenanceError, source_identity_for
from .search_runtime import SearchQueryError, SearchRuntime, SearchRuntimeError


class RetrievalError(RuntimeError):
    """Base error for internal retrieval failures."""


class RetrievalQueryError(RetrievalError):
    """Raised when a retrieval request violates the exact search contract."""


class RetrievalUnavailableError(RetrievalError):
    """Raised when canonical exact retrieval is unavailable."""


class RetrievalInvariantError(RetrievalError):
    """Raised when a retrieved candidate cannot prove canonical provenance."""


@dataclass(frozen=True)
class RetrievalRequest:
    query: str
    limit: int = 30
    section_id: str | None = None


@dataclass(frozen=True)
class RetrievalHit:
    rank: int
    score: int
    identity: SourceIdentity
    source_kind: str
    source_id: str
    object_type: str | None
    number: str | None
    title_zh: str | None
    title_en: str | None
    formula: str | None
    pdf_page: int | None
    printed_page: int | str | None
    source_anchor: str | None
    snippet: str | None


class Retriever(Protocol):
    def search(self, request: RetrievalRequest) -> list[RetrievalHit]: ...


class CanonicalExactRetriever:
    """Field-for-field wrapper around the frozen canonical SearchRuntime."""

    def __init__(self, course: CourseRuntime, search_runtime: SearchRuntime) -> None:
        self.course = course
        self._search_runtime = search_runtime

    @classmethod
    def from_course(cls, course: CourseRuntime) -> "CanonicalExactRetriever":
        try:
            search_runtime = SearchRuntime.from_course(course)
        except SearchRuntimeError as exc:
            raise RetrievalUnavailableError(str(exc)) from exc
        return cls(course, search_runtime)

    def search(self, request: RetrievalRequest) -> list[RetrievalHit]:
        try:
            search_hits = self._search_runtime.search(
                request.query,
                limit=request.limit,
                section_id=request.section_id,
            )
            return [self._convert_hit(hit) for hit in search_hits]
        except SearchQueryError as exc:
            raise RetrievalQueryError(str(exc)) from exc
        except SearchRuntimeError as exc:
            raise RetrievalUnavailableError(str(exc)) from exc
        except RuntimeProvenanceError as exc:
            raise RetrievalInvariantError(str(exc)) from exc

    def _convert_hit(self, hit: object) -> RetrievalHit:
        identity = source_identity_for(
            self.course,
            hit.source_kind,
            hit.source_id,
        )
        return RetrievalHit(
            rank=hit.rank,
            score=hit.score,
            identity=identity,
            source_kind=hit.source_kind,
            source_id=hit.source_id,
            object_type=hit.object_type,
            number=hit.number,
            title_zh=hit.title_zh,
            title_en=hit.title_en,
            formula=hit.formula,
            pdf_page=hit.pdf_page,
            printed_page=hit.printed_page,
            source_anchor=hit.source_anchor,
            snippet=hit.snippet,
        )


class RetrievalEngine:
    def __init__(self, retriever: Retriever) -> None:
        self._retriever = retriever

    @classmethod
    def exact(cls, course: CourseRuntime) -> "RetrievalEngine":
        return cls(CanonicalExactRetriever.from_course(course))

    @classmethod
    def fuzzy_objects(
        cls,
        course: CourseRuntime,
        *,
        min_score: int = 70,
        scorer: Callable[[str, str], int] | None = None,
    ) -> "RetrievalEngine":
        return cls(FuzzyObjectRetriever(course, min_score=min_score, scorer=scorer))

    @classmethod
    def hybrid(
        cls,
        course: CourseRuntime,
        *,
        min_score: int = 70,
        scorer: Callable[[str, str], int] | None = None,
    ) -> "RetrievalEngine":
        return cls(
            HybridExactFuzzyRetriever(
                CanonicalExactRetriever.from_course(course),
                FuzzyObjectRetriever(course, min_score=min_score, scorer=scorer),
            )
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 30,
        section_id: str | None = None,
    ) -> list[RetrievalHit]:
        return self._retriever.search(
            RetrievalRequest(query=query, limit=limit, section_id=section_id)
        )



def _default_fuzzy_score(query: str, candidate: str) -> int:
    try:
        from rapidfuzz.fuzz import WRatio
        return int(round(float(WRatio(query, candidate))))
    except ImportError:
        return int(round(100.0 * SequenceMatcher(None, query, candidate).ratio()))


class FuzzyObjectRetriever:
    """Typo-tolerant object-title retrieval with canonical provenance."""

    def __init__(
        self,
        course: CourseRuntime,
        *,
        min_score: int = 70,
        scorer: Callable[[str, str], int] | None = None,
    ) -> None:
        if not 0 <= min_score <= 100:
            raise ValueError("min_score must be in 0..100")
        self.course = course
        self.book = course.main_book()
        self.min_score = min_score
        self.scorer = scorer or _default_fuzzy_score

    def search(self, request: RetrievalRequest) -> list[RetrievalHit]:
        query = str(request.query).strip()
        if not query:
            raise RetrievalQueryError("query cannot be empty")
        if request.limit < 1:
            return []
        rows: list[tuple[int, str, Any]] = []
        for obj in self.book.objects.values():
            if request.section_id is not None and obj.section_id != request.section_id:
                continue
            candidates = [
                obj.id,
                obj.number or "",
                obj.name_zh or "",
                obj.name_en or "",
            ]
            score = max(self.scorer(query, str(value)) for value in candidates if str(value))
            if score >= self.min_score:
                rows.append((score, obj.id, obj))
        rows.sort(key=lambda item: (-item[0], item[1]))

        hits: list[RetrievalHit] = []
        for rank, (score, _object_id, obj) in enumerate(rows[: request.limit], start=1):
            try:
                identity = source_identity_for(self.course, "object", obj.id)
            except RuntimeProvenanceError as exc:
                raise RetrievalInvariantError(str(exc)) from exc
            hits.append(
                RetrievalHit(
                    rank=rank,
                    score=score,
                    identity=identity,
                    source_kind="object",
                    source_id=obj.id,
                    object_type=obj.type,
                    number=obj.number,
                    title_zh=obj.name_zh,
                    title_en=obj.name_en,
                    formula=obj.formula,
                    pdf_page=obj.anchor.pdf_page,
                    printed_page=obj.anchor.printed_page,
                    source_anchor=obj.anchor.source_anchor,
                    snippet=obj.name_zh or obj.name_en or obj.formula,
                )
            )
        return hits


class HybridExactFuzzyRetriever:
    """Exact search first; fuzzy object titles only when exact search finds nothing."""

    def __init__(self, exact: CanonicalExactRetriever, fuzzy: FuzzyObjectRetriever) -> None:
        self.exact = exact
        self.fuzzy = fuzzy

    def search(self, request: RetrievalRequest) -> list[RetrievalHit]:
        exact_hits = self.exact.search(request)
        return exact_hits if exact_hits else self.fuzzy.search(request)
