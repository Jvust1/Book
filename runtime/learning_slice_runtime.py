"""Deterministic, source-referenced learning-slice projections for Section modes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .section_learning_runtime import SectionLearningRuntime


LEARNING_SLICE_SCHEMA_VERSION = "learning_slice_v1"
REVIEW_PRESET_IDS = ("one_minute", "five_minute", "full")
PRACTICE_KIND_IDS = ("all", "exercise", "problem")

_THEOREM_FAMILY_TYPES = frozenset({"theorem", "proposition", "lemma", "corollary"})
_OBJECTIVE_CATEGORY_ORDER = ("definition", "theorem_family", "formula", "example", "practice")
_QUICK_CHECK_CATEGORY_ORDER = ("definition", "theorem_family", "formula")


class LearningSliceRuntimeError(RuntimeError):
    """Base error for deterministic learning-slice projection failures."""


class LearningSliceIntegrityError(LearningSliceRuntimeError):
    """Raised when source-backed learning identities are invalid or ambiguous."""


class LearningSliceModeError(LearningSliceRuntimeError):
    """Raised when a learning-slice mode cannot be projected."""


@dataclass(frozen=True)
class LearningSliceProjection:
    payload: dict[str, object]
    source_refs: tuple[tuple[str, str], ...]


class LearningSliceRuntime:
    """Project SectionLearningRuntime evidence into deterministic UI metadata."""

    def __init__(self, learning: SectionLearningRuntime):
        self._learning = learning
        source = learning.source()
        self._objects = [dict(row) for row in source.objects]
        self._figures = [dict(row) for row in source.figures]
        self._translations = [dict(row) for row in source.translation_sources]
        self._validate_source_identities()

    def preview(self) -> LearningSliceProjection:
        object_counts = self._object_counts()
        objective_rows = self._select_diverse(
            self._objects,
            category_order=_OBJECTIVE_CATEGORY_ORDER,
            cap=8,
        )
        quick_check_rows = self._select_diverse(
            self._objects,
            category_order=_QUICK_CHECK_CATEGORY_ORDER,
            cap=6,
        )

        payload: dict[str, object] = {
            "schema_version": LEARNING_SLICE_SCHEMA_VERSION,
            "mode": "preview",
            "overview": {
                "object_count": len(self._objects),
                "figure_count": len(self._figures),
                "translation_available": any(
                    row.get("available") is True for row in self._translations
                ),
            },
            "object_counts": object_counts,
            "objectives": [self._objective_prompt(row) for row in objective_rows],
            "prerequisites": {"status": "unavailable", "items": []},
            "core_definitions": [
                self._source_ref("object", row.get("id"))
                for row in self._objects
                if self._normalize_type(row) == "definition"
            ],
            "core_formulas": self._core_formula_refs(),
            "key_figures": [
                self._source_ref("figure", row.get("id")) for row in self._figures
            ],
            "quick_checks": [self._quick_check_prompt(row) for row in quick_check_rows],
        }
        return self._projection(payload)

    def review(self) -> LearningSliceProjection:
        return self._projection(
            {
                "schema_version": LEARNING_SLICE_SCHEMA_VERSION,
                "mode": "review",
                "presets": [
                    {"id": "one_minute", "label": "1 分钟", "source_refs": []},
                    {"id": "five_minute", "label": "5 分钟", "source_refs": []},
                    {"id": "full", "label": "完整复习", "source_refs": []},
                ],
                "prompts": [],
            }
        )

    def practice(self) -> LearningSliceProjection:
        return self._projection(
            {
                "schema_version": LEARNING_SLICE_SCHEMA_VERSION,
                "mode": "practice",
                "filters": [{"id": "all", "label": "全部"}],
                "items": [],
            }
        )

    def learn(self) -> LearningSliceProjection:
        return self._projection(
            {
                "schema_version": LEARNING_SLICE_SCHEMA_VERSION,
                "mode": "learn",
                "groups": [],
                "extensions": {
                    "supplementary": {"status": "unavailable"},
                    "lecture": {"status": "unavailable"},
                },
            }
        )

    def presentation(self, mode: str) -> LearningSliceProjection:
        normalized = str(mode or "").strip().casefold()
        if normalized == "preview":
            return self.preview()
        if normalized == "review":
            return self.review()
        if normalized == "practice":
            return self.practice()
        if normalized == "learn":
            return self.learn()
        raise LearningSliceModeError(f"Unsupported learning-slice mode: {mode!r}")

    def _validate_source_identities(self) -> None:
        seen: set[tuple[str, str]] = set()
        rows = (
            [("object", row.get("id")) for row in self._objects]
            + [("figure", row.get("id")) for row in self._figures]
            + [("translation", row.get("batch_id")) for row in self._translations]
        )
        for kind, source_id in rows:
            ref = self._source_pair(kind, source_id)
            if ref in seen:
                raise LearningSliceIntegrityError(
                    f"Duplicate learning source identity: {ref[0]}:{ref[1]}"
                )
            seen.add(ref)

    @staticmethod
    def _normalize_type(row: dict[str, Any]) -> str:
        return str(row.get("type") or "").strip().casefold()

    def _category(self, row: dict[str, Any]) -> str | None:
        object_type = self._normalize_type(row)
        if object_type == "definition":
            return "definition"
        if object_type in _THEOREM_FAMILY_TYPES:
            return "theorem_family"
        if object_type == "formula":
            return "formula"
        if object_type == "example":
            return "example"
        if object_type in {"exercise", "problem"}:
            return "practice"
        return None

    def _label(self, row: dict[str, Any]) -> str:
        for field in ("name_zh", "name_en", "number"):
            value = str(row.get(field) or "").strip()
            if value:
                return value
        object_type = self._normalize_type(row)
        return object_type or "object"

    def _select_diverse(
        self,
        rows: list[dict[str, Any]],
        *,
        category_order: tuple[str, ...],
        cap: int,
    ) -> list[dict[str, Any]]:
        eligible = [row for row in rows if self._category(row) in category_order]
        selected: list[dict[str, Any]] = []
        selected_ids: set[tuple[str, str]] = set()

        for category in category_order:
            match = next((row for row in eligible if self._category(row) == category), None)
            if match is None:
                continue
            identity = self._source_pair("object", match.get("id"))
            selected.append(match)
            selected_ids.add(identity)
            if len(selected) >= cap:
                return selected

        for row in eligible:
            identity = self._source_pair("object", row.get("id"))
            if identity in selected_ids:
                continue
            selected.append(row)
            selected_ids.add(identity)
            if len(selected) >= cap:
                break
        return selected

    def _objective_prompt(self, row: dict[str, Any]) -> dict[str, object]:
        category = self._category(row)
        label = self._label(row)
        templates = {
            "definition": "理解并能复述：{label}",
            "theorem_family": "理解并能说明结论与条件：{label}",
            "formula": "识别并能写出：{label}",
            "example": "能够跟随教材例题：{label}",
            "practice": "尝试教材练习：{label}",
        }
        if category not in templates:
            raise LearningSliceIntegrityError(
                f"Unsupported objective category for source {row.get('id')!r}"
            )
        return {
            "text": templates[category].format(label=label),
            "derivation": "deterministic_template",
            "source_ref": self._source_ref("object", row.get("id")),
        }

    def _quick_check_prompt(self, row: dict[str, Any]) -> dict[str, object]:
        category = self._category(row)
        label = self._label(row)
        templates = {
            "definition": "你能说出「{label}」的定义吗？",
            "theorem_family": "你能说明「{label}」的条件和结论吗？",
            "formula": "你能不看教材写出「{label}」吗？",
        }
        if category not in templates:
            raise LearningSliceIntegrityError(
                f"Unsupported quick-check category for source {row.get('id')!r}"
            )
        return {
            "text": templates[category].format(label=label),
            "derivation": "deterministic_template",
            "source_ref": self._source_ref("object", row.get("id")),
        }

    def _object_counts(self) -> list[dict[str, object]]:
        counts: dict[str, int] = {}
        order: list[str] = []
        for row in self._objects:
            object_type = self._normalize_type(row)
            if object_type not in counts:
                counts[object_type] = 0
                order.append(object_type)
            counts[object_type] += 1
        return [{"object_type": value, "count": counts[value]} for value in order]

    def _core_formula_refs(self) -> list[dict[str, str]]:
        refs: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for row in self._objects:
            has_formula = bool(str(row.get("formula") or "").strip())
            if self._normalize_type(row) != "formula" and not has_formula:
                continue
            pair = self._source_pair("object", row.get("id"))
            if pair in seen:
                continue
            seen.add(pair)
            refs.append({"kind": pair[0], "source_id": pair[1]})
        return refs

    def _projection(self, payload: dict[str, object]) -> LearningSliceProjection:
        refs: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()

        def visit(value: object) -> None:
            if isinstance(value, dict):
                if "kind" in value and "source_id" in value:
                    pair = self._source_pair(value.get("kind"), value.get("source_id"))
                    if pair not in seen:
                        seen.add(pair)
                        refs.append(pair)
                for nested in value.values():
                    visit(nested)
            elif isinstance(value, (list, tuple)):
                for nested in value:
                    visit(nested)

        visit(payload)
        return LearningSliceProjection(payload=payload, source_refs=tuple(refs))

    def _source_ref(self, kind: object, source_id: object) -> dict[str, str]:
        pair = self._source_pair(kind, source_id)
        return {"kind": pair[0], "source_id": pair[1]}

    @staticmethod
    def _source_pair(kind: object, source_id: object) -> tuple[str, str]:
        normalized_kind = str(kind or "").strip()
        normalized_id = str(source_id or "").strip()
        if not normalized_kind or not normalized_id:
            raise LearningSliceIntegrityError("Learning source identity must be non-blank")
        return normalized_kind, normalized_id
