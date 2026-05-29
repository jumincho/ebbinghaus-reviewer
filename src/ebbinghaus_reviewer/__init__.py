"""Ebbinghaus Reviewer -- a spaced-repetition study tool.

A clean-room Python reimplementation of a 2021 WPF study-reminder app. It
captures study items and schedules their reviews along the Ebbinghaus
forgetting curve using the SM-2 algorithm, so that each card is shown again
right around the moment you would otherwise start to forget it.

Layers:

* :mod:`ebbinghaus_reviewer.algorithm` -- pure SM-2 (no I/O).
* :mod:`ebbinghaus_reviewer.storage`   -- SQLite repository of study items.
* :mod:`ebbinghaus_reviewer.scheduler` -- use cases (add / due / review / stats).
* :mod:`ebbinghaus_reviewer.cli`       -- a ``click`` + ``rich`` command line.
* :mod:`ebbinghaus_reviewer.web`       -- an optional FastAPI + Jinja2 web UI.
"""

from __future__ import annotations

import os
from pathlib import Path

from .algorithm import ReviewState, review
from .scheduler import Scheduler, Stats
from .storage import Storage, StudyItem

__version__ = "1.0.0"

__all__ = [
    "ReviewState",
    "review",
    "Scheduler",
    "Stats",
    "Storage",
    "StudyItem",
    "default_db_path",
    "__version__",
]


def default_db_path() -> Path:
    """Return the default on-disk database path.

    Honours the ``EBBINGHAUS_DB`` environment variable when set; otherwise uses
    ``~/.local/share/ebbinghaus-reviewer/reviews.db`` (XDG-style). The parent
    directory is created on demand by the storage layer, not here.
    """
    override = os.environ.get("EBBINGHAUS_DB")
    if override:
        return Path(override).expanduser()
    data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(data_home) if data_home else Path.home() / ".local" / "share"
    return base / "ebbinghaus-reviewer" / "reviews.db"
