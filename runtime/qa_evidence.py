"""Deterministic evidence selection and citation verification for textbook QA."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

from .course_runtime import CourseRuntime
from .qa_models import EvidenceItem, EvidencePack, ProviderAnswer, QACitation
from .qa_provider import AnswerProviderInvalidResponseError
from .search_runtime import SearchHit, SearchRuntime, SearchRuntimeError
from .source_resolver import SourceResolutionError, SourceResolver


class QAEvidenceError(RuntimeError):
    """Base error for trusted textbook evidence preparation."""


class QAEvidenceUnavailableError(QAEvidenceError):
    """Trusted search/source evidence cannot currently be constructed."""


class QuestionProbeBuilder:
    """Convert one natural-language question into bounded lexical probes."""

    MAX_PROBES = 24
    _LATIN_TOKEN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9_\-]*")
    _CJK_RUN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")

    @classmethod
    def build(cls, question: str) -> tuple[str, ...]:
        text = str(question).strip()
        if not text:
            return ()

        probes: list[str] = []
        seen: set[str] = set()

        def add(value: str) -> bool:
            candidate = value.strip()
            if not candidate or candidate in seen:
                return False
            seen.add(candidate)
            probes.append(candidate)
            return len(probes) >= cls.MAX_PROBES

        if add(text):
            return tuple(probes)

        for match in cls._LATIN_TOKEN.finditer(text):
            token = match.group(0)
            if len(token) >= 3 and add(token):
                return tuple(probes)

        for match in cls._CJK_RUN.finditer(text):
            run = match.group(0)
            for width in range(min(8, len(run)), 1, -1):
                for start in range(0, len(run) - width + 1):
                    if add(run[start : start + width]):
                        return tuple(probes)

        return tuple(probes)


@dataclass(frozen=True)
class _EvidenceCandidate:
    hit: SearchHit
    probe_index: int

    @property
    def key(self) -> tuple[str, str]:
        return (self.hit.source_kind, self.hit.source_id)


class EvidenceRetriever:
    """Retrieve and re-resolve bounded evidence from one course's canonical index."""

    def __init__(self, course: CourseRuntime):
        self.course = course

    @classmethod
    def from_course(cls, course: CourseRuntime) -> "EvidenceRetriever":
        return cls(course)

    def retrieve(self, question: str, *, limit: int) -> EvidencePack:
        probes = QuestionProbeBuilder.build(question)
        book = self.course.main_book()
        if not probes:
            return EvidencePack(
                course_id=self.course.course_id,
                book_id=book.book_id,
                question=str(question).strip(),
                evidence=(),
            )

        try:
            search = SearchRuntime.from_course(self.course)
            merged: dict[tuple[str, str], _EvidenceCandidate] = {}
            for probe_index, probe in enumerate(probes):
                for hit in search.search(probe, limit=limit):
                    candidate = _EvidenceCandidate(hit=hit, probe_index=probe_index)
                    existing = merged.get(candidate.key)
                    if existing is None or self._is_better(candidate, existing):
                        merged[candidate.key] = candidate
        except SearchRuntimeError as exc:
            raise QAEvidenceUnavailableError(str(exc)) from exc

        ordered = sorted(
            merged.values(),
            key=lambda item: (
                -item.hit.score,
                item.probe_index,
                item.hit.rank,
                item.hit.source_kind,
                item.hit.source_id,
            ),
        )[:limit]

        resolver = SourceResolver(self.course)
        evidence: list[EvidenceItem] = []
        try:
            for index, candidate in enumerate(ordered, start=1):
                hit = candidate.hit
                resolved = resolver.resolve(hit.source_kind, hit.source_id)
                if resolved.course_id != self.course.course_id or resolved.book_id != book.book_id:
                    raise QAEvidenceUnavailableError(
                        "Resolved evidence identity does not match the selected course/book"
                    )
                evidence.append(
                    EvidenceItem(
                        evidence_id=f"E{index}",
                        source_kind=resolved.kind,
                        source_id=resolved.source_id,
                        object_type=resolved.type,
                        title_zh=resolved.title_zh,
                        title_en=resolved.title_en,
                        number=resolved.number,
                        formula=resolved.formula,
                        content_zh=resolved.content_zh,
                        source_anchor=resolved.source_anchor,
                        pdf_page=resolved.pdf_page,
                        printed_page=resolved.printed_page,
                        search_score=hit.score,
                    )
                )
        except SourceResolutionError as exc:
            raise QAEvidenceUnavailableError(str(exc)) from exc

        return EvidencePack(
            course_id=self.course.course_id,
            book_id=book.book_id,
            question=str(question).strip(),
            evidence=tuple(evidence),
        )

    @staticmethod
    def _is_better(candidate: _EvidenceCandidate, existing: _EvidenceCandidate) -> bool:
        if candidate.hit.score != existing.hit.score:
            return candidate.hit.score > existing.hit.score
        return (candidate.probe_index, candidate.hit.rank) < (
            existing.probe_index,
            existing.hit.rank,
        )


