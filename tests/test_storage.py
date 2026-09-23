from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from ebbinghaus_reviewer.scheduling import DEFAULT_EASE, Grade, Schedule, Strategy
from ebbinghaus_reviewer.storage import SCHEMA_VERSION, DatabaseError, Repository

T0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
DAY = timedelta(days=1)


def schedule(due_in: timedelta | None, *, interval: timedelta = DAY) -> Schedule:
    return Schedule(
        Strategy.LADDER, 1, DEFAULT_EASE, interval, None if due_in is None else T0 + due_in
    )


def add(repo: Repository, title: str, due_in: timedelta | None, subject: str | None = None) -> int:
    item = repo.insert_item(
        title=title,
        notes="",
        subject=subject,
        schedule=schedule(due_in),
        studied_at=T0,
        created_at=T0,
    )
    return item.id


def test_new_database_is_migrated_to_the_current_schema(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "collection.sqlite3"
    with Repository(path) as repo:
        assert repo.schema_version == SCHEMA_VERSION
    assert path.exists()
    # Re-opening an up-to-date database is a no-op.
    with Repository(path) as repo:
        assert repo.schema_version == SCHEMA_VERSION


def test_items_round_trip_with_timezones_normalised_to_utc(repository: Repository) -> None:
    seoul = timezone(timedelta(hours=9))
    stored = repository.insert_item(
        title="Title",
        notes="Notes",
        subject="Subject",
        schedule=Schedule(
            Strategy.SM2, 3, 2.36, 15 * DAY, datetime(2026, 1, 20, 18, 30, tzinfo=seoul)
        ),
        studied_at=datetime(2026, 1, 1, 18, 0, tzinfo=seoul),
        created_at=T0,
    )
    loaded = repository.get_item(stored.id)
    assert loaded == stored
    assert loaded is not None
    assert loaded.schedule.due_at == datetime(2026, 1, 20, 9, 30, tzinfo=timezone.utc)
    assert loaded.schedule.due_at.utcoffset() == timedelta()
    assert (loaded.review_count, loaded.lapse_count) == (0, 0)


def test_naive_timestamps_are_rejected(repository: Repository) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        repository.insert_item(
            title="x",
            notes="",
            subject=None,
            schedule=schedule(DAY),
            studied_at=datetime(2026, 1, 1),
            created_at=T0,
        )


def test_database_constraints(repository: Repository) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        add(repository, "   ", DAY)


def test_listing_orders_by_due_time_with_mastered_last(repository: Repository) -> None:
    later = add(repository, "later", 2 * DAY)
    mastered = add(repository, "mastered", None)
    sooner = add(repository, "sooner", DAY)
    assert [i.id for i in repository.list_items()] == [sooner, later, mastered]
    assert [i.id for i in repository.list_items(include_mastered=False)] == [sooner, later]


def test_items_due_before(repository: Repository) -> None:
    overdue = add(repository, "overdue", -DAY, subject="A")
    exactly = add(repository, "exactly now", timedelta(), subject="B")
    add(repository, "future", DAY, subject="A")
    add(repository, "mastered", None)
    assert [i.id for i in repository.items_due_before(T0)] == [overdue, exactly]
    assert [i.id for i in repository.items_due_before(T0, inclusive=False)] == [overdue]
    assert [i.id for i in repository.items_due_before(T0, subject="A")] == [overdue]


def test_subjects_are_distinct_and_sorted_case_insensitively(repository: Repository) -> None:
    for subject in ("biology", "Algebra", None, "biology", "Chemistry"):
        add(repository, "x", DAY, subject=subject)
    assert repository.subjects() == ["Algebra", "biology", "Chemistry"]


def test_reviews_and_counts(repository: Repository) -> None:
    item_id = add(repository, "x", DAY)
    for offset, grade in ((1, Grade.GOOD), (2, Grade.AGAIN), (3, Grade.GOOD)):
        repository.insert_review(
            item_id=item_id,
            reviewed_at=T0 + offset * DAY,
            grade=grade,
            scheduled_for=T0,
            interval=DAY,
        )
    item = repository.get_item(item_id)
    assert item is not None
    assert (item.review_count, item.lapse_count) == (3, 1)
    history = repository.reviews_for(item_id)
    assert [r.grade for r in history] == [Grade.GOOD, Grade.AGAIN, Grade.GOOD]
    assert [r.reviewed_at for r in repository.reviews_since(T0 + 2 * DAY)] == [
        T0 + 2 * DAY,
        T0 + 3 * DAY,
    ]
    assert repository.review_times() == [T0 + DAY, T0 + 2 * DAY, T0 + 3 * DAY]


def test_deleting_an_item_cascades_to_its_reviews(repository: Repository) -> None:
    item_id = add(repository, "x", DAY)
    repository.insert_review(
        item_id=item_id, reviewed_at=T0, grade=Grade.GOOD, scheduled_for=None, interval=DAY
    )
    assert repository.delete_item(item_id)
    assert repository.get_item(item_id) is None
    assert repository.review_times() == []
    assert not repository.delete_item(item_id)


def test_update_of_a_missing_item_raises(repository: Repository) -> None:
    item_id = add(repository, "x", DAY)
    item = repository.get_item(item_id)
    assert item is not None
    repository.delete_item(item_id)
    with pytest.raises(LookupError):
        repository.update_item(item, updated_at=T0)


def test_transaction_rolls_back_on_error(repository: Repository) -> None:
    def failing_block() -> None:
        with repository.transaction():
            add(repository, "x", DAY)
            with repository.transaction():  # nested blocks join the outer transaction
                add(repository, "y", DAY)
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        failing_block()
    assert repository.list_items() == []


def test_newer_schema_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "future.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
    with pytest.raises(DatabaseError, match="upgrade"):
        Repository(path)


def test_foreign_files_are_refused(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("definitely not a database, but long enough to have a header " * 10)
    with pytest.raises(DatabaseError, match="not an Ebbinghaus Reviewer database"):
        Repository(path)


def test_unrelated_sqlite_databases_are_refused(tmp_path: Path) -> None:
    path = tmp_path / "other.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE items (x)")
    with pytest.raises(DatabaseError, match="not an Ebbinghaus Reviewer database"):
        Repository(path)


def test_unopenable_paths_are_reported(tmp_path: Path) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("")
    with pytest.raises(DatabaseError, match="cannot open"):
        Repository(blocker / "collection.sqlite3")


def test_home_directory_is_expanded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    with Repository("~/nested/collection.sqlite3") as repo:
        assert repo.path == str(tmp_path / "nested" / "collection.sqlite3")
    assert (tmp_path / "nested" / "collection.sqlite3").exists()
