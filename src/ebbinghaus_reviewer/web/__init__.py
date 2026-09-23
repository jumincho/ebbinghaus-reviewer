"""Optional local web app (install the ``web`` extra).

The ASGI application is built by :func:`create_app`; importing this package
does not require FastAPI, so the core library stays dependency-light.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import FastAPI

__all__ = ["create_app"]


def create_app(*args: Any, **kwargs: Any) -> FastAPI:
    """Build the FastAPI application; see :func:`ebbinghaus_reviewer.web.app.create_app`."""
    from ebbinghaus_reviewer.web.app import create_app as _create_app

    return _create_app(*args, **kwargs)
