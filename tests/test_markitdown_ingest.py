import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from runtime.markitdown_ingest import DocumentIngestFallback, MarkItDownIngestor


class Converter:
    def convert_local(self, path):
        assert Path(path).is_file()
        return SimpleNamespace(text_content="# 内容\n\nBanach 空间")


class Failing:
    def convert_local(self, path):
        raise RuntimeError("primary failed")


class Success:
    def convert_local(self, path):
        return SimpleNamespace(backend="fallback", source_path=str(path), markdown="ok")


class MarkItDownIngestTests(unittest.TestCase):
    def test_markitdown_local_conversion_returns_markdown(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "book.docx"
            path.write_bytes(b"x")
            result = MarkItDownIngestor(Converter()).convert_local(path)
            self.assertEqual(result.backend, "markitdown")
            self.assertIn("Banach", result.markdown)

    def test_fallback_tries_next_ingestor(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "book.pdf"
            path.write_bytes(b"x")
            result = DocumentIngestFallback([Failing(), Success()]).convert_local(path)
            self.assertEqual(result.backend, "fallback")

    def test_fallback_reports_all_failures(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "book.pdf"
            path.write_bytes(b"x")
            with self.assertRaises(RuntimeError):
                DocumentIngestFallback([Failing(), Failing()]).convert_local(path)


if __name__ == "__main__":
    unittest.main()
