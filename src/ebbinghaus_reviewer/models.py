"""Immutable domain records returned by the service layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from ebbinghaus_reviewer.retention import estimated_retention
from ebbinghaus_reviewer.scheduling import Grade, Schedule

__all__ = ["AgendaDay", "Item", "Review", "Stats"]


@dataclass(frozen=True)
class Item:
    """Something you studied, together with its review schedule.

    Attributes:
        id: Database identifier.
        title: What you studied (the prompt shown during review).
        notes: Optional notes or the answer, revealed during review.
        subject: Optional grouping such as a course name.
        schedule: The current review schedule.
        studied_at: When the item was first studied.
        last_reviewed_at: When it was last reviewed, if ever.
        created_at: When the record was created.
        updated_at: When the record last changed.
        review_count: Number of reviews so far.
        lapse_count: Number of reviews graded ``again``.
    """

    id: int
    title: str
    notes: str
    subject: str | None
    schedule: Schedule
    studied_at: datetime
    last_reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    review_count: int = 0
    lapse_count: int = 0

    @property
    def due_at(self) -> datetime | None:
        """When the next review is due (``None`` once mastered)."""
        return self.schedule.due_at

    @property
    def mastered(self) -> bool:
        """``True`` once the item needs no further reviews."""
        return self.schedule.mastered

    def is_due(self, now: datetime) -> bool:
        """Whether a review is due at ``now``."""
        return self.schedule.due_at is not None and self.schedule.due_at <= now

    def retention(self, now: datetime) -> float | None:
        """Estimated recall probability at ``now`` (``None`` once mastered)."""
        last_seen = self.schedule.last_seen_at
        if last_seen is None:
            return None
        return estimated_retention(now - last_seen, self.schedule.interval)


@dataclass(frozen=True)
class Review:
    """One graded review of an item.

    Attributes:
        id: Database identifier.
        item_id: The reviewed item.
        reviewed_at: When the review happened.
        grade: How well the item was recalled.
        scheduled_for: The due time this review answered (``None`` if the
            item was already mastered).
        interval: The interval chosen for the next review.
    """

    id: int
    item_id: int
    reviewed_at: datetime
    grade: Grade
    scheduled_for: datetime | None
    interval: timedelta


@dataclass(frozen=True)
class Stats:
    """A snapshot of the whole collection.

    Attributes:
        total: Number of items.
        active: Items still being reviewed.
        mastered: Items that climbed past the end of their ladder.
        due_now: Items due at the moment.
        due_later_today: Items that become due before local midnight.
        reviews_today: Reviews done today (local time).
        reviews_last_7_days: Reviews done in the last seven days, today included.
        recall_rate_30_days: Share of reviews in the last 30 days not graded
            ``again`` (``None`` without reviews).
        streak_days: Consecutive local days with at least one review, ending
            today or, if nothing was reviewed yet today, yesterday.
    """

    total: int
    active: int
    mastered: int
    due_now: int
    due_later_today: int
    reviews_today: int
    reviews_last_7_days: int
    recall_rate_30_days: float | None
    streak_days: int


@dataclass(frozen=True)
class AgendaDay:
    """The items whose next review falls on a given local date."""

    day: date
    items: tuple[Item, ...]
