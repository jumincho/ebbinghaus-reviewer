"""The plumbob: a Sims-style diamond that shows how an item is doing.

Like the plumbob above a Sim's head, it changes colour with the state of the
item underneath:

* **fresh** (green, happy): not due yet, or mastered;
* **due** (yellow, neutral): the review is due and the estimated recall is
  still at least :data:`FADING_BELOW`;
* **fading** (red, worried): overdue for so long that the estimated recall has
  dropped below :data:`FADING_BELOW`.

With the forgetting-curve model of :mod:`ebbinghaus_reviewer.retention`, recall
is 90% when an item becomes due and falls to 80% after about 2.1 intervals, so
an item turns red roughly one interval after it became due: about 11 minutes
late on the first rung of the ladder, a month late on the last.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import Enum

from ebbinghaus_reviewer.models import Item

__all__ = ["FADING_BELOW", "Mood", "collection_mood", "mood_of"]

FADING_BELOW = 0.8
"""Estimated recall below which a due item's plumbob turns red."""


class Mood(str, Enum):
    """The state a plumbob shows, from best to worst."""

    FRESH = "fresh"
    DUE = "due"
    FADING = "fading"

    @property
    def style(self) -> str:
        """The colour of the plumbob, as a Rich style."""
        return _STYLES[self]

    @property
    def description(self) -> str:
        """What the state means, in one sentence."""
        return _DESCRIPTIONS[self]


_STYLES = {Mood.FRESH: "green", Mood.DUE: "yellow", Mood.FADING: "bold red"}
_DESCRIPTIONS = {
    Mood.FRESH: "Fresh: nothing to review yet.",
    Mood.DUE: "Due: review it now, while recall is still high.",
    Mood.FADING: f"Fading: long overdue, estimated recall is below {FADING_BELOW:.0%}.",
}
_ORDER = list(Mood)


def mood_of(item: Item, now: datetime) -> Mood:
    """The plumbob state of ``item`` at ``now``."""
    if not item.is_due(now):
        return Mood.FRESH
    retention = item.retention(now)
    if retention is not None and retention < FADING_BELOW:
        return Mood.FADING
    return Mood.DUE


def collection_mood(items: Iterable[Item], now: datetime) -> Mood:
    """The worst state among ``items`` (fresh for an empty collection)."""
    return max((mood_of(item, now) for item in items), key=_ORDER.index, default=Mood.FRESH)
