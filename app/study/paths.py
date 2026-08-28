from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path


def resolve_study_db_path(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    env = os.environ if environ is None else environ
    base_home = Path.home() if home is None else Path(home)
    override = str(env.get("BOOK_APP_DATA_DIR") or "").strip()

    if override:
        data_dir = Path(override).expanduser()
    elif os.name == "nt":
        data_dir = (
            Path(env.get("LOCALAPPDATA") or (base_home / "AppData" / "Local"))
            / "BookApp"
        )
    elif sys.platform == "darwin":
        data_dir = base_home / "Library" / "Application Support" / "BookApp"
    else:
        xdg = str(env.get("XDG_DATA_HOME") or "").strip()
        data_dir = (
            Path(xdg).expanduser() if xdg else base_home / ".local" / "share"
        ) / "BookApp"

    return data_dir / "book-app.sqlite3"
