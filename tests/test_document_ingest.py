import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from runtime.document_ingest import DocumentIngestPipeline


class Failing:
    def convert_local(self, _path):
        raise RuntimeError("fail")


class Success:
    def convert_local(self, path):
        return SimpleNamespace(
            source_path=str(path),
            markdown="# Chapter\n\nBanach space",
            backend="docling",
        )


class DocumentIngestPipelineTests(unittest.TestCase):
    def test_fallback_result_has_source_hash_and_backend(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "book.pdf"
            path.write_bytes(b"source-pdf-bytes")
            result = DocumentIngestPipeline([Failing(), Success()]).convert_local(path)
            self.assertEqual(result.backend, "docling")
            self.assertEqual(len(result.source_sha256), 64)
            self.assertIn("Banach", result.markdown)
            self.assertEqual(result.manifest()["backend"], "docling")

    def test_all_failures_are_reported_without_mutating_source(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "book.pdf"
            path.write_bytes(b"original")
            with self.assertRaises(RuntimeError):
                DocumentIngestPipeline([Failing(), Failing()]).convert_local(path)
            self.assertEqual(path.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main()
