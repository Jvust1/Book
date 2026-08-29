"""Pure deterministic Concept / ConceptAlignment contract for Foundation B H3a."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


CONCEPT_GRAPH_SCHEMA_VERSION = "concept_graph_v1"
ALIGNMENT_RELATIONS = frozenset(
    {
        "defines",
        "explains",
        "proves",
        "examples",
        "exercises",
        "extends",
        "contrasts",
    }
)


class ConceptGraphValidationError(ValueError):
    """Raised when a Concept graph violates the local v1 contract."""


@dataclass(frozen=True)
class Concept:
    concept_id: str
    title: str
    aliases: tuple[str, ...] = ()
    prerequisite_concept_ids: tuple[str, ...] = ()
    revision: str = ""
    provenance: str = ""


@dataclass(frozen=True)
class ConceptAlignment:
    alignment_id: str
    concept_id: str
    book_version_id: str
    relation: str
    section_id: str | None = None
    source_kind: str | None = None
    source_id: str | None = None
    confidence: float | None = None
    revision: str = ""
    provenance: str = ""


@dataclass(frozen=True)
class ConceptGraph:
    schema_version: str
    concepts: tuple[Concept, ...]
    alignments: tuple[ConceptAlignment, ...]


_TOP_LEVEL_FIELDS = frozenset({"schema_version", "concepts", "alignments"})
_CONCEPT_FIELDS = frozenset(
    {
        "concept_id",
        "title",
        "aliases",
        "prerequisite_concept_ids",
        "revision",
        "provenance",
    }
)
_ALIGNMENT_FIELDS = frozenset(
    {
        "alignment_id",
        "concept_id",
        "book_version_id",
        "section_id",
        "source_kind",
        "source_id",
        "relation",
        "confidence",
        "revision",
        "provenance",
    }
)


def _require_mapping(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConceptGraphValidationError(f"{label} must be an object")
    if not all(isinstance(key, str) for key in value):
        raise ConceptGraphValidationError(f"{label} keys must be strings")
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
        raise ConceptGraphValidationError(
            f"{label} missing fields: {', '.join(sorted(missing))}"
        )
    if extra:
        raise ConceptGraphValidationError(
            f"{label} has unsupported fields: {', '.join(sorted(extra))}"
        )


def _require_nonblank_string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConceptGraphValidationError(f"{label} must be a non-blank string")
    return value


def _optional_nonblank_string(value: object, *, label: str) -> str | None:
    if value is None:
        return None
    return _require_nonblank_string(value, label=label)


def _parse_string_list(value: object, *, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConceptGraphValidationError(f"{label} must be an array")
    items = tuple(
        _require_nonblank_string(item, label=f"{label} item") for item in value
    )
    if len(set(items)) != len(items):
        raise ConceptGraphValidationError(f"{label} contains duplicate entries")
    return tuple(sorted(items))


def parse_concept_graph(value: object) -> ConceptGraph:
    raw = _require_mapping(value, label="concept graph")
    _require_exact_fields(
        raw,
        allowed=_TOP_LEVEL_FIELDS,
        required=_TOP_LEVEL_FIELDS,
        label="concept graph",
    )

    schema_version = _require_nonblank_string(
        raw["schema_version"], label="schema_version"
    )
    if schema_version != CONCEPT_GRAPH_SCHEMA_VERSION:
        raise ConceptGraphValidationError(
            f"unsupported schema_version: {schema_version}"
        )

    raw_concepts = raw["concepts"]
    if not isinstance(raw_concepts, list):
        raise ConceptGraphValidationError("concepts must be an array")

    concepts: list[Concept] = []
    concept_ids: set[str] = set()
    for index, raw_concept_value in enumerate(raw_concepts):
        raw_concept = _require_mapping(
            raw_concept_value, label=f"concepts[{index}]"
        )
        _require_exact_fields(
            raw_concept,
            allowed=_CONCEPT_FIELDS,
            required=frozenset(
                {"concept_id", "title", "revision", "provenance"}
            ),
            label=f"concepts[{index}]",
        )
        concept_id = _require_nonblank_string(
            raw_concept["concept_id"], label=f"concepts[{index}].concept_id"
        )
        if concept_id in concept_ids:
            raise ConceptGraphValidationError(
                f"duplicate concept_id: {concept_id}"
            )
        concept_ids.add(concept_id)
        concepts.append(
            Concept(
                concept_id=concept_id,
                title=_require_nonblank_string(
                    raw_concept["title"], label=f"concepts[{index}].title"
                ),
                aliases=_parse_string_list(
                    raw_concept.get("aliases", []),
                    label=f"concepts[{index}].aliases",
                ),
                prerequisite_concept_ids=_parse_string_list(
                    raw_concept.get("prerequisite_concept_ids", []),
                    label=f"concepts[{index}].prerequisite_concept_ids",
                ),
                revision=_require_nonblank_string(
                    raw_concept["revision"],
                    label=f"concepts[{index}].revision",
                ),
                provenance=_require_nonblank_string(
                    raw_concept["provenance"],
                    label=f"concepts[{index}].provenance",
                ),
            )
        )

    for concept in concepts:
        for prerequisite_id in concept.prerequisite_concept_ids:
            if prerequisite_id == concept.concept_id:
                raise ConceptGraphValidationError(
                    f"self prerequisite is not allowed: {concept.concept_id}"
                )
            if prerequisite_id not in concept_ids:
                raise ConceptGraphValidationError(
                    f"unknown prerequisite concept_id: {prerequisite_id}"
                )

    raw_alignments = raw["alignments"]
    if not isinstance(raw_alignments, list):
        raise ConceptGraphValidationError("alignments must be an array")

    alignments: list[ConceptAlignment] = []
    alignment_ids: set[str] = set()
    for index, raw_alignment_value in enumerate(raw_alignments):
        raw_alignment = _require_mapping(
            raw_alignment_value, label=f"alignments[{index}]"
        )
        _require_exact_fields(
            raw_alignment,
            allowed=_ALIGNMENT_FIELDS,
            required=frozenset(
                {
                    "alignment_id",
                    "concept_id",
                    "book_version_id",
                    "relation",
                    "revision",
                    "provenance",
                }
            ),
            label=f"alignments[{index}]",
        )
        alignment_id = _require_nonblank_string(
            raw_alignment["alignment_id"],
            label=f"alignments[{index}].alignment_id",
        )
        if alignment_id in alignment_ids:
            raise ConceptGraphValidationError(
                f"duplicate alignment_id: {alignment_id}"
            )
        alignment_ids.add(alignment_id)

        concept_id = _require_nonblank_string(
            raw_alignment["concept_id"],
            label=f"alignments[{index}].concept_id",
        )
        if concept_id not in concept_ids:
            raise ConceptGraphValidationError(
                f"alignment references unknown concept_id: {concept_id}"
            )

        relation = _require_nonblank_string(
            raw_alignment["relation"], label=f"alignments[{index}].relation"
        )
        if relation not in ALIGNMENT_RELATIONS:
            raise ConceptGraphValidationError(
                f"unsupported alignment relation: {relation}"
            )

        confidence_value = raw_alignment.get("confidence")
        confidence: float | None
        if confidence_value is None:
            confidence = None
        else:
            if isinstance(confidence_value, bool) or not isinstance(
                confidence_value, (int, float)
            ):
                raise ConceptGraphValidationError(
                    f"alignments[{index}].confidence must be a number"
                )
            confidence = float(confidence_value)
            if not 0.0 <= confidence <= 1.0:
                raise ConceptGraphValidationError(
                    f"alignments[{index}].confidence must be within [0.0, 1.0]"
                )

        alignments.append(
            ConceptAlignment(
                alignment_id=alignment_id,
                concept_id=concept_id,
                book_version_id=_require_nonblank_string(
                    raw_alignment["book_version_id"],
                    label=f"alignments[{index}].book_version_id",
                ),
                relation=relation,
                section_id=_optional_nonblank_string(
                    raw_alignment.get("section_id"),
                    label=f"alignments[{index}].section_id",
                ),
                source_kind=_optional_nonblank_string(
                    raw_alignment.get("source_kind"),
                    label=f"alignments[{index}].source_kind",
                ),
                source_id=_optional_nonblank_string(
                    raw_alignment.get("source_id"),
                    label=f"alignments[{index}].source_id",
                ),
                confidence=confidence,
                revision=_require_nonblank_string(
                    raw_alignment["revision"],
                    label=f"alignments[{index}].revision",
                ),
                provenance=_require_nonblank_string(
                    raw_alignment["provenance"],
                    label=f"alignments[{index}].provenance",
                ),
            )
        )

    return ConceptGraph(
        schema_version=schema_version,
        concepts=tuple(sorted(concepts, key=lambda item: item.concept_id)),
        alignments=tuple(
            sorted(alignments, key=lambda item: item.alignment_id)
        ),
    )


def concept_graph_to_canonical_json(graph: ConceptGraph) -> str:
    value = {
        "schema_version": graph.schema_version,
        "concepts": [
            {
                "concept_id": concept.concept_id,
                "title": concept.title,
                "aliases": list(concept.aliases),
                "prerequisite_concept_ids": list(
                    concept.prerequisite_concept_ids
                ),
                "revision": concept.revision,
                "provenance": concept.provenance,
            }
            for concept in sorted(graph.concepts, key=lambda item: item.concept_id)
        ],
        "alignments": [
            {
                "alignment_id": alignment.alignment_id,
                "concept_id": alignment.concept_id,
                "book_version_id": alignment.book_version_id,
                "section_id": alignment.section_id,
                "source_kind": alignment.source_kind,
                "source_id": alignment.source_id,
                "relation": alignment.relation,
                "confidence": alignment.confidence,
                "revision": alignment.revision,
                "provenance": alignment.provenance,
            }
            for alignment in sorted(
                graph.alignments, key=lambda item: item.alignment_id
            )
        ],
    }
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _normalize_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    if not cycle:
        return cycle
    rotations = tuple(cycle[index:] + cycle[:index] for index in range(len(cycle)))
    return min(rotations)


def find_prerequisite_cycles(graph: ConceptGraph) -> tuple[tuple[str, ...], ...]:
    adjacency = {
        concept.concept_id: tuple(sorted(concept.prerequisite_concept_ids))
        for concept in graph.concepts
    }
    state: dict[str, int] = {concept_id: 0 for concept_id in adjacency}
    stack: list[str] = []
    stack_index: dict[str, int] = {}
    found: set[tuple[str, ...]] = set()

    def visit(concept_id: str) -> None:
        state[concept_id] = 1
        stack_index[concept_id] = len(stack)
        stack.append(concept_id)
        for prerequisite_id in adjacency.get(concept_id, ()):
            prerequisite_state = state.get(prerequisite_id, 0)
            if prerequisite_state == 0:
                visit(prerequisite_id)
            elif prerequisite_state == 1:
                cycle = tuple(stack[stack_index[prerequisite_id] :])
                found.add(_normalize_cycle(cycle))
        stack.pop()
        stack_index.pop(concept_id, None)
        state[concept_id] = 2

    for concept_id in sorted(adjacency):
        if state[concept_id] == 0:
            visit(concept_id)

    return tuple(sorted(found))
