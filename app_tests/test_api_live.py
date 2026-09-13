from __future__ import annotations

import json
import os
import socket
import threading
import time
import unittest
import urllib.parse
import urllib.request
from unittest.mock import patch

import uvicorn

from app.api.main import app, default_service


SUFFICIENT_QA_QUESTION = "1/p + 1/q = 1"


class BookAppLiveApiTests(unittest.TestCase):
    def _start_server(self) -> str:
        # Keep the chosen socket bound until Uvicorn takes it. Fixed test ports
        # may be reserved by Windows/Hyper-V or occupied by another test run.
        listener = socket.socket()
        self.addCleanup(listener.close)
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        self.addCleanup(self._stop_server, server, thread)

        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        self.assertTrue(server.started, "Uvicorn did not start on 127.0.0.1")
        return f"http://127.0.0.1:{port}"

    def test_uvicorn_serves_real_library_and_search_on_loopback(self) -> None:
        default_service.cache_clear()
        self.addCleanup(default_service.cache_clear)
        base_url = self._start_server()

        with urllib.request.urlopen(f"{base_url}/api/health", timeout=3) as response:
            health = json.loads(response.read().decode("utf-8"))
        with urllib.request.urlopen(f"{base_url}/api/library", timeout=3) as response:
            library = json.loads(response.read().decode("utf-8"))
        query = urllib.parse.quote("Hölder")
        with urllib.request.urlopen(
            f"{base_url}/api/courses/functional_analysis_course/search?q={query}",
            timeout=3,
        ) as response:
            search = json.loads(response.read().decode("utf-8"))

        self.assertEqual(health, {"status": "ok"})
        self.assertEqual(library["courses"][0]["course_id"], "functional_analysis_course")
        self.assertEqual(library["courses"][0]["section_count"], 132)
        self.assertGreater(search["result_count"], 0)
        self.assertEqual(search["results"][0]["source_kind"], "object")
        self.assertEqual(search["results"][0]["object_type"], "theorem")

    def test_uvicorn_serves_scoped_conversational_v2_qa_with_explicit_fake_provider(self) -> None:
        default_service.cache_clear()
        self.addCleanup(default_service.cache_clear)
        with patch.dict(os.environ, {"BOOK_QA_PROVIDER": "fake"}, clear=False):
            base_url = self._start_server()

            request = urllib.request.Request(
                f"{base_url}/api/courses/functional_analysis_course/qa",
                data=json.dumps(
                    {
                        "question": SUFFICIENT_QA_QUESTION,
                        "section_id": "ch01_s01",
                        "history": [
                            {"role": "user", "content": "什么是共轭指数？"},
                            {"role": "assistant", "content": "上一轮回答只用于理解追问。"},
                        ],
                    },
                    ensure_ascii=False,
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))

            self.assertEqual(payload["course_id"], "functional_analysis_course")
            self.assertEqual(payload["book_id"], "stein_shakarchi_functional_analysis_2011")
            self.assertEqual(payload["answer_kind"], "generated")
            self.assertEqual(payload["answer_style"], "brief")
            self.assertEqual(payload["scope_requested"], "section_then_book")
            self.assertIn(payload["scope_used"], ("section", "book"))
            self.assertFalse(payload["insufficient_evidence"])
            self.assertIsNone(payload["message"])
            self.assertTrue(payload["citations"])
            first = payload["citations"][0]
            self.assertEqual(first["source_kind"], "object")
            self.assertTrue(first["source_id"])
            self.assertIsNotNone(first["chapter_id"])
            self.assertIsNotNone(first["section_id"])
            self.assertTrue(first["type_zh"])
            self.assertNotIn("citation_id", first)
            self.assertNotIn("evidence_status", payload)

    @staticmethod
    def _stop_server(server: uvicorn.Server, thread: threading.Thread) -> None:
        server.should_exit = True
        thread.join(timeout=5)
        if thread.is_alive():
            server.force_exit = True
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
