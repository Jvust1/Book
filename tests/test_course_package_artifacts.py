from __future__ import annotations

# Verification bridge until Foundation A CI paths include course_package/**.

import json
import os
import tempfile
import unittest
from pathlib import Path

from course_package.artifacts import (
    ArtifactInventoryError,
    ArtifactRecord,
    build_book_artifact_inventory,
    compute_content_identity,
    repository_relative,
)


ROOT = Path(__file__).resolve().parents[1]
BOOK_ID = "stein_shakarchi_functional_analysis_2011"


class CoursePackageArtifactTests(unittest.TestCase):
    def test_real_golden_book_inventory_contains_all_contract_categories(self):
        records = build_book_artifact_inventory(
            ROOT,
            "books/functional-analysis",
            BOOK_ID,
        )
        categories = {record.artifact_type for record in records}
        self.assertTrue(
            {
                "book_metadata",
                "structured_complete",
                "audit_report",
                "toc",
                "page_map",
                "search_index",
                "qa_policy",
                "structure",
                "readiness",
            }.issubset(categories)
        )
        self.assertEqual(
            sum(record.artifact_type == "structure" for record in records),
            43,
        )
        self.assertTrue(
            all(
                record.relative_path.startswith("books/functional-analysis/")
                for record in records
            )
        )
        self.assertRegex(compute_content_identity(records), r"^[0-9a-f]{64}$")

    def test_missing_required_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            book = repo / "books" / "fixture"
            self._write_minimal_book(book, omit="BOOK_AUDIT_REPORT.md")
            with self.assertRaisesRegex(ArtifactInventoryError, "required artifact missing"):
                build_book_artifact_inventory(repo, "books/fixture", "fixture_book")

    def test_repository_relative_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            repo = Path(temp)
            with self.assertRaisesRegex(ArtifactInventoryError, "escapes repository root"):
                repository_relative(Path(outside) / "artifact.json", repo)

    def test_symlinked_required_artifact_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            repo = Path(temp)
            book = repo / "books" / "fixture"
            self._write_minimal_book(book)
            external_toc = Path(outside) / "toc.json"
            external_toc.write_text("{}", encoding="utf-8")
            toc = book / "toc.json"
            toc.unlink()
            try:
                os.symlink(external_toc, toc)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink unavailable: {exc}")
            with self.assertRaisesRegex(ArtifactInventoryError, "escapes repository root"):
                build_book_artifact_inventory(repo, "books/fixture", "fixture_book")

    def test_content_identity_is_independent_of_input_order(self):
        records = (
            ArtifactRecord(
                artifact_type="toc",
                relative_path="books/a/toc.json",
                sha256="a" * 64,
                size_bytes=10,
                required=True,
                book_id="book_a",
            ),
            ArtifactRecord(
                artifact_type="page_map",
                relative_path="books/a/page_map.csv",
                sha256="b" * 64,
                size_bytes=20,
                required=True,
                book_id="book_a",
            ),
        )
        self.assertEqual(
            compute_content_identity(records),
            compute_content_identity(tuple(reversed(records))),
        )

    @staticmethod
    def _write_json(path: Path, data: dict[str, object]) -> None:
        path.write_text(json.dumps(data), encoding="utf-8")

    @classmethod
    def _write_minimal_book(cls, book: Path, *, omit: str | None = None) -> None:
        book.mkdir(parents=True)
        files: dict[str, str] = {
            "BOOK_AUDIT_REPORT.md": "audit ok\n",
            "toc.json": "{}\n",
            "page_map.csv": "pdf_page,printed_page\n1,1\n",
            "search.jsonl": '{"id":"x"}\n',
            "qa_retrieval_policy.json": '{"book_id":"fixture_book"}\n',
            "RUNTIME_READINESS.json": '{"status":"READY","book_id":"fixture_book"}\n',
            "chunk_001_structure.json": "{}\n",
        }
        for name, text in files.items():
            if name != omit:
                (book / name).write_text(text, encoding="utf-8")
        cls._write_json(
            book / "book_metadata.json",
            {
                "book_id": "fixture_book",
                "toc_file": "toc.json",
                "page_map_file": "page_map.csv",
            },
        )
        cls._write_json(
            book / "STRUCTURED_COMPLETE.json",
            {
                "status": "STRUCTURED_COMPLETE",
                "book_id": "fixture_book",
                "version": "v1",
                "audit_report": "BOOK_AUDIT_REPORT.md",
                "search_index": "search.jsonl",
            },
        )


if __name__ == "__main__":
    unittest.main()
