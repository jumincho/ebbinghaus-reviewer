from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from ebbinghaus_reviewer import Grade, ItemNotFoundError, Repository, Reviewer, Strategy
from tests.conftest import KST, START, FakeClock

MIN = timedelta(minutes=1)
DAY = timedelta(days=1)


class TestAdd:
    def test_ladder_item_is_first_due_ten_minutes_later(self, reviewer: Reviewer) -> None:
        item = reviewer.add("Krebs cycle", notes="  eight steps  ", subject=" Biology ")
        assert item.id == 1
        assert (item.title, item.notes, item.subject) == ("Krebs cycle", "eight steps", "Biology")
        assert item.schedule.strategy is Strategy.LADDER
        assert item.studied_at == START
        assert item.due_at == START + 10 * MIN
        assert item.last_reviewed_at is None

    def test_sm2_item_is_first_due_a_day_later(self, reviewer: Reviewer) -> None:
        item = reviewer.add("Heap costs", strategy=Strategy.SM2)
        assert item.due_at == START + DAY

    def test_backfilled_study_time(self, reviewer: Reviewer) -> None:
        item = reviewer.add("Earlier", studied_at=START - 2 * DAY)
        assert item.studied_at == START - 2 * DAY
        assert item.is_due(reviewer.now())

    def test_title_whitespace_is_collapsed_and_blank_subjects_dropped(
        self, reviewer: Reviewer
    ) -> None:
        item = reviewer.add("  two\n  words ", subject="   ")
        assert (item.title, item.subject) == ("two words", None)

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"title": "   "}, "must not be empty"),
            ({"title": "x" * 201}, "at most 200"),
            ({"title": "x", "studied_at": START + MIN}, "future"),
            ({"title": "x", "studied_at": datetime(2026, 1, 1)}, "timezone-aware"),
        ],
    )
    def test_invalid_input(
        self, reviewer: Reviewer, kwargs: dict[str, object], message: str
    ) -> None:
        with pytest.raises(ValueError, match=message):
            reviewer.add(**kwargs)  # type: ignore[arg-type]


class TestReviewing:
    def test_a_ladder_item_climbs_to_mastery(self, reviewer: Reviewer, clock: FakeClock) -> None:
        item = reviewer.add("Avogadro constant")
        expected_intervals = [DAY, 7 * DAY, 30 * DAY]
        for interval in expected_intervals:
            assert item.due_at is not None
            clock.set(item.due_at)
            item = reviewer.grade(item.id, Grade.GOOD)
            assert item.schedule.interval == interval
            assert item.due_at == clock.moment + interval
        assert item.due_at is not None
        clock.set(item.due_at)
        item = reviewer.grade(item.id, Grade.GOOD)
        assert item.mastered
        assert item.review_count == 4
        assert item.last_reviewed_at == clock.moment
        assert reviewer.due() == []

    def test_reviews_are_logged(self, reviewer: Reviewer, clock: FakeClock) -> None:
        item = reviewer.add("x")
        clock.advance(15 * MIN)
        reviewer.grade(item.id, Grade.AGAIN)
        clock.advance(20 * MIN)
        updated = reviewer.grade(item.id, Grade.GOOD)
        history = reviewer.history(item.id)
        assert [(r.grade, r.reviewed_at) for r in history] == [
            (Grade.AGAIN, START + 15 * MIN),
            (Grade.GOOD, START + 35 * MIN),
        ]
        assert history[0].scheduled_for == START + 10 * MIN
        assert history[1].scheduled_for == START + 25 * MIN
        assert history[1].interval == DAY
        assert (updated.review_count, updated.lapse_count) == (2, 1)

    def test_microseconds_are_truncated(self, reviewer: Reviewer, clock: FakeClock) -> None:
        clock.set(START + timedelta(microseconds=750_000))
        item = reviewer.add("x")
        assert item.studied_at == START

    def test_unknown_items(self, reviewer: Reviewer) -> None:
        for call in (
            lambda: reviewer.grade(42, Grade.GOOD),
            lambda: reviewer.get(42),
            lambda: reviewer.history(42),
            lambda: reviewer.restart(42),
            lambda: reviewer.edit(42, title="x"),
            lambda: reviewer.delete(42),
        ):
            with pytest.raises(ItemNotFoundError) as excinfo:
                call()
            assert excinfo.value.item_id == 42


