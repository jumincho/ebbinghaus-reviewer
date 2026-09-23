"""Human-friendly durations: parse ``"10m"``/``"1w"`` and format intervals for display."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

__all__ = ["format_interval", "format_relative", "parse_duration"]

MONTH = timedelta(days=30)
"""A "month" in review schedules is a fixed 30 days."""

_UNITS: dict[str, timedelta] = {
    "s": timedelta(seconds=1),
    "m": timedelta(minutes=1),
    "min": timedelta(minutes=1),
    "h": timedelta(hours=1),
    "d": timedelta(days=1),
    "w": timedelta(weeks=1),
    "mo": MONTH,
}

_DURATION = re.compile(r"(\d+)\s*(mo|min|[smhdw])", re.IGNORECASE)


def parse_duration(text: str) -> timedelta:
    """Parse a compact duration such as ``"10m"``, ``"1d"``, ``"2w"`` or ``"1h30m"``.

    Units: ``s``, ``m``/``min``, ``h``, ``d``, ``w`` and ``mo`` (30 days).

    Raises:
        ValueError: If ``text`` is not a positive duration in that syntax.
    """
    compact = re.sub(r"\s+", "", text)
    if not compact or _DURATION.sub("", compact):
        raise ValueError(f"invalid duration {text!r}; use e.g. '10m', '1d', '2w', '1mo'")
    total = timedelta()
    for amount, unit in _DURATION.findall(compact):
        total += int(amount) * _UNITS[unit.lower()]
    if total <= timedelta():
        raise ValueError(f"duration must be positive, got {text!r}")
    return total


def _plural(amount: int, unit: str) -> str:
    return f"{amount} {unit}" if amount == 1 else f"{amount} {unit}s"


def format_interval(interval: timedelta) -> str:
    """Format a schedule interval: ``"10 min"``, ``"5 h"``, ``"1 week"``, ``"16 days"``.

    Whole weeks below a month and whole 30-day months are named as such so the
    classic ladder reads naturally (10 min, 1 day, 1 week, 1 month).
    """
    seconds = interval.total_seconds()
    if seconds < 3600:
        return f"{max(1, round(seconds / 60))} min"
    if seconds < 86400:
        return f"{round(seconds / 3600)} h"
    days = round(seconds / 86400)
    if days % 30 == 0:
        return _plural(days // 30, "month")
    if days < 30 and days % 7 == 0:
        return _plural(days // 7, "week")
    return _plural(days, "day")


def format_relative(moment: datetime, now: datetime) -> str:
    """Describe ``moment`` relative to ``now``: ``"now"``, ``"in 3 h"``, ``"2 days ago"``."""
    seconds = (moment - now).total_seconds()
    magnitude = abs(seconds)
    if magnitude < 60:
        return "now"
    if round(magnitude / 60) < 60:
        span = f"{round(magnitude / 60)} min"
    elif round(magnitude / 3600) < 24:
        span = f"{round(magnitude / 3600)} h"
    else:
        span = _plural(round(magnitude / 86400), "day")
    return f"in {span}" if seconds > 0 else f"{span} ago"
