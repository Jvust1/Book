from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

import evaluation.h4a_runtime as h4a_runtime
from runtime.shadow_fts import ShadowFtsUnavailableError


ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = ROOT / "tools" / "evaluate_h4a_retrieval.py"


class H4aCliTests(unittest.TestCase):
    def _load_cli(self):
        self.assertTrue(
            CLI_PATH.is_file(),
            "tools/evaluate_h4a_retrieval.py must exist for the H4a CLI contract",
        )
        spec = importlib.util.spec_from_file_location("h4a_cli_under_test", CLI_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _report(self) -> dict[str, object]:
        query_set = h4a_runtime.parse_h4a_query_set(
            {
                "schema_version": "h4a_query_set_v1",
                "dataset_id": "cli_synthetic_v1",
                "course_id": "functional_analysis_course",
                "queries": [
                    {
                        "query_id": "q-negative",
                        "category": "negative_zero_result",
                        "query": "synthetic absent phrase",
                        "section_id": None,
                        "expected_sources": [],
                        "notes": None,
                    }
                ],
            }
        )
        return h4a_runtime.build_h4a_report(
            query_set=query_set,
            course_identity={
                "course_id": "functional_analysis_course",
                "book_id": "stein_shakarchi_functional_analysis_2011",
                "book_version_id": "functional-analysis-2011-structured-v0.36",
            },
            profile_definitions=(
                {"profile_id": "exact_v1", "kind": "exact"},
                {
                    "profile_id": "fts_unicode61_bm25_v1",
                    "kind": "shadow_fts5",
                    "tokenizer": "unicode61",
                },
                {
                    "profile_id": "fts_trigram_bm25_v1",
                    "kind": "shadow_fts5",
                    "tokenizer": "trigram",
                },
            ),
            sqlite_version="3.synthetic",
            fts5_available=True,
            query_results=(),
            aggregate_metrics={},
            gates={
                "provenance": "PASS",
                "section_scope": "PASS",
                "determinism": "PASS",
            },
            evidence={
                "public_contract_regression": "synthetic",
                "canonical_tree_integrity": "synthetic",
            },
        )

    def _run(self, argv: list[str], *, evaluator):
        module = self._load_cli()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = module.main(argv, evaluator=evaluator)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_writes_report_under_build_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            report = self._report()
            code, stdout, stderr = self._run(
                ["--repository-root", str(root)],
                evaluator=lambda repository_root, query_set_path: report,
            )
            expected = (
                root
                / ".build"
                / "evaluations"
                / "h4a"
                / "functional_analysis_course"
                / "report.json"
            )
            self.assertEqual(code, 0)
            self.assertTrue(expected.is_file())
            self.assertEqual(
                expected.read_text(encoding="utf-8"),
                h4a_runtime.canonical_h4a_report_json(report),
            )
            self.assertNotIn("Traceback", stdout + stderr)

    def test_cli_success_stdout_is_stable_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            report = self._report()
            args = ["--repository-root", tempdir]
            first = self._run(
                args,
                evaluator=lambda repository_root, query_set_path: report,
            )
            second = self._run(
                args,
                evaluator=lambda repository_root, query_set_path: report,
            )

            self.assertEqual(first[0], 0)
            self.assertEqual(second[0], 0)
            self.assertEqual(first[1], second[1])
            summary = json.loads(first[1])
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["stage"], "H4a")
            self.assertEqual(summary["dataset_id"], "cli_synthetic_v1")
            self.assertNotIn("Traceback", first[1] + first[2])

    def test_cli_invalid_dataset_returns_exit_2_without_traceback(self) -> None:
        def invalid_dataset(repository_root, query_set_path):
            raise h4a_runtime.H4aDatasetError("synthetic invalid dataset")

        with tempfile.TemporaryDirectory() as tempdir:
            code, stdout, stderr = self._run(
                ["--repository-root", tempdir],
                evaluator=invalid_dataset,
            )

        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", stdout + stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ERROR")
        self.assertEqual(payload["error_kind"], "dataset")

    def test_cli_fts_unavailable_returns_nonzero_stable_error_without_fallback(self) -> None:
        def unavailable(repository_root, query_set_path):
            raise ShadowFtsUnavailableError("synthetic FTS5 unavailable")

        with tempfile.TemporaryDirectory() as tempdir:
            code, stdout, stderr = self._run(
                ["--repository-root", tempdir],
                evaluator=unavailable,
            )

        self.assertEqual(code, 3)
        self.assertNotIn("Traceback", stdout + stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ERROR")
        self.assertEqual(payload["error_kind"], "shadow_fts")
        self.assertNotIn("fallback", stdout.lower())

    def test_cli_rejects_output_path_outside_repository_build_area(self) -> None:
        called = False

        def evaluator(repository_root, query_set_path):
            nonlocal called
            called = True
            return self._report()

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            outside = root / "report.json"
            code, stdout, stderr = self._run(
                [
                    "--repository-root",
                    str(root),
                    "--output",
                    str(outside),
                ],
                evaluator=evaluator,
            )

        self.assertEqual(code, 2)
        self.assertFalse(called)
        self.assertNotIn("Traceback", stdout + stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ERROR")
        self.assertEqual(payload["error_kind"], "output_path")


if __name__ == "__main__":
    unittest.main()
