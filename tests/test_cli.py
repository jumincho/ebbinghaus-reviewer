from __future__ import annotations

import importlib.util
import json
from datetime import timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from ebbinghaus_reviewer import __version__
from ebbinghaus_reviewer.cli import AppContext, cli
from tests.conftest import KST, START, FakeClock


class Harness:
    """Runs the CLI against a temporary database with a controllable clock."""

    def __init__(self, db: Path, clock: FakeClock) -> None:
        self.db = db
        self.clock = clock
        self.runner = CliRunner()

    def __call__(self, *args: str, input: str | None = None, ok: bool = True) -> Result:
        app = AppContext(clock=self.clock, tz=KST)
        result = self.runner.invoke(
            cli, ["--db", str(self.db), *args], input=input, obj=app, catch_exceptions=False
        )
        if ok:
            assert result.exit_code == 0, result.output
        return result


@pytest.fixture
def run(tmp_path: Path, clock: FakeClock) -> Harness:
    return Harness(tmp_path / "cli.sqlite3", clock)


def test_version_and_help(run: Harness) -> None:
    assert __version__ in run("--version").output
    output = run("--help").output
    for command in ("add", "due", "review", "grade", "agenda", "stats", "export", "serve"):
        assert command in output


def test_add_and_list(run: Harness) -> None:
    output = run("add", "Krebs cycle", "--notes", "eight steps", "--subject", "Biology").output
    assert "Added #1 Krebs cycle - first review in 10 min." in output
    listing = run("list").output
    assert "Krebs cycle" in listing
    assert "Biology" in listing
    assert "ladder 1/4" in listing


def test_add_with_a_past_study_time(run: Harness) -> None:
    assert "first review is due now" in run("add", "x", "--studied", "2h ago").output
    run("add", "y", "--studied", "2026-03-01T20:00")
    run("add", "z", "--studied", "now", "--strategy", "sm2")
    assert "Items (3)" in run("list").output


def test_add_rejects_bad_input(run: Harness) -> None:
    result = run("add", "x", "--studied", "yesterday-ish", ok=False)
    assert result.exit_code == 2
    assert "Invalid value for '--studied'" in result.output
    result = run("add", "   ", ok=False)
    assert result.exit_code == 1
    assert "title must not be empty" in result.output
    result = run("add", "x", "--studied", "2030-01-01T00:00", ok=False)
    assert "cannot be in the future" in result.output


def test_due_and_grade(run: Harness, clock: FakeClock) -> None:
    run("add", "Avogadro constant")
    assert "All caught up." in run("due").output
    assert "Next up: #1 Avogadro constant (in 10 min)" in run("due").output
    clock.advance(timedelta(minutes=11))
    assert "Due now (1)" in run("due").output
    output = run("grade", "1", "good").output
    assert "good - next review in 1 day" in output
    assert "All caught up." in run("due").output


def test_grade_errors(run: Harness) -> None:
    result = run("grade", "7", "good", ok=False)
    assert "There is no item #7." in result.output
    result = run("grade", "1", "perfect", ok=False)
    assert result.exit_code == 2


def test_interactive_review(run: Harness, clock: FakeClock) -> None:
    run("add", "first", "--notes", "the answer")
    run("add", "second")
    run("add", "third")
    clock.advance(timedelta(minutes=10))
    # first: reveal notes, grade good; second: skip; third: quit.
    output = run("review", input="\ng\ns\nq\n").output
    assert "3 to review. Grades: [a]gain  [h]ard  [g]ood  [e]asy" in output
    assert "the answer" in output
    assert "good - next review in 1 day" in output
    assert "Reviewed 1 item." in output
    assert "Due now (2)" in run("due").output


def test_review_single_item_and_quit_before_reveal(run: Harness) -> None:
    run("add", "x", "--notes", "secret")
    output = run("review", "1", input="q\n").output
    assert "secret" not in output
    assert "Reviewed 0 items." in output


def test_review_when_nothing_is_due(run: Harness) -> None:
    assert "Nothing is scheduled" in run("review").output


