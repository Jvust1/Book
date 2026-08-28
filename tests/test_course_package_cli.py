from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPILE_CLI = ROOT / "tools" / "compile_course_package.py"
VALIDATE_CLI = ROOT / "tools" / "validate_course_package.py"
COURSE_DIR = Path("courses/functional-analysis")


class CoursePackageCliTests(unittest.TestCase):
    def run_cli(self, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *(str(arg) for arg in args)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_compile_then_validate_real_functional_analysis_package(self):
        with tempfile.TemporaryDirectory(prefix=".tmp-course-package-cli-", dir=ROOT) as tmp:
            output_root = Path(tmp)
            compiled = self.run_cli(
                COMPILE_CLI,
                COURSE_DIR,
                "--repository-root",
                ".",
                "--output-root",
                output_root,
            )

            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            compile_payload = json.loads(compiled.stdout)
            self.assertEqual(compile_payload["status"], "PASS")
            self.assertEqual(compile_payload["course_id"], "functional_analysis_course")
            self.assertRegex(compile_payload["package_identity"], r"^[0-9a-f]{64}$")
            package_dir = ROOT / compile_payload["package_dir"]
            self.assertTrue(package_dir.is_dir())

            validated = self.run_cli(
                VALIDATE_CLI,
                package_dir,
                "--repository-root",
                ".",
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(
                json.loads(validated.stdout),
                {"status": "PASS", "diagnostics": []},
            )

    def test_compile_invalid_course_path_returns_two_without_traceback(self):
        completed = self.run_cli(
            COMPILE_CLI,
            "courses/does-not-exist",
            "--repository-root",
            ".",
        )

        self.assertEqual(completed.returncode, 2)
        self.assertNotIn("Traceback", completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)

    def test_validate_invalid_package_path_returns_two_without_traceback(self):
        completed = self.run_cli(
            VALIDATE_CLI,
            "does-not-exist/course-package",
            "--repository-root",
            ".",
        )

        self.assertEqual(completed.returncode, 2)
        self.assertNotIn("Traceback", completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)

    def test_public_package_surface_exports_compiler_golden_and_validator(self):
        import course_package

        expected = {
            "CompiledCoursePackage",
            "PackageCompileError",
            "compile_course_package",
            "verify_golden_course",
            "validate_compiled_package",
            "validate_course_package",
        }
        self.assertTrue(expected.issubset(set(course_package.__all__)))
        for name in expected:
            self.assertTrue(hasattr(course_package, name), name)


if __name__ == "__main__":
    unittest.main()
