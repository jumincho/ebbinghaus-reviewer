from __future__ import annotations

from pathlib import Path

import pytest

from ebbinghaus_reviewer.config import default_db_path


def test_environment_variable_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EBBINGHAUS_DB", str(tmp_path / "custom.sqlite3"))
    assert default_db_path() == tmp_path / "custom.sqlite3"


def test_home_is_expanded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EBBINGHAUS_DB", "~/reviews.sqlite3")
    assert default_db_path() == Path.home() / "reviews.sqlite3"


def test_platform_data_directory_is_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EBBINGHAUS_DB", raising=False)
    path = default_db_path()
    assert path.name == "ebbinghaus.sqlite3"
    assert path.parent.name == "ebbinghaus-reviewer"
