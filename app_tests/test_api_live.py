from __future__ import annotations

import json
import os
import threading
import time
import unittest
import urllib.parse
import urllib.request
from unittest.mock import patch

import uvicorn

from app.api.main import app, default_service


class BookAppLiveApiTests(unittest.TestCase):
    def test_uvicorn_serves_real_library_and_search_on_loopback(self) -> None:
        default_service.cache_clear()
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8765,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        self.addCleanup(self._stop_server, server, thread)
        self.addCleanup(default_service.cache_clear)

        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        self.assertTrue(server.started, "Uvicorn did not start on 127.0.0.1")

        with urllib.request.urlopen("http://127.0.0.1:8765/api/health", timeout=3) as response:
            health = json.loads(response.read().decode("utf-8"))
        with urllib.request.urlopen("http://127.0.0.1:8765/api/library", timeout=3) as response:
            library = json.loads(response.read().decode("utf-8"))
        query = urllib.parse.quote("Hölder")
        with urllib.request.urlopen(
            f"http://127.0.0.1:8765/api/courses/functional_analysis_course/search?q={query}",
            timeout=3,
        ) as response:
            search = json.loads(response.read().decode("utf-8"))

        self.assertEqual(health, {"status": "ok"})
        self.assertEqual(library["courses"][0]["course_id"], "functional_analysis_course")
        self.assertEqual(library["courses"][0]["section_count"], 132)
        self.assertGreater(search["result_count"], 0)
        self.assertEqual(search["results"][0]["source_kind"], "object")
        self.assertEqual(search["results"][0]["object_type"], "theorem")

    def test_uvicorn_serves_real_textbook_qa_with_explicit_fake_provider(self) -> None:
        default_service.cache_clear()
        self.addCleanup(default_service.cache_clear)
        with patch.dict(os.environ, {"BOOK_QA_PROVIDER": "fake"}, clear=False):
            config = uvicorn.Config(
                app,
                host="127.0.0.1",
                port=8766,
                log_level="warning",
                access_log=False,
            )
            server = uvicorn.Server(config)
            thread = threading.Thread(target=server.run, daemon=True)
            thread.start()
            self.addCleanup(self._stop_server, server, thread)

            for _ in range(100):
                if server.started:
                    break
                time.sleep(0.05)
            self.assertTrue(server.started, "Uvicorn did not start on 127.0.0.1")

            request = urllib.request.Request(
                "http://127.0.0.1:8766/api/courses/functional_analysis_course/qa",
                data=json.dumps(
                    {"question": "什么是巴拿赫空间？"},
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
            self.assertEqual(payload["evidence_status"], "sufficient")
            self.assertTrue(payload["citations"])
            self.assertEqual(payload["citations"][0]["source_kind"], "object")
            self.assertTrue(payload["citations"][0]["source_id"])

    @staticmethod
    def _stop_server(server: uvicorn.Server, thread: threading.Thread) -> None:
        server.should_exit = True
        thread.join(timeout=5)
        if thread.is_alive():
            server.force_exit = True
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
