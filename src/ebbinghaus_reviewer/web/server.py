"""FastAPI web UI for ebbinghaus-reviewer.

A small server that exposes the same operations as the CLI through a browser.
Server-rendered with Jinja2 and progressively enhanced with HTMX, so there is
no JS toolchain and no separate frontend build step.

The Storage instance is process-global and resolved from the env var
EBBINGHAUS_DB_PATH (set by `ebbinghaus serve`) or the default path.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ebbinghaus_reviewer.algorithm import ReviewQuality
from ebbinghaus_reviewer.scheduler import Scheduler
from ebbinghaus_reviewer.storage import Storage, default_db_path

_HERE = Path(__file__).parent
TEMPLATES_DIR = _HERE / "templates"


def create_app(storage: Storage | None = None) -> FastAPI:
    """Build a FastAPI app, optionally with an injected Storage (tests use this)."""
    storage = storage or Storage(default_db_path())
    scheduler = Scheduler(storage)

    app = FastAPI(title="ebbinghaus-reviewer", version="0.1.0")
    app.state.storage = storage
    app.state.scheduler = scheduler

    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    templates.env.filters["humanize_due"] = _humanize_due
    templates.env.filters["fmt_dt"] = _fmt_dt

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        now = datetime.utcnow()
        due = scheduler.due_cards(now=now)
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "due": due,
                "total": storage.card_count(),
                "reviews": storage.review_count(),
                "now": now,
            },
        )

    @app.get("/cards", response_class=HTMLResponse)
    def cards_list(request: Request, tag: str | None = None) -> HTMLResponse:
        cards = storage.list_cards(tag=tag)
        return templates.TemplateResponse(
            request,
            "list.html",
            {"cards": cards, "tag": tag, "now": datetime.utcnow()},
        )

    @app.get("/cards/new", response_class=HTMLResponse)
    def cards_new(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "new.html", {})

    @app.post("/cards", response_class=HTMLResponse)
    def cards_create(
        request: Request,
        front: str = Form(""),
        back: str = Form(""),
        tags: str = Form(""),
    ) -> HTMLResponse:
        front = front.strip()
        if not front:
            raise HTTPException(status_code=400, detail="front is required")
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        scheduler.add_card(front=front, back=back.strip(), tags=tag_list)
        return _redirect("/")

    @app.get("/cards/{card_id}/review", response_class=HTMLResponse)
    def card_review_show(request: Request, card_id: int) -> HTMLResponse:
        card = storage.get_card(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="card not found")
        return templates.TemplateResponse(request, "review.html", {"card": card})

    @app.post("/cards/{card_id}/review", response_class=HTMLResponse)
    def card_review_submit(
        request: Request,
        card_id: int,
        quality: int = Form(...),
    ) -> HTMLResponse:
        if quality not in range(6):
            raise HTTPException(status_code=400, detail="quality must be 0-5")
        try:
            updated = scheduler.review_card(card_id, ReviewQuality(quality))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return templates.TemplateResponse(
            request, "review_done.html", {"card": updated}
        )

    @app.post("/cards/{card_id}/delete", response_class=HTMLResponse)
    def card_delete(request: Request, card_id: int) -> HTMLResponse:
        if not storage.delete_card(card_id):
            raise HTTPException(status_code=404, detail="card not found")
        return _redirect("/cards")

    @app.get("/stats", response_class=HTMLResponse)
    def stats(request: Request) -> HTMLResponse:
        now = datetime.utcnow()
        return templates.TemplateResponse(
            request,
            "stats.html",
            {
                "total": storage.card_count(),
                "reviews": storage.review_count(),
                "due": storage.due_count(now),
                "db_path": str(storage.db_path),
            },
        )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


def _redirect(path: str) -> HTMLResponse:
    """Redirect that also works for HTMX (it follows HX-Redirect header)."""
    response = HTMLResponse(content="", status_code=303)
    response.headers["Location"] = path
    response.headers["HX-Redirect"] = path
    return response


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def _humanize_due(target: datetime, now: datetime | None = None) -> str:
    now = now or datetime.utcnow()
    seconds = int((target - now).total_seconds())
    if seconds <= 0:
        return "due now"
    days, rem = divmod(seconds, 86400)
    hours, _ = divmod(rem, 3600)
    if days >= 1:
        return f"in {days}d {hours}h"
    if hours >= 1:
        return f"in {hours}h"
    minutes, _ = divmod(rem, 60)
    return f"in {minutes}m"


# Default app for `uvicorn ebbinghaus_reviewer.web.server:app`
app = create_app()
