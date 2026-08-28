from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from course_package.manifest import ManifestNormalizationError, normalize_course_manifest

ROOT = Path(__file__).resolve().parents[1]


class CourseManifestNormalizationTests(unittest.TestCase):
    def test_real_legacy_manifest_normalizes_main_to_primary(self):
        normalized = normalize_course_manifest(ROOT / "courses" / "functional-analysis", ROOT)
        self.assertEqual(normalized.course_id, "functional_analysis_course")
        self.assertEqual(normalized.course_name, "Functional Analysis")
        self.assertEqual(normalized.language, "bilingual")
        self.assertEqual(normalized.primary_book_id, "stein_shakarchi_functional_analysis_2011")
        self.assertEqual(len(normalized.books), 1)
        book = normalized.books[0]
        self.assertEqual(book.role, "primary")
        self.assertEqual(book.canonical_path, "books/functional-analysis")
        self.assertEqual(book.logical_book_id, book.book_id)
        self.assertEqual(book.book_version_id, f"{book.book_id}@v0.36")
        self.assertEqual(book.structured_version, "v0.36")

    def test_path_escape_fails_closed(self):
        repo, course = self._synthetic_repo()
        self._write_manifest(course, path="../../../outside")
        with self.assertRaisesRegex(ManifestNormalizationError, "escapes repository root"):
            normalize_course_manifest(course, repo)

    def test_absolute_book_path_is_rejected_even_inside_repository(self):
        repo, course = self._synthetic_repo()
        book = repo / "books" / "a"
        self._write_ready_book(book, "book_a")
        self._write_manifest(course, path=str(book.resolve()))
        with self.assertRaisesRegex(ManifestNormalizationError, "absolute book paths are not allowed"):
            normalize_course_manifest(course, repo)

    def test_unsupported_legacy_role_fails_closed(self):
        repo, course = self._synthetic_repo()
        self._write_ready_book(repo / "books" / "a", "book_a")
        self._write_manifest(course, role="primary")
        with self.assertRaisesRegex(ManifestNormalizationError, "unsupported legacy role"):
            normalize_course_manifest(course, repo)

    def test_duplicate_enabled_book_ids_fail_closed(self):
        repo, course = self._synthetic_repo()
        self._write_ready_book(repo / "books" / "a", "book_a")
        data = self._manifest(book_id="book_a", role="main", path="../../books/a")
        data["books"].append({
            "book_id": "book_a", "role": "reference", "path": "../../books/a",
            "required": True, "enabled": True,
        })
        self._write_json(course / "course.json", data)
        with self.assertRaisesRegex(ManifestNormalizationError, "duplicate enabled book_id"):
            normalize_course_manifest(course, repo)

    def test_zero_enabled_primary_fails_closed(self):
        repo, course = self._synthetic_repo()
        self._write_ready_book(repo / "books" / "a", "book_a")
        self._write_manifest(course, role="reference")
        with self.assertRaisesRegex(ManifestNormalizationError, "exactly one enabled primary"):
            normalize_course_manifest(course, repo)

    def test_two_enabled_primary_books_fail_closed(self):
        repo, course = self._synthetic_repo()
        self._write_ready_book(repo / "books" / "a", "book_a")
        self._write_ready_book(repo / "books" / "b", "book_b")
        data = self._manifest(book_id="book_a", role="main", path="../../books/a")
        data["books"].append({
            "book_id": "book_b", "role": "main", "path": "../../books/b",
            "required": True, "enabled": True,
        })
        self._write_json(course / "course.json", data)
        with self.assertRaisesRegex(ManifestNormalizationError, "exactly one enabled primary"):
            normalize_course_manifest(course, repo)

    def test_completion_book_id_must_match_manifest(self):
        repo, course = self._synthetic_repo()
        self._write_ready_book(repo / "books" / "a", "other_book")
        self._write_manifest(course)
        with self.assertRaisesRegex(ManifestNormalizationError, "does not match canonical book_id"):
            normalize_course_manifest(course, repo)

    def test_structured_version_must_be_non_empty(self):
        repo, course = self._synthetic_repo()
        book = repo / "books" / "a"
        book.mkdir(parents=True)
        self._write_json(book / "STRUCTURED_COMPLETE.json", {"status": "STRUCTURED_COMPLETE", "book_id": "book_a", "version": ""})
        self._write_manifest(course)
        with self.assertRaisesRegex(ManifestNormalizationError, "structured version"):
            normalize_course_manifest(course, repo)

    def test_legacy_english_maps_to_translation(self):
        repo, course = self._synthetic_repo()
        self._write_ready_book(repo / "books" / "a", "book_a")
        self._write_ready_book(repo / "books" / "b", "book_b")
        data = self._manifest(book_id="book_a", role="main", path="../../books/a")
        data["books"].append({
            "book_id": "book_b", "role": "english", "path": "../../books/b",
            "required": False, "enabled": True,
        })
        self._write_json(course / "course.json", data)
        normalized = normalize_course_manifest(course, repo)
        self.assertEqual(normalized.books[1].role, "translation")

    def _synthetic_repo(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        repo = Path(temp.name)
        course = repo / "courses" / "fixture"
        course.mkdir(parents=True)
        (repo / "books").mkdir()
        return repo, course

    def _manifest(self, *, book_id="book_a", role="main", path="../../books/a"):
        return {
            "schema_version": "course_manifest_v1",
            "course_id": "fixture_course",
            "name": "Fixture Course",
            "language": "en",
            "main_book_id": book_id,
            "books": [{"book_id": book_id, "role": role, "path": path, "required": True, "enabled": True}],
        }

    def _write_manifest(self, course: Path, **kwargs):
        self._write_json(course / "course.json", self._manifest(**kwargs))

    @staticmethod
    def _write_ready_book(book: Path, book_id: str):
        book.mkdir(parents=True, exist_ok=True)
        CourseManifestNormalizationTests._write_json(book / "STRUCTURED_COMPLETE.json", {
            "status": "STRUCTURED_COMPLETE", "book_id": book_id, "version": "v1",
        })

    @staticmethod
    def _write_json(path: Path, data):
        path.write_text(json.dumps(data), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
