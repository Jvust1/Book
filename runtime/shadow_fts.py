"""Evaluation-only ephemeral FTS5 corpus for H4a shadow retrieval experiments."""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from book_core.provenance import SourceIdentity

from .course_runtime import CourseRuntime
from .provenance import RuntimeProvenanceError, source_identity_for
from .source_resolver import SourceResolutionError, SourceResolver


UNICODE61_PROFILE = "fts_unicode61_bm25_v1"
TRIGRAM_PROFILE = "fts_trigram_bm25_v1"
H4A_PROFILES = (UNICODE61_PROFILE, TRIGRAM_PROFILE)

_PROFILE_TOKENIZERS = {
    UNICODE61_PROFILE: "unicode61",
    TRIGRAM_PROFILE: "trigram",
}


class ShadowFtsError(RuntimeError):
    """Base error for H4a shadow FTS evaluation failures."""


class ShadowFtsUnavailableError(ShadowFtsError):
    """Raised when the required SQLite FTS5 capability is unavailable."""


class ShadowFtsInvariantError(ShadowFtsError):
    """Raised when canonical corpus or provenance invariants cannot be proved."""


class ShadowFtsQueryError(ShadowFtsError):
    """Raised when an H4a shadow query violates the closed query contract."""


@dataclass(frozen=True)
class ShadowDocument:
    rowid: int
    identity: SourceIdentity
    source_kind: str
    source_id: str
    section_id: str | None
    object_type: str | None
    number: str
    title_zh: str
    title_en: str
    formula: str
    concepts_zh: str
    snippet: str


@dataclass(frozen=True)
class ShadowHit:
    profile_id: str
    rank: int
    bm25_score: float
    identity: SourceIdentity
    source_kind: str
    source_id: str
    section_id: str | None


class ShadowFtsIndex:
    """One in-memory H4a corpus plus its two evaluation-only FTS5 profiles."""

    def __init__(
        self,
        course: CourseRuntime,
        connection: sqlite3.Connection,
        documents: tuple[ShadowDocument, ...],
    ) -> None:
        self.course = course
        self.connection = connection
        self.documents = documents
        self.document_count = len(documents)

    @classmethod
    def from_course(cls, course: CourseRuntime) -> "ShadowFtsIndex":
        if not fts5_available():
            raise ShadowFtsUnavailableError("SQLite FTS5 is unavailable")

        documents = _load_shadow_documents(course)
        connection = sqlite3.connect(":memory:")
        try:
            _create_schema(connection)
            _insert_documents(connection, documents)
        except sqlite3.Error as exc:
            connection.close()
            raise ShadowFtsUnavailableError(
                f"Cannot build H4a FTS5 shadow index: {exc}"
            ) from exc
        except Exception:
            connection.close()
            raise
        return cls(course, connection, documents)

    def close(self) -> None:
        self.connection.close()

    def search(
        self,
        profile_id: str,
        query: str,
        *,
        limit: int = 30,
        section_id: str | None = None,
    ) -> list[ShadowHit]:
        table_name = _profile_table_name(profile_id)
        normalized_query = _validate_query(query)
        _validate_limit(limit)
        normalized_section_id = _validate_section_id(section_id)

        if profile_id == TRIGRAM_PROFILE and len(normalized_query) < 3:
            return []

        match_expression = _compile_match_phrase(normalized_query)
        sql = f"""
            SELECT
                d.rowid,
                d.source_kind,
                d.source_id,
                d.section_id,
                bm25({table_name}) AS bm25_score
            FROM {table_name}
            JOIN shadow_documents AS d
                ON d.rowid = {table_name}.rowid
            WHERE {table_name} MATCH ?
        """
        parameters: list[object] = [match_expression]
        if normalized_section_id is not None:
            sql += " AND d.section_id = ?"
            parameters.append(normalized_section_id)
        sql += f" ORDER BY bm25({table_name}) ASC, d.rowid ASC LIMIT ?"
        parameters.append(limit)

        try:
            rows = self.connection.execute(sql, parameters).fetchall()
        except sqlite3.Error as exc:
            raise ShadowFtsQueryError("H4a shadow FTS query execution failed") from exc

        documents_by_rowid = {document.rowid: document for document in self.documents}
        hits: list[ShadowHit] = []
        for rank, row in enumerate(rows, start=1):
            rowid = int(row[0])
            source_kind = str(row[1])
            source_id = str(row[2])
            returned_section_id = row[3]
            bm25_score = float(row[4])

            if not math.isfinite(bm25_score):
                raise ShadowFtsInvariantError("Shadow FTS returned non-finite BM25 score")

            document = documents_by_rowid.get(rowid)
            if document is None:
                raise ShadowFtsInvariantError(
                    f"Shadow FTS returned unknown corpus rowid: {rowid}"
                )
            if (
                document.source_kind != source_kind
                or document.source_id != source_id
                or document.section_id != returned_section_id
            ):
                raise ShadowFtsInvariantError(
                    f"Shadow FTS metadata drift for rowid {rowid}"
                )

            resolved, identity = _revalidate_hit_identity(
                self.course,
                source_kind,
                source_id,
            )
            if (
                resolved.section_id != returned_section_id
                or identity != document.identity
            ):
                raise ShadowFtsInvariantError(
                    f"Shadow FTS canonical identity drift for {source_kind}:{source_id}"
                )

            hits.append(
                ShadowHit(
                    profile_id=profile_id,
                    rank=rank,
                    bm25_score=bm25_score,
                    identity=identity,
                    source_kind=source_kind,
                    source_id=source_id,
                    section_id=returned_section_id,
                )
            )
        return hits


