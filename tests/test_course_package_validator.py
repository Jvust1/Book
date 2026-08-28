from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from course_package.compiler import CompiledCoursePackage, compile_course_package
from course_package.validator import validate_compiled_package, validate_course_package


ROOT = Path(__file__).resolve().parents[1]
COURSE_DIR = ROOT / "courses" / "functional-analysis"

# This test path intentionally triggers the current legacy full CI gates for validator changes.


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _diagnostic_codes(result: object) -> set[str]:
    return {diagnostic.code for diagnostic in result.diagnostics}


class CoursePackageValidatorTests(unittest.TestCase):
    def _compiled_package_dir(self, temp_root: Path) -> tuple[CompiledCoursePackage, Path]:
        package = compile_course_package(ROOT, COURSE_DIR)
        package_dir = package.write(temp_root / "packages")
        return package, package_dir

    def _copy_artifact_repository(
        self,
        package: CompiledCoursePackage,
        target_root: Path,
    ) -> None:
        for artifact in package.documents["artifacts.json"]["artifacts"]:
            relative = Path(artifact["relative_path"])
            source = ROOT / relative
            target = target_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def test_valid_golden_package_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            package, package_dir = self._compiled_package_dir(Path(temp))

            disk_result = validate_course_package(package_dir, ROOT)
            memory_result = validate_compiled_package(package, ROOT)

            self.assertEqual(disk_result.status, "PASS")
            self.assertEqual(disk_result.diagnostics, ())
            self.assertEqual(memory_result.status, "PASS")
            self.assertEqual(memory_result.diagnostics, ())

    def test_missing_package_file_fails_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            _, package_dir = self._compiled_package_dir(Path(temp))
            (package_dir / "sections.json").unlink()

            result = validate_course_package(package_dir, ROOT)

            self.assertEqual(result.status, "FAIL")
            self.assertIn("schema_error", _diagnostic_codes(result))

    def test_primary_count_not_equal_to_one_fails_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            _, package_dir = self._compiled_package_dir(Path(temp))
            path = package_dir / "books.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["books"][0]["role"] = "supplementary"
            _write_json(path, document)

            result = validate_course_package(package_dir, ROOT)

            self.assertEqual(result.status, "FAIL")
            self.assertIn("schema_error", _diagnostic_codes(result))

    def test_absolute_canonical_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            _, package_dir = self._compiled_package_dir(Path(temp))
            path = package_dir / "books.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["books"][0]["canonical_path"] = str(ROOT.resolve())
            _write_json(path, document)

            result = validate_course_package(package_dir, ROOT)

            self.assertEqual(result.status, "FAIL")
            self.assertIn("path_escape", _diagnostic_codes(result))

    def test_parent_escape_canonical_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            _, package_dir = self._compiled_package_dir(Path(temp))
            path = package_dir / "books.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["books"][0]["canonical_path"] = "../outside"
            _write_json(path, document)

            result = validate_course_package(package_dir, ROOT)

            self.assertEqual(result.status, "FAIL")
            self.assertIn("path_escape", _diagnostic_codes(result))

    def test_missing_canonical_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            package, package_dir = self._compiled_package_dir(temp_root)
            fixture_root = temp_root / "repository"
            self._copy_artifact_repository(package, fixture_root)
            first = package.documents["artifacts.json"]["artifacts"][0]
            (fixture_root / first["relative_path"]).unlink()

            result = validate_course_package(package_dir, fixture_root)

            self.assertEqual(result.status, "FAIL")
            self.assertIn("artifact_missing", _diagnostic_codes(result))

    def test_changed_canonical_artifact_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            package, package_dir = self._compiled_package_dir(temp_root)
            fixture_root = temp_root / "repository"
            self._copy_artifact_repository(package, fixture_root)
            first = package.documents["artifacts.json"]["artifacts"][0]
            target = fixture_root / first["relative_path"]
            target.write_bytes(target.read_bytes() + b"\nTAMPERED\n")

            result = validate_course_package(package_dir, fixture_root)

            self.assertEqual(result.status, "FAIL")
            self.assertIn("artifact_hash_mismatch", _diagnostic_codes(result))

    def test_changed_package_sha_fails_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            _, package_dir = self._compiled_package_dir(Path(temp))
            (package_dir / "package.sha256").write_text("0" * 64 + "\n", encoding="ascii")

            result = validate_course_package(package_dir, ROOT)

            self.assertEqual(result.status, "FAIL")
            self.assertIn("identity_error", _diagnostic_codes(result))

    def test_structural_count_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            _, package_dir = self._compiled_package_dir(Path(temp))
            path = package_dir / "course_package.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["chapter_count"] += 1
            _write_json(path, document)

            result = validate_course_package(package_dir, ROOT)

            self.assertEqual(result.status, "FAIL")
            self.assertIn("structural_baseline_mismatch", _diagnostic_codes(result))

    def test_non_ready_book_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            _, package_dir = self._compiled_package_dir(Path(temp))
            path = package_dir / "books.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["books"][0]["runtime_status"] = "BLOCKED"
            _write_json(path, document)

            result = validate_course_package(package_dir, ROOT)

            self.assertEqual(result.status, "FAIL")
            self.assertIn("book_not_ready", _diagnostic_codes(result))

    def test_secret_like_key_anywhere_fails_schema_without_leaking_value(self):
        with tempfile.TemporaryDirectory() as temp:
            _, package_dir = self._compiled_package_dir(Path(temp))
            path = package_dir / "chapters.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            secret_value = "never-echo-this-secret"
            document["chapters"][0]["ToKeN"] = secret_value
            _write_json(path, document)

            result = validate_course_package(package_dir, ROOT)

            self.assertEqual(result.status, "FAIL")
            self.assertIn("schema_error", _diagnostic_codes(result))
            self.assertNotIn(
                secret_value,
                "\n".join(diagnostic.detail for diagnostic in result.diagnostics),
            )

    def test_compiled_package_identity_drift_is_nondeterministic(self):
        package = compile_course_package(ROOT, COURSE_DIR)
        drifted = CompiledCoursePackage(
            course_id=package.course_id,
            package_identity="0" * 64,
            documents=copy.deepcopy(package.documents),
        )

        result = validate_compiled_package(drifted, ROOT)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("package_nondeterministic", _diagnostic_codes(result))


if __name__ == "__main__":
    unittest.main()
