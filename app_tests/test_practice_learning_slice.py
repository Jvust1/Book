from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app, get_service
from app.api.service import BookAppService
from tests.runtime_fixture_factory import (
    dump_json,
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


def build_practice_repo(root: Path) -> Path:
    repo = make_repo(root)
    write_ready_book(
        repo / "books" / "fixture-book",
        book_id="fixture_book",
        objects=[
            {
                "type": "exercise",
                "id": "ex_fixture",
                "name_zh": "练习甲",
                "content_zh": "solution sentinel that must not become verified solution metadata",
                "anchor": {"pdf_page": 1, "printed_page": 1},
            },
            {
                "type": "problem",
                "id": "prob_fixture",
                "name_zh": "习题乙",
                "content_zh": "解析 sentinel that must not become verified solution metadata",
                "anchor": {"pdf_page": 1, "printed_page": 1},
            },
        ],
    )
    write_course(
        repo / "courses" / "fixture-course",
        course_id="fixture_course",
        main_book_id="fixture_book",
        book_entries=[main_book_entry("fixture_book", "../../books/fixture-book")],
    )
    dump_json(
        repo / "library" / "library.json",
        {
            "schema_version": "library_manifest_v1",
            "library_id": "fixture_library",
            "name": "测试书架",
            "courses": [
                {
                    "course_id": "fixture_course",
                    "name": "测试课程",
                    "path": "../courses/fixture-course",
                    "enabled": True,
                    "order": 10,
                }
            ],
        },
    )
    return repo


def expected_practice_presentation() -> dict[str, object]:
    ex_ref = {"kind": "object", "source_id": "ex_fixture"}
    prob_ref = {"kind": "object", "source_id": "prob_fixture"}
    return {
        "schema_version": "learning_slice_v1",
        "mode": "practice",
        "filters": [
            {"id": "all", "label": "全部", "source_refs": [ex_ref, prob_ref]},
            {"id": "exercise", "label": "练习", "source_refs": [ex_ref]},
            {"id": "problem", "label": "习题", "source_refs": [prob_ref]},
        ],
        "items": [
            {"source_ref": ex_ref, "solution_status": "unavailable"},
            {"source_ref": prob_ref, "solution_status": "unavailable"},
        ],
    }


class PracticeLearningSliceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.repo = build_practice_repo(Path(self.tempdir.name))
        self.service = BookAppService(self.repo)

    def test_service_serializes_exact_practice_filters_and_solution_status(self) -> None:
        response = self.service.mode("fixture_course", "ch01_s01", "practice")
        self.assertEqual(
            [(item.kind, item.source_id) for item in response.items],
            [("object", "ex_fixture"), ("object", "prob_fixture")],
        )
        presentation = response.model_dump()["presentation"]
        self.assertEqual(presentation, expected_practice_presentation())
        self.assertNotIn("solution sentinel", json.dumps(presentation, ensure_ascii=False))
        self.assertNotIn("解析 sentinel", json.dumps(presentation, ensure_ascii=False))

    def test_filter_refs_are_closed_over_current_practice_mode_items(self) -> None:
        response = self.service.mode("fixture_course", "ch01_s01", "practice")
        allowed = {(item.kind, item.source_id) for item in response.items}
        presentation = response.model_dump()["presentation"]
        for filter_row in presentation["filters"]:
            refs = {
                (str(ref["kind"]), str(ref["source_id"]))
                for ref in filter_row["source_refs"]
            }
            self.assertTrue(refs.issubset(allowed))
        for item in presentation["items"]:
            ref = item["source_ref"]
            self.assertIn((str(ref["kind"]), str(ref["source_id"])), allowed)


class PracticeLearningSliceApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        repo = build_practice_repo(Path(self.tempdir.name))
        self.service = BookAppService(repo)
        app.dependency_overrides[get_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.client.close()

    def test_practice_route_serializes_filter_refs_and_unavailable_solution_state(self) -> None:
        response = self.client.get("/api/courses/fixture_course/sections/ch01_s01/practice")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["presentation"], expected_practice_presentation())
        presentation_text = json.dumps(payload["presentation"], ensure_ascii=False)
        self.assertNotIn("solution sentinel", presentation_text)
        self.assertNotIn("解析 sentinel", presentation_text)


if __name__ == "__main__":
    unittest.main()
