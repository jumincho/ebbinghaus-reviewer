"""Server-rendered web app over the same collection as the command line.

Every page works without JavaScript: navigation is plain links and every
action is an HTML form that redirects back (POST/redirect/GET). The app is
meant to run on your own machine - it binds to localhost and has no accounts.
"""

# No ``from __future__ import annotations`` here: FastAPI inspects the route
# signatures at runtime and must resolve the ``Annotated`` dependency alias that
# is defined inside create_app().

import math
import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ebbinghaus_reviewer import __version__
from ebbinghaus_reviewer.config import default_db_path
from ebbinghaus_reviewer.durations import format_interval, format_relative
from ebbinghaus_reviewer.models import Item
from ebbinghaus_reviewer.plumbob import Mood, collection_mood, mood_of
from ebbinghaus_reviewer.presentation import (
    GRADE_HINTS,
    due_label,
    interval_label,
    retention_label,
    schedule_label,
)
from ebbinghaus_reviewer.retention import TARGET_RETENTION, curve, estimated_retention
from ebbinghaus_reviewer.scheduling import Grade, Strategy
from ebbinghaus_reviewer.service import Clock, ItemNotFoundError, Reviewer, system_clock
from ebbinghaus_reviewer.storage import Repository

__all__ = ["create_app"]

_HERE = Path(__file__).parent


@dataclass(frozen=True)
class Tick:
    """A horizontal grid line of the forgetting-curve chart."""

    y: float
    label: str


@dataclass(frozen=True)
class CurveChart:
    """Geometry of the forgetting-curve chart on an item page (SVG user units)."""

    width: int
    height: int
    left: int
    right: int
    top: int
    bottom: int
    points: str
    due_x: float
    now_x: float | None
    now_y: float | None
    y_ticks: tuple[Tick, ...]
    target: float
    description: str


def _curve_chart(item: Item, now: datetime) -> CurveChart | None:
    """Plot estimated recall from the last review until a bit past now (or the due time)."""
    last_seen = item.schedule.last_seen_at
    if last_seen is None:
        return None
    interval = item.schedule.interval
    elapsed = (now - last_seen) / interval
    horizon = max(2.5, min(elapsed * 1.15, 8.0))
    floor = min(
        0.6, math.floor((estimated_retention(interval * horizon, interval) - 0.05) * 10) / 10
    )
    floor = max(floor, 0.0)
    width, height, left, right, top, bottom = 360, 190, 40, 350, 12, 164

    def x_of(fraction: float) -> float:
        return round(left + (right - left) * min(fraction, horizon) / horizon, 1)

    def y_of(retention: float) -> float:
        return round(top + (bottom - top) * (1 - retention) / (1 - floor), 1)

    step = 0.1 if 1 - floor <= 0.5 else 0.2
    ticks = tuple(
        Tick(y_of(level), f"{level:.0%}")
        for level in (round(1 - i * step, 2) for i in range(round((1 - floor) / step) + 1))
    )
    retention = estimated_retention(now - last_seen, interval)
    visible = 0 <= elapsed <= horizon
    return CurveChart(
        width=width,
        height=height,
        left=left,
        right=right,
        top=top,
        bottom=bottom,
        points=" ".join(
            f"{x_of(x)},{y_of(r)}" for x, r in curve(interval, horizon=horizon, points=61)
        ),
        due_x=x_of(1.0),
        now_x=x_of(elapsed) if visible else None,
        now_y=y_of(retention) if visible else None,
        y_ticks=ticks,
        target=TARGET_RETENTION,
        description=(
            f"Estimated recall is {retention:.0%} now and is scheduled to be "
            f"{TARGET_RETENTION:.0%} when the review is due."
        ),
    )


