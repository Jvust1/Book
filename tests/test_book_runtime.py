from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.book_runtime import BookRuntime, BookRuntimeBlockedError
from tests.test_search_recovery_diagnostics import SearchRecoveryDiagnostics  # noqa: F401
from tools import rebuild_runtime_artifacts as rebuild


class BookRuntimeTests(unittest.TestCase):
    def test_current_functional_analysis_fixture_is_blocked_until_assets_are_restored(self) -> None:
        root = Path(__file__).resolve().parents[1] / "books" / "functional-analysis"
        if not root.exists():
            self.skipTest("repository fixture not present")

        with self.assertRaises(BookRuntimeBlockedError):
            BookRuntime.open(root)

    def test_v036_index_tail_falls_back_to_completed_learning_layer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._dump(
                root / "chunk_023a_structure.json",
                {
                    "chunk_id": "chunk_023a",
                    "index_entry_range": [135, 137],
                    "key_object_count": 3,
                },
            )
            (root / "chunk_023a_translation_zh.md").write_text(
                "# final index learning layer\n\n"
                "## PDF 441 / printed 422\n\n"
                "- **measure** — `measure, 29`\n"
                "- **Minkowski inequality** — `Minkowski inequality, 4`\n\n"
                "## PDF 442 / printed 423\n\n"
                "- **zig-zag function** — `zig-zag function, 165`\n",
                encoding="utf-8",
            )

            records: dict[str, dict[str, object]] = {}
            stats = {"expanded_index_v036_tail_count": 0}
            rebuild.append_v036_index_tail(
                records,
                root,
                book_id="fixture_book_2026",
                stats=stats,
            )

            self.assertEqual(
                list(records),
                ["index_entry_135", "index_entry_136", "index_entry_137"],
            )
            self.assertEqual(records["index_entry_135"]["term"], "measure")
            self.assertEqual(records["index_entry_135"]["pdf_page"], 441)
            self.assertEqual(records["index_entry_137"]["pdf_page"], 442)
            self.assertEqual(stats["expanded_index_v036_tail_count"], 3)

    def test_minimal_ready_fixture_normalizes_sections_objects_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_ready_fixture(root)

            runtime = BookRuntime.open(root)

            self.assertTrue(runtime.is_ready)
            self.assertEqual(runtime.book_id, "fixture_book_2026")
            self.assertEqual(runtime.chapter_ids(), ["chapter_01"])
            self.assertIn("ch01_s01", runtime.sections)
            self.assertIn("def_x", runtime.objects)
            self.assertEqual(runtime.object("def_x").section_id, "ch01_s01")
            self.assertEqual(runtime.page_map_row(1)["printed_page"], "1")

            hits = runtime.search("测试定义")
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["id"], "def_x")

    @staticmethod
    def _dump(path: Path, data: object) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _write_ready_fixture(self, root: Path) -> None:
        self._dump(
            root / "RUNTIME_READINESS.json",
            {
                "status": "READY",
                "book_id": "fixture_book_2026",
                "structured_version": "v1",
                "missing_required_files": [],
                "stale_files": [],
            },
        )
        self._dump(
            root / "STRUCTURED_COMPLETE.json",
            {
                "status": "STRUCTURED_COMPLETE",
                "book_id": "fixture_book_2026",
                "pdf_pages": 2,
                "printed_final_page": 2,
                "version": "v1",
                "audit_fail_count": 0,
                "audit_report": "BOOK_AUDIT_REPORT.md",
                "search_index": "search_index_v1.jsonl",
            },
        )
        self._dump(
            root / "book_metadata.json",
            {
                "book_id": "fixture_book_2026",
                "title_en": "Fixture",
                "title_zh": "测试教材",
                "pdf_total_pages": 2,
                "toc_file": "toc_bilingual.json",
                "page_map_file": "page_map.csv",
            },
        )
        self._dump(
            root / "qa_retrieval_policy.json",
            {
                "version": "1",
                "book_id": "fixture_book_2026",
                "answer_policy": {"must_return_source_anchors": True},
            },
        )
        self._dump(
            root / "toc_bilingual.json",
            {
                "chapters": [
                    {
                        "id": "chapter_01",
                        "number": "1",
                        "title_en": "Test chapter",
                        "title_zh": "测试章",
                    }
                ]
            },
        )
        (root / "page_map.csv").write_text(
            "pdf_page,printed_page,page_label\n1,1,1\n2,2,2\n",
            encoding="utf-8",
        )
        (root / "BOOK_AUDIT_REPORT.md").write_text("FAIL = 0\n", encoding="utf-8")
        self._dump(
            root / "chunk_001a_structure.json",
            {
                "chunk_id": "chunk_001a",
                "pdf_pages": [1, 2],
                "printed_pages": [1, 2],
                "chapter_id": "chapter_01",
                "sections": [
                    {
                        "id": "ch01_s01",
                        "number": "1",
                        "title_en": "Section",
                        "title_zh": "小节",
                        "pdf_pages": [1, 2],
                        "printed_pages": [1, 2],
                    }
                ],
                "key_objects": [
                    {
                        "type": "definition",
                        "id": "def_x",
                        "name_zh": "测试定义",
                        "anchor": {"pdf_page": 1, "printed_page": 1},
                    }
                ],
            },
        )
        (root / "chunk_001a_translation_zh.md").write_text("# 测试学习层\n", encoding="utf-8")
        (root / "search_index_v1.jsonl").write_text(
            json.dumps(
                {
                    "id": "def_x",
                    "book_id": "fixture_book_2026",
                    "type": "definition",
                    "name_zh": "测试定义",
                    "pdf_page": 1,
                    "printed_page": 1,
                    "source_anchor": "fixture_book_2026:pdf:1:def_x",
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
