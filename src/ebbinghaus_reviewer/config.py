"""Where the collection lives on disk."""

from __future__ import annotations

import os
from pathlib import Path

import platformdirs

__all__ = ["APP_NAME", "DB_ENV_VAR", "default_db_path"]

APP_NAME = "ebbinghaus-reviewer"
DB_ENV_VAR = "EBBINGHAUS_DB"


def default_db_path() -> Path:
    """The database used when none is given explicitly.

    ``$EBBINGHAUS_DB`` wins when set; otherwise the per-user data directory of
    the platform (e.g. ``~/.local/share/ebbinghaus-reviewer`` on Linux,
    ``%LOCALAPPDATA%\\ebbinghaus-reviewer`` on Windows).
    """
    override = os.environ.get(DB_ENV_VAR)
    if override:
        return Path(override).expanduser()
    return platformdirs.user_data_path(APP_NAME, appauthor=False) / "ebbinghaus.sqlite3"
