from __future__ import annotations

import json
import threading
import time
import unittest
import urllib.parse
import urllib.request

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

    @staticmethod
    def _stop_server(server: uvicorn.Server, thread: threading.Thread) -> None:
        server.should_exit = True
        thread.join(timeout=5)
        if thread.is_alive():
            server.force_exit = True
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
