from __future__ import annotations

import unittest
from pathlib import Path

from course_package.artifacts import sha256_file
from course_package.compiler import compile_course_package
from course_package.golden import (
    GOLDEN_COURSE_DIR,
    load_golden_baseline,
    verify_golden_course,
)


ROOT = Path(__file__).resolve().parents[1]
BOOK_ROOT = ROOT / "books" / "functional-analysis"
EXPECTED_BASELINE = {
    "course_id": "functional_analysis_course",
    "book_id": "stein_shakarchi_functional_analysis_2011",
    "chapter_count": 8,
    "section_count": 132,
    "search_record_count": 1493,
    "pdf_page_count": 442,
    "printed_final_page": 423,
    "structured_status": "STRUCTURED_COMPLETE",
    "runtime_status": "READY",
}


def snapshot_tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class GoldenCoursePackageTests(unittest.TestCase):
    def test_golden_baseline_contract_is_exact(self):
        self.assertEqual(GOLDEN_COURSE_DIR, Path("courses/functional-analysis"))
        self.assertEqual(load_golden_baseline(ROOT), EXPECTED_BASELINE)

    def test_golden_course_gate_passes_without_canonical_mutation(self):
        before = snapshot_tree(BOOK_ROOT)

        result = verify_golden_course(ROOT)

        after = snapshot_tree(BOOK_ROOT)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.diagnostics, ())
        self.assertEqual(before, after)

    def test_golden_course_compile_is_deterministic(self):
        first = compile_course_package(ROOT, ROOT / GOLDEN_COURSE_DIR)
        second = compile_course_package(ROOT, ROOT / GOLDEN_COURSE_DIR)

        self.assertEqual(first.package_identity, second.package_identity)
        self.assertEqual(first.file_bytes(), second.file_bytes())


if __name__ == "__main__":
    unittest.main()
