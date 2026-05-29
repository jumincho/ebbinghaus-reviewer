"""Optional FastAPI + Jinja2 web UI for Ebbinghaus Reviewer.

The web layer shares the same SQLite database as the CLI. FastAPI is an
*optional* dependency: the core package and its tests never import this
subpackage, and even within it the heavy imports live inside
:func:`create_app`, so merely importing :mod:`ebbinghaus_reviewer.web` stays
cheap. Call :func:`create_app` to build the ASGI application.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from fastapi import FastAPI

__all__ = ["create_app"]


def create_app(*args: Any, **kwargs: Any) -> FastAPI:
    """Lazily build and return the FastAPI application.

    Importing FastAPI is deferred to call time so that this module can be
    imported even when FastAPI is not installed. See :func:`app.create_app`.
    """
    from .app import create_app as _create_app

    return _create_app(*args, **kwargs)