def _safe_next(target: str | None, default: str) -> str:
    """Only allow redirects to local paths (no scheme, host or protocol-relative URLs)."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return default


def create_app(
    db_path: str | os.PathLike[str] | None = None,
    *,
    clock: Clock = system_clock,
    tz: tzinfo | None = None,
) -> FastAPI:
    """Build the web app.

    Args:
        db_path: The collection to serve (default: the same one as the CLI).
        clock: Source of the current time (injectable for tests).
        tz: Time zone that defines "today" (default: the system's).
    """
    path = Path(db_path) if db_path is not None else default_db_path()
    Repository(path).close()  # create or migrate now, so a bad file fails at startup

    templates = Jinja2Templates(directory=_HERE / "templates")
    templates.env.globals.update(
        version=__version__,
        grades=list(Grade),
        grade_hints=GRADE_HINTS,
        strategies=list(Strategy),
        due_label=due_label,
        schedule_label=schedule_label,
        retention_label=retention_label,
        interval_label=interval_label,
        mood_of=mood_of,
        format_interval=format_interval,
        format_relative=format_relative,
    )
    templates.env.filters["local"] = lambda moment, fmt="%Y-%m-%d %H:%M": moment.astimezone(
        tz
    ).strftime(fmt)

    app = FastAPI(title="Ebbinghaus Reviewer", version=__version__, docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")

    def get_reviewer() -> Iterator[Reviewer]:
        repository = Repository(path)
        try:
            yield Reviewer(repository, clock=clock, tz=tz)
        finally:
            repository.close()

    ReviewerDep = Annotated[Reviewer, Depends(get_reviewer)]

    def render(
        request: Request, template: str, context: dict[str, Any], *, status_code: int = 200
    ) -> HTMLResponse:
        return templates.TemplateResponse(request, template, context, status_code=status_code)

    def redirect(url: str) -> RedirectResponse:
        return RedirectResponse(url, status_code=303)

    def items_context(reviewer: Reviewer, subject: str | None, **extra: Any) -> dict[str, Any]:
        return {
            "now": reviewer.now(),
            "items": reviewer.items(subject=subject),
            "subject": subject,
            "subjects": reviewer.subjects(),
            **extra,
        }

    def item_context(reviewer: Reviewer, item_id: int, **extra: Any) -> dict[str, Any]:
        item = reviewer.get(item_id)
        now = reviewer.now()
        return {
            "now": now,
            "item": item,
            "history": list(reversed(reviewer.history(item_id))),
            "chart": _curve_chart(item, now),
            "subjects": reviewer.subjects(),
            **extra,
        }

    @app.exception_handler(ItemNotFoundError)
    async def item_not_found(request: Request, exc: ItemNotFoundError) -> HTMLResponse:
        return render(
            request,
            "error.html",
            {"title": "Not found", "message": f"There is no item #{exc.item_id}."},
            status_code=404,
        )

    @app.get("/healthz")
    def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": __version__})

    @app.get("/", response_class=HTMLResponse)
    def today(request: Request, reviewer: ReviewerDep) -> HTMLResponse:
        due = reviewer.due()
        now = reviewer.now()
        return render(
            request,
            "today.html",
            {
                "now": now,
                "stats": reviewer.stats(),
                "due": due,
                "mood": collection_mood(due, now),
                "fading": sum(mood_of(item, now) is Mood.FADING for item in due),
                "next_up": None if due else reviewer.next_scheduled(),
                "subjects": reviewer.subjects(),
            },
        )

    @app.get("/review", response_class=HTMLResponse)
    def review(
        request: Request, reviewer: ReviewerDep, subject: Annotated[str | None, Query()] = None
    ) -> HTMLResponse:
        due = reviewer.due(subject=subject or None)
        return render(
            request,
            "review.html",
            {
                "now": reviewer.now(),
                "item": due[0] if due else None,
                "remaining": len(due),
                "subject": subject or None,
                "next_up": None if due else reviewer.next_scheduled(subject=subject or None),
            },
        )

    @app.post("/items/{item_id}/grade")
    def grade(
        item_id: int,
        reviewer: ReviewerDep,
        grade: Annotated[Grade, Form()],
        next: Annotated[str | None, Form()] = None,
    ) -> RedirectResponse:
        reviewer.grade(item_id, grade)
        return redirect(_safe_next(next, "/review"))

    @app.get("/items", response_class=HTMLResponse)
    def items(
        request: Request,
        reviewer: ReviewerDep,
        subject: Annotated[str | None, Query()] = None,
    ) -> HTMLResponse:
        return render(request, "items.html", items_context(reviewer, subject or None))

    @app.post("/items", response_model=None)
    def add_item(
        request: Request,
        reviewer: ReviewerDep,
        title: Annotated[str, Form()],
        notes: Annotated[str, Form()] = "",
        subject: Annotated[str, Form()] = "",
        strategy: Annotated[Strategy, Form()] = Strategy.LADDER,
        next: Annotated[str | None, Form()] = None,
    ) -> HTMLResponse | RedirectResponse:
        try:
            reviewer.add(title, notes=notes, subject=subject or None, strategy=strategy)
        except ValueError as exc:
            draft = {"title": title, "notes": notes, "subject": subject, "strategy": strategy}
            context = items_context(reviewer, None, error=str(exc), draft=draft)
            return render(request, "items.html", context, status_code=400)
        return redirect(_safe_next(next, "/items"))

    @app.get("/items/{item_id}", response_class=HTMLResponse)
    def item_detail(request: Request, item_id: int, reviewer: ReviewerDep) -> HTMLResponse:
        return render(request, "item.html", item_context(reviewer, item_id))

    @app.post("/items/{item_id}", response_model=None)
    def edit_item(
        request: Request,
        item_id: int,
        reviewer: ReviewerDep,
        title: Annotated[str, Form()],
        notes: Annotated[str, Form()] = "",
        subject: Annotated[str, Form()] = "",
    ) -> HTMLResponse | RedirectResponse:
        try:
            reviewer.edit(item_id, title=title, notes=notes, subject=subject or None)
        except ValueError as exc:
            context = item_context(reviewer, item_id, error=str(exc))
            return render(request, "item.html", context, status_code=400)
        return redirect(f"/items/{item_id}")

    @app.post("/items/{item_id}/restart")
    def restart_item(
        item_id: int,
        reviewer: ReviewerDep,
        strategy: Annotated[str, Form()] = "",
    ) -> RedirectResponse:
        chosen = Strategy(strategy) if strategy in {member.value for member in Strategy} else None
        reviewer.restart(item_id, strategy=chosen)
        return redirect(f"/items/{item_id}")

    @app.post("/items/{item_id}/delete")
    def delete_item(item_id: int, reviewer: ReviewerDep) -> RedirectResponse:
        reviewer.delete(item_id)
        return redirect("/items")

    @app.get("/agenda", response_class=HTMLResponse)
    def agenda(
        request: Request,
        reviewer: ReviewerDep,
        days: Annotated[int, Query(ge=1, le=366)] = 14,
    ) -> HTMLResponse:
        today = reviewer.today()
        return render(
            request,
            "agenda.html",
            {
                "now": reviewer.now(),
                "today": today,
                "tomorrow": today + timedelta(days=1),
                "days": days,
                "agenda": reviewer.agenda(days=days),
            },
        )

    return app
