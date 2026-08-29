"""Internal Exact-only retrieval seam over the canonical SearchRuntime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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
