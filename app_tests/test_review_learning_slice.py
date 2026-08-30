from __future__ import annotations

import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app, get_service
from app.api.service import BookAppService


REPO_ROOT = Path(__file__).resolve().parents[1]
THEOREM_FAMILY = {"theorem", "proposition", "lemma", "corollary"}


def source_pairs(items) -> list[tuple[str, str]]:
    return [(item.kind, item.source_id) for item in items]


def expected_preset_pairs(items, cap: int | None) -> list[tuple[str, str]]:
    if cap is None:
        return source_pairs(items)

    selected = []
    selected_pairs: set[tuple[str, str]] = set()

    def category(item) -> str | None:
        object_type = str(item.object_type or "").strip().casefold()
        if object_type == "definition":
            return "definition"
        if object_type in THEOREM_FAMILY:
            return "theorem_family"
        if object_type == "formula":
            return "formula"
        return None

    for wanted in ("definition", "theorem_family", "formula"):
        match = next((item for item in items if category(item) == wanted), None)
        if match is None:
            continue
        pair = (match.kind, match.source_id)
        selected.append(pair)
        selected_pairs.add(pair)
        if len(selected) >= cap:
            return selected

    for item in items:
        pair = (item.kind, item.source_id)
        if pair in selected_pairs:
            continue
        selected.append(pair)
        selected_pairs.add(pair)
        if len(selected) >= cap:
            break
    return selected


class ReviewLearningSliceServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = BookAppService(REPO_ROOT)

    def test_review_service_serializes_exact_presets_membership_and_prompts(self) -> None:
        response = self.service.mode("functional_analysis_course", "ch01_s01", "review")
        presentation = response.presentation

        self.assertEqual(presentation.mode, "review")
        self.assertEqual(
            [(preset.id, preset.label) for preset in presentation.presets],
            [
                ("one_minute", "1 分钟"),
                ("five_minute", "5 分钟"),
                ("full", "完整复习"),
            ],
        )

        presets = {preset.id: preset for preset in presentation.presets}
        self.assertEqual(
            [(ref.kind, ref.source_id) for ref in presets["one_minute"].source_refs],
            expected_preset_pairs(response.items, 3),
        )
        self.assertEqual(
            [(ref.kind, ref.source_id) for ref in presets["five_minute"].source_refs],
            expected_preset_pairs(response.items, 5),
        )
        self.assertEqual(
            [(ref.kind, ref.source_id) for ref in presets["full"].source_refs],
            expected_preset_pairs(response.items, None),
        )
        self.assertEqual(
            [(prompt.source_ref.kind, prompt.source_ref.source_id) for prompt in presentation.prompts],
            source_pairs(response.items),
        )
        self.assertTrue(
            all(prompt.derivation == "deterministic_template" for prompt in presentation.prompts)
        )


class ReviewLearningSliceApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = BookAppService(REPO_ROOT)
        app.dependency_overrides[get_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.client.close()

    def test_review_api_emits_exact_preset_ids_labels_and_closed_refs(self) -> None:
        response = self.client.get(
            "/api/courses/functional_analysis_course/sections/ch01_s01/review"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        presentation = payload["presentation"]

        self.assertEqual(presentation["mode"], "review")
        self.assertEqual(presentation["schema_version"], "learning_slice_v1")
        self.assertEqual(
            [(preset["id"], preset["label"]) for preset in presentation["presets"]],
            [
                ("one_minute", "1 分钟"),
                ("five_minute", "5 分钟"),
                ("full", "完整复习"),
            ],
        )

        item_pairs = [(item["kind"], item["source_id"]) for item in payload["items"]]
        full_pairs = [
            (ref["kind"], ref["source_id"])
            for ref in next(
                preset for preset in presentation["presets"] if preset["id"] == "full"
            )["source_refs"]
        ]
        prompt_pairs = [
            (prompt["source_ref"]["kind"], prompt["source_ref"]["source_id"])
            for prompt in presentation["prompts"]
        ]
        self.assertEqual(full_pairs, item_pairs)
        self.assertEqual(prompt_pairs, item_pairs)
        self.assertTrue(
            all(prompt["derivation"] == "deterministic_template" for prompt in presentation["prompts"])
        )


if __name__ == "__main__":
    unittest.main()
