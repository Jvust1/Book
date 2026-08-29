from __future__ import annotations

from pathlib import Path
import unittest

from runtime.course_runtime import CourseRuntime
from runtime.qa_evidence import EvidenceBuilder
from runtime.search_runtime import SearchRuntime
from runtime.section_learning_runtime import SectionLearningRuntime


ROOT = Path(__file__).resolve().parents[1]


class FoundationBIsolationTests(unittest.TestCase):
    def test_product_runtime_and_app_do_not_import_concept_foundation(self) -> None:
        product_files = [
            ROOT / "runtime" / "search_runtime.py",
            ROOT / "runtime" / "qa_evidence.py",
            ROOT / "runtime" / "section_learning_runtime.py",
            ROOT / "runtime" / "__init__.py",
            ROOT / "app" / "api" / "service.py",
            *(ROOT / "app" / "study").glob("*.py"),
        ]
        forbidden_tokens = (
            "book_core.concepts",
            "runtime.concept_validation",
            ".concept_validation",
        )

        for path in product_files:
            with self.subTest(path=str(path.relative_to(ROOT))):
                source = path.read_text(encoding="utf-8")
                for token in forbidden_tokens:
                    self.assertNotIn(token, source)

    def test_no_production_concept_graph_authority_exists(self) -> None:
        roots = (
            ROOT / "books",
            ROOT / "courses",
            ROOT / "tests" / "golden",
            ROOT / ".build",
        )
        offenders: list[str] = []
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("*.json"):
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if "concept_graph_v1" in text:
                    offenders.append(str(path.relative_to(ROOT)))

        self.assertEqual(offenders, [])

    def test_existing_search_qa_and_section_learning_run_without_concept_data(self) -> None:
        course = CourseRuntime.open(ROOT / "courses" / "functional-analysis")

        hits = SearchRuntime.from_course(course).search("Hölder", limit=3)
        evidence = EvidenceBuilder.from_course(course).build(
            "Hölder inequality",
            section_id=None,
            limit=3,
        )
        section = SectionLearningRuntime.from_course(course, "ch01_s01").preview()

        self.assertGreater(len(hits), 0)
        self.assertGreater(len(evidence.evidence), 0)
        self.assertEqual(section["section_id"], "ch01_s01")


if __name__ == "__main__":
    unittest.main()
