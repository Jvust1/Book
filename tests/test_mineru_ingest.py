import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from runtime.mineru_ingest import MinerUCliIngestor


class MinerUIngestTests(unittest.TestCase):
    def test_cli_command_and_output_are_bounded(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            out = Path(command[command.index("-o") + 1])
            out.write_text("# 第一章\n\n公式与表格", encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "book.pdf"
            out = Path(td) / "book.md"
            src.write_bytes(b"pdf")
            result = MinerUCliIngestor(runner=runner).convert_local(
                src, out, tier="standard"
            )
            self.assertEqual(result.tier, "standard")
            self.assertIn("公式与表格", result.markdown)
            self.assertEqual(calls[0][0][:3], ["mineru-kit", "parse", str(src)])
            self.assertIn("--tier", calls[0][0])

    def test_invalid_tier_fails_before_running_cli(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "book.pdf"
            src.write_bytes(b"x")
            with self.assertRaises(ValueError):
                MinerUCliIngestor(runner=lambda *a, **k: None).convert_local(
                    src, Path(td) / "out.md", tier="unknown"
                )


if __name__ == "__main__":
    unittest.main()