def fts5_available() -> bool:
    """Probe runtime FTS5 support by creating a real virtual table in memory."""

    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE VIRTUAL TABLE fts5_probe USING fts5(content)")
        connection.execute("DROP TABLE fts5_probe")
    except sqlite3.Error:
        return False
    finally:
        connection.close()
    return True


def _profile_table_name(profile_id: object) -> str:
    if not isinstance(profile_id, str) or profile_id not in _PROFILE_TOKENIZERS:
        raise ShadowFtsQueryError("Unknown H4a shadow FTS profile")
    return profile_id


def _validate_query(query: object) -> str:
    if not isinstance(query, str) or not query.strip():
        raise ShadowFtsQueryError("Shadow FTS query must be a non-blank string")
    return query.strip()


def _validate_limit(limit: object) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ShadowFtsQueryError("Shadow FTS limit must be a positive integer")


def _validate_section_id(section_id: object) -> str | None:
    if section_id is None:
        return None
    if not isinstance(section_id, str) or not section_id.strip():
        raise ShadowFtsQueryError("Shadow FTS section_id must be non-blank when supplied")
    return section_id.strip()


def _compile_match_phrase(query: str) -> str:
    escaped = query.replace('"', '""')
    return f'"{escaped}"'


def _revalidate_hit_identity(
    course: CourseRuntime,
    source_kind: str,
    source_id: str,
):
    try:
        resolved = SourceResolver(course).resolve(source_kind, source_id)
        identity = source_identity_for(course, source_kind, source_id)
    except (SourceResolutionError, RuntimeProvenanceError) as exc:
        raise ShadowFtsInvariantError(
            f"Shadow FTS hit cannot prove provenance: {source_kind}:{source_id}"
        ) from exc

    main_book = course.main_book()
    if (
        resolved.course_id != course.course_id
        or resolved.book_id != main_book.book_id
        or resolved.kind != source_kind
        or resolved.source_id != source_id
        or identity.course_id != course.course_id
        or identity.book != course.main_book_identity()
        or identity.source_kind != source_kind
        or identity.source_id != source_id
    ):
        raise ShadowFtsInvariantError(
            f"Shadow FTS hit identity mismatch: {source_kind}:{source_id}"
        )
    return resolved, identity


def _load_shadow_documents(course: CourseRuntime) -> tuple[ShadowDocument, ...]:
    book = course.main_book()
    path = book.search_index_path
    if path is None:
        raise ShadowFtsInvariantError("Canonical search index path is unavailable")
    path = Path(path)
    if not path.is_file():
        raise ShadowFtsInvariantError(f"Canonical search index is missing: {path}")

    resolver = SourceResolver(course)
    documents: list[ShadowDocument] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = _parse_index_row(line, line_number)
                row_book_id = row.get("book_id")
                if row_book_id != book.book_id:
                    raise ShadowFtsInvariantError(
                        "Search-index book identity mismatch at "
                        f"line {line_number}: {row_book_id!r} != {book.book_id!r}"
                    )

                source_id_value = row.get("id") or row.get("unit_id")
                if source_id_value is None:
                    continue
                source_id = str(source_id_value)
                if source_id in book.objects:
                    source_kind = "object"
                elif source_id in book.figures:
                    source_kind = "figure"
                else:
                    continue

                try:
                    resolved = resolver.resolve(source_kind, source_id)
                    identity = source_identity_for(course, source_kind, source_id)
                except (SourceResolutionError, RuntimeProvenanceError) as exc:
                    raise ShadowFtsInvariantError(
                        f"Search-index {source_kind} source cannot prove provenance: "
                        f"{source_id!r}"
                    ) from exc

                if (
                    resolved.course_id != course.course_id
                    or resolved.book_id != book.book_id
                    or resolved.kind != source_kind
                    or resolved.source_id != source_id
                    or identity.course_id != course.course_id
                    or identity.book != course.main_book_identity()
                    or identity.source_kind != source_kind
                    or identity.source_id != source_id
                ):
                    raise ShadowFtsInvariantError(
                        f"Search-index source identity mismatch: {source_kind}:{source_id}"
                    )

                documents.append(
                    _project_document(
                        rowid=len(documents) + 1,
                        row=row,
                        identity=identity,
                        source_kind=source_kind,
                        source_id=source_id,
                        section_id=resolved.section_id,
                        object_type=resolved.type,
                    )
                )
    except ShadowFtsInvariantError:
        raise
    except OSError as exc:
        raise ShadowFtsInvariantError(
            f"Cannot read canonical search index {path}: {exc}"
        ) from exc

    return tuple(documents)


