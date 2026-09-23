"""Use cases shared by the command line and the web app.

:class:`Reviewer` is the only entry point the delivery layers need. It owns
the clock and the local time zone, so every rule that depends on "now" or on
"today" can be tested deterministically by injecting both.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from typing import Any, Final

from ebbinghaus_reviewer import transfer
from ebbinghaus_reviewer.models import AgendaDay, Item, Review, Stats
from ebbinghaus_reviewer.scheduling import (
    Grade,
    LadderScheduler,
    Scheduler,
    SM2Scheduler,
    Strategy,
)
from ebbinghaus_reviewer.storage import Repository

__all__ = ["Clock", "ItemNotFoundError", "Reviewer", "system_clock"]

Clock = Callable[[], datetime]
"""A zero-argument callable returning the current, timezone-aware time."""

MAX_TITLE_LENGTH: Final = 200


def system_clock() -> datetime:
    """The real clock, in UTC."""
    return datetime.now(timezone.utc)


class ItemNotFoundError(LookupError):
    """No item has the requested id."""

    def __init__(self, item_id: int) -> None:
        super().__init__(f"no item with id {item_id}")
        self.item_id = item_id


class _Unset:
    """Marker for "argument not given" where ``None`` is a meaningful value."""


_UNSET: Final = _Unset()


def _clean_title(title: str) -> str:
    cleaned = " ".join(title.split())
    if not cleaned:
        raise ValueError("title must not be empty")
    if len(cleaned) > MAX_TITLE_LENGTH:
        raise ValueError(f"title must be at most {MAX_TITLE_LENGTH} characters")
    return cleaned


def _clean_subject(subject: str | None) -> str | None:
    if subject is None:
        return None
    return " ".join(subject.split()) or None


def _streak(days: set[date], today: date) -> int:
    """Consecutive days in ``days`` ending today, or yesterday if today is missing."""
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


class Reviewer:
    """Application service over a :class:`~ebbinghaus_reviewer.storage.Repository`.

    Args:
        repository: Where items and reviews are stored.
        clock: Source of the current time (injectable for tests and demos).
        tz: Time zone that defines "today"; ``None`` uses the system's local zone.
        schedulers: Overrides for the default ladder / SM-2 schedulers.
    """

    def __init__(
        self,
        repository: Repository,
        *,
        clock: Clock = system_clock,
        tz: tzinfo | None = None,
        schedulers: Mapping[Strategy, Scheduler] | None = None,
    ) -> None:
        self.repository = repository
        self._clock = clock
        self._tz = tz
        self._schedulers: dict[Strategy, Scheduler] = {
            Strategy.LADDER: LadderScheduler(),
            Strategy.SM2: SM2Scheduler(),
        }
        self._schedulers.update(schedulers or {})

    # -- time ----------------------------------------------------------------

    def now(self) -> datetime:
        """The current time in UTC, truncated to whole seconds (storage precision)."""
        moment = self._clock()
        if moment.tzinfo is None:
            raise ValueError("the clock must return timezone-aware datetimes")
        return moment.astimezone(timezone.utc).replace(microsecond=0)

    def local(self, moment: datetime) -> datetime:
        """Convert ``moment`` to the reviewer's local time zone."""
        return moment.astimezone(self._tz)

    def today(self) -> date:
        """The current local date."""
        return self.local(self.now()).date()

    def localize(self, naive: datetime) -> datetime:
        """Attach the local time zone to a naive local ``datetime``."""
        if naive.tzinfo is not None:
            raise ValueError("expected a naive datetime")
        return naive.astimezone() if self._tz is None else naive.replace(tzinfo=self._tz)

    def start_of(self, day: date) -> datetime:
        """Local midnight at the start of ``day``."""
        return self.localize(datetime.combine(day, time.min))

    # -- queries -------------------------------------------------------------

    def get(self, item_id: int) -> Item:
        """Return an item.

        Raises:
            ItemNotFoundError: If there is no such item.
        """
        item = self.repository.get_item(item_id)
        if item is None:
            raise ItemNotFoundError(item_id)
        return item

    def items(self, *, subject: str | None = None, include_mastered: bool = True) -> list[Item]:
        """All items ordered by due time, mastered items last."""
        return self.repository.list_items(subject=subject, include_mastered=include_mastered)

    def due(self, *, subject: str | None = None, limit: int | None = None) -> list[Item]:
        """Items due now, most overdue first."""
        items = self.repository.items_due_before(self.now(), subject=subject)
        return items if limit is None else items[: max(limit, 0)]

    def next_scheduled(self, *, subject: str | None = None) -> Item | None:
        """The item with the earliest scheduled review, due or not."""
        items = self.repository.list_items(subject=subject, include_mastered=False)
        return items[0] if items else None

    def history(self, item_id: int) -> list[Review]:
        """An item's reviews, oldest first."""
        self.get(item_id)
        return self.repository.reviews_for(item_id)

    def subjects(self) -> list[str]:
        """Subjects in use, alphabetically."""
        return self.repository.subjects()

    def agenda(self, *, days: int = 14, subject: str | None = None) -> list[AgendaDay]:
        """Scheduled reviews for the next ``days`` local days, grouped by day.

        Overdue items are listed under today, since that is when they should be
        reviewed.
        """
        if days < 1:
            raise ValueError("days must be at least 1")
        today = self.today()
        end = self.start_of(today + timedelta(days=days))
        groups: dict[date, list[Item]] = {}
        for item in self.repository.items_due_before(end, subject=subject, inclusive=False):
            if item.due_at is not None:
                day = max(today, self.local(item.due_at).date())
                groups.setdefault(day, []).append(item)
        return [AgendaDay(day, tuple(items)) for day, items in sorted(groups.items())]

    def stats(self) -> Stats:
        """A snapshot of the collection and recent review activity."""
        now = self.now()
        today = self.today()
        tomorrow = self.start_of(today + timedelta(days=1))
        items = self.repository.list_items()
        recent = self.repository.reviews_since(self.start_of(today - timedelta(days=29)))
        since_today = self.start_of(today)
        since_week = self.start_of(today - timedelta(days=6))
        review_days = {self.local(moment).date() for moment in self.repository.review_times()}
        return Stats(
            total=len(items),
            active=sum(1 for item in items if not item.mastered),
            mastered=sum(1 for item in items if item.mastered),
            due_now=sum(1 for item in items if item.is_due(now)),
            due_later_today=sum(
                1 for item in items if item.due_at is not None and now < item.due_at < tomorrow
            ),
            reviews_today=sum(1 for review in recent if review.reviewed_at >= since_today),
            reviews_last_7_days=sum(1 for review in recent if review.reviewed_at >= since_week),
            recall_rate_30_days=(
                sum(1 for review in recent if review.grade.passed) / len(recent) if recent else None
            ),
            streak_days=_streak(review_days, today),
        )

    # -- commands ------------------------------------------------------------

    def add(
        self,
        title: str,
        *,
        notes: str = "",
        subject: str | None = None,
        strategy: Strategy = Strategy.LADDER,
        studied_at: datetime | None = None,
    ) -> Item:
        """Record something you just studied (or studied at ``studied_at``).

        Raises:
            ValueError: On an empty/too long title or a future ``studied_at``.
        """
        now = self.now()
        if studied_at is None:
            studied = now
        elif studied_at.tzinfo is None:
            raise ValueError("studied_at must be timezone-aware")
        else:
            studied = studied_at.astimezone(timezone.utc).replace(microsecond=0)
        if studied > now:
            raise ValueError("studied_at cannot be in the future")
        return self.repository.insert_item(
            title=_clean_title(title),
            notes=notes.strip(),
            subject=_clean_subject(subject),
            schedule=self._schedulers[strategy].initial(studied),
            studied_at=studied,
            created_at=now,
        )

    def grade(self, item_id: int, grade: Grade) -> Item:
        """Record a review of an item and schedule the next one.

        Raises:
            ItemNotFoundError: If there is no such item.
        """
        with self.repository.transaction():
            item = self.get(item_id)
            now = self.now()
            schedule = self._schedulers[item.schedule.strategy].next(item.schedule, grade, now)
            self.repository.insert_review(
                item_id=item.id,
                reviewed_at=now,
                grade=grade,
                scheduled_for=item.due_at,
                interval=schedule.interval,
            )
            return self.repository.update_item(
                replace(item, schedule=schedule, last_reviewed_at=now), updated_at=now
            )

    def restart(self, item_id: int, *, strategy: Strategy | None = None) -> Item:
        """Start an item's schedule over from now, optionally switching strategy.

        The review history is kept.
        """
        with self.repository.transaction():
            item = self.get(item_id)
            now = self.now()
            chosen = strategy or item.schedule.strategy
            return self.repository.update_item(
                replace(item, schedule=self._schedulers[chosen].initial(now)), updated_at=now
            )

    def edit(
        self,
        item_id: int,
        *,
        title: str | None = None,
        notes: str | None = None,
        subject: str | _Unset | None = _UNSET,
    ) -> Item:
        """Change an item's text. Pass ``subject=None`` to clear the subject."""
        with self.repository.transaction():
            item = self.get(item_id)
            changed = replace(
                item,
                title=item.title if title is None else _clean_title(title),
                notes=item.notes if notes is None else notes.strip(),
                subject=item.subject if isinstance(subject, _Unset) else _clean_subject(subject),
            )
            return self.repository.update_item(changed, updated_at=self.now())

    def delete(self, item_id: int) -> Item:
        """Delete an item and its history; return what was deleted."""
        with self.repository.transaction():
            item = self.get(item_id)
            self.repository.delete_item(item_id)
            return item

    # -- import / export -----------------------------------------------------

    def export_data(self) -> dict[str, Any]:
        """The whole collection as a JSON-compatible document."""
        entries = [(item, self.repository.reviews_for(item.id)) for item in self.items()]
        return transfer.dump(entries, exported_at=self.now())

    def import_data(self, document: Any) -> int:
        """Add every item of an export document; return how many were added.

        Nothing is imported if any part of the document is invalid.

        Raises:
            ValueError: If the document is not a valid export.
        """
        imported = transfer.load(document)
        now = self.now()
        with self.repository.transaction():
            for entry in imported:
                item = self.repository.insert_item(
                    title=_clean_title(entry.title),
                    notes=entry.notes,
                    subject=_clean_subject(entry.subject),
                    schedule=entry.schedule,
                    studied_at=entry.studied_at,
                    last_reviewed_at=entry.last_reviewed_at,
                    created_at=entry.created_at,
                    updated_at=now,
                )
                for review in entry.reviews:
                    self.repository.insert_review(
                        item_id=item.id,
                        reviewed_at=review.reviewed_at,
                        grade=review.grade,
                        scheduled_for=review.scheduled_for,
                        interval=review.interval,
                    )
        return len(imported)
