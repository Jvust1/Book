from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.library_runtime import (
    LibraryCourseResolutionError,
    LibraryManifestError,
    LibraryRuntime,
    LibraryRuntimeBlockedError,
)
from tests.runtime_fixture_factory import (
    dump_json,
    main_book_entry,
    make_repo,
    write_course,
    write_ready_book,
)


class LibraryRuntimeContractTests(unittest.TestCase):
    def _entry(
        self,
        *,
        course_id: str = "fixture_course",
        name: str = "Fixture Course",
        path: str = "../courses/fixture-course",
        enabled: bool = True,
        order: int = 10,
    ) -> dict[str, object]:
        return {
            "course_id": course_id,
            "name": name,
            "path": path,
            "enabled": enabled,
            "order": order,
        }

    def _manifest(self) -> dict[str, object]:
        return {
            "schema_version": "library_manifest_v1",
            "library_id": "fixture_library",
            "name": "Fixture Library",
            "courses": [self._entry()],
        }

    def _ready_repo(self, root: Path, *, readiness: str = "READY") -> tuple[Path, Path]:
        repo = make_repo(root)
        write_ready_book(
            repo / "books" / "fixture",
            book_id="fixture_book",
            readiness=readiness,
        )
        write_course(
            repo / "courses" / "fixture-course",
            course_id="fixture_course",
            book_entries=[main_book_entry("fixture_book", "../../books/fixture")],
            main_book_id="fixture_book",
        )
        library_dir = repo / "library"
        dump_json(library_dir / "library.json", self._manifest())
        return repo, library_dir

    def _open_override(self, override: dict[str, object]) -> LibraryRuntime:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        _, library_dir = self._ready_repo(Path(temp.name))
        manifest = self._manifest()
        manifest.update(override)
        dump_json(library_dir / "library.json", manifest)
        return LibraryRuntime.open(library_dir)

    def test_valid_library_opens(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            library = LibraryRuntime.open(library_dir)
            self.assertEqual(
                (library.library_id, library.name),
                ("fixture_library", "Fixture Library"),
            )

    def test_unsupported_schema_version_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"schema_version": "library_manifest_v2"})

    def test_missing_library_id_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"library_id": ""})

    def test_missing_library_name_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"name": ""})

    def test_empty_courses_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"courses": []})

    def test_zero_enabled_courses_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"courses": [self._entry(enabled=False)]})

    def test_malformed_course_entry_fails(self) -> None:
        with self.assertRaises(LibraryManifestError):
            self._open_override({"courses": [{"course_id": "fixture_course"}]})

    def test_bool_order_is_not_accepted_as_integer(self) -> None:
        entry = self._entry()
        entry["order"] = True
        with self.assertRaises(LibraryManifestError):
            self._open_override({"courses": [entry]})

    def test_duplicate_enabled_course_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            write_course(
                repo / "courses" / "second-course",
                course_id="fixture_course",
                book_entries=[main_book_entry("fixture_book", "../../books/fixture")],
                main_book_id="fixture_book",
            )
            manifest = self._manifest()
            manifest["courses"] = [
                self._entry(),
                self._entry(path="../courses/second-course", order=20),
            ]
            dump_json(library_dir / "library.json", manifest)
            with self.assertRaises(LibraryManifestError):
                LibraryRuntime.open(library_dir)

    def test_missing_enabled_course_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            manifest = self._manifest()
            manifest["courses"] = [self._entry(path="../courses/missing")]
            dump_json(library_dir / "library.json", manifest)
            with self.assertRaises(LibraryCourseResolutionError):
                LibraryRuntime.open(library_dir)

    def test_course_path_escape_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            _, library_dir = self._ready_repo(Path(temp))
            manifest = self._manifest()
            manifest["courses"] = [self._entry(path=str(Path(outside).resolve()))]
            dump_json(library_dir / "library.json", manifest)
            with self.assertRaises(LibraryCourseResolutionError):
                LibraryRuntime.open(library_dir)

    def test_nonstandard_layout_without_explicit_root_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, _ = self._ready_repo(Path(temp))
            custom = repo / "catalog"
            dump_json(custom / "library.json", self._manifest())
            with self.assertRaises(LibraryCourseResolutionError):
                LibraryRuntime.open(custom)

    def test_explicit_root_supports_nonstandard_library_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, _ = self._ready_repo(Path(temp))
            custom = repo / "catalog"
            manifest = self._manifest()
            manifest["courses"] = [self._entry(path="../courses/fixture-course")]
            dump_json(custom / "library.json", manifest)
            library = LibraryRuntime.open(custom, repository_root=repo)
            self.assertEqual(library.library_id, "fixture_library")

    def test_canonical_course_id_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            manifest = self._manifest()
            manifest["courses"] = [self._entry(course_id="wrong_course")]
            dump_json(library_dir / "library.json", manifest)
            with self.assertRaises(LibraryManifestError):
                LibraryRuntime.open(library_dir)

    def test_blocked_enabled_course_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp), readiness="BLOCKED")
            with self.assertRaises(LibraryRuntimeBlockedError):
                LibraryRuntime.open(library_dir)

    def test_disabled_incomplete_course_is_ignored_when_one_valid_course_remains(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            manifest = self._manifest()
            courses = manifest["courses"]
            assert isinstance(courses, list)
            courses.append(
                self._entry(
                    course_id="future_course",
                    path="../courses/not-created",
                    enabled=False,
                    order=20,
                )
            )
            dump_json(library_dir / "library.json", manifest)
            library = LibraryRuntime.open(library_dir)
            self.assertEqual(library.course_ids(), ["fixture_course"])


class LibraryRuntimeCatalogTests(LibraryRuntimeContractTests):
    def test_courses_are_ordered_by_order_then_manifest_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            write_ready_book(repo / "books" / "second", book_id="second_book")
            write_course(
                repo / "courses" / "second-course",
                course_id="second_course",
                book_entries=[main_book_entry("second_book", "../../books/second")],
                main_book_id="second_book",
            )
            manifest = self._manifest()
            manifest["courses"] = [
                self._entry(course_id="fixture_course", order=20),
                self._entry(
                    course_id="second_course",
                    path="../courses/second-course",
                    order=10,
                ),
            ]
            dump_json(library_dir / "library.json", manifest)
            library = LibraryRuntime.open(library_dir)
            self.assertEqual(library.course_ids(), ["second_course", "fixture_course"])
            self.assertEqual(
                [course.course_id for course in library.courses()],
                ["second_course", "fixture_course"],
            )

    def test_equal_order_preserves_manifest_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            write_ready_book(repo / "books" / "second", book_id="second_book")
            write_course(
                repo / "courses" / "second-course",
                course_id="second_course",
                book_entries=[main_book_entry("second_book", "../../books/second")],
                main_book_id="second_book",
            )
            manifest = self._manifest()
            manifest["courses"] = [
                self._entry(course_id="fixture_course", order=10),
                self._entry(
                    course_id="second_course",
                    path="../courses/second-course",
                    order=10,
                ),
            ]
            dump_json(library_dir / "library.json", manifest)
            self.assertEqual(
                LibraryRuntime.open(library_dir).course_ids(),
                ["fixture_course", "second_course"],
            )

    def test_course_returns_already_mounted_course(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            library = LibraryRuntime.open(library_dir)
            self.assertIs(library.course("fixture_course"), library.courses()[0])

    def test_unknown_or_disabled_course_id_raises_library_error(self) -> None:
        from runtime.library_runtime import LibraryRuntimeError

        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            library = LibraryRuntime.open(library_dir)
            with self.assertRaises(LibraryRuntimeError):
                library.course("missing")

    def test_multi_book_course_is_rejected_by_product_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, library_dir = self._ready_repo(Path(temp))
            write_ready_book(repo / "books" / "supplementary", book_id="supp_book")
            course_path = repo / "courses" / "fixture-course" / "course.json"
            course = __import__("json").loads(course_path.read_text(encoding="utf-8"))
            course["books"].append(
                {
                    "book_id": "supp_book",
                    "role": "supplementary",
                    "path": "../../books/supplementary",
                    "required": True,
                    "enabled": True,
                }
            )
            dump_json(course_path, course)
            with self.assertRaises(LibraryManifestError):
                LibraryRuntime.open(library_dir)

    def test_exactly_one_main_book_course_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            course = LibraryRuntime.open(library_dir).course("fixture_course")
            self.assertEqual(course.book_ids(), ["fixture_book"])
            self.assertEqual(course.main_book().book_id, "fixture_book")

    def test_summary_reports_independent_courses(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, library_dir = self._ready_repo(Path(temp))
            summary = LibraryRuntime.open(library_dir).summary()
            self.assertEqual(summary["library_id"], "fixture_library")
            self.assertEqual(summary["course_count"], 1)
            self.assertEqual(
                summary["courses"],
                [
                    {
                        "course_id": "fixture_course",
                        "name": "fixture_course",
                        "book_count": 1,
                        "main_book_id": "fixture_book",
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()
