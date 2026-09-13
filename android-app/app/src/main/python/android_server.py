"""Start the existing Book FastAPI app inside the Android process."""

from __future__ import annotations

import mimetypes
import os
import threading
from pathlib import Path

import uvicorn
from fastapi.responses import FileResponse

from app.api.main import app


WEB_ROOT = Path(__file__).resolve().parent / "android_web"
_server: uvicorn.Server | None = None
_thread: threading.Thread | None = None


@app.get("/{web_path:path}", include_in_schema=False)
def android_web(web_path: str = "") -> FileResponse:
    """Serve built React assets and use index.html for browser-router paths."""

    requested = (WEB_ROOT / web_path).resolve()
    try:
        requested.relative_to(WEB_ROOT.resolve())
    except ValueError:
        requested = WEB_ROOT / "index.html"

    if not requested.is_file():
        requested = WEB_ROOT / "index.html"

    media_type, _ = mimetypes.guess_type(str(requested))
    return FileResponse(requested, media_type=media_type)


def start(data_dir: str) -> None:
    """Start one loopback server and return after its thread is launched."""

    global _server, _thread
    if _thread is not None and _thread.is_alive():
        return

    app_data = Path(data_dir) / "book-data"
    app_data.mkdir(parents=True, exist_ok=True)
    os.environ["BOOK_APP_DATA_DIR"] = str(app_data)

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8765,
        log_level="warning",
        access_log=False,
    )
    _server = uvicorn.Server(config)
    _thread = threading.Thread(target=_server.run, name="book-api", daemon=True)
    _thread.start()
