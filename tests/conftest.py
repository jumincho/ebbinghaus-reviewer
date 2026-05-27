"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pytest

from ebbinghaus_reviewer.scheduler import Scheduler
from ebbinghaus_reviewer.storage import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Iterator[Storage]:
    """Fresh on-disk SQLite store under tmp_path."""
    db = tmp_path / "test.sqlite"
    s = Storage(db)
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def scheduler(storage: Storage) -> Scheduler:
    return Scheduler(storage)


@pytest.fixture
def t0() -> datetime:
    """A fixed reference timestamp for deterministic tests."""
    return datetime(2026, 1, 1, 12, 0, 0)
