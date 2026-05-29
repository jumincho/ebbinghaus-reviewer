"""Tests for the SQLite storage layer."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from ebbinghaus_reviewer.storage import MEMORY, Storage, StudyItem


@pytest.fixture
def store() -> Storage:
    return Storage(MEMORY)


def test_add_assigns_id_and_defaults(store: Storage) -> None:
    item = store.add(StudyItem(front="Q", back="A"))
    assert item.id == 1
    assert item.created_at is not None
    assert item.due_date is not None
    assert item.due_date == item.created_at.date()


def test_round_trip_preserves_fields(store: Storage) -> None:
    created = datetime(2026, 1, 1, 9, 30, 0)
    reviewed = datetime(2026, 1, 2, 10, 0, 0)
    original = StudyItem(
        front="capital of France",
        back="Paris",
        repetitions=3,
        ease_factor=2.36,
        interval=15,
        due_date=date(2026, 1, 17),
        created_at=created,
        last_reviewed=reviewed,
    )
    stored = store.add(original)
    fetched = store.get(stored.id)  # type: ignore[arg-type]
    assert fetched is not None
    assert fetched.front == "capital of France"
    assert fetched.back == "Paris"
    assert fetched.repetitions == 3
    assert fetched.ease_factor == pytest.approx(2.36)
    assert fetched.interval == 15
    assert fetched.due_date == date(2026, 1, 17)
    assert fetched.created_at == created
    assert fetched.last_reviewed == reviewed


def test_get_missing_returns_none(store: Storage) -> None:
    assert store.get(999) is None


def test_list_all_orders_by_due_date(store: Storage) -> None:
    base = datetime(2026, 1, 1)
    store.add(StudyItem(front="late", due_date=date(2026, 2, 1), created_at=base))
    store.add(StudyItem(front="early", due_date=date(2026, 1, 5), created_at=base))
    fronts = [i.front for i in store.list_all()]
    assert fronts == ["early", "late"]


def test_list_due_filters_by_date(store: Storage) -> None:
    base = datetime(2026, 1, 1)
    store.add(StudyItem(front="due", due_date=date(2026, 1, 10), created_at=base))
    store.add(StudyItem(front="future", due_date=date(2026, 1, 20), created_at=base))
    due = store.list_due(on=date(2026, 1, 15))
    assert [i.front for i in due] == ["due"]


def test_list_due_defaults_to_today(store: Storage) -> None:
    store.add(StudyItem(front="overdue", due_date=date.today() - timedelta(days=1)))
    store.add(StudyItem(front="tomorrow", due_date=date.today() + timedelta(days=1)))
    fronts = [i.front for i in store.list_due()]
    assert "overdue" in fronts
    assert "tomorrow" not in fronts


def test_update_persists_changes(store: Storage) -> None:
    item = store.add(StudyItem(front="Q", back="A"))
    item.repetitions = 7
    item.ease_factor = 1.8
    item.interval = 42
    item.due_date = date(2027, 1, 1)
    item.last_reviewed = datetime(2026, 6, 1, 12, 0, 0)
    store.update(item)
    fetched = store.get(item.id)  # type: ignore[arg-type]
    assert fetched is not None
    assert fetched.repetitions == 7
    assert fetched.ease_factor == pytest.approx(1.8)
    assert fetched.interval == 42
    assert fetched.due_date == date(2027, 1, 1)
    assert fetched.last_reviewed == datetime(2026, 6, 1, 12, 0, 0)


def test_update_without_id_raises(store: Storage) -> None:
    with pytest.raises(ValueError):
        store.update(StudyItem(front="no id"))


def test_delete_returns_true_when_removed(store: Storage) -> None:
    item = store.add(StudyItem(front="Q"))
    assert store.delete(item.id) is True  # type: ignore[arg-type]
    assert store.get(item.id) is None  # type: ignore[arg-type]


def test_delete_returns_false_when_absent(store: Storage) -> None:
    assert store.delete(123) is False


def test_count(store: Storage) -> None:
    assert store.count() == 0
    store.add(StudyItem(front="a"))
    store.add(StudyItem(front="b"))
    assert store.count() == 2


def test_file_backed_storage_persists_across_instances(tmp_path: Path) -> None:
    db = tmp_path / "nested" / "reviews.db"  # parent dir does not exist yet
    s1 = Storage(db)
    s1.add(StudyItem(front="persisted", back="value"))
    assert db.exists()

    s2 = Storage(db)
    items = s2.list_all()
    assert len(items) == 1
    assert items[0].front == "persisted"


def test_state_property_reflects_item(store: Storage) -> None:
    item = StudyItem(front="Q", repetitions=2, ease_factor=2.3, interval=6)
    state = item.state
    assert state.repetitions == 2
    assert state.ease_factor == pytest.approx(2.3)
    assert state.interval == 6


def test_close_is_idempotent(store: Storage) -> None:
    store.close()
    store.close()  # should not raise
