"""Ebbinghaus Reviewer: review what you study along the forgetting curve.

Log what you studied; the reviewer schedules each item for review at
expanding intervals (a fixed Ebbinghaus ladder or the adaptive SM-2
algorithm) and tells you what is due.

Package layout (dependencies point inward)::

    cli / web      delivery: click + rich, FastAPI + Jinja2
        |
    service        use cases: add, review, agenda, stats, import/export
        |
    storage        SQLite repository with schema migrations
        |
    models, scheduling, retention, durations   pure domain logic
"""

from ebbinghaus_reviewer.models import AgendaDay, Item, Review, Stats
from ebbinghaus_reviewer.scheduling import (
    DEFAULT_LADDER,
    Grade,
    LadderScheduler,
    Schedule,
    SM2Scheduler,
    Strategy,
)
from ebbinghaus_reviewer.service import ItemNotFoundError, Reviewer
from ebbinghaus_reviewer.storage import Repository

__version__ = "1.0.0"

__all__ = [
    "DEFAULT_LADDER",
    "AgendaDay",
    "Grade",
    "Item",
    "ItemNotFoundError",
    "LadderScheduler",
    "Repository",
    "Review",
    "Reviewer",
    "SM2Scheduler",
    "Schedule",
    "Stats",
    "Strategy",
    "__version__",
]