class EvidencePolicy:
    """Conservative deterministic sufficiency policy for Phase 1F."""

    @staticmethod
    def status(pack: EvidencePack) -> Literal["sufficient", "insufficient_evidence"]:
        if not pack.evidence:
            return "insufficient_evidence"
        if max(item.search_score for item in pack.evidence) <= 300:
            return "insufficient_evidence"
        return "sufficient"


class CitationVerifier:
    """Map provider evidence IDs back to revalidated server-owned citations."""

    def __init__(self, course: CourseRuntime):
        self.course = course
        self._resolver = SourceResolver(course)

    @classmethod
    def from_course(cls, course: CourseRuntime) -> "CitationVerifier":
        return cls(course)

    def verify(
        self,
        pack: EvidencePack,
        provider_answer: ProviderAnswer,
    ) -> tuple[QACitation, ...]:
        cited_ids = provider_answer.cited_evidence_ids
        if provider_answer.answer_text.strip() and not cited_ids:
            raise AnswerProviderInvalidResponseError(
                "Non-empty provider answer must cite at least one evidence item"
            )

        by_id = {item.evidence_id: item for item in pack.evidence}
        citations: list[QACitation] = []
        seen: set[str] = set()
        for evidence_id in cited_ids:
            if evidence_id in seen:
                continue
            evidence = by_id.get(evidence_id)
            if evidence is None:
                raise AnswerProviderInvalidResponseError(
                    f"Provider cited unknown evidence ID: {evidence_id!r}"
                )
            seen.add(evidence_id)
            try:
                resolved = self._resolver.resolve(evidence.source_kind, evidence.source_id)
            except SourceResolutionError as exc:
                raise QAEvidenceUnavailableError(str(exc)) from exc
            if not self._matches_resolved(evidence, resolved):
                raise QAEvidenceUnavailableError(
                    f"Evidence identity drift detected for {evidence.source_kind}:{evidence.source_id}"
                )
            citations.append(
                QACitation(
                    citation_id=f"C{len(citations) + 1}",
                    evidence_id=evidence.evidence_id,
                    source_kind=evidence.source_kind,
                    source_id=evidence.source_id,
                    object_type=evidence.object_type,
                    number=evidence.number,
                    title_zh=evidence.title_zh,
                    title_en=evidence.title_en,
                    source_anchor=evidence.source_anchor,
                    pdf_page=evidence.pdf_page,
                    printed_page=evidence.printed_page,
                )
            )
        return tuple(citations)

    @staticmethod
    def _matches_resolved(evidence: EvidenceItem, resolved: object) -> bool:
        return (
            evidence.source_kind == getattr(resolved, "kind", None)
            and evidence.source_id == getattr(resolved, "source_id", None)
            and evidence.object_type == getattr(resolved, "type", None)
            and evidence.number == getattr(resolved, "number", None)
            and evidence.title_zh == getattr(resolved, "title_zh", None)
            and evidence.title_en == getattr(resolved, "title_en", None)
            and evidence.source_anchor == getattr(resolved, "source_anchor", None)
            and evidence.pdf_page == getattr(resolved, "pdf_page", None)
            and evidence.printed_page == getattr(resolved, "printed_page", None)
        )
