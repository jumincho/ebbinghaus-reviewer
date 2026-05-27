"""High-level scheduling service that combines algorithm + storage."""

from __future__ import annotations

from datetime import datetime

from ebbinghaus_reviewer.algorithm import ReviewQuality, ScheduleState, schedule_next
from ebbinghaus_reviewer.models import Card, Review
from ebbinghaus_reviewer.storage import Storage


class Scheduler:
    """Coordinates SM-2 with persistence.

    All time-dependent operations accept an explicit `now` so callers (CLI,
    web, tests) can control the clock. Default uses utcnow.
    """

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    @staticmethod
    def _now(now: datetime | None) -> datetime:
        return now if now is not None else datetime.utcnow()

    def add_card(
        self,
        front: str,
        back: str = "",
        tags: list[str] | None = None,
        *,
        now: datetime | None = None,
    ) -> Card:
        """Create a card; its first review is scheduled for `now`."""
        ts = self._now(now)
        card = Card(
            id=None,
            front=front,
            back=back,
            tags=tags or [],
            created_at=ts,
            next_review_at=ts,
        )
        return self.storage.add_card(card)

    def due_cards(self, *, now: datetime | None = None) -> list[Card]:
        return self.storage.due_cards(self._now(now))

    def review_card(
        self,
        card_id: int,
        quality: ReviewQuality,
        *,
        now: datetime | None = None,
    ) -> Card:
        """Apply a review outcome to a card and advance its schedule."""
        ts = self._now(now)
        card = self.storage.get_card(card_id)
        if card is None:
            raise KeyError(f"card {card_id} not found")

        before = ScheduleState(
            repetition=card.repetition,
            ease_factor=card.ease_factor,
            interval_days=card.interval_days,
            next_review_at=card.next_review_at,
        )
        after = schedule_next(before, quality, ts)

        self.storage.update_card_schedule(
            card_id,
            repetition=after.repetition,
            ease_factor=after.ease_factor,
            interval_days=after.interval_days,
            next_review_at=after.next_review_at,
        )
        self.storage.add_review(
            Review(
                id=None,
                card_id=card_id,
                reviewed_at=ts,
                quality=int(quality),
                interval_days_before=before.interval_days,
                interval_days_after=after.interval_days,
                ease_factor_after=after.ease_factor,
            )
        )

        card.repetition = after.repetition
        card.ease_factor = after.ease_factor
        card.interval_days = after.interval_days
        card.next_review_at = after.next_review_at
        return card
