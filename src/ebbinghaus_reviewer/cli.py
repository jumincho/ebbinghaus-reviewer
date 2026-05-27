"""Click-based CLI for ebbinghaus-reviewer."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from ebbinghaus_reviewer import __version__
from ebbinghaus_reviewer.algorithm import ReviewQuality
from ebbinghaus_reviewer.scheduler import Scheduler
from ebbinghaus_reviewer.storage import Storage

console = Console()


def _scheduler(ctx: click.Context) -> Scheduler:
    scheduler: Scheduler = ctx.obj["scheduler"]
    return scheduler


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def _humanize_due(target: datetime, now: datetime) -> str:
    delta = target - now
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return Text("due now", style="bold red").plain
    days, rem = divmod(seconds, 86400)
    hours, _ = divmod(rem, 3600)
    if days >= 1:
        return f"in {days}d {hours}h"
    if hours >= 1:
        return f"in {hours}h"
    minutes, _ = divmod(rem, 60)
    return f"in {minutes}m"


@click.group()
@click.version_option(version=__version__, prog_name="ebbinghaus")
@click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to the SQLite database (overrides EBBINGHAUS_DB_PATH).",
)
@click.pass_context
def cli(ctx: click.Context, db_path: Path | None) -> None:
    """Spaced-repetition study reviewer based on the Ebbinghaus forgetting curve."""
    storage = Storage(db_path)
    ctx.ensure_object(dict)
    ctx.obj["storage"] = storage
    ctx.obj["scheduler"] = Scheduler(storage)
    ctx.call_on_close(storage.close)


@cli.command()
@click.argument("front")
@click.option("-b", "--back", default="", help="Answer / detail on the back of the card.")
@click.option("-t", "--tag", "tags", multiple=True, help="Tag to attach (repeatable).")
@click.pass_context
def add(ctx: click.Context, front: str, back: str, tags: tuple[str, ...]) -> None:
    """Add a new study card. The card is due immediately for first review."""
    card = _scheduler(ctx).add_card(front=front, back=back, tags=list(tags))
    console.print(
        f"[green]Card #{card.id} added.[/green] First review: [bold]due now[/bold]."
    )


@cli.command(name="list")
@click.option("-t", "--tag", default=None, help="Filter by tag (substring match).")
@click.pass_context
def list_cards(ctx: click.Context, tag: str | None) -> None:
    """List all cards (optionally filtered by tag)."""
    cards = _scheduler(ctx).storage.list_cards(tag=tag)
    if not cards:
        console.print("[dim]No cards yet. Add one with `ebbinghaus add`.[/dim]")
        return

    now = datetime.utcnow()
    table = Table(title=f"Cards ({len(cards)})", show_lines=False)
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Front")
    table.add_column("Tags", style="magenta")
    table.add_column("Reps", justify="right")
    table.add_column("EF", justify="right")
    table.add_column("Next review")

    for card in cards:
        next_review = _format_dt(card.next_review_at)
        when = _humanize_due(card.next_review_at, now)
        table.add_row(
            str(card.id),
            card.front,
            ", ".join(card.tags) or "—",
            str(card.repetition),
            f"{card.ease_factor:.2f}",
            f"{next_review} ({when})",
        )
    console.print(table)


@cli.command()
@click.pass_context
def today(ctx: click.Context) -> None:
    """Show cards that are due for review now."""
    now = datetime.utcnow()
    cards = _scheduler(ctx).due_cards(now=now)
    if not cards:
        console.print("[green]Nothing due. You're caught up.[/green]")
        return

    table = Table(title=f"Due now ({len(cards)})")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Front")
    table.add_column("Tags", style="magenta")
    table.add_column("Was due", style="yellow")
    for card in cards:
        delta_h = int((now - card.next_review_at).total_seconds() // 3600)
        was_due = "just now" if delta_h <= 0 else f"{delta_h}h ago"
        table.add_row(str(card.id), card.front, ", ".join(card.tags) or "—", was_due)
    console.print(table)
    console.print(
        "\n[dim]Review with [bold]ebbinghaus review[/bold] (all due) "
        "or [bold]ebbinghaus review <id>[/bold] (one card).[/dim]"
    )


def _quality_prompt() -> ReviewQuality:
    console.print(
        "\n[dim]Quality:[/dim] "
        "[red]0[/red] blackout · "
        "[red]1[/red] wrong/hard · "
        "[red]2[/red] wrong/easy · "
        "[green]3[/green] correct/hard · "
        "[green]4[/green] correct/hesitant · "
        "[green]5[/green] perfect"
    )
    value = IntPrompt.ask("How well did you recall?", choices=["0", "1", "2", "3", "4", "5"])
    return ReviewQuality(value)


def _review_one(scheduler: Scheduler, card_id: int) -> None:
    card = scheduler.storage.get_card(card_id)
    if card is None:
        console.print(f"[red]Card #{card_id} not found.[/red]")
        return

    console.rule(f"Card #{card.id}")
    console.print(f"[bold]{card.front}[/bold]")
    if card.tags:
        console.print(f"[magenta]tags:[/magenta] {', '.join(card.tags)}")
    Prompt.ask("\n[dim]Press Enter to reveal answer[/dim]", default="", show_default=False)
    if card.back:
        console.print(f"\n[cyan]{card.back}[/cyan]")
    else:
        console.print("[dim](no back content)[/dim]")

    quality = _quality_prompt()
    updated = scheduler.review_card(card.id, quality)  # type: ignore[arg-type]
    console.print(
        f"\n[green]Saved.[/green] Next review: [bold]{_format_dt(updated.next_review_at)}[/bold] "
        f"(in {updated.interval_days}d, EF={updated.ease_factor:.2f})"
    )


@cli.command()
@click.argument("card_id", required=False, type=int)
@click.pass_context
def review(ctx: click.Context, card_id: int | None) -> None:
    """Review one card by id, or step through every card currently due."""
    scheduler = _scheduler(ctx)
    if card_id is not None:
        _review_one(scheduler, card_id)
        return

    due = scheduler.due_cards()
    if not due:
        console.print("[green]Nothing due. You're caught up.[/green]")
        return

    console.print(f"[bold]Reviewing {len(due)} due card(s).[/bold]\n")
    for i, card in enumerate(due, 1):
        console.print(f"[dim]({i}/{len(due)})[/dim]")
        assert card.id is not None
        _review_one(scheduler, card.id)


@cli.command()
@click.argument("card_id", type=int)
@click.confirmation_option(prompt="Delete this card and all its reviews?")
@click.pass_context
def delete(ctx: click.Context, card_id: int) -> None:
    """Delete a card and its review history."""
    if _scheduler(ctx).storage.delete_card(card_id):
        console.print(f"[green]Deleted card #{card_id}.[/green]")
    else:
        console.print(f"[red]Card #{card_id} not found.[/red]")


@cli.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show summary statistics."""
    storage = _scheduler(ctx).storage
    now = datetime.utcnow()
    table = Table(title="Stats", show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Total cards", str(storage.card_count()))
    table.add_row("Total reviews", str(storage.review_count()))
    table.add_row("Due now", str(storage.due_count(now)))
    table.add_row("Database", str(storage.db_path))
    console.print(table)


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
@click.option(
    "--reload",
    is_flag=True,
    default=False,
    help="Auto-reload on code changes (development).",
)
@click.pass_context
def serve(ctx: click.Context, host: str, port: int, reload: bool) -> None:
    """Launch the web UI."""
    import uvicorn

    storage_path = ctx.obj["storage"].db_path
    # Re-export so the FastAPI app picks it up from env (it lives in a separate process under --reload).
    import os

    os.environ["EBBINGHAUS_DB_PATH"] = str(storage_path)

    console.print(
        f"[green]Serving[/green] at [bold]http://{host}:{port}[/bold] · "
        f"db=[dim]{storage_path}[/dim]"
    )
    uvicorn.run(
        "ebbinghaus_reviewer.web.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    cli()
