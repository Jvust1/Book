import json
import unittest
from pathlib import Path

from book_core.identity import CANONICAL_BOOK_ROLES as CORE_BOOK_ROLES
from course_package.contracts import (
    CANONICAL_BOOK_ROLES,
    PACKAGE_FILENAMES,
    PACKAGE_VERSION,
    READINESS_STATUSES,
    SCHEMA_VERSION,
    canonical_json_bytes,
    sha256_bytes,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "course-package"


class CoursePackageSchemaTests(unittest.TestCase):
    def test_contract_constants_are_frozen(self):
        self.assertEqual(SCHEMA_VERSION, "course_package_v1")
        self.assertEqual(PACKAGE_VERSION, "1.0.0")
        self.assertEqual(
            CANONICAL_BOOK_ROLES,
            frozenset({"primary", "supplementary", "reference", "translation"}),
        )
        self.assertEqual(READINESS_STATUSES, frozenset({"PASS", "WARN", "FAIL"}))
        self.assertEqual(
            PACKAGE_FILENAMES,
            (
                "course_package.json",
                "books.json",
                "artifacts.json",
                "chapters.json",
                "sections.json",
                "readiness.json",
                "package.sha256",
            ),
        )

    def test_course_package_roles_share_core_owner(self):
        self.assertIs(CANONICAL_BOOK_ROLES, CORE_BOOK_ROLES)

    def test_published_schemas_match_contract_enums(self):
        course_schema = json.loads(
            (SCHEMAS / "course-package-v1.schema.json").read_text(encoding="utf-8")
        )
        books_schema = json.loads(
            (SCHEMAS / "books-v1.schema.json").read_text(encoding="utf-8")
        )
        readiness_schema = json.loads(
            (SCHEMAS / "readiness-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(course_schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)
        self.assertEqual(course_schema["properties"]["package_version"]["const"], PACKAGE_VERSION)
        self.assertEqual(
            set(books_schema["$defs"]["book"]["properties"]["role"]["enum"]),
            set(CANONICAL_BOOK_ROLES),
        )
        self.assertEqual(
            set(readiness_schema["properties"]["status"]["enum"]),
            set(READINESS_STATUSES),
        )

    def test_canonical_json_is_stable(self):
        left = {"b": 2, "a": {"y": False, "x": 1}}
        right = {"a": {"x": 1, "y": False}, "b": 2}
        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(right))
        self.assertEqual(
            sha256_bytes(canonical_json_bytes(left)),
            sha256_bytes(canonical_json_bytes(right)),
        )


if __name__ == "__main__":
    unittest.main()