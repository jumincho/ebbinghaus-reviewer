"""Tests for the high-level Scheduler service."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ebbinghaus_reviewer.algorithm import ReviewQuality
from ebbinghaus_reviewer.scheduler import Scheduler

T0 = datetime(2026, 1, 1, 12, 0, 0)


def test_add_card_is_due_at_creation_time(scheduler: Scheduler) -> None:
    card = scheduler.add_card("What?", back="A.", tags=["psych"], now=T0)
    assert card.id is not None
    assert card.next_review_at == T0
    assert scheduler.due_cards(now=T0) == [card]


def test_review_advances_schedule_and_persists(scheduler: Scheduler) -> None:
    card = scheduler.add_card("Q", now=T0)
    assert card.id is not None

    updated = scheduler.review_card(card.id, ReviewQuality.PERFECT, now=T0)
    assert updated.repetition == 1
    assert updated.interval_days == 1
    assert updated.next_review_at == T0 + timedelta(days=1)

    # Persisted: re-read from storage and confirm.
    fetched = scheduler.storage.get_card(card.id)
    assert fetched is not None
    assert fetched.repetition == 1
    assert fetched.interval_days == 1


def test_review_records_history(scheduler: Scheduler) -> None:
    card = scheduler.add_card("Q", now=T0)
    assert card.id is not None
    scheduler.review_card(card.id, ReviewQuality.CORRECT_HARD, now=T0)
    scheduler.review_card(card.id, ReviewQuality.PERFECT, now=T0 + timedelta(days=1))
    reviews = scheduler.storage.list_reviews(card_id=card.id)
    assert len(reviews) == 2
    # Most recent first.
    assert reviews[0].quality == ReviewQuality.PERFECT
    assert reviews[1].quality == ReviewQuality.CORRECT_HARD


def test_due_cards_excludes_reviewed_cards(scheduler: Scheduler) -> None:
    a = scheduler.add_card("A", now=T0)
    b = scheduler.add_card("B", now=T0)
    assert a.id is not None and b.id is not None

    scheduler.review_card(a.id, ReviewQuality.PERFECT, now=T0)

    due = scheduler.due_cards(now=T0 + timedelta(minutes=1))
    assert {c.id for c in due} == {b.id}


def test_review_unknown_card_raises(scheduler: Scheduler) -> None:
    with pytest.raises(KeyError):
        scheduler.review_card(9999, ReviewQuality.PERFECT)


def test_full_learn_cycle(scheduler: Scheduler) -> None:
    """A card that's recalled perfectly three times in a row stretches its interval."""
    card = scheduler.add_card("Q", now=T0)
    assert card.id is not None

    now = T0
    intervals = []
    for _ in range(3):
        updated = scheduler.review_card(card.id, ReviewQuality.PERFECT, now=now)
        intervals.append(updated.interval_days)
        now = updated.next_review_at

    # 1 → 6 → ~15+
    assert intervals[0] == 1
    assert intervals[1] == 6
    assert intervals[2] >= 15