class TestQueries:
    def test_due_is_most_overdue_first_and_filterable(
        self, reviewer: Reviewer, clock: FakeClock
    ) -> None:
        old = reviewer.add("old", subject="A", studied_at=START - 3 * DAY)
        newer = reviewer.add("newer", subject="B", studied_at=START - DAY)
        reviewer.add("fresh")
        assert [i.id for i in reviewer.due()] == [old.id, newer.id]
        assert [i.id for i in reviewer.due(limit=1)] == [old.id]
        assert [i.id for i in reviewer.due(subject="B")] == [newer.id]
        clock.advance(10 * MIN)
        assert len(reviewer.due()) == 3

    def test_next_scheduled(self, reviewer: Reviewer) -> None:
        assert reviewer.next_scheduled() is None
        reviewer.add("sm2", strategy=Strategy.SM2, subject="B")
        ladder = reviewer.add("ladder", subject="A")
        soonest = reviewer.next_scheduled()
        assert soonest is not None
        assert soonest.id == ladder.id
        in_b = reviewer.next_scheduled(subject="B")
        assert in_b is not None
        assert in_b.title == "sm2"

    def test_items_and_subjects(self, reviewer: Reviewer) -> None:
        reviewer.add("a", subject="Math")
        reviewer.add("b", subject="Art")
        assert [i.title for i in reviewer.items(subject="Math")] == ["a"]
        assert reviewer.subjects() == ["Art", "Math"]


class TestChanges:
    def test_restart_keeps_history(self, reviewer: Reviewer, clock: FakeClock) -> None:
        item = reviewer.add("x")
        clock.advance(10 * MIN)
        reviewer.grade(item.id, Grade.GOOD)
        clock.advance(DAY)
        restarted = reviewer.restart(item.id)
        assert restarted.schedule.step == 0
        assert restarted.due_at == clock.moment + 10 * MIN
        assert restarted.review_count == 1

    def test_restart_can_switch_strategy(self, reviewer: Reviewer) -> None:
        item = reviewer.add("x")
        switched = reviewer.restart(item.id, strategy=Strategy.SM2)
        assert switched.schedule.strategy is Strategy.SM2
        assert switched.due_at == START + DAY

    def test_edit(self, reviewer: Reviewer) -> None:
        item = reviewer.add("title", notes="notes", subject="subject")
        assert reviewer.edit(item.id, title="new  title").title == "new title"
        kept = reviewer.edit(item.id, notes="new notes")
        assert (kept.notes, kept.subject) == ("new notes", "subject")
        assert reviewer.edit(item.id, subject=None).subject is None
        with pytest.raises(ValueError, match="empty"):
            reviewer.edit(item.id, title=" ")

    def test_delete(self, reviewer: Reviewer) -> None:
        item = reviewer.add("x")
        assert reviewer.delete(item.id).title == "x"
        assert reviewer.items() == []


class TestAgenda:
    def test_groups_by_local_day_with_overdue_items_today(self, reviewer: Reviewer) -> None:
        overdue = reviewer.add("overdue", studied_at=START - 2 * DAY)
        later_today = reviewer.add("later today")
        tomorrow = reviewer.add("tomorrow", strategy=Strategy.SM2)
        far = reviewer.add("far", strategy=Strategy.SM2)
        for _ in range(3):
            reviewer.grade(far.id, Grade.EASY)  # 1 day, 6 days, then 17 days
        mastered = reviewer.add("mastered")
        reviewer.grade(mastered.id, Grade.EASY)
        reviewer.grade(mastered.id, Grade.EASY)

        agenda = reviewer.agenda(days=7)
        assert [day.day for day in agenda] == [date(2026, 3, 2), date(2026, 3, 3)]
        assert [i.id for i in agenda[0].items] == [overdue.id, later_today.id]
        assert [i.id for i in agenda[1].items] == [tomorrow.id]
        assert reviewer.agenda(days=30)[-1].items == (reviewer.get(far.id),)

    def test_local_midnight_is_the_day_boundary(
        self, repository: Repository, clock: FakeClock
    ) -> None:
        clock.set(datetime(2026, 3, 2, 23, 45, tzinfo=KST))
        seoul = Reviewer(repository, clock=clock, tz=KST)
        seoul.add("due 23:55 on 2 March (KST)")
        seoul.add("due 23:45 on 3 March (KST)", strategy=Strategy.SM2)
        assert [len(day.items) for day in seoul.agenda(days=2)] == [1, 1]

        clock.set(datetime(2026, 3, 3, 0, 5, tzinfo=KST))  # still 2 March in UTC
        utc = Reviewer(repository, clock=clock, tz=timezone.utc)
        assert (seoul.today(), utc.today()) == (date(2026, 3, 3), date(2026, 3, 2))
        assert [(d.day, len(d.items)) for d in seoul.agenda(days=2)] == [(date(2026, 3, 3), 2)]
        assert [(d.day, len(d.items)) for d in utc.agenda(days=2)] == [
            (date(2026, 3, 2), 1),
            (date(2026, 3, 3), 1),
        ]

    def test_days_must_be_positive(self, reviewer: Reviewer) -> None:
        with pytest.raises(ValueError, match="at least 1"):
            reviewer.agenda(days=0)


