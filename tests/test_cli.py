"""Tests for the Click CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ebbinghaus_reviewer.cli import cli


@pytest.fixture
def runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """A CliRunner with an isolated DB path."""
    monkeypatch.setenv("EBBINGHAUS_DB_PATH", str(tmp_path / "cli.sqlite"))
    return CliRunner()


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "ebbinghaus" in result.output.lower()


def test_add_then_list(runner: CliRunner) -> None:
    r1 = runner.invoke(cli, ["add", "What is SM-2?", "-b", "A 1985 algorithm.", "-t", "algo"])
    assert r1.exit_code == 0, r1.output
    assert "added" in r1.output.lower()

    r2 = runner.invoke(cli, ["list"])
    assert r2.exit_code == 0
    assert "What is SM-2?" in r2.output
    assert "algo" in r2.output


def test_list_empty(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "No cards" in result.output


def test_today_when_due(runner: CliRunner) -> None:
    runner.invoke(cli, ["add", "Q1"])
    result = runner.invoke(cli, ["today"])
    assert result.exit_code == 0
    assert "Q1" in result.output
    assert "Due now" in result.output


def test_today_when_empty(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["today"])
    assert result.exit_code == 0
    assert "caught up" in result.output.lower()


def test_review_single_card(runner: CliRunner) -> None:
    runner.invoke(cli, ["add", "Capital of France?", "-b", "Paris"])
    # Two prompts: Enter to reveal, then quality.
    result = runner.invoke(cli, ["review", "1"], input="\n5\n")
    assert result.exit_code == 0
    assert "Saved" in result.output
    assert "Paris" in result.output


def test_review_unknown_card(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["review", "9999"], input="")
    assert result.exit_code == 0
    assert "not found" in result.output.lower()


def test_review_all_due(runner: CliRunner) -> None:
    runner.invoke(cli, ["add", "Q1"])
    runner.invoke(cli, ["add", "Q2"])
    # Two cards: each asks reveal-Enter then quality.
    result = runner.invoke(cli, ["review"], input="\n5\n\n5\n")
    assert result.exit_code == 0
    assert "Reviewing 2" in result.output


def test_review_all_when_nothing_due(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["review"])
    assert result.exit_code == 0
    assert "caught up" in result.output.lower()


def test_delete(runner: CliRunner) -> None:
    runner.invoke(cli, ["add", "Q"])
    result = runner.invoke(cli, ["delete", "1", "--yes"])
    assert result.exit_code == 0
    assert "Deleted" in result.output

    listing = runner.invoke(cli, ["list"])
    assert "No cards" in listing.output


def test_delete_missing(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["delete", "999", "--yes"])
    assert result.exit_code == 0
    assert "not found" in result.output.lower()


def test_stats(runner: CliRunner) -> None:
    runner.invoke(cli, ["add", "Q1"])
    runner.invoke(cli, ["add", "Q2"])
    result = runner.invoke(cli, ["stats"])
    assert result.exit_code == 0
    assert "Total cards" in result.output
    assert "2" in result.output


def test_list_filter_by_tag(runner: CliRunner) -> None:
    runner.invoke(cli, ["add", "P", "-t", "psych"])
    runner.invoke(cli, ["add", "A", "-t", "algo"])
    result = runner.invoke(cli, ["list", "-t", "psych"])
    assert result.exit_code == 0
    assert "P" in result.output
    # The 'A' card should not appear (it has no 'psych' tag).
    # We check the table doesn't include "algo" tag.
    assert "algo" not in result.output
