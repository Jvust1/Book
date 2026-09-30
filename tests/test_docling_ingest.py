import tempfile
import unittest
from pathlib import Path

from runtime.docling_ingest import DoclingIngestor


class Document:
    def export_to_markdown(self):
        return "# 第一章\n\nBanach 空间定义"


class Result:
    document = Document()


class Converter:
    def __init__(self):
        self.source = None
    def convert(self, source):
        self.source = Path(source)
        return Result()


class DoclingIngestTests(unittest.TestCase):
    def test_local_file_is_converted_to_markdown(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "book.pdf"
            path.write_bytes(b"pdf")
            converter = Converter()
            result = DoclingIngestor(converter).convert_local(path)
            self.assertEqual(result.backend, "docling")
            self.assertIn("Banach", result.markdown)
            self.assertEqual(converter.source, path)

    def test_missing_file_is_rejected_before_converter_call(self):
        with self.assertRaises(FileNotFoundError):
            DoclingIngestor(Converter()).convert_local("/definitely/missing/book.pdf")


if __name__ == "__main__":
    unittest.main()
