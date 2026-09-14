"""Book Windows desktop shell: loopback FastAPI + persistent Edge WebView2."""

from __future__ import annotations

import argparse
import ctypes
import logging
import mimetypes
import os
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path


APP_NAME = "Book 学习"
APP_VERSION = "0.1.4"
HOST = "127.0.0.1"
PORT = 17866
ORIGIN = f"http://{HOST}:{PORT}"


def bundle_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    return Path(frozen_root) if frozen_root else Path(__file__).resolve().parents[1]


def data_root() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    return base / "BookApp"


def configure_logging() -> None:
    log_dir = data_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "desktop.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        encoding="utf-8",
    )


def show_error(message: str) -> None:
    logging.exception(message)
    ctypes.windll.user32.MessageBoxW(None, message, f"{APP_NAME} · 启动失败", 0x10)


def claim_port() -> None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind((HOST, PORT))
    except OSError as exc:
        raise RuntimeError("Book 已经在运行，或本机端口 17866 正被其他程序使用。") from exc
    finally:
        probe.close()


def create_application():
    from fastapi import HTTPException
    from fastapi.responses import FileResponse, HTMLResponse

    root = bundle_root()
    if not getattr(sys, "_MEIPASS", None) and str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import app.api.main as api_main

    web_root = root / "desktop_web" if getattr(sys, "_MEIPASS", None) else root / ".build" / "desktop" / "web"
    if not (web_root / "index.html").is_file():
        raise RuntimeError("桌面页面资源不完整，请重新下载应用。")

    os.environ.setdefault("BOOK_APP_DATA_DIR", str(data_root()))
    api_main.REPOSITORY_ROOT = root
    api_main.default_service.cache_clear()
    api_main.default_study_repository.cache_clear()

    @api_main.app.get("/{web_path:path}", include_in_schema=False)
    def desktop_web(web_path: str = ""):
        if web_path == "api" or web_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")

        requested = (web_root / web_path).resolve()
        try:
            requested.relative_to(web_root.resolve())
        except ValueError:
            raise HTTPException(status_code=404, detail="File not found") from None

        if not requested.is_file():
            if web_path.startswith("assets/") or Path(web_path).suffix:
                raise HTTPException(status_code=404, detail="File not found")
            requested = web_root / "index.html"

        headers = {
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        }
        if requested.name == "index.html":
            html = requested.read_text(encoding="utf-8").replace(
                "<head>",
                '<head><script>window.BookDesktop={platform:"windows"}</script>',
                1,
            )
            return HTMLResponse(html, headers=headers)
        media_type, _ = mimetypes.guess_type(str(requested))
        return FileResponse(requested, media_type=media_type, headers=headers)

    return api_main.app


def run_server(application):
    import uvicorn

    config = uvicorn.Config(
        application,
        host=HOST,
        port=PORT,
        log_level="warning",
        log_config=None,
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="book-desktop-api", daemon=True)
    thread.start()

    deadline = time.monotonic() + 30
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if not thread.is_alive():
            break
        try:
            with urllib.request.urlopen(f"{ORIGIN}/api/health", timeout=1) as response:
                if response.status == 200:
                    return server, thread
        except Exception as exc:
            last_error = exc
            time.sleep(0.1)
    server.should_exit = True
    raise RuntimeError(f"本地学习服务启动失败：{last_error or '服务已退出'}")


def self_test(window) -> None:
    deadline = time.monotonic() + 30
    passed = False
    while time.monotonic() < deadline:
        try:
            passed = bool(window.evaluate_js(
                "document.title.includes('Book') && "
                "document.body.innerText.includes('教材库') && "
                "typeof MediaRecorder !== 'undefined' && "
                "typeof indexedDB !== 'undefined' && "
                "!!navigator.mediaDevices"
            ))
            if passed:
                break
        except Exception:
            pass
        time.sleep(0.25)

    logging.info("Desktop self-test result: %s", passed)
    window.destroy()
    if not passed:
        os.environ["BOOK_DESKTOP_SELF_TEST_FAILED"] = "1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--server-only", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    configure_logging()

    server = None
    thread = None
    try:
        claim_port()
        application = create_application()
        server, thread = run_server(application)
        if args.server_only:
            while thread.is_alive():
                time.sleep(0.25)
            return 0

        import webview

        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.settings["ALLOW_FILE_URLS"] = False
        window = webview.create_window(
            APP_NAME,
            ORIGIN,
            width=1280,
            height=840,
            min_size=(360, 640),
            hidden=args.self_test,
            background_color="#f7f5ef",
            text_select=True,
            zoomable=True,
        )
        webview.start(
            self_test if args.self_test else None,
            [window] if args.self_test else None,
            gui="edgechromium",
            private_mode=False,
            storage_path=str(data_root() / "WebView2"),
        )
        return 2 if os.environ.get("BOOK_DESKTOP_SELF_TEST_FAILED") else 0
    except Exception as exc:
        show_error(str(exc))
        return 1
    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None:
            thread.join(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
