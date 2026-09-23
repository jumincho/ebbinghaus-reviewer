"""Display helpers shared by the command line and the web app."""

from __future__ import annotations

from datetime import datetime

from ebbinghaus_reviewer.durations import format_interval, format_relative
from ebbinghaus_reviewer.models import Item
from ebbinghaus_reviewer.scheduling import DEFAULT_LADDER, Grade, Strategy

__all__ = ["GRADE_HINTS", "due_label", "interval_label", "retention_label", "schedule_label"]

GRADE_HINTS: dict[Grade, str] = {
    Grade.AGAIN: "forgot it - start over",
    Grade.HARD: "recalled with serious difficulty",
    Grade.GOOD: "recalled after some thought",
    Grade.EASY: "recalled instantly",
}


def schedule_label(item: Item, *, rungs: int = len(DEFAULT_LADDER), compact: bool = False) -> str:
    """Where the item stands on its schedule.

    Full form: ``"ladder · step 2 of 4"`` or ``"SM-2 · rep 3 · EF 2.60"``; compact
    form (for narrow tables): ``"ladder 2/4"`` or ``"SM-2 rep 3"``.
    """
    schedule = item.schedule
    if schedule.strategy is Strategy.LADDER:
        if schedule.mastered:
            return "ladder done" if compact else "ladder · mastered"
        if compact:
            return f"ladder {schedule.step + 1}/{rungs}"
        return f"ladder · step {schedule.step + 1} of {rungs}"
    if compact:
        return f"SM-2 rep {schedule.step}"
    return f"SM-2 · rep {schedule.step} · EF {schedule.ease:.2f}"


def due_label(item: Item, now: datetime) -> str:
    """``"due now"``, ``"due 3 h ago"``, ``"due in 2 days"`` or ``"mastered"``."""
    if item.due_at is None:
        return "mastered"
    relative = format_relative(item.due_at, now)
    return "due now" if relative == "now" else f"due {relative}"


def retention_label(item: Item, now: datetime) -> str:
    """Estimated recall probability as a percentage, or an em dash once mastered."""
    retention = item.retention(now)
    return "—" if retention is None else f"{retention:.0%}"


def interval_label(item: Item) -> str:
    """The current scheduling interval, e.g. ``"1 week"``."""
    return format_interval(item.schedule.interval)
