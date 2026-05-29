"""Tests for the scheduler use-case layer."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from ebbinghaus_reviewer.scheduler import Scheduler


@pytest.fixture
def sched() -> Scheduler:
    return Scheduler()


def test_add_item_is_due_immediately(sched: Scheduler) -> None:
    item = sched.add_item("front", "back")
    assert item.id is not None
    assert item.due_date == date.today()
    due = sched.due_today()
    assert [i.id for i in due] == [item.id]


def test_add_item_strips_and_rejects_empty(sched: Scheduler) -> None:
    item = sched.add_item("  spaced  ", "  back  ")
    assert item.front == "spaced"
    assert item.back == "back"
    with pytest.raises(ValueError):
        sched.add_item("   ")


def test_review_advances_schedule_out_of_due(sched: Scheduler) -> None:
    item = sched.add_item("q")
    assert len(sched.due_today()) == 1

    updated = sched.record_review(item.id, 5)  # type: ignore[arg-type]
    assert updated.repetitions == 1
    assert updated.interval == 1
    assert updated.due_date == date.today() + timedelta(days=1)
    assert updated.last_reviewed is not None
    # No longer due today.
    assert sched.due_today() == []


def test_review_workflow_progression(sched: Scheduler) -> None:
    """A multi-review workflow follows the 1 -> 6 -> round(6*EF) curve."""
    when = datetime(2026, 1, 1, 8, 0, 0)
    item = sched.add_item("compound interest", when=when)

    r1 = sched.record_review(item.id, 5, when=when)  # type: ignore[arg-type]
    assert r1.interval == 1
    assert r1.due_date == date(2026, 1, 2)

    r2 = sched.record_review(item.id, 5, when=datetime(2026, 1, 2, 8, 0))  # type: ignore[arg-type]
    assert r2.interval == 6
    assert r2.due_date == date(2026, 1, 8)

    r3 = sched.record_review(item.id, 5, when=datetime(2026, 1, 8, 8, 0))  # type: ignore[arg-type]
    # Canonical SM-2: previous interval (6) times the ease *before* this update
    # (2.7, which is r2's ease factor) -> round(6 * 2.7) = 16.
    assert r3.interval == round(6 * r2.ease_factor) == 16
    assert r3.due_date == date(2026, 1, 8) + timedelta(days=r3.interval)


def test_review_failure_resets_and_makes_due_soon(sched: Scheduler) -> None:
    when = datetime(2026, 1, 1, 8, 0, 0)
    item = sched.add_item("hard fact", when=when)
    sched.record_review(item.id, 5, when=when)  # type: ignore[arg-type]
    sched.record_review(item.id, 5, when=datetime(2026, 1, 2, 8, 0))  # type: ignore[arg-type]

    failed = sched.record_review(item.id, 1, when=datetime(2026, 1, 8, 8, 0))  # type: ignore[arg-type]
    assert failed.repetitions == 0
    assert failed.interval == 1
    assert failed.due_date == date(2026, 1, 9)


def test_record_review_rejects_invalid_quality(sched: Scheduler) -> None:
    item = sched.add_item("q")
    for bad in (-1, 6, 100):
        with pytest.raises(ValueError):
            sched.record_review(item.id, bad)  # type: ignore[arg-type]


def test_record_review_unknown_id_raises(sched: Scheduler) -> None:
    with pytest.raises(KeyError):
        sched.record_review(4242, 5)


def test_delete_item(sched: Scheduler) -> None:
    item = sched.add_item("q")
    assert sched.delete_item(item.id) is True  # type: ignore[arg-type]
    assert sched.list_items() == []
    assert sched.delete_item(item.id) is False  # type: ignore[arg-type]


def test_due_today_respects_reference_date(sched: Scheduler) -> None:
    when = datetime(2026, 1, 1, 8, 0)
    item = sched.add_item("q", when=when)
    sched.record_review(item.id, 5, when=when)  # type: ignore[arg-type]  # due 2026-01-02
    assert sched.due_today(on=date(2026, 1, 1)) == []
    assert len(sched.due_today(on=date(2026, 1, 2))) == 1


def test_stats(sched: Scheduler) -> None:
    when = datetime(2026, 1, 1, 8, 0)
    a = sched.add_item("a", when=when)
    sched.add_item("b", when=when)
    # Mature 'a' by pushing it past 21 days of interval.
    cursor = when
    for _ in range(6):
        r = sched.record_review(a.id, 5, when=cursor)  # type: ignore[arg-type]
        cursor = datetime.combine(r.due_date, datetime.min.time())

    s = sched.stats(on=date(2026, 1, 1))
    assert s.total == 2
    assert s.learning == 1  # 'b' still has 0 reps
    assert s.mature == 1  # 'a' interval >= 21
    assert s.average_ease > 0


def test_stats_empty_collection(sched: Scheduler) -> None:
    s = sched.stats()
    assert s.total == 0
    assert s.average_ease == 0.0
