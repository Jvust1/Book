from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from course_package.artifacts import sha256_file
from course_package.compiler import compile_course_package
from course_package.fitness import (
    check_browser_source,
    check_compiled_documents,
    run_architecture_fitness,
)
from course_package.golden import GOLDEN_COURSE_DIR


ROOT = Path(__file__).resolve().parents[1]
BOOK_ROOT = ROOT / "books" / "functional-analysis"


def snapshot_tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    }


class ArchitectureFitnessTests(unittest.TestCase):
    def test_current_repository_fitness_passes_without_canonical_mutation(self):
        before = snapshot_tree(BOOK_ROOT)

        result = run_architecture_fitness(ROOT)

        after = snapshot_tree(BOOK_ROOT)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.diagnostics, ())
        self.assertEqual(before, after)

    def test_browser_source_rejects_durable_sqlite_patterns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "app" / "web" / "src"
            source.mkdir(parents=True)
            (source / "bad.ts").write_text(
                "const a = 'sqlite3';\n"
                "const b = 'sqlite:///tmp/book.db';\n"
                "const c = 'profile.sqlite3';\n",
                encoding="utf-8",
            )

            diagnostics = check_browser_source(root)

        self.assertTrue(diagnostics)
        self.assertEqual(
            {item.code for item in diagnostics},
            {"browser_durable_storage_forbidden"},
        )
        self.assertEqual(
            {item.relative_path for item in diagnostics},
            {"app/web/src/bad.ts"},
        )

    def test_browser_source_ignores_non_source_explanatory_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "app" / "web" / "src"
            source.mkdir(parents=True)
            (source / "clean.ts").write_text("export const ok = true;\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "notes.md").write_text("sqlite3 sqlite:/// x.sqlite3\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "fixture.txt").write_text("sqlite3\n", encoding="utf-8")

            diagnostics = check_browser_source(root)

        self.assertEqual(diagnostics, ())

    def test_compiled_document_scan_rejects_absolute_paths_and_secret_fields(self):
        diagnostics = check_compiled_documents(
            {
                "course_package.json": {
                    "api_key": "do-not-commit",
                    "unix_path": "/tmp/book.db",
                    "windows_path": r"C:\\book\\state.sqlite3",
                }
            }
        )

        self.assertEqual(
            {item.code for item in diagnostics},
            {"compiled_absolute_path", "compiled_secret_key"},
        )

    def test_real_golden_compiled_documents_are_fitness_clean(self):
        package = compile_course_package(ROOT, ROOT / GOLDEN_COURSE_DIR)
        self.assertEqual(check_compiled_documents(package.documents), ())

    def test_architecture_fitness_cli_prints_json_and_exits_zero(self):
        completed = subprocess.run(
            [sys.executable, "tools/check_architecture_fitness.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload, {"status": "PASS", "diagnostics": []})


if __name__ == "__main__":
    unittest.main()