def test_show_edit_restart_delete(run: Harness, clock: FakeClock) -> None:
    run("add", "Treaty", "--subject", "History", "--strategy", "sm2")
    clock.advance(timedelta(days=1))
    run("grade", "1", "hard")
    shown = run("show", "1").output
    assert "SM-2 · rep 1 · EF 2.36" in shown
    assert "on time" in shown

    run("edit", "1", "--title", "Treaty of Westphalia", "--notes", "1648")
    assert "Treaty of Westphalia" in run("show", "1").output
    run("edit", "1", "--clear-subject")
    assert "History" not in run("list").output
    assert run("edit", "1", ok=False).exit_code == 2
    assert run("edit", "1", "-s", "A", "--clear-subject", ok=False).exit_code == 2

    restarted = run("restart", "1", "--strategy", "ladder").output
    assert "Restarted #1 (ladder · step 1 of 4)" in restarted

    assert run("delete", "1", input="n\n", ok=False).exit_code == 1  # aborted
    assert "Deleted #1." in run("delete", "1", "--yes").output
    assert "No items yet." in run("list").output


def test_agenda_and_stats(run: Harness, clock: FakeClock) -> None:
    run("add", "overdue", "--studied", "1d ago")
    run("add", "tomorrow", "--strategy", "sm2")
    agenda = run("agenda", "--days", "3").output
    assert "Today 2026-03-02" in agenda
    assert "overdue  #1 overdue" in agenda
    assert "Tomorrow 2026-03-03" in agenda
    assert "09:00  #2 tomorrow" in agenda
    run("grade", "1", "again")
    stats = run("stats").output
    assert "Reviews today" in stats
    assert "0%" in stats  # the only review was "again"
    assert "1 day" in stats  # streak


def test_empty_agenda(run: Harness) -> None:
    assert "Nothing scheduled in the next 14 days." in run("agenda").output


def test_export_and_import(run: Harness, tmp_path: Path, clock: FakeClock) -> None:
    run("add", "exported", "--subject", "S")
    out = tmp_path / "export.json"
    run("export", "--output", str(out))
    document = json.loads(out.read_text(encoding="utf-8"))
    assert document["items"][0]["title"] == "exported"
    assert json.loads(run("export").output)["format"] == "ebbinghaus-reviewer"

    other = Harness(tmp_path / "other.sqlite3", clock)
    assert "Imported 1 item." in other("import", str(out)).output
    assert "exported" in other("list").output

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert "Not valid JSON" in other("import", str(bad), ok=False).output
    bad.write_text('{"format": "x"}', encoding="utf-8")
    assert "not an ebbinghaus-reviewer export" in other("import", str(bad), ok=False).output


def test_demo(run: Harness) -> None:
    assert "Added 8 sample items." in run("demo").output
    assert "not empty" in run("demo", ok=False).output
    assert "Added 8 sample items." in run("demo", "--force").output


def test_incompatible_database(tmp_path: Path, clock: FakeClock) -> None:
    db = tmp_path / "text.sqlite3"
    db.write_text("not sqlite " * 100)
    harness = Harness(db, clock)
    assert "is not an Ebbinghaus Reviewer database" in harness("list", ok=False).output
    if importlib.util.find_spec("fastapi") is not None:
        assert "is not an Ebbinghaus Reviewer database" in harness("serve", ok=False).output


def test_serve_explains_missing_extra(run: Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "uvicorn":
            raise ImportError(name)
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", fake_import)
    result = run("serve", ok=False)
    assert "pip install 'ebbinghaus-reviewer[web]'" in result.output


def test_default_database_comes_from_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "env.sqlite3"
    monkeypatch.setenv("EBBINGHAUS_DB", str(db))
    result = CliRunner().invoke(cli, ["add", "from env"], obj=AppContext(clock=FakeClock(START)))
    assert result.exit_code == 0, result.output
    assert db.exists()


def test_serve_runs_uvicorn(run: Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("fastapi")
    import uvicorn

    calls: list[tuple[object, str, int]] = []
    monkeypatch.setattr(uvicorn, "run", lambda app, host, port: calls.append((app, host, port)))
    output = run("serve", "--port", "8123").output
    assert "http://127.0.0.1:8123" in output
    [(app, host, port)] = calls
    assert (host, port) == ("127.0.0.1", 8123)
    assert type(app).__name__ == "FastAPI"


def test_python_dash_m(tmp_path: Path) -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "ebbinghaus_reviewer", "--db", str(tmp_path / "m.sqlite3"), "list"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "No items yet." in result.stdout
