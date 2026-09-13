from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError

import app.api.models as models
from app.api.errors import AppUnavailableError
from app.api.main import app, get_service
from app.api.service import BookAppService
from runtime import LearningSliceProjection


REPO_ROOT = Path(__file__).resolve().parents[1]


def preview_payload(source_id: str = "def_fixture") -> dict[str, object]:
    return {
        "schema_version": "learning_slice_v1",
        "mode": "preview",
        "overview": {
            "object_count": 1,
            "figure_count": 0,
            "translation_available": False,
        },
        "object_counts": [],
        "objectives": [
            {
                "text": "理解并能复述：测试定义",
                "derivation": "deterministic_template",
                "source_ref": {"kind": "object", "source_id": source_id},
            }
        ],
        "prerequisites": {"status": "unavailable", "items": []},
        "core_definitions": [],
        "core_formulas": [],
        "key_figures": [],
        "quick_checks": [],
    }


def minimal_mode_response_payload() -> dict[str, object]:
    return {
        "mode": "preview",
        "course_id": "course",
        "book_id": "book",
        "chapter_id": "chapter",
        "section_id": "section",
        "source_status": "READY",
        "items": [],
        "source_refs": [],
    }


class LearningSliceModelContractTests(unittest.TestCase):
    def test_mode_response_requires_typed_presentation(self) -> None:
        self.assertIn("presentation", models.ModeResponse.model_fields)
        with self.assertRaises(ValidationError):
            models.ModeResponse(**minimal_mode_response_payload())

    def test_learning_slice_presentation_is_discriminated_by_mode(self) -> None:
        self.assertTrue(hasattr(models, "LearningSlicePresentation"))
        adapter = TypeAdapter(models.LearningSlicePresentation)
        payloads = (
            preview_payload(),
            {
                "schema_version": "learning_slice_v1",
                "mode": "review",
                "presets": [],
                "prompts": [],
            },
            {
                "schema_version": "learning_slice_v1",
                "mode": "practice",
                "filters": [],
                "items": [],
            },
            {
                "schema_version": "learning_slice_v1",
                "mode": "learn",
                "groups": [],
                "extensions": {
                    "supplementary": {"status": "unavailable"},
                    "lecture": {"status": "unavailable"},
                },
            },
        )
        for payload in payloads:
            with self.subTest(mode=payload["mode"]):
                parsed = adapter.validate_python(payload)
                self.assertEqual(parsed.mode, payload["mode"])

        wrong_shape = {
            "schema_version": "learning_slice_v1",
            "mode": "review",
            "overview": {
                "object_count": 0,
                "figure_count": 0,
                "translation_available": False,
            },
            "object_counts": [],
            "objectives": [],
            "prerequisites": {"status": "unavailable", "items": []},
            "core_definitions": [],
            "core_formulas": [],
            "key_figures": [],
            "quick_checks": [],
        }
        with self.assertRaises(ValidationError):
            adapter.validate_python(wrong_shape)

    def test_presentation_is_added_only_to_mode_response_top_level(self) -> None:
        self.assertIn("presentation", models.ModeResponse.model_fields)
        for response_model in (models.SearchResponse, models.SourceResponse, models.QAResponse):
            with self.subTest(model=response_model.__name__):
                self.assertNotIn("presentation", response_model.model_fields)


class LearningSliceServiceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = BookAppService(REPO_ROOT)

    def test_preview_service_response_contains_typed_presentation_with_closed_refs(self) -> None:
        response = self.service.mode("functional_analysis_course", "ch01_s01", "preview")
        dumped = response.model_dump()
        self.assertIn("presentation", dumped)
        self.assertEqual(dumped["presentation"]["mode"], "preview")
        allowed = {(item.kind, item.source_id) for item in response.items}
        projection_refs: set[tuple[str, str]] = set()

        def visit(value: object) -> None:
            if isinstance(value, dict):
                if "kind" in value and "source_id" in value:
                    projection_refs.add((str(value["kind"]), str(value["source_id"])))
                for nested in value.values():
                    visit(nested)
            elif isinstance(value, list):
                for nested in value:
                    visit(nested)

        visit(dumped["presentation"])
        self.assertTrue(projection_refs.issubset(allowed))

    def test_all_four_service_modes_emit_matching_presentation_discriminators(self) -> None:
        for mode in ("preview", "learn", "review", "practice"):
            with self.subTest(mode=mode):
                response = self.service.mode("functional_analysis_course", "ch01_s01", mode)
                self.assertEqual(response.presentation.mode, mode)

    def test_projection_ref_outside_current_mode_items_fails_closed(self) -> None:
        bad_payload = preview_payload("missing_source")
        bad_projection = LearningSliceProjection(
            payload=bad_payload,
            source_refs=(("object", "missing_source"),),
        )
        with patch(
            "runtime.learning_slice_runtime.LearningSliceRuntime.presentation",
            return_value=bad_projection,
        ):
            with self.assertRaises(AppUnavailableError) as ctx:
                self.service.mode("functional_analysis_course", "ch01_s01", "preview")
        self.assertEqual(ctx.exception.code, "learning_slice_integrity_error")
        self.assertEqual(ctx.exception.user_message, "学习内容暂不可用")


class LearningSliceApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = BookAppService(REPO_ROOT)
        app.dependency_overrides[get_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.client.close()

    def test_integrity_error_maps_to_safe_503_without_internal_detail(self) -> None:
        bad_payload = preview_payload("missing_source")
        bad_projection = LearningSliceProjection(
            payload=bad_payload,
            source_refs=(("object", "missing_source"),),
        )
        with patch(
            "runtime.learning_slice_runtime.LearningSliceRuntime.presentation",
            return_value=bad_projection,
        ):
            response = self.client.get(
                "/api/courses/functional_analysis_course/sections/ch01_s01/preview"
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"error": {"code": "learning_slice_integrity_error", "message": "学习内容暂不可用"}},
        )
        self.assertNotIn("missing_source", response.text)
        self.assertNotIn("Traceback", response.text)


if __name__ == "__main__":
    unittest.main()
