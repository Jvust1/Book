from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.course_runtime import (
    CourseBookResolutionError,
    CourseManifestError,
    CourseRuntime,
    CourseRuntimeBlockedError,
)


class CourseRuntimeTests(unittest.TestCase):
    def test_valid_one_book_course_opens(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(Path(temp))
            book = repo / "books" / "fixture"
            course_dir = repo / "courses" / "fixture-course"
            self._write_ready_book(book, book_id="fixture_book_2026")
            self._write_course_manifest(
                course_dir,
                book_entries=[self._entry("fixture_book_2026", "main", "../../books/fixture")],
                main_book_id="fixture_book_2026",
            )

            course = CourseRuntime.open(course_dir)

            self.assertEqual(course.course_id, "fixture_course")
            self.assertEqual(course.main_book_id, "fixture_book_2026")
            self.assertEqual(course.book_ids(), ["fixture_book_2026"])

    def test_missing_course_id_fails(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override({"course_id": ""})

    def test_empty_books_fails(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override({"books": []})

    def test_duplicate_enabled_book_id_fails(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override(
                {
                    "books": [
                        self._entry("fixture_book_2026", "main", "../../books/a"),
                        self._entry("fixture_book_2026", "supplementary", "../../books/b"),
                    ]
                }
            )

    def test_no_enabled_main_book_fails(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override(
                {"books": [self._entry("fixture_book_2026", "reference", "../../books/a")]}
            )

    def test_multiple_enabled_main_books_fail(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override(
                {
                    "books": [
                        self._entry("fixture_book_2026", "main", "../../books/a"),
                        self._entry("fixture_book_2027", "main", "../../books/b"),
                    ]
                }
            )

    def test_unsupported_role_fails(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override(
                {"books": [self._entry("fixture_book_2026", "primary", "../../books/a")]}
            )

    def test_main_book_id_must_match_enabled_main_entry(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_manifest_override({"main_book_id": "other_book"})

    def test_missing_book_path_fails(self) -> None:
        with self.assertRaises(CourseBookResolutionError):
            self._open_course_with_entry(path="../../books/missing")

    def test_book_path_cannot_escape_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            repo = self._make_repo(Path(temp))
            course_dir = repo / "courses" / "fixture-course"
            outside_book = Path(outside) / "book"
            self._write_ready_book(outside_book, book_id="fixture_book_2026")
            self._write_course_manifest(
                course_dir,
                book_entries=[self._entry("fixture_book_2026", "main", str(outside_book))],
                main_book_id="fixture_book_2026",
            )
            with self.assertRaises(CourseBookResolutionError):
                CourseRuntime.open(course_dir)

    def test_manifest_book_id_must_match_canonical_runtime_id(self) -> None:
        with self.assertRaises(CourseManifestError):
            self._open_course_with_ready_book(
                manifest_book_id="wrong_id",
                canonical_book_id="fixture_book_2026",
            )

    def test_blocked_enabled_book_fails_closed(self) -> None:
        with self.assertRaises(CourseRuntimeBlockedError):
            self._open_course_with_blocked_book()

    @staticmethod
    def _make_repo(root: Path) -> Path:
        (root / "runtime").mkdir(parents=True, exist_ok=True)
        (root / "books").mkdir(parents=True, exist_ok=True)
        (root / "courses").mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _entry(book_id: str, role: str, path: str) -> dict[str, object]:
        return {
            "book_id": book_id,
            "role": role,
            "path": path,
            "required": True,
            "enabled": True,
        }

    def _open_manifest_override(self, override: dict[str, object]) -> CourseRuntime:
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(Path(temp))
            course_dir = repo / "courses" / "fixture-course"
            base: dict[str, object] = {
                "schema_version": "course_manifest_v1",
                "course_id": "fixture_course",
                "name": "Fixture Course",
                "main_book_id": "fixture_book_2026",
                "books": [self._entry("fixture_book_2026", "main", "../../books/a")],
            }
            base.update(override)
            entries = base.get("books")
            if isinstance(entries, list):
                for index, entry in enumerate(entries):
                    if not isinstance(entry, dict) or entry.get("enabled") is not True:
                        continue
                    raw_path = entry.get("path")
                    book_id = entry.get("book_id")
                    if not isinstance(raw_path, str) or not raw_path or not isinstance(book_id, str) or not book_id:
                        continue
                    candidate = (course_dir / raw_path).resolve()
                    try:
                        candidate.relative_to(repo.resolve())
                    except ValueError:
                        continue
                    self._write_ready_book(candidate, book_id=book_id or f"fixture_{index}")
            self._write_course_manifest_raw(course_dir, base)
            return CourseRuntime.open(course_dir)

    def _open_course_with_entry(self, *, path: str) -> CourseRuntime:
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(Path(temp))
            course_dir = repo / "courses" / "fixture-course"
            self._write_course_manifest(
                course_dir,
                book_entries=[self._entry("fixture_book_2026", "main", path)],
                main_book_id="fixture_book_2026",
            )
            return CourseRuntime.open(course_dir)

    def _open_course_with_ready_book(
        self, *, manifest_book_id: str, canonical_book_id: str
    ) -> CourseRuntime:
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(Path(temp))
            book = repo / "books" / "fixture"
            course_dir = repo / "courses" / "fixture-course"
            self._write_ready_book(book, book_id=canonical_book_id)
            self._write_course_manifest(
                course_dir,
                book_entries=[self._entry(manifest_book_id, "main", "../../books/fixture")],
                main_book_id=manifest_book_id,
            )
            return CourseRuntime.open(course_dir)

    def _open_course_with_blocked_book(self) -> CourseRuntime:
        with tempfile.TemporaryDirectory() as temp:
            repo = self._make_repo(Path(temp))
            book = repo / "books" / "fixture"
            course_dir = repo / "courses" / "fixture-course"
            self._write_ready_book(book, book_id="fixture_book_2026")
            self._dump(
                book / "RUNTIME_READINESS.json",
                {
                    "status": "BLOCKED",
                    "book_id": "fixture_book_2026",
                    "structured_version": "v1",
                    "missing_required_files": [],
                    "stale_files": ["search_index_v1.jsonl"],
                },
            )
            self._write_course_manifest(
                course_dir,
                book_entries=[self._entry("fixture_book_2026", "main", "../../books/fixture")],
                main_book_id="fixture_book_2026",
            )
            return CourseRuntime.open(course_dir)

    def _write_course_manifest(
        self,
        course_dir: Path,
        *,
        book_entries: list[dict[str, object]],
        main_book_id: str,
    ) -> None:
        self._write_course_manifest_raw(
            course_dir,
            {
                "schema_version": "course_manifest_v1",
                "course_id": "fixture_course",
                "name": "Fixture Course",
                "language": "bilingual",
                "status": "active",
                "main_book_id": main_book_id,
                "books": book_entries,
            },
        )

    def _write_course_manifest_raw(self, course_dir: Path, data: dict[str, object]) -> None:
        course_dir.mkdir(parents=True, exist_ok=True)
        self._dump(course_dir / "course.json", data)

    @staticmethod
    def _dump(path: Path, data: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _write_ready_book(self, root: Path, *, book_id: str) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self._dump(
            root / "RUNTIME_READINESS.json",
            {
                "status": "READY",
                "book_id": book_id,
                "structured_version": "v1",
                "missing_required_files": [],
                "stale_files": [],
            },
        )
        self._dump(
            root / "STRUCTURED_COMPLETE.json",
            {
                "status": "STRUCTURED_COMPLETE",
                "book_id": book_id,
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
                "book_id": book_id,
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
                "book_id": book_id,
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
                "key_objects": [],
            },
        )
        (root / "chunk_001a_translation_zh.md").write_text("# 测试学习层\n", encoding="utf-8")
        (root / "search_index_v1.jsonl").write_text(
            json.dumps(
                {
                    "id": "section_ch01_s01",
                    "book_id": book_id,
                    "type": "section",
                    "name_zh": "小节",
                    "pdf_page": 1,
                    "printed_page": 1,
                    "source_anchor": f"{book_id}:pdf:1:ch01_s01",
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