def _parse_index_row(line: str, line_number: int) -> dict[str, Any]:
    try:
        parsed = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ShadowFtsInvariantError(
            f"Invalid search-index JSON at line {line_number}: {exc}"
        ) from exc
    if not isinstance(parsed, dict):
        raise ShadowFtsInvariantError(
            f"Search-index row {line_number} must be a JSON object"
        )
    return parsed


def _project_document(
    *,
    rowid: int,
    row: dict[str, Any],
    identity: SourceIdentity,
    source_kind: str,
    source_id: str,
    section_id: str | None,
    object_type: str | None,
) -> ShadowDocument:
    title_zh = _first_text(row, "title_zh", "name_zh")
    title_en = _first_text(row, "title_en", "name_en")
    formula = _text(row.get("formula"))
    concepts = _concepts(row.get("initial_concepts_zh"))
    return ShadowDocument(
        rowid=rowid,
        identity=identity,
        source_kind=source_kind,
        source_id=source_id,
        section_id=section_id,
        object_type=_optional_text(object_type),
        number=_text(row.get("number")),
        title_zh=title_zh,
        title_en=title_en,
        formula=formula,
        concepts_zh="\n".join(concepts),
        snippet=_snippet(row, concepts),
    )


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE shadow_documents (
            rowid INTEGER PRIMARY KEY,
            source_kind TEXT NOT NULL,
            source_id TEXT NOT NULL,
            section_id TEXT,
            object_type TEXT,
            number TEXT NOT NULL,
            title_zh TEXT NOT NULL,
            title_en TEXT NOT NULL,
            formula TEXT NOT NULL,
            concepts_zh TEXT NOT NULL,
            snippet TEXT NOT NULL
        )
        """
    )
    for profile_id in H4A_PROFILES:
        tokenizer = _PROFILE_TOKENIZERS[profile_id]
        connection.execute(
            f"""
            CREATE VIRTUAL TABLE {profile_id} USING fts5(
                title_zh,
                title_en,
                concepts_zh,
                formula,
                number,
                object_type,
                snippet,
                tokenize='{tokenizer}'
            )
            """
        )


def _insert_documents(
    connection: sqlite3.Connection,
    documents: tuple[ShadowDocument, ...],
) -> None:
    metadata_sql = """
        INSERT INTO shadow_documents (
            rowid,
            source_kind,
            source_id,
            section_id,
            object_type,
            number,
            title_zh,
            title_en,
            formula,
            concepts_zh,
            snippet
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    fts_sql = {
        profile_id: f"""
            INSERT INTO {profile_id} (
                rowid,
                title_zh,
                title_en,
                concepts_zh,
                formula,
                number,
                object_type,
                snippet
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        for profile_id in H4A_PROFILES
    }

    for document in documents:
        connection.execute(
            metadata_sql,
            (
                document.rowid,
                document.source_kind,
                document.source_id,
                document.section_id,
                document.object_type,
                document.number,
                document.title_zh,
                document.title_en,
                document.formula,
                document.concepts_zh,
                document.snippet,
            ),
        )
        values = (
            document.rowid,
            document.title_zh,
            document.title_en,
            document.concepts_zh,
            document.formula,
            document.number,
            document.object_type or "",
            document.snippet,
        )
        for profile_id in H4A_PROFILES:
            connection.execute(fts_sql[profile_id], values)
    connection.commit()


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _optional_text(value: object) -> str | None:
    text = _text(value)
    return text or None


def _first_text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        text = _text(row.get(key))
        if text:
            return text
    return ""


def _concepts(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    )


def _snippet(row: dict[str, Any], concepts: tuple[str, ...]) -> str:
    for key in ("title_zh", "name_zh", "title_en", "name_en", "formula"):
        text = _text(row.get(key))
        if text:
            return text
    if concepts:
        return "；".join(concepts[:3])
    return ""
