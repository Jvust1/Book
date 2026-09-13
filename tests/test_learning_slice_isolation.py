from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime" / "learning_slice_runtime.py"


class LearningSliceIsolationTests(unittest.TestCase):
    def test_learning_slice_runtime_imports_only_allowed_runtime_modules(self) -> None:
        tree = ast.parse(RUNTIME_PATH.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)

        forbidden_prefixes = (
            "runtime.shadow_fts",
            "evaluation",
            "book_core.concepts",
            "runtime.concept_validation",
            "runtime.qa_",
            "app.study",
        )
        self.assertFalse(
            any(
                module == forbidden or module.startswith(forbidden + ".")
                for module in imported
                for forbidden in forbidden_prefixes
            ),
            msg=f"forbidden imports found: {sorted(imported)}",
        )

    def test_learning_slice_runtime_has_no_model_provider_construction(self) -> None:
        source = RUNTIME_PATH.read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(
                r"(?i)(openai|anthropic|modelprovider|chatcompletion|inference)",
                source,
            )
        )


if __name__ == "__main__":
    unittest.main()
