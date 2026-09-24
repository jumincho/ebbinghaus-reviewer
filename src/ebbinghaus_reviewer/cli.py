"""The ``ebbinghaus`` command line."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from pathlib import Path
from typing import IO

import click
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ebbinghaus_reviewer import __version__
from ebbinghaus_reviewer.config import DB_ENV_VAR, default_db_path
from ebbinghaus_reviewer.demo import seed_demo
from ebbinghaus_reviewer.durations import format_interval, format_relative, parse_duration
from ebbinghaus_reviewer.models import Item
from ebbinghaus_reviewer.plumbob import Mood, collection_mood, mood_of
from ebbinghaus_reviewer.presentation import (
    due_label,
    retention_label,
    schedule_label,
)
from ebbinghaus_reviewer.scheduling import Grade, Strategy
from ebbinghaus_reviewer.service import Clock, ItemNotFoundError, Reviewer, system_clock
from ebbinghaus_reviewer.storage import DatabaseError, Repository

console = Console(highlight=False)

_GRADE_KEYS = "[a]gain  [h]ard  [g]ood  [e]asy"
_STRATEGY_HELP = (
    "ladder: fixed reviews after 10 min, 1 day, 1 week and 1 month; "
    "sm2: adaptive SuperMemo-2 intervals."
)


@dataclass
class AppContext:
    """Per-invocation settings; tests inject a clock and a time zone through ``obj``."""

    db_path: Path | None = None
    clock: Clock = system_clock
    tz: tzinfo | None = None

    @contextmanager
    def reviewer(self) -> Iterator[Reviewer]:
        """Open the collection and translate domain errors into CLI errors."""
        path = self.db_path or default_db_path()
        try:
            repository = Repository(path)
        except DatabaseError as exc:
            raise click.ClickException(str(exc)) from None
        try:
            yield Reviewer(repository, clock=self.clock, tz=self.tz)
        except ItemNotFoundError as exc:
            raise click.ClickException(f"There is no item #{exc.item_id}.") from None
        except ValueError as exc:
            raise click.ClickException(str(exc)) from None
        finally:
            repository.close()


pass_app = click.make_pass_decorator(AppContext, ensure=True)


def _parse_when(text: str, reviewer: Reviewer) -> datetime:
    """Parse ``now``, ``<duration> ago`` (e.g. ``2h ago``) or an ISO local date/time."""
    value = text.strip().lower()
    if value == "now":
        return reviewer.now()
    if value.endswith(" ago"):
        return reviewer.now() - parse_duration(value.removesuffix(" ago"))
    try:
        moment = datetime.fromisoformat(text.strip())
    except ValueError:
        raise click.BadParameter(
            "use 'now', '<duration> ago' (e.g. '2h ago') or an ISO time like 2026-09-23T14:00",
            param_hint="'--studied'",
        ) from None
    return moment if moment.tzinfo else reviewer.localize(moment)


def _due_text(item: Item, now: datetime, *, prefix: bool = True) -> Text:
    """The next review as styled text: red when due, green once mastered."""
    if item.due_at is None:
        return Text("mastered", style="green")
    label = due_label(item, now) if prefix else format_relative(item.due_at, now)
    return Text(label, style="bold red" if item.due_at <= now else "")


def _plumbob(mood: Mood) -> Text:
    """The plumbob as a coloured diamond: green fresh, yellow due, red fading."""
    return Text("◆", style=mood.style)


def _items_table(items: list[Item], reviewer: Reviewer, *, title: str) -> Table:
    now = reviewer.now()
    table = Table(title=title, title_justify="left", header_style="bold")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Item", ratio=1)
    table.add_column("Schedule", no_wrap=True)
    table.add_column("Next review", no_wrap=True)
    table.add_column("Recall*", justify="right", no_wrap=True)
    for item in items:
        label = Text(item.title)
        if item.subject:
            label.append(f"  {item.subject}", style="magenta")
        table.add_row(
            str(item.id),
            label,
            schedule_label(item, compact=True),
            _due_text(item, now, prefix=False),
            Text.assemble(_plumbob(mood_of(item, now)), " ", retention_label(item, now)),
        )
    table.caption = (
        "*estimated probability of recall right now\n"
        "◆ plumbob: green = fresh, yellow = due, red = fading"
    )
    table.caption_justify = "left"
    return table


def _next_review_hint(reviewer: Reviewer, subject: str | None) -> str:
    upcoming = reviewer.next_scheduled(subject=subject)
    if upcoming is None or upcoming.due_at is None:
        return "Nothing is scheduled. Add what you study with [bold]ebbinghaus add[/bold]."
    when = format_relative(upcoming.due_at, reviewer.now())
    return f"Next up: #{upcoming.id} {escape(upcoming.title)} ({when})."


def _timing(reviewed_at: datetime, scheduled_for: datetime | None) -> str:
    """How a review related to its due time: ``"on time"``, ``"2 days late"``, ``"3 h early"``."""
    if scheduled_for is None:
        return "-"
    delta = reviewed_at - scheduled_for
    if abs(delta) < timedelta(minutes=1):
        return "on time"
    return f"{format_interval(abs(delta))} {'late' if delta > timedelta() else 'early'}"


def _outcome(item: Item, grade: Grade, reviewer: Reviewer) -> str:
    if item.due_at is None:
        return f"[green]{grade.value}[/green] - mastered, no more reviews needed."
    local = reviewer.local(item.due_at)
    return (
        f"[green]{grade.value}[/green] - next review in {format_interval(item.schedule.interval)} "
        f"({local:%a %d %b %H:%M})."
    )


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version", prog_name="ebbinghaus")
@click.option(
    "--db",
    "db_path",
    type=click.Path(dir_okay=False, path_type=Path),
    envvar=DB_ENV_VAR,
    show_envvar=True,
    help="SQLite file holding your collection (default: the per-user data directory).",
)
@pass_app
def cli(app: AppContext, db_path: Path | None) -> None:
    """Review what you study along the Ebbinghaus forgetting curve.

    Log an item right after you study it; it comes back for review at expanding
    intervals, and each review is graded again, hard, good or easy.
    """
    if db_path is not None:
        app.db_path = db_path


@cli.command()
@click.argument("title")
@click.option("-n", "--notes", default="", help="Notes or the answer, revealed during review.")
@click.option("-s", "--subject", help="Group items, e.g. by course.")
@click.option(
    "--strategy",
    type=click.Choice([strategy.value for strategy in Strategy]),
    default=Strategy.LADDER.value,
    show_default=True,
    help=_STRATEGY_HELP,
)
@click.option(
    "--studied",
    metavar="WHEN",
    help="When you studied it: 'now' (default), '<duration> ago' such as '2h ago', "
    "or an ISO time like 2026-09-23T14:00.",
)
@pass_app
def add(
    app: AppContext,
    title: str,
    notes: str,
    subject: str | None,
    strategy: str,
    studied: str | None,
) -> None:
    """Log something you just studied."""
    with app.reviewer() as reviewer:
        studied_at = _parse_when(studied, reviewer) if studied else None
        item = reviewer.add(
            title, notes=notes, subject=subject, strategy=Strategy(strategy), studied_at=studied_at
        )
        now = reviewer.now()
        first = "is due now" if item.is_due(now) else due_label(item, now).removeprefix("due ")
        console.print(f"Added [cyan]#{item.id}[/cyan] {escape(item.title)} - first review {first}.")


@cli.command()
@click.option("-s", "--subject", help="Only this subject.")
@click.option("--limit", type=click.IntRange(min=1), help="Show at most this many items.")
@pass_app
def due(app: AppContext, subject: str | None, limit: int | None) -> None:
    """Show what is due for review now."""
    with app.reviewer() as reviewer:
        items = reviewer.due(subject=subject, limit=limit)
        if not items:
            console.print(f"[green]All caught up.[/green] {_next_review_hint(reviewer, subject)}")
            return
        console.print(_items_table(items, reviewer, title=f"Due now ({len(items)})"))


@cli.command()
@click.argument("item_id", type=int, required=False)
@click.option("-s", "--subject", help="Only review this subject.")
@click.option("--limit", type=click.IntRange(min=1), help="Stop after this many items.")
@pass_app
def review(app: AppContext, item_id: int | None, subject: str | None, limit: int | None) -> None:
    """Review due items one by one (or just ITEM_ID)."""
    with app.reviewer() as reviewer:
        queue = (
            [reviewer.get(item_id)]
            if item_id is not None
            else reviewer.due(subject=subject, limit=limit)
        )
        if not queue:
            console.print(f"[green]All caught up.[/green] {_next_review_hint(reviewer, subject)}")
            return
        console.print(Text(f"{len(queue)} to review. Grades: {_GRADE_KEYS}; [s]kip, [q]uit."))
        reviewed = 0
        for position, item in enumerate(queue, start=1):
            mood = mood_of(item, reviewer.now())
            console.print(
                Panel(
                    Text(item.title, style="bold"),
                    title=Text.assemble(
                        _plumbob(mood), f" #{item.id}", f" · {item.subject}" if item.subject else ""
                    ),
                    subtitle=f"{position}/{len(queue)} · {schedule_label(item)} · "
                    f"{due_label(item, reviewer.now())}",
                    border_style=mood.style,
                )
            )
            if item.notes:
                answer = click.prompt(
                    "Recall it, then press Enter to see your notes",
                    default="",
                    show_default=False,
                )
                if answer.strip().lower() == "q":
                    break
                console.print(Panel(Text(item.notes), title="Notes", border_style="dim"))
            choice = click.prompt(
                "Grade",
                type=click.Choice(["a", "h", "g", "e", "s", "q"], case_sensitive=False),
                show_choices=False,
            ).lower()
            if choice == "q":
                break
            if choice == "s":
                continue
            grade = Grade.parse(choice)
            console.print(_outcome(reviewer.grade(item.id, grade), grade, reviewer))
            reviewed += 1
        console.print(f"Reviewed {reviewed} item{'s' if reviewed != 1 else ''}.")


@cli.command()
@click.argument("item_id", type=int)
@click.argument("grade", type=click.Choice([grade.value for grade in Grade], case_sensitive=False))
@pass_app
def grade(app: AppContext, item_id: int, grade: str) -> None:
    """Record a review of ITEM_ID without the interactive prompt.

    GRADE is again, hard, good or easy.
    """
    with app.reviewer() as reviewer:
        chosen = Grade.parse(grade)
        console.print(
            f"[cyan]#{item_id}[/cyan] {_outcome(reviewer.grade(item_id, chosen), chosen, reviewer)}"
        )


@cli.command(name="list")
@click.option("-s", "--subject", help="Only this subject.")
@click.option("--active", is_flag=True, help="Hide mastered items.")
@pass_app
def list_items(app: AppContext, subject: str | None, active: bool) -> None:
    """List your items and their schedules."""
    with app.reviewer() as reviewer:
        items = reviewer.items(subject=subject, include_mastered=not active)
        if not items:
            console.print("No items yet. Log what you study with [bold]ebbinghaus add[/bold].")
            return
        console.print(_items_table(items, reviewer, title=f"Items ({len(items)})"))


@cli.command()
@click.argument("item_id", type=int)
@pass_app
def show(app: AppContext, item_id: int) -> None:
    """Show one item with its review history."""
    with app.reviewer() as reviewer:
        item = reviewer.get(item_id)
        now = reviewer.now()
        details = Table.grid(padding=(0, 2))
        details.add_column(style="bold")
        details.add_column()
        details.add_row("Subject", item.subject or "-")
        details.add_row("Schedule", schedule_label(item))
        details.add_row("Interval", format_interval(item.schedule.interval))
        details.add_row("Next review", _due_text(item, now))
        details.add_row("Recall now", retention_label(item, now) + " (estimated)")
        mood = mood_of(item, now)
        details.add_row("Plumbob", Text.assemble(_plumbob(mood), " ", mood.description))
        details.add_row("Studied", f"{reviewer.local(item.studied_at):%Y-%m-%d %H:%M}")
        details.add_row("Reviews", f"{item.review_count} ({item.lapse_count} forgotten)")
        if item.notes:
            details.add_row("Notes", Text(item.notes))
        console.print(Panel(details, title=f"#{item.id} {escape(item.title)}", title_align="left"))

        history = reviewer.history(item_id)
        if history:
            table = Table(title="History", title_justify="left", header_style="bold")
            table.add_column("When")
            table.add_column("Grade")
            table.add_column("Timing")
            table.add_column("Next interval", justify="right")
            for entry in history:
                table.add_row(
                    f"{reviewer.local(entry.reviewed_at):%Y-%m-%d %H:%M}",
                    entry.grade.value,
                    _timing(entry.reviewed_at, entry.scheduled_for),
                    format_interval(entry.interval),
                )
            console.print(table)


@cli.command()
@click.argument("item_id", type=int)
@click.option("--title", help="New title.")
@click.option("-n", "--notes", help="New notes.")
@click.option("-s", "--subject", help="New subject.")
@click.option("--clear-subject", is_flag=True, help="Remove the subject.")
@pass_app
def edit(
    app: AppContext,
    item_id: int,
    title: str | None,
    notes: str | None,
    subject: str | None,
    clear_subject: bool,
) -> None:
    """Change the text of ITEM_ID (its schedule is kept)."""
    if subject is not None and clear_subject:
        raise click.UsageError("--subject and --clear-subject are mutually exclusive.")
    if title is None and notes is None and subject is None and not clear_subject:
        raise click.UsageError("Nothing to change; pass --title, --notes or --subject.")
    with app.reviewer() as reviewer:
        if clear_subject:
            item = reviewer.edit(item_id, title=title, notes=notes, subject=None)
        elif subject is not None:
            item = reviewer.edit(item_id, title=title, notes=notes, subject=subject)
        else:
            item = reviewer.edit(item_id, title=title, notes=notes)
        console.print(f"Updated [cyan]#{item.id}[/cyan] {escape(item.title)}.")


@cli.command()
@click.argument("item_id", type=int)
@click.option(
    "--strategy",
    type=click.Choice([strategy.value for strategy in Strategy]),
    help="Switch to this strategy as well.",
)
@pass_app
def restart(app: AppContext, item_id: int, strategy: str | None) -> None:
    """Start the schedule of ITEM_ID over, as if you had just studied it."""
    with app.reviewer() as reviewer:
        item = reviewer.restart(item_id, strategy=Strategy(strategy) if strategy else None)
        console.print(
            f"Restarted [cyan]#{item.id}[/cyan] ({schedule_label(item)}) - "
            f"{due_label(item, reviewer.now())}."
        )


@cli.command()
@click.argument("item_id", type=int)
@click.option("-y", "--yes", is_flag=True, help="Do not ask for confirmation.")
@pass_app
def delete(app: AppContext, item_id: int, yes: bool) -> None:
    """Delete ITEM_ID and its review history."""
    with app.reviewer() as reviewer:
        item = reviewer.get(item_id)
        if not yes:
            click.confirm(f"Delete #{item.id} '{item.title}' and its history?", abort=True)
        reviewer.delete(item_id)
        console.print(f"Deleted [cyan]#{item_id}[/cyan].")


@cli.command()
@click.option(
    "--days",
    type=click.IntRange(min=1, max=366),
    default=14,
    show_default=True,
    help="How many days ahead.",
)
@click.option("-s", "--subject", help="Only this subject.")
@pass_app
def agenda(app: AppContext, days: int, subject: str | None) -> None:
    """Show upcoming reviews day by day (overdue ones count as today)."""
    with app.reviewer() as reviewer:
        schedule = reviewer.agenda(days=days, subject=subject)
        if not schedule:
            console.print(f"Nothing scheduled in the next {days} days.")
            return
        today = reviewer.today()
        now = reviewer.now()
        for entry in schedule:
            offset = (entry.day - today).days
            heading = {0: "Today", 1: "Tomorrow"}.get(offset, f"{entry.day:%A}")
            console.print(f"[bold]{heading}[/bold] [dim]{entry.day:%Y-%m-%d}[/dim]")
            for item in entry.items:
                if item.due_at is None:
                    continue
                when = "overdue" if item.due_at < now else f"{reviewer.local(item.due_at):%H:%M}"
                line = Text.assemble("  ", _plumbob(mood_of(item, now)), f" {when:>7}  ")
                line.append(f"#{item.id}", style="cyan").append(f" {item.title}")
                if item.subject:
                    line.append(f" {item.subject}", style="magenta")
                console.print(line)


@cli.command()
@pass_app
def stats(app: AppContext) -> None:
    """Summarise your collection and recent reviews."""
    with app.reviewer() as reviewer:
        summary = reviewer.stats()
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold")
        table.add_column(justify="right")
        recall = (
            "-" if summary.recall_rate_30_days is None else f"{summary.recall_rate_30_days:.0%}"
        )
        mood = collection_mood(reviewer.due(), reviewer.now())
        for label, value in (
            ("Items", str(summary.total)),
            ("  being reviewed", str(summary.active)),
            ("  mastered", str(summary.mastered)),
            ("Due now", str(summary.due_now)),
            ("Due later today", str(summary.due_later_today)),
            ("Reviews today", str(summary.reviews_today)),
            ("Reviews, last 7 days", str(summary.reviews_last_7_days)),
            ("Recall rate, last 30 days", recall),
            ("Streak", f"{summary.streak_days} day{'s' if summary.streak_days != 1 else ''}"),
        ):
            table.add_row(label, value)
        table.add_row("Plumbob", Text.assemble(_plumbob(mood), f" {mood.value}"))
        console.print(table)


@cli.command()
@click.option(
    "-o",
    "--output",
    type=click.File("w", encoding="utf-8"),
    default="-",
    help="Write to this file instead of standard output.",
)
@pass_app
def export(app: AppContext, output: IO[str]) -> None:
    """Export the whole collection, with history, as JSON."""
    with app.reviewer() as reviewer:
        json.dump(reviewer.export_data(), output, ensure_ascii=False, indent=2)
        output.write("\n")


@cli.command(name="import")
@click.argument("source", type=click.File("r", encoding="utf-8"))
@pass_app
def import_items(app: AppContext, source: IO[str]) -> None:
    """Add every item from a JSON export (SOURCE may be '-' for stdin)."""
    try:
        document = json.load(source)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Not valid JSON: {exc}") from None
    with app.reviewer() as reviewer:
        count = reviewer.import_data(document)
        console.print(f"Imported {count} item{'s' if count != 1 else ''}.")


@cli.command()
@click.option("--force", is_flag=True, help="Add the samples even if the collection is not empty.")
@pass_app
def demo(app: AppContext, force: bool) -> None:
    """Fill the collection with sample items and review history."""
    with app.reviewer() as reviewer:
        if reviewer.items() and not force:
            raise click.ClickException(
                "The collection is not empty. Use --db to pick another file, or --force."
            )
        count = seed_demo(reviewer.repository, now=reviewer.now())
        console.print(f"Added {count} sample items. Try [bold]ebbinghaus due[/bold].")


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Interface to bind.")
@click.option("--port", type=click.IntRange(1, 65535), default=8000, show_default=True)
@pass_app
def serve(app: AppContext, host: str, port: int) -> None:
    """Run the web app (needs the 'web' extra)."""
    try:
        import uvicorn

        from ebbinghaus_reviewer.web import create_app
    except ImportError:
        raise click.ClickException(
            "The web app needs extra packages: pip install 'ebbinghaus-reviewer[web]'"
        ) from None
    path = app.db_path or default_db_path()
    try:
        web_app = create_app(path, clock=app.clock, tz=app.tz)
    except DatabaseError as exc:
        raise click.ClickException(str(exc)) from None
    console.print(f"Serving {path} at [bold]http://{host}:{port}[/bold] (Ctrl+C to stop)")
    uvicorn.run(web_app, host=host, port=port)


def main() -> None:
    """Console-script entry point."""
    cli()


__all__ = ["AppContext", "cli", "main"]
