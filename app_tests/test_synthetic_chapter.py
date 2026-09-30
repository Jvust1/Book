"""Real API/runtime integration on a wholly original temporary chapter."""
import importlib.util
import unittest

from fastapi.testclient import TestClient

from app_tests.synthetic_chapter import BOOK_ID, COURSE_ID, EXPECTED, QUESTION, SECTION_ID, SOURCE_ID
from app_tests.synthetic_pilot_server import create_app
from runtime.symbolic_answer import SymPyAnswerChecker


class SyntheticChapterTests(unittest.TestCase):
    def test_file_backed_chapter_source_search_qa_and_progress(self):
        with TestClient(create_app()) as client:
            prefix = f"/api/courses/{COURSE_ID}"
            self.assertEqual(client.get("/api/library").json()["courses"][0]["course_id"], COURSE_ID)
            self.assertEqual(client.get(prefix).json()["course"]["chapter_count"], 1)
            for mode in ("preview", "learn", "review", "practice"):
                response = client.get(f"{prefix}/sections/{SECTION_ID}/{mode}")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["items"])
                self.assertEqual(response.json()["book_id"], BOOK_ID)
                touched = client.post(f"{prefix}/sections/{SECTION_ID}/study/{mode}/touch")
                self.assertEqual(touched.status_code, 200)
                self.assertEqual(touched.json()["progress"], 0)
            source = client.get(f"{prefix}/sources/object/{SOURCE_ID}").json()
            self.assertEqual((source["pdf_page"], source["printed_page"]), (2, 1))
            self.assertIn("原创试点", source["content_zh"])
            search = client.get(f"{prefix}/search", params={"q": QUESTION}).json()
            self.assertEqual(search["results"][0]["source_id"], SOURCE_ID)
            answer = client.post(f"{prefix}/qa", json={"question": QUESTION, "section_id": SECTION_ID, "history": []})
            self.assertEqual(answer.status_code, 200)
            answer = answer.json()
            self.assertEqual(answer["answer_kind"], "generated")
            self.assertEqual(answer["scope_used"], "section")
            self.assertEqual(answer["citations"][0]["source_id"], source["source_id"])
            self.assertEqual(answer["citations"][0]["source_anchor"], source["source_anchor"])
            self.assertIn("$$x+x=4$$", answer["answer"])
            self.assertEqual(client.post(f"{prefix}/sections/{SECTION_ID}/study/learn/complete").json()["progress"], 100)
            missing = client.post(f"{prefix}/qa", json={"question": "unrelated-zebra-984", "section_id": SECTION_ID, "history": []}).json()
            self.assertEqual(missing["answer_kind"], "system_notice")
            self.assertEqual(missing["citations"], [])
            # An unrelated canonical/private book is not present in this fixture server.
            self.assertEqual(client.get("/api/courses/functional_analysis_course").status_code, 404)
        # Each explicit server factory uses a fresh temporary StudyRecord database.
        with TestClient(create_app()) as fresh:
            touched = fresh.post(f"/api/courses/{COURSE_ID}/sections/{SECTION_ID}/study/learn/touch").json()
            self.assertEqual(touched["progress"], 0)

    @unittest.skipUnless(importlib.util.find_spec("sympy"), "optional pinned SymPy is tested in the pilot CI job")
    def test_original_practice_expected_answer_remains_a_diagnostic(self):
        checker = SymPyAnswerChecker()
        self.assertTrue(checker.check("2+2", EXPECTED).equivalent)
        self.assertFalse(checker.check("5", EXPECTED).equivalent)
        self.assertIsNone(checker.check('__import__("os")', EXPECTED).equivalent)


if __name__ == "__main__":
    unittest.main()
