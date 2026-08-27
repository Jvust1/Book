"""Deterministic course-scoped search over the canonical textbook JSONL index."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .course_runtime import CourseRuntime
from .source_resolver import SourceResolutionError, SourceResolver


class SearchRuntimeError(RuntimeError):
    """Base error for textbook search runtime failures."""


class SearchIndexUnavailableError(SearchRuntimeError):
    """Raised when the canonical search index cannot be trusted or loaded."""


class SearchQueryError(SearchRuntimeError):
    """Raised when a search query violates the public search contract."""


@dataclass(frozen=True)
class SearchHit:
    rank: int
    score: int
    course_id: str
    book_id: str
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


@dataclass(frozen=True)
class _SearchCandidate:
    line_number: int
    raw: dict[str, Any]
    source_kind: str
    source_id: str
    object_type: str | None
    section_id: str | None


class SearchRuntime:
    """Read and rank one course's audited main-book search index."""

    def __init__(
        self,
        course: CourseRuntime,
        *,
        records: list[dict[str, Any]],
        candidates: list[_SearchCandidate],
    ) -> None:
        self.course = course
        self.book = course.main_book()
        self._records = records
        self._candidates = candidates
        self.index_record_count = len(records)
        self.searchable_candidate_count = len(candidates)

    @classmethod
    def from_course(cls, course: CourseRuntime) -> "SearchRuntime":
        book = course.main_book()
        path = book.search_index_path
        if path is None:
            raise SearchIndexUnavailableError("Canonical search index path is unavailable")
        path = Path(path)
        if not path.is_file():
            raise SearchIndexUnavailableError(f"Canonical search index is missing: {path}")

        records: list[dict[str, Any]] = []
        candidates: list[_SearchCandidate] = []
        resolver = SourceResolver(course)
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        parsed = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise SearchIndexUnavailableError(
                            f"Invalid search-index JSON at line {line_number}: {exc}"
                        ) from exc
                    if not isinstance(parsed, dict):
                        raise SearchIndexUnavailableError(
                            f"Search-index row {line_number} must be a JSON object"
                        )
                    row_book_id = parsed.get("book_id")
                    if row_book_id != book.book_id:
                        raise SearchIndexUnavailableError(
                            "Search-index book identity mismatch at "
                            f"line {line_number}: {row_book_id!r} != {book.book_id!r}"
                        )
                    records.append(parsed)

                    source_id_value = parsed.get("id") or parsed.get("unit_id")
                    if source_id_value is None:
                        continue
                    source_id = str(source_id_value)
                    if source_id in book.objects:
                        obj = book.objects[source_id]
                        candidates.append(
                            _SearchCandidate(
                                line_number=line_number,
                                raw=parsed,
                                source_kind="object",
                                source_id=source_id,
                                object_type=obj.type,
                                section_id=obj.section_id,
                            )
                        )
                    elif source_id in book.figures:
                        try:
                            figure_section_id = resolver.resolve("figure", source_id).section_id
                        except SourceResolutionError as exc:
                            raise SearchIndexUnavailableError(
                                f"Search-index figure source cannot be resolved: {source_id!r}"
                            ) from exc
                        candidates.append(
                            _SearchCandidate(
                                line_number=line_number,
                                raw=parsed,
                                source_kind="figure",
                                source_id=source_id,
                                object_type="figure",
                                section_id=figure_section_id,
                            )
                        )
        except SearchIndexUnavailableError:
            raise
        except OSError as exc:
            raise SearchIndexUnavailableError(
                f"Cannot read canonical search index {path}: {exc}"
            ) from exc

        return cls(course, records=records, candidates=candidates)

    def search(
        self,
        query: str,
        *,
        limit: int = 30,
        section_id: str | None = None,
    ) -> list[SearchHit]:
        normalized_query = str(query).strip().casefold()
        if not normalized_query:
            raise SearchQueryError("Search query must not be blank")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise SearchQueryError("Search limit must be an integer from 1 through 100")

        normalized_section_id: str | None = None
        if section_id is not None:
            normalized_section_id = str(section_id).strip()
            if not normalized_section_id:
                raise SearchQueryError("Search section ID must not be blank")

        ranked: list[tuple[int, int, _SearchCandidate]] = []
        for candidate in self._candidates:
            if (
                normalized_section_id is not None
                and candidate.section_id != normalized_section_id
            ):
                continue
            score = self._score(candidate.raw, normalized_query)
            if score > 0:
                ranked.append((-score, candidate.line_number, candidate))
        ranked.sort(key=lambda item: (item[0], item[1]))

        hits: list[SearchHit] = []
        for rank, (negative_score, _line_number, candidate) in enumerate(
            ranked[:limit], start=1
        ):
            row = candidate.raw
            jump_target = row.get("jump_target") if isinstance(row.get("jump_target"), dict) else {}
            hits.append(
                SearchHit(
                    rank=rank,
                    score=-negative_score,
                    course_id=self.course.course_id,
                    book_id=self.book.book_id,
                    source_kind=candidate.source_kind,
                    source_id=candidate.source_id,
                    object_type=candidate.object_type,
                    number=self._optional_text(row.get("number")),
                    title_zh=self._first_text(row, "title_zh", "name_zh"),
                    title_en=self._first_text(row, "title_en", "name_en"),
                    formula=self._optional_text(row.get("formula")),
                    pdf_page=self._optional_int(
                        row.get("pdf_page")
                        if row.get("pdf_page") is not None
                        else jump_target.get("pdf_page")
                    ),
                    printed_page=self._printed_page(
                        row.get("printed_page")
                        if row.get("printed_page") is not None
                        else jump_target.get("printed_page")
                    ),
                    source_anchor=self._optional_text(row.get("source_anchor")),
                    snippet=self._snippet(row),
                )
            )
        return hits

    @classmethod
    def _score(cls, row: dict[str, Any], query: str) -> int:
        titles = [
            cls._normalized(row.get(key))
            for key in ("title_zh", "name_zh", "title_en", "name_en")
        ]
        titles = [value for value in titles if value]
        identities = [
            cls._normalized(row.get(key)) for key in ("number", "id", "unit_id")
        ]
        identities = [value for value in identities if value]
        formula = cls._normalized(row.get("formula"))
        concepts_raw = row.get("initial_concepts_zh")
        concepts = (
            [item.strip().casefold() for item in concepts_raw if isinstance(item, str) and item.strip()]
            if isinstance(concepts_raw, list)
            else []
        )
        object_type = cls._normalized(row.get("type"))

        scores = [0]
        if any(value == query for value in titles):
            scores.append(1000)
        if any(value == query for value in identities):
            scores.append(900)
        if any(value.startswith(query) for value in titles):
            scores.append(800)
        if any(query in value for value in titles):
            scores.append(700)
        if formula and formula == query:
            scores.append(600)
        if formula and query in formula:
            scores.append(500)
        if any(value == query for value in concepts):
            scores.append(400)
        if any(query in value for value in concepts):
            scores.append(350)
        if object_type and object_type == query:
            scores.append(300)
        return max(scores)

    @staticmethod
    def _normalized(value: object) -> str:
        if value is None:
            return ""
        return str(value).strip().casefold()

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @classmethod
    def _first_text(cls, row: dict[str, Any], *keys: str) -> str | None:
        for key in keys:
            text = cls._optional_text(row.get(key))
            if text:
                return text
        return None

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _printed_page(value: object) -> int | str | None:
        if value is None or value == "":
            return None
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        text = str(value).strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return text

    @classmethod
    def _snippet(cls, row: dict[str, Any]) -> str | None:
        for key in ("title_zh", "name_zh", "title_en", "name_en", "formula"):
            text = cls._optional_text(row.get(key))
            if text:
                return text
        concepts = row.get("initial_concepts_zh")
        if isinstance(concepts, list):
            values = [item.strip() for item in concepts if isinstance(item, str) and item.strip()]
            if values:
                return "；".join(values[:3])
        return None