class TestStats:
    def test_empty_collection(self, reviewer: Reviewer) -> None:
        stats = reviewer.stats()
        assert stats.total == 0
        assert stats.recall_rate_30_days is None
        assert stats.streak_days == 0

    def test_counts(self, reviewer: Reviewer, clock: FakeClock) -> None:
        item = reviewer.add("reviewed", studied_at=START - 2 * DAY)
        reviewer.add("due soon")
        reviewer.add("due tomorrow", strategy=Strategy.SM2)
        mastered = reviewer.add("mastered", studied_at=START - DAY)
        reviewer.grade(mastered.id, Grade.EASY)
        reviewer.grade(mastered.id, Grade.EASY)
        reviewer.grade(item.id, Grade.AGAIN)
        stats = reviewer.stats()
        assert (stats.total, stats.active, stats.mastered) == (4, 3, 1)
        assert stats.due_now == 0
        assert stats.due_later_today == 2  # "due soon" and the relearning "reviewed"
        assert (stats.reviews_today, stats.reviews_last_7_days) == (3, 3)
        assert stats.recall_rate_30_days == pytest.approx(2 / 3)
        assert stats.streak_days == 1

    def test_streak(self, reviewer: Reviewer, clock: FakeClock) -> None:
        item = reviewer.add("x", strategy=Strategy.SM2)
        for day in (0, 1, 2, 4, 5):  # a gap on day 3
            clock.set(START + day * DAY)
            reviewer.grade(item.id, Grade.GOOD)
        assert reviewer.stats().streak_days == 2
        clock.set(START + 6 * DAY)  # nothing yet today: yesterday still counts
        assert reviewer.stats().streak_days == 2
        clock.set(START + 7 * DAY)
        assert reviewer.stats().streak_days == 0

    def test_recent_windows(self, reviewer: Reviewer, clock: FakeClock) -> None:
        item = reviewer.add("x", strategy=Strategy.SM2)
        clock.set(START - 40 * DAY)
        reviewer.grade(item.id, Grade.AGAIN)  # outside every window
        clock.set(START - 10 * DAY)
        reviewer.grade(item.id, Grade.GOOD)  # in the 30-day window only
        clock.set(START)
        stats = reviewer.stats()
        assert (stats.reviews_today, stats.reviews_last_7_days) == (0, 0)
        assert stats.recall_rate_30_days == 1.0


class TestExportImport:
    def test_round_trip(self, reviewer: Reviewer, clock: FakeClock, repository: Repository) -> None:
        first = reviewer.add("first", notes="n", subject="S")
        clock.advance(10 * MIN)
        reviewer.grade(first.id, Grade.GOOD)
        reviewer.add("second", strategy=Strategy.SM2)
        document = json.loads(json.dumps(reviewer.export_data()))
        assert document["format"] == "ebbinghaus-reviewer"
        assert len(document["items"]) == 2

        with Repository() as other:
            target = Reviewer(other, clock=clock, tz=KST)
            assert target.import_data(document) == 2
            copied = {item.title: item for item in target.items()}
            original = {item.title: item for item in reviewer.items()}
            for title, item in original.items():
                assert copied[title].schedule == item.schedule
                assert copied[title].studied_at == item.studied_at
                assert copied[title].review_count == item.review_count
            assert [r.grade for r in target.history(copied["first"].id)] == [Grade.GOOD]

    def test_invalid_documents_import_nothing(self, reviewer: Reviewer) -> None:
        reviewer.add("valid")
        document = reviewer.export_data()
        document["items"].append({"title": "broken"})
        with Repository() as other:
            target = Reviewer(other, clock=FakeClock(), tz=KST)
            with pytest.raises(ValueError, match=r"items\[1\]"):
                target.import_data(document)
            assert target.items() == []


def test_clock_must_be_timezone_aware(repository: Repository) -> None:
    reviewer = Reviewer(repository, clock=lambda: datetime(2026, 1, 1), tz=KST)
    with pytest.raises(ValueError, match="timezone-aware"):
        reviewer.now()


def test_localize_and_start_of(reviewer: Reviewer) -> None:
    assert reviewer.localize(datetime(2026, 3, 2, 14, 0)) == datetime(2026, 3, 2, 14, 0, tzinfo=KST)
    assert reviewer.start_of(date(2026, 3, 2)) == datetime(2026, 3, 2, tzinfo=KST)
    with pytest.raises(ValueError, match="naive"):
        reviewer.localize(START)


def test_system_local_time_zone_is_the_default(repository: Repository) -> None:
    reviewer = Reviewer(repository, clock=FakeClock())
    assert reviewer.start_of(date(2026, 3, 2)).tzinfo is not None
    assert reviewer.today() == START.astimezone().date()
