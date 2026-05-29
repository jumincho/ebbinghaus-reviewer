"""Scheduler: glue between the SM-2 algorithm and the storage layer.

The :class:`Scheduler` is the application's use-case layer. It exposes the
operations the CLI and web UI need -- add a card, list cards, list what is due
today, record a graded review, compute stats -- and keeps the pure algorithm
and the persistence layer cleanly separated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .algorithm import MAX_QUALITY, MIN_QUALITY, PASSING_QUALITY, review
from .storage import MEMORY, Storage, StudyItem


@dataclass(frozen=True)
class Stats:
    """A snapshot summary of the collection.

    Attributes:
        total: Total number of items.
        due_today: Items due on or before today.
        learning: Items still in the early phase (fewer than two reps).
        mature: Items with an interval of at least 21 days.
        average_ease: Mean ease factor across all items (0.0 if empty).
    """

    total: int
    due_today: int
    learning: int
    mature: int
    average_ease: float


#: Interval (days) at or above which an item is considered "mature".
MATURE_INTERVAL_DAYS = 21


class Scheduler:
    """Use-case layer tying SM-2 scheduling to a :class:`Storage` backend.

    Args:
        storage: The repository to read from and write to. Defaults to a
            private in-memory store, which is convenient for tests.
    """

    def __init__(self, storage: Storage | None = None) -> None:
        self.storage = storage if storage is not None else Storage(MEMORY)

    def add_item(self, front: str, back: str = "", *, when: datetime | None = None) -> StudyItem:
        """Create and persist a new study item, due immediately.

        Args:
            front: The prompt / subject (must be non-empty after stripping).
            back: The answer / note (optional).
            when: Creation timestamp; defaults to :func:`datetime.now`.

        Returns:
            The stored item, including its assigned ``id``.

        Raises:
            ValueError: If ``front`` is empty or whitespace only.
        """
        front = front.strip()
        if not front:
            raise ValueError("front text must not be empty")
        created = when or datetime.now()
        item = StudyItem(
            front=front,
            back=back.strip(),
            created_at=created,
            due_date=created.date(),
        )
        return self.storage.add(item)

    def list_items(self) -> list[StudyItem]:
        """Return all items ordered by due date."""
        return self.storage.list_all()

    def due_today(self, on: date | None = None) -> list[StudyItem]:
        """Return items due for review on or before ``on`` (default: today)."""
        return self.storage.list_due(on)

    def record_review(
        self, item_id: int, quality: int, *, when: datetime | None = None
    ) -> StudyItem:
        """Grade a recall and advance the item's schedule.

        Applies one pure SM-2 step to the item, sets its new ``due_date`` to
        ``review date + interval`` days, stamps ``last_reviewed``, and persists
        the result.

        Args:
            item_id: Id of the item being reviewed.
            quality: Recall grade ``0..5`` (validated, not silently clamped).
            when: Review timestamp; defaults to :func:`datetime.now`.

        Returns:
            The updated item.

        Raises:
            KeyError: If no item has ``item_id``.
            ValueError: If ``quality`` is outside ``0..5``.
        """
        if not MIN_QUALITY <= quality <= MAX_QUALITY:
            raise ValueError(f"quality must be between {MIN_QUALITY} and {MAX_QUALITY}")
        item = self.storage.get(item_id)
        if item is None:
            raise KeyError(f"no study item with id {item_id}")

        reviewed_at = when or datetime.now()
        new_state = review(item.state, quality)

        item.repetitions = new_state.repetitions
        item.ease_factor = new_state.ease_factor
        item.interval = new_state.interval
        item.due_date = reviewed_at.date() + timedelta(days=new_state.interval)
        item.last_reviewed = reviewed_at

        self.storage.update(item)
        return item

    def delete_item(self, item_id: int) -> bool:
        """Delete the item with ``item_id``; return ``True`` if it existed."""
        return self.storage.delete(item_id)

    def stats(self, on: date | None = None) -> Stats:
        """Compute a :class:`Stats` snapshot of the collection."""
        items = self.storage.list_all()
        total = len(items)
        due = len(self.storage.list_due(on))
        learning = sum(1 for i in items if i.repetitions < 2)
        mature = sum(1 for i in items if i.interval >= MATURE_INTERVAL_DAYS)
        avg_ease = sum(i.ease_factor for i in items) / total if total else 0.0
        return Stats(
            total=total,
            due_today=due,
            learning=learning,
            mature=mature,
            average_ease=avg_ease,
        )


__all__ = ["Scheduler", "Stats", "PASSING_QUALITY", "MATURE_INTERVAL_DAYS"]
