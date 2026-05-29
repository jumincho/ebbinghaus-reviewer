"""CLI smoke tests via click's CliRunner."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ebbinghaus_reviewer.cli import cli


@pytest.fixture
def db(tmp_path: Path) -> list[str]:
    """Return the ``--db <path>`` argument prefix for an isolated database."""
    return ["--db", str(tmp_path / "reviews.db")]


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_help_lists_commands(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    for cmd in ("add", "list", "today", "review", "stats", "delete"):
        assert cmd in result.output


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "ebbinghaus" in result.output


def test_add_and_list(runner: CliRunner, db: list[str]) -> None:
    add = runner.invoke(cli, [*db, "add", "What is SM-2?", "-b", "An algorithm"])
    assert add.exit_code == 0, add.output
    assert "Added" in add.output

    listed = runner.invoke(cli, [*db, "list"])
    assert listed.exit_code == 0
    assert "What is SM-2?" in listed.output


def test_list_empty(runner: CliRunner, db: list[str]) -> None:
    result = runner.invoke(cli, [*db, "list"])
    assert result.exit_code == 0
    assert "No study items" in result.output


def test_today_empty(runner: CliRunner, db: list[str]) -> None:
    result = runner.invoke(cli, [*db, "today"])
    assert result.exit_code == 0
    assert "caught up" in result.output


def test_today_shows_due(runner: CliRunner, db: list[str]) -> None:
    runner.invoke(cli, [*db, "add", "due item"])
    result = runner.invoke(cli, [*db, "today"])
    assert result.exit_code == 0
    assert "due item" in result.output


def test_review_interactive(runner: CliRunner, db: list[str]) -> None:
    runner.invoke(cli, [*db, "add", "recall me"])
    # Provide quality "5" on stdin for the single due item.
    result = runner.invoke(cli, [*db, "review"], input="5\n")
    assert result.exit_code == 0, result.output
    assert "Reviewed 1 item" in result.output
    # After review it should no longer be due.
    after = runner.invoke(cli, [*db, "today"])
    assert "caught up" in after.output


def test_review_specific_id(runner: CliRunner, db: list[str]) -> None:
    runner.invoke(cli, [*db, "add", "first"])
    result = runner.invoke(cli, [*db, "review", "--id", "1"], input="4\n")
    assert result.exit_code == 0, result.output
    assert "next review" in result.output


def test_review_nothing_due(runner: CliRunner, db: list[str]) -> None:
    result = runner.invoke(cli, [*db, "review"])
    assert result.exit_code == 0
    assert "caught up" in result.output


def test_review_bad_id_errors(runner: CliRunner, db: list[str]) -> None:
    result = runner.invoke(cli, [*db, "review", "--id", "999"])
    assert result.exit_code != 0
    assert "No item with id 999" in result.output


def test_stats(runner: CliRunner, db: list[str]) -> None:
    runner.invoke(cli, [*db, "add", "x"])
    result = runner.invoke(cli, [*db, "stats"])
    assert result.exit_code == 0
    assert "Total items" in result.output


def test_delete_with_confirmation(runner: CliRunner, db: list[str]) -> None:
    runner.invoke(cli, [*db, "add", "to delete"])
    result = runner.invoke(cli, [*db, "delete", "1"], input="y\n")
    assert result.exit_code == 0
    assert "Deleted" in result.output
    listed = runner.invoke(cli, [*db, "list"])
    assert "to delete" not in listed.output


def test_delete_yes_flag(runner: CliRunner, db: list[str]) -> None:
    runner.invoke(cli, [*db, "add", "to delete"])
    result = runner.invoke(cli, [*db, "delete", "1", "--yes"])
    assert result.exit_code == 0
    assert "Deleted" in result.output


def test_delete_missing_errors(runner: CliRunner, db: list[str]) -> None:
    result = runner.invoke(cli, [*db, "delete", "42", "--yes"])
    assert result.exit_code != 0
    assert "No item with id 42" in result.output
