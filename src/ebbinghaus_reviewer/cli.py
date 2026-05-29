"""Command-line interface for Ebbinghaus Reviewer.

A ``click`` application with ``rich`` output. Commands:

* ``add``    -- add a study item
* ``list``   -- list all items
* ``today``  -- show items due for review
* ``review`` -- interactively grade due items
* ``stats``  -- show collection statistics
* ``delete`` -- remove an item

The database path defaults to :func:`ebbinghaus_reviewer.default_db_path` and
can be overridden per-invocation with ``--db`` or via the ``EBBINGHAUS_DB``
environment variable.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__, default_db_path
from .algorithm import MAX_QUALITY, MIN_QUALITY, PASSING_QUALITY
from .scheduler import Scheduler
from .storage import Storage, StudyItem

console = Console()

#: Human-friendly descriptions of each SM-2 recall grade, shown during review.
QUALITY_HELP: dict[int, str] = {
    0: "total blackout",
    1: "wrong; answer felt familiar",
    2: "wrong; answer was easy to recall once shown",
    3: "correct, but with serious difficulty",
    4: "correct, after some hesitation",
    5: "perfect recall",
}


def _scheduler(ctx: click.Context) -> Scheduler:
    """Build a :class:`Scheduler` bound to the db path stored on the context."""
    db_path: Path = ctx.obj["db_path"]
    return Scheduler(Storage(db_path))


def _items_table(items: list[StudyItem], *, title: str) -> Table:
    """Render a list of items as a rich table."""
    table = Table(title=title, header_style="bold cyan", expand=False)
    table.add_column("ID", justify="right", style="bold")
    table.add_column("Front")
    table.add_column("Back", style="dim")
    table.add_column("Due", justify="center")
    table.add_column("Reps", justify="right")
    table.add_column("EF", justify="right")
    table.add_column("Interval", justify="right")
    today = date.today()
    for item in items:
        overdue = item.due_date <= today
        due_style = "bold red" if overdue else "green"
        table.add_row(
            str(item.id),
            item.front,
            item.back,
            f"[{due_style}]{item.due_date.isoformat()}[/{due_style}]",
            str(item.repetitions),
            f"{item.ease_factor:.2f}",
            f"{item.interval}d",
        )
    return table


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="ebbinghaus")
@click.option(
    "--db",
    "db_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Path to the SQLite database (default: $EBBINGHAUS_DB or XDG data dir).",
)
@click.pass_context
def cli(ctx: click.Context, db_path: Path | None) -> None:
    """Ebbinghaus Reviewer -- spaced-repetition study at the command line."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db_path or default_db_path()


@cli.command()
@click.argument("front")
@click.option("-b", "--back", default="", help="The answer / note for the card.")
@click.pass_context
def add(ctx: click.Context, front: str, back: str) -> None:
    """Add a study item with FRONT (prompt) and an optional --back (answer)."""
    sched = _scheduler(ctx)
    item = sched.add_item(front, back)
    console.print(
        f"[green]Added[/green] item [bold]#{item.id}[/bold]: {item.front} "
        f"(due {item.due_date.isoformat()})"
    )


@cli.command(name="list")
@click.pass_context
def list_items(ctx: click.Context) -> None:
    """List every study item and its schedule."""
    sched = _scheduler(ctx)
    items = sched.list_items()
    if not items:
        console.print("[yellow]No study items yet. Add one with 'ebbinghaus add'.[/yellow]")
        return
    console.print(_items_table(items, title=f"All items ({len(items)})"))


@cli.command()
@click.pass_context
def today(ctx: click.Context) -> None:
    """Show the items that are due for review today (or overdue)."""
    sched = _scheduler(ctx)
    due = sched.due_today()
    if not due:
        console.print("[green]Nothing due. You're all caught up![/green]")
        return
    console.print(_items_table(due, title=f"Due today ({len(due)})"))


@cli.command()
@click.option(
    "--id",
    "item_id",
    type=int,
    default=None,
    help="Review only this item id (default: walk every due item).",
)
@click.pass_context
def review(ctx: click.Context, item_id: int | None) -> None:
    """Interactively grade due items (recall quality 0-5)."""
    sched = _scheduler(ctx)
    if item_id is not None:
        item = sched.storage.get(item_id)
        if item is None:
            raise click.ClickException(f"No item with id {item_id}.")
        queue = [item]
    else:
        queue = sched.due_today()

    if not queue:
        console.print("[green]Nothing to review. You're all caught up![/green]")
        return

    grade_legend = "  ".join(f"{q}={desc}" for q, desc in QUALITY_HELP.items())
    reviewed = 0
    for item in queue:
        console.print(
            Panel(
                f"[bold]{item.front}[/bold]\n\n[dim]{item.back or '(no answer recorded)'}[/dim]",
                title=f"Item #{item.id}",
                subtitle="recall it, then grade yourself",
            )
        )
        console.print(f"[dim]{grade_legend}[/dim]")
        quality = click.prompt(
            "Quality",
            type=click.IntRange(MIN_QUALITY, MAX_QUALITY),
        )
        updated = sched.record_review(item.id, quality)  # type: ignore[arg-type]
        verdict = (
            "[green]passed[/green]"
            if quality >= PASSING_QUALITY
            else "[red]missed -- schedule reset[/red]"
        )
        console.print(
            f"{verdict}; next review in [bold]{updated.interval}d[/bold] "
            f"on {updated.due_date.isoformat()} (EF {updated.ease_factor:.2f})\n"
        )
        reviewed += 1

    console.print(f"[cyan]Reviewed {reviewed} item(s).[/cyan]")


@cli.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show summary statistics for the whole collection."""
    sched = _scheduler(ctx)
    s = sched.stats()
    table = Table(title="Statistics", header_style="bold cyan", show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Total items", str(s.total))
    table.add_row("Due today", str(s.due_today))
    table.add_row("Learning (<2 reps)", str(s.learning))
    table.add_row("Mature (>=21d interval)", str(s.mature))
    table.add_row("Average ease factor", f"{s.average_ease:.2f}")
    console.print(table)


@cli.command()
@click.argument("item_id", type=int)
@click.option("-y", "--yes", is_flag=True, help="Skip the confirmation prompt.")
@click.pass_context
def delete(ctx: click.Context, item_id: int, yes: bool) -> None:
    """Delete the study item with ITEM_ID."""
    sched = _scheduler(ctx)
    item = sched.storage.get(item_id)
    if item is None:
        raise click.ClickException(f"No item with id {item_id}.")
    if not yes:
        click.confirm(f"Delete #{item.id} '{item.front}'?", abort=True)
    sched.delete_item(item_id)
    console.print(f"[red]Deleted[/red] item #{item_id}.")


def main() -> None:
    """Console-script entry point."""
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
