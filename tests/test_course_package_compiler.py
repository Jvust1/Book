from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from course_package.compiler import PackageCompileError, compile_course_package
from course_package.contracts import PACKAGE_FILENAMES


# Touching this test file also triggers the current legacy CI path filters.
ROOT = Path(__file__).resolve().parents[1]
COURSE_DIR = ROOT / "courses" / "functional-analysis"


class CoursePackageCompilerTests(unittest.TestCase):
    def test_real_golden_course_compiles_deterministically(self):
        first = compile_course_package(ROOT, COURSE_DIR)
        second = compile_course_package(ROOT, COURSE_DIR)

        self.assertEqual(first.course_id, "functional_analysis_course")
        self.assertEqual(first.package_identity, second.package_identity)
        self.assertRegex(first.package_identity, r"^[0-9a-f]{64}$")
        self.assertEqual(first.file_bytes(), second.file_bytes())
        self.assertEqual(set(first.file_bytes()), set(PACKAGE_FILENAMES))

        course_doc = first.documents["course_package.json"]
        self.assertEqual(course_doc["chapter_count"], 8)
        self.assertEqual(course_doc["section_count"], 132)
        self.assertEqual(course_doc["search_record_count"], 1493)
        self.assertEqual(course_doc["package_identity"], first.package_identity)
        self.assertEqual(course_doc["readiness"], "PASS")

        books_doc = first.documents["books.json"]
        self.assertEqual(len(books_doc["books"]), 1)
        self.assertEqual(books_doc["books"][0]["role"], "primary")
        self.assertEqual(books_doc["books"][0]["runtime_status"], "READY")
        self.assertEqual(books_doc["books"][0]["pdf_page_count"], 442)
        self.assertEqual(books_doc["books"][0]["printed_final_page"], 423)

        root_text = str(ROOT.resolve())
        for payload in first.file_bytes().values():
            self.assertNotIn(root_text, payload.decode("utf-8"))

    def test_write_is_additive_and_idempotent_for_identical_bytes(self):
        package = compile_course_package(ROOT, COURSE_DIR)
        with tempfile.TemporaryDirectory() as temp:
            output_root = Path(temp)
            first_dir = package.write(output_root)
            first_snapshot = {
                path.name: path.read_bytes()
                for path in first_dir.iterdir()
                if path.is_file()
            }

            second_dir = package.write(output_root)
            second_snapshot = {
                path.name: path.read_bytes()
                for path in second_dir.iterdir()
                if path.is_file()
            }

            self.assertEqual(
                first_dir,
                output_root / package.course_id / package.package_identity,
            )
            self.assertEqual(first_dir, second_dir)
            self.assertEqual(first_snapshot, second_snapshot)
            self.assertEqual(set(first_snapshot), set(PACKAGE_FILENAMES))

    def test_write_conflict_fails_closed_without_overwriting_existing_bytes(self):
        package = compile_course_package(ROOT, COURSE_DIR)
        with tempfile.TemporaryDirectory() as temp:
            package_dir = package.write(Path(temp))
            target = package_dir / "course_package.json"
            original = target.read_bytes()
            conflicting = json.dumps({"tampered": True}).encode("utf-8") + b"\n"
            target.write_bytes(conflicting)

            with self.assertRaisesRegex(PackageCompileError, "conflicting generated file"):
                package.write(Path(temp))

            self.assertEqual(target.read_bytes(), conflicting)
            self.assertNotEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
