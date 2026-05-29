"""FastAPI application factory for the web UI.

Server-rendered HTML via Jinja2, sharing the same SQLite file as the CLI.
A sprinkle of HTMX (loaded from a CDN in the base template) makes the review
buttons update in place without a full-page reload, but every route also works
as a plain form POST, so the UI degrades gracefully without JavaScript.

Routes:

* ``GET  /``           -- dashboard: due items + stats
* ``GET  /cards``      -- all cards
* ``POST /cards``      -- add a card (form)
* ``GET  /review``     -- the next due card to grade
* ``POST /review/{id}`` -- record a grade for a card
* ``POST /cards/{id}/delete`` -- delete a card
* ``GET  /healthz``    -- liveness probe (JSON)
"""

from __future__ import annotations

import contextlib
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import __version__, default_db_path
from ..algorithm import MAX_QUALITY, MIN_QUALITY
from ..scheduler import Scheduler
from ..storage import Storage

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_app(db_path: str | Path | None = None) -> FastAPI:
    """Build the FastAPI app.

    Args:
        db_path: Database path to use. Defaults to
            :func:`ebbinghaus_reviewer.default_db_path`, i.e. the same store
            the CLI uses.

    Returns:
        A configured :class:`fastapi.FastAPI` instance.
    """
    resolved = Path(db_path) if db_path is not None else default_db_path()
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    app = FastAPI(title="Ebbinghaus Reviewer", version=__version__)

    def scheduler() -> Scheduler:
        return Scheduler(Storage(resolved))

    @app.get("/healthz")
    def healthz() -> JSONResponse:
        """Liveness probe."""
        return JSONResponse({"status": "ok", "version": __version__})

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        sched = scheduler()
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "due": sched.due_today(),
                "stats": sched.stats(),
            },
        )

    @app.get("/cards", response_class=HTMLResponse)
    def cards(request: Request) -> HTMLResponse:
        sched = scheduler()
        return templates.TemplateResponse(request, "cards.html", {"items": sched.list_items()})

    @app.post("/cards")
    def add_card(front: str = Form(...), back: str = Form("")) -> RedirectResponse:
        sched = scheduler()
        if front.strip():
            sched.add_item(front, back)
        return RedirectResponse(url="/cards", status_code=303)

    @app.get("/review", response_class=HTMLResponse)
    def review_page(request: Request) -> HTMLResponse:
        sched = scheduler()
        due = sched.due_today()
        return templates.TemplateResponse(
            request,
            "review.html",
            {
                "item": due[0] if due else None,
                "remaining": len(due),
                "min_quality": MIN_QUALITY,
                "max_quality": MAX_QUALITY,
            },
        )

    @app.post("/review/{item_id}")
    def submit_review(item_id: int, quality: int = Form(...)) -> RedirectResponse:
        sched = scheduler()
        q = max(MIN_QUALITY, min(MAX_QUALITY, quality))
        with contextlib.suppress(KeyError):
            sched.record_review(item_id, q)
        return RedirectResponse(url="/review", status_code=303)

    @app.post("/cards/{item_id}/delete")
    def delete_card(item_id: int) -> RedirectResponse:
        sched = scheduler()
        sched.delete_item(item_id)
        return RedirectResponse(url="/cards", status_code=303)

    return app
