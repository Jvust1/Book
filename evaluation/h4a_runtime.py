"""Deterministic H4a evaluation query-set, metric, and report contracts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping, Sequence


H4A_QUERY_SET_SCHEMA_VERSION = "h4a_query_set_v1"
H4A_REPORT_SCHEMA_VERSION = "h4a_report_v1"
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


@dataclass(frozen=True)
class RankedSource:
    source_kind: str
    source_id: str
    rank: int

    @property
    def key(self) -> tuple[str, str]:
        return (self.source_kind, self.source_id)


@dataclass(frozen=True)
class QueryMetrics:
    hit_at_1: bool | None
    hit_at_5: bool | None
    hit_at_10: bool | None
    recall_at_10: float | None
    reciprocal_rank: float | None
    negative_clean_at_10: bool | None
    unexpected_hit_count_at_10: int | None


@dataclass(frozen=True)
class ComparativeRecovery:
    fts_only_recovery_at_10: tuple[ExpectedSource, ...]
    exact_only_recovery_at_10: tuple[ExpectedSource, ...]


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
_REPORT_TOP_LEVEL_FIELDS = (
    "schema_version",
    "stage",
    "course",
    "dataset",
    "profiles",
    "environment",
    "queries",
    "aggregates",
    "gates",
    "evidence",
)
_FORBIDDEN_REPORT_KEYS = frozenset(
    {
        "timestamp",
        "wall_clock",
        "wall_clock_time",
        "activate_fts",
        "activation_flag",
        "absolute_path",
        "temp_path",
    }
)


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


def load_h4a_query_set(path: Path) -> H4aQuerySet:
    """Load and validate one UTF-8 H4a query set without modifying it."""

    try:
        payload_text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise H4aDatasetError(f"cannot read H4a query set: {path}") from exc

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise H4aDatasetError(f"invalid H4a query set JSON: {path}") from exc

    return parse_h4a_query_set(payload)


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


def _validate_ranked_sources(
    ranked_sources: Sequence[RankedSource],
) -> tuple[RankedSource, ...]:
    validated: list[RankedSource] = []
    seen: set[tuple[str, str]] = set()
    for source in ranked_sources:
        if not isinstance(source, RankedSource):
            raise H4aEvaluationError("ranked result must be RankedSource")
        if source.source_kind not in H4A_SOURCE_KINDS:
            raise H4aEvaluationError(
                f"unsupported ranked source kind: {source.source_kind}"
            )
        if not source.source_id.strip():
            raise H4aEvaluationError("ranked source_id must be non-blank")
        if isinstance(source.rank, bool) or not isinstance(source.rank, int) or source.rank <= 0:
            raise H4aEvaluationError("rank must be a positive integer")
        if source.key in seen:
            raise H4aEvaluationError(
                f"duplicate ranked source identity: {source.source_kind}:{source.source_id}"
            )
        seen.add(source.key)
        validated.append(source)
    return tuple(validated)


def _expected_keys(query: H4aQuery) -> tuple[tuple[str, str], ...]:
    return tuple((source.source_kind, source.source_id) for source in query.expected_sources)


def compute_query_metrics(
    query: H4aQuery,
    ranked_sources: Sequence[RankedSource],
) -> QueryMetrics:
    """Compute positive or deliberate-negative metrics without synthetic denominators."""

    ranked = _validate_ranked_sources(ranked_sources)
    is_negative = query.category == "negative_zero_result"
    expected_keys = _expected_keys(query)

    if is_negative:
        if expected_keys:
            raise H4aEvaluationError("negative query must not have expected sources")
        top_10_count = sum(source.rank <= 10 for source in ranked)
        return QueryMetrics(
            hit_at_1=None,
            hit_at_5=None,
            hit_at_10=None,
            recall_at_10=None,
            reciprocal_rank=None,
            negative_clean_at_10=top_10_count == 0,
            unexpected_hit_count_at_10=top_10_count,
        )

    if not expected_keys:
        raise H4aEvaluationError("positive query requires expected sources")

    ranks_by_key = {source.key: source.rank for source in ranked}
    matched_ranks = [
        ranks_by_key[key]
        for key in expected_keys
        if key in ranks_by_key
    ]
    top_10_relevant_count = sum(rank <= 10 for rank in matched_ranks)
    first_rank = min(matched_ranks) if matched_ranks else None

    return QueryMetrics(
        hit_at_1=any(rank <= 1 for rank in matched_ranks),
        hit_at_5=any(rank <= 5 for rank in matched_ranks),
        hit_at_10=any(rank <= 10 for rank in matched_ranks),
        recall_at_10=top_10_relevant_count / len(expected_keys),
        reciprocal_rank=0.0 if first_rank is None else 1.0 / first_rank,
        negative_clean_at_10=None,
        unexpected_hit_count_at_10=None,
    )


def comparative_recovery_at_10(
    query: H4aQuery,
    *,
    exact_ranked: Sequence[RankedSource],
    candidate_ranked: Sequence[RankedSource],
) -> ComparativeRecovery:
    """Compare relevant top-10 identity coverage while preserving ground-truth order."""

    if query.category == "negative_zero_result" or not query.expected_sources:
        raise H4aEvaluationError("comparative recovery requires a positive query")

    exact = _validate_ranked_sources(exact_ranked)
    candidate = _validate_ranked_sources(candidate_ranked)
    exact_top_10 = {source.key for source in exact if source.rank <= 10}
    candidate_top_10 = {source.key for source in candidate if source.rank <= 10}

    fts_only: list[ExpectedSource] = []
    exact_only: list[ExpectedSource] = []
    for expected in query.expected_sources:
        key = (expected.source_kind, expected.source_id)
        if key in candidate_top_10 and key not in exact_top_10:
            fts_only.append(expected)
        if key in exact_top_10 and key not in candidate_top_10:
            exact_only.append(expected)

    return ComparativeRecovery(
        fts_only_recovery_at_10=tuple(fts_only),
        exact_only_recovery_at_10=tuple(exact_only),
    )


def _ensure_metric_value_is_finite(value: float | None, *, label: str) -> None:
    if value is not None and not math.isfinite(value):
        raise H4aEvaluationError(f"{label} must be finite")


def aggregate_query_metrics(
    metrics: Sequence[QueryMetrics],
) -> dict[str, object]:
    """Aggregate metrics with separate positive and negative denominators."""

    positive: list[QueryMetrics] = []
    negative: list[QueryMetrics] = []
    for item in metrics:
        if not isinstance(item, QueryMetrics):
            raise H4aEvaluationError("aggregate input must contain QueryMetrics")
        _ensure_metric_value_is_finite(item.recall_at_10, label="recall_at_10")
        _ensure_metric_value_is_finite(
            item.reciprocal_rank, label="reciprocal_rank"
        )

        positive_shape = (
            item.hit_at_1 is not None
            and item.hit_at_5 is not None
            and item.hit_at_10 is not None
            and item.recall_at_10 is not None
            and item.reciprocal_rank is not None
            and item.negative_clean_at_10 is None
            and item.unexpected_hit_count_at_10 is None
        )
        negative_shape = (
            item.hit_at_1 is None
            and item.hit_at_5 is None
            and item.hit_at_10 is None
            and item.recall_at_10 is None
            and item.reciprocal_rank is None
            and item.negative_clean_at_10 is not None
            and item.unexpected_hit_count_at_10 is not None
        )
        if positive_shape:
            positive.append(item)
        elif negative_shape:
            if (
                isinstance(item.unexpected_hit_count_at_10, bool)
                or item.unexpected_hit_count_at_10 < 0
            ):
                raise H4aEvaluationError(
                    "unexpected_hit_count_at_10 must be a non-negative integer"
                )
            negative.append(item)
        else:
            raise H4aEvaluationError("QueryMetrics has inconsistent positive/negative shape")

    positive_count = len(positive)
    negative_count = len(negative)
    result: dict[str, object] = {
        "positive_query_count": positive_count,
        "negative_query_count": negative_count,
        "hit_at_1_rate": None,
        "hit_at_5_rate": None,
        "hit_at_10_rate": None,
        "recall_at_10": None,
        "mrr": None,
        "negative_clean_at_10_rate": None,
        "unexpected_hit_count_at_10": None,
    }
    if positive_count:
        result.update(
            {
                "hit_at_1_rate": sum(bool(item.hit_at_1) for item in positive)
                / positive_count,
                "hit_at_5_rate": sum(bool(item.hit_at_5) for item in positive)
                / positive_count,
                "hit_at_10_rate": sum(bool(item.hit_at_10) for item in positive)
                / positive_count,
                "recall_at_10": sum(float(item.recall_at_10) for item in positive)
                / positive_count,
                "mrr": sum(float(item.reciprocal_rank) for item in positive)
                / positive_count,
            }
        )
    if negative_count:
        result.update(
            {
                "negative_clean_at_10_rate": sum(
                    bool(item.negative_clean_at_10) for item in negative
                )
                / negative_count,
                "unexpected_hit_count_at_10": sum(
                    int(item.unexpected_hit_count_at_10) for item in negative
                ),
            }
        )

    _validate_finite_recursively(result)
    return result


def _validate_finite_recursively(value: object, *, path: str = "report") -> None:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise H4aEvaluationError(f"{path} contains non-finite numeric value")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise H4aEvaluationError(f"{path} contains non-string mapping key")
            _validate_finite_recursively(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_finite_recursively(item, path=f"{path}[{index}]")
        return
    raise H4aEvaluationError(f"{path} contains unsupported value type")


def _is_absolute_path_string(value: str) -> bool:
    return PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()


def _copy_report_value(value: object, *, path: str) -> object:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise H4aEvaluationError(f"{path} contains non-finite numeric value")
        return value
    if isinstance(value, str):
        if _is_absolute_path_string(value):
            raise H4aEvaluationError(f"{path} must not contain an absolute path")
        return value
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise H4aEvaluationError(f"{path} contains non-string mapping key")
            if key.lower() in _FORBIDDEN_REPORT_KEYS:
                raise H4aEvaluationError(f"{path} contains forbidden field: {key}")
            copied[key] = _copy_report_value(item, path=f"{path}.{key}")
        return copied
    if isinstance(value, (list, tuple)):
        return [
            _copy_report_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    raise H4aEvaluationError(f"{path} contains unsupported value type")


def build_h4a_report(
    *,
    query_set: H4aQuerySet,
    course_identity: Mapping[str, object],
    profile_definitions: Sequence[Mapping[str, object]],
    sqlite_version: str,
    fts5_available: bool,
    query_results: Sequence[Mapping[str, object]],
    aggregate_metrics: Mapping[str, object],
    gates: Mapping[str, object],
    evidence: Mapping[str, object],
) -> dict[str, object]:
    """Assemble the closed deterministic H4a report envelope without wall clock data."""

    if not isinstance(query_set, H4aQuerySet):
        raise H4aEvaluationError("query_set must be H4aQuerySet")
    if not isinstance(sqlite_version, str) or not sqlite_version.strip():
        raise H4aEvaluationError("sqlite_version must be non-blank")
    if not isinstance(fts5_available, bool):
        raise H4aEvaluationError("fts5_available must be boolean")

    report: dict[str, object] = {
        "schema_version": H4A_REPORT_SCHEMA_VERSION,
        "stage": "H4a",
        "course": _copy_report_value(course_identity, path="report.course"),
        "dataset": {
            "schema_version": query_set.schema_version,
            "dataset_id": query_set.dataset_id,
            "content_sha256": query_set_sha256(query_set),
        },
        "profiles": _copy_report_value(
            tuple(profile_definitions), path="report.profiles"
        ),
        "environment": {
            "sqlite_version": sqlite_version,
            "fts5_available": fts5_available,
        },
        "queries": _copy_report_value(tuple(query_results), path="report.queries"),
        "aggregates": _copy_report_value(
            aggregate_metrics, path="report.aggregates"
        ),
        "gates": _copy_report_value(gates, path="report.gates"),
        "evidence": _copy_report_value(evidence, path="report.evidence"),
    }
    if tuple(report) != _REPORT_TOP_LEVEL_FIELDS:
        raise H4aEvaluationError("H4a report top-level shape drifted")
    _validate_finite_recursively(report)
    return report


def canonical_h4a_report_json(report: Mapping[str, object]) -> str:
    """Serialize H4a evidence canonically while rejecting unstable/non-finite data."""

    if not isinstance(report, Mapping):
        raise H4aEvaluationError("H4a report must be a mapping")
    if set(report) != set(_REPORT_TOP_LEVEL_FIELDS):
        raise H4aEvaluationError("H4a report has unsupported top-level shape")
    copied = _copy_report_value(report, path="report")
    _validate_finite_recursively(copied)
    return json.dumps(
        copied,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
