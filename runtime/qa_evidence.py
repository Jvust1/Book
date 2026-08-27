"""Deterministic evidence selection and citation verification for textbook QA."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Literal, Mapping

from .course_runtime import CourseRuntime
from .qa_models import (
    EvidenceItem,
    EvidencePack,
    ModelResponse,
    ProviderAnswer,
    QACitation,
    QAHistoryMessage,
)
from .qa_provider import AnswerProviderInvalidResponseError
from .search_runtime import SearchHit, SearchRuntime, SearchRuntimeError
from .source_resolver import SourceResolutionError, SourceResolver


MAX_EVIDENCE_ITEMS = 8
MAX_EVIDENCE_TEXT_CODEPOINTS = 12000
MAX_HISTORY_MESSAGES = 6
MAX_HISTORY_TEXT_CODEPOINTS = 6000


class QAEvidenceError(RuntimeError):
    """Base error for trusted textbook evidence preparation."""


class QAEvidenceUnavailableError(QAEvidenceError):
    """Trusted search/source evidence cannot currently be constructed."""


class QAHistoryValidationError(ValueError):
    """Short-lived dialogue history violates the Phase 1F context contract."""


class QuestionProbeBuilder:
    """Convert one natural-language question into bounded lexical probes."""

    MAX_PROBES = 24
    _LATIN_TOKEN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9_\-]*")
    _CJK_RUN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
    _GENERIC_CJK_PROBES = frozenset({"概念"})

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
                    probe = run[start : start + width]
                    if probe in cls._GENERIC_CJK_PROBES:
                        continue
                    if add(probe):
                        return tuple(probes)

        return tuple(probes)


def normalize_history(
    history: Iterable[QAHistoryMessage | Mapping[str, object]],
) -> tuple[QAHistoryMessage, ...]:
    """Validate and bound recent dialogue without turning it into textbook evidence."""

    if isinstance(history, (str, bytes)):
        raise QAHistoryValidationError("QA history must be a sequence of messages")

    rows: list[QAHistoryMessage] = []
    try:
        values = list(history)
    except TypeError as exc:
        raise QAHistoryValidationError("QA history must be iterable") from exc

    for value in values:
        if isinstance(value, QAHistoryMessage):
            role = value.role
            content = value.content
        elif isinstance(value, Mapping):
            role = value.get("role")
            content = value.get("content")
        else:
            raise QAHistoryValidationError("Every QA history row must be a message object")

        if role not in ("user", "assistant"):
            raise QAHistoryValidationError("QA history role must be user or assistant")
        if not isinstance(content, str) or not content.strip():
            raise QAHistoryValidationError("QA history content must be a non-blank string")
        rows.append(QAHistoryMessage(role=role, content=content.strip()))  # type: ignore[arg-type]

    rows = rows[-MAX_HISTORY_MESSAGES:]
    while rows and sum(len(row.content) for row in rows) > MAX_HISTORY_TEXT_CODEPOINTS:
        total = sum(len(row.content) for row in rows)
        excess = total - MAX_HISTORY_TEXT_CODEPOINTS
        if excess >= len(rows[0].content):
            rows.pop(0)
            continue
        first = rows[0]
        rows[0] = QAHistoryMessage(role=first.role, content=first.content[excess:])

    return tuple(rows)


@dataclass(frozen=True)
class _EvidenceCandidate:
    hit: SearchHit
    probe_index: int

    @property
    def key(self) -> tuple[str, str]:
        return (self.hit.source_kind, self.hit.source_id)


class EvidenceBuilder:
    """Build bounded, source-resolved evidence from one course's canonical index."""

    def __init__(self, course: CourseRuntime):
        self.course = course

    @classmethod
    def from_course(cls, course: CourseRuntime) -> "EvidenceBuilder":
        return cls(course)

    def build(
        self,
        question: str,
        *,
        section_id: str | None,
        limit: int = MAX_EVIDENCE_ITEMS,
    ) -> EvidencePack:
        normalized_limit = min(max(int(limit), 1), MAX_EVIDENCE_ITEMS)
        probes = QuestionProbeBuilder.build(question)
        book = self.course.main_book()
        scope_requested = "section_then_book" if section_id is not None else "book"
        scope_used = "section" if section_id is not None else "book"
        if not probes:
            return EvidencePack(
                course_id=self.course.course_id,
                book_id=book.book_id,
                question=str(question).strip(),
                evidence=(),
                scope_requested=scope_requested,
                scope_used=scope_used,
            )

        try:
            search = SearchRuntime.from_course(self.course)
            merged: dict[tuple[str, str], _EvidenceCandidate] = {}
            search_limit = min(100, max(30, normalized_limit * 4))
            for probe_index, probe in enumerate(probes):
                for hit in search.search(
                    probe,
                    limit=search_limit,
                    section_id=section_id,
                ):
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
        )

        resolver = SourceResolver(self.course)
        evidence: list[EvidenceItem] = []
        remaining_text = MAX_EVIDENCE_TEXT_CODEPOINTS
        try:
            for candidate in ordered:
                if len(evidence) >= normalized_limit:
                    break
                hit = candidate.hit
                resolved = resolver.resolve(hit.source_kind, hit.source_id)
                if resolved.course_id != self.course.course_id or resolved.book_id != book.book_id:
                    raise QAEvidenceUnavailableError(
                        "Resolved evidence identity does not match the selected course/book"
                    )
                if section_id is not None and resolved.section_id != section_id:
                    raise QAEvidenceUnavailableError(
                        "Resolved evidence escaped the requested Section scope"
                    )

                chapter_id = None
                if resolved.section_id:
                    try:
                        chapter_id = self.course.section(resolved.section_id).chapter_id
                    except Exception as exc:  # canonical section drift is infrastructure failure
                        raise QAEvidenceUnavailableError(
                            f"Resolved evidence Section is unavailable: {resolved.section_id!r}"
                        ) from exc

                content_zh, formula, remaining_text = self._bounded_text_fields(
                    resolved.content_zh,
                    resolved.formula,
                    remaining_text,
                )
                evidence.append(
                    EvidenceItem(
                        evidence_id=f"E{len(evidence) + 1}",
                        source_kind=resolved.kind,
                        source_id=resolved.source_id,
                        object_type=resolved.type,
                        title_zh=resolved.title_zh,
                        title_en=resolved.title_en,
                        number=resolved.number,
                        formula=formula,
                        content_zh=content_zh,
                        source_anchor=resolved.source_anchor,
                        pdf_page=resolved.pdf_page,
                        printed_page=resolved.printed_page,
                        search_score=hit.score,
                        course_id=resolved.course_id,
                        book_id=resolved.book_id,
                        chapter_id=chapter_id,
                        section_id=resolved.section_id,
                        type_zh=resolved.type_zh,
                    )
                )
        except SourceResolutionError as exc:
            raise QAEvidenceUnavailableError(str(exc)) from exc

        return EvidencePack(
            course_id=self.course.course_id,
            book_id=book.book_id,
            question=str(question).strip(),
            evidence=tuple(evidence),
            scope_requested=scope_requested,
            scope_used=scope_used,
        )

    # Legacy method name retained until provider/runtime migration is complete.
    def retrieve(self, question: str, *, limit: int) -> EvidencePack:
        return self.build(question, section_id=None, limit=limit)

    @staticmethod
    def _bounded_text_fields(
        content_zh: str | None,
        formula: str | None,
        remaining: int,
    ) -> tuple[str | None, str | None, int]:
        if remaining <= 0:
            return None, None, 0

        def take(value: str | None, budget: int) -> tuple[str | None, int]:
            if value is None or not value:
                return None, budget
            if budget <= 0:
                return None, 0
            clipped = value[:budget]
            return clipped, budget - len(clipped)

        bounded_content, remaining = take(content_zh, remaining)
        bounded_formula, remaining = take(formula, remaining)
        return bounded_content, bounded_formula, remaining

    @staticmethod
    def _is_better(candidate: _EvidenceCandidate, existing: _EvidenceCandidate) -> bool:
        if candidate.hit.score != existing.hit.score:
            return candidate.hit.score > existing.hit.score
        return (candidate.probe_index, candidate.hit.rank) < (
            existing.probe_index,
            existing.hit.rank,
        )


