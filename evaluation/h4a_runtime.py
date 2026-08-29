"""Deterministic H4a evaluation query-set contract."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


H4A_QUERY_SET_SCHEMA_VERSION = "h4a_query_set_v1"
H4A_QUERY_CATEGORIES = frozenset(
    {
        "english_exact",
        "english_partial",
        "chinese_complete",
        "chinese_partial",
        "formula_symbol",
        "section_scoped",
        "negative_zero_result",
    }
)
H4A_SOURCE_KINDS = frozenset({"object", "figure"})


class H4aEvaluationError(RuntimeError):
    """Base error for H4a evaluation-only failures."""


class H4aDatasetError(H4aEvaluationError):
    """Raised when an H4a query dataset violates the v1 contract."""


@dataclass(frozen=True)
class ExpectedSource:
    source_kind: str
    source_id: str


@dataclass(frozen=True)
class H4aQuery:
    query_id: str
    category: str
    query: str
    section_id: str | None
    expected_sources: tuple[ExpectedSource, ...]
    notes: str | None


@dataclass(frozen=True)
class H4aQuerySet:
    schema_version: str
    dataset_id: str
    course_id: str
    queries: tuple[H4aQuery, ...]


_TOP_LEVEL_FIELDS = frozenset(
    {"schema_version", "dataset_id", "course_id", "queries"}
)
_QUERY_FIELDS = frozenset(
    {
        "query_id",
        "category",
        "query",
        "section_id",
        "expected_sources",
        "notes",
    }
)
_EXPECTED_SOURCE_FIELDS = frozenset({"source_kind", "source_id"})


def _require_mapping(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise H4aDatasetError(f"{label} must be an object")
    if not all(isinstance(key, str) for key in value):
        raise H4aDatasetError(f"{label} keys must be strings")
    return value


def _require_exact_fields(
    value: dict[str, Any],
    *,
    allowed: frozenset[str],
    required: frozenset[str],
    label: str,
) -> None:
    keys = frozenset(value)
    missing = required - keys
    extra = keys - allowed
    if missing:
        raise H4aDatasetError(
            f"{label} missing fields: {', '.join(sorted(missing))}"
        )
    if extra:
        raise H4aDatasetError(
            f"{label} has unsupported fields: {', '.join(sorted(extra))}"
        )


def _require_nonblank_string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise H4aDatasetError(f"{label} must be a non-blank string")
    return value


def _optional_nonblank_string(value: object, *, label: str) -> str | None:
    if value is None:
        return None
    return _require_nonblank_string(value, label=label)


def parse_h4a_query_set(payload: object) -> H4aQuerySet:
    raw = _require_mapping(payload, label="H4a query set")
    _require_exact_fields(
        raw,
        allowed=_TOP_LEVEL_FIELDS,
        required=_TOP_LEVEL_FIELDS,
        label="H4a query set",
    )

    schema_version = _require_nonblank_string(
        raw["schema_version"], label="schema_version"
    )
    if schema_version != H4A_QUERY_SET_SCHEMA_VERSION:
        raise H4aDatasetError(f"unsupported schema_version: {schema_version}")

    dataset_id = _require_nonblank_string(raw["dataset_id"], label="dataset_id")
    course_id = _require_nonblank_string(raw["course_id"], label="course_id")

    raw_queries = raw["queries"]
    if not isinstance(raw_queries, list):
        raise H4aDatasetError("queries must be an array")

    queries: list[H4aQuery] = []
    query_ids: set[str] = set()
    for index, raw_query_value in enumerate(raw_queries):
        label = f"queries[{index}]"
        raw_query = _require_mapping(raw_query_value, label=label)
        _require_exact_fields(
            raw_query,
            allowed=_QUERY_FIELDS,
            required=_QUERY_FIELDS,
            label=label,
        )

        query_id = _require_nonblank_string(
            raw_query["query_id"], label=f"{label}.query_id"
        )
        if query_id in query_ids:
            raise H4aDatasetError(f"duplicate query_id: {query_id}")
        query_ids.add(query_id)

        category = _require_nonblank_string(
            raw_query["category"], label=f"{label}.category"
        )
        if category not in H4A_QUERY_CATEGORIES:
            raise H4aDatasetError(f"unsupported query category: {category}")

        query_text = _require_nonblank_string(
            raw_query["query"], label=f"{label}.query"
        )
        section_id = _optional_nonblank_string(
            raw_query["section_id"], label=f"{label}.section_id"
        )
        notes = _optional_nonblank_string(
            raw_query["notes"], label=f"{label}.notes"
        )

        raw_expected_sources = raw_query["expected_sources"]
        if not isinstance(raw_expected_sources, list):
            raise H4aDatasetError(f"{label}.expected_sources must be an array")

        expected_sources: list[ExpectedSource] = []
        source_identities: set[tuple[str, str]] = set()
        for source_index, raw_source_value in enumerate(raw_expected_sources):
            source_label = f"{label}.expected_sources[{source_index}]"
            raw_source = _require_mapping(raw_source_value, label=source_label)
            _require_exact_fields(
                raw_source,
                allowed=_EXPECTED_SOURCE_FIELDS,
                required=_EXPECTED_SOURCE_FIELDS,
                label=source_label,
            )
            source_kind = _require_nonblank_string(
                raw_source["source_kind"], label=f"{source_label}.source_kind"
            )
            if source_kind not in H4A_SOURCE_KINDS:
                raise H4aDatasetError(f"unsupported source_kind: {source_kind}")
            source_id = _require_nonblank_string(
                raw_source["source_id"], label=f"{source_label}.source_id"
            )
            identity = (source_kind, source_id)
            if identity in source_identities:
                raise H4aDatasetError(
                    f"{label}.expected_sources contains duplicate source identity: "
                    f"{source_kind}:{source_id}"
                )
            source_identities.add(identity)
            expected_sources.append(
                ExpectedSource(source_kind=source_kind, source_id=source_id)
            )

        if category == "negative_zero_result":
            if expected_sources:
                raise H4aDatasetError(
                    f"{label}.negative_zero_result must have no expected sources"
                )
        elif not expected_sources:
            raise H4aDatasetError(
                f"{label}.{category} requires at least one expected source"
            )

        queries.append(
            H4aQuery(
                query_id=query_id,
                category=category,
                query=query_text,
                section_id=section_id,
                expected_sources=tuple(expected_sources),
                notes=notes,
            )
        )

    return H4aQuerySet(
        schema_version=schema_version,
        dataset_id=dataset_id,
        course_id=course_id,
        queries=tuple(queries),
    )


def canonical_query_set_json(query_set: H4aQuerySet) -> str:
    value = {
        "schema_version": query_set.schema_version,
        "dataset_id": query_set.dataset_id,
        "course_id": query_set.course_id,
        "queries": [
            {
                "query_id": item.query_id,
                "category": item.category,
                "query": item.query,
                "section_id": item.section_id,
                "expected_sources": [
                    {
                        "source_kind": source.source_kind,
                        "source_id": source.source_id,
                    }
                    for source in item.expected_sources
                ],
                "notes": item.notes,
            }
            for item in query_set.queries
        ],
    }
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def query_set_sha256(query_set: H4aQuerySet) -> str:
    canonical = canonical_query_set_json(query_set).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