class EvidenceGate:
    """Conservative deterministic sufficiency gate before any model call."""

    @staticmethod
    def status(pack: EvidencePack) -> Literal["sufficient", "insufficient_evidence"]:
        if not pack.evidence:
            return "insufficient_evidence"
        if max(item.search_score for item in pack.evidence) <= 300:
            return "insufficient_evidence"
        if not any(
            bool((item.content_zh or "").strip()) or bool((item.formula or "").strip())
            for item in pack.evidence
        ):
            return "insufficient_evidence"
        if any(
            item.course_id not in (None, pack.course_id)
            or item.book_id not in (None, pack.book_id)
            for item in pack.evidence
        ):
            return "insufficient_evidence"
        return "sufficient"


class CitationVerifier:
    """Map model evidence IDs back to revalidated server-owned citations."""

    def __init__(self, course: CourseRuntime):
        self.course = course
        self._resolver = SourceResolver(course)

    @classmethod
    def from_course(cls, course: CourseRuntime) -> "CitationVerifier":
        return cls(course)

    def verify(
        self,
        pack: EvidencePack,
        model_response: ModelResponse | ProviderAnswer,
    ) -> tuple[QACitation, ...]:
        if isinstance(model_response, ModelResponse):
            cited_ids = model_response.evidence_ids
            answer_text = model_response.answer or ""
        else:
            cited_ids = model_response.cited_evidence_ids
            answer_text = model_response.answer_text

        if answer_text.strip() and not cited_ids:
            raise AnswerProviderInvalidResponseError(
                "Non-empty model answer must cite at least one evidence item"
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
                    f"Model cited unknown evidence ID: {evidence_id!r}"
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
                    chapter_id=evidence.chapter_id,
                    section_id=evidence.section_id,
                    type_zh=evidence.type_zh,
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
            and evidence.section_id == getattr(resolved, "section_id", None)
            and evidence.type_zh == getattr(resolved, "type_zh", None)
        )


# Transitional aliases keep the existing app import surface stable until Task 5 cleanup.
EvidenceRetriever = EvidenceBuilder
EvidencePolicy = EvidenceGate
