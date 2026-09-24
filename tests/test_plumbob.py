from __future__ import annotations

import math
from datetime import datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from ebbinghaus_reviewer import Grade, Reviewer, Strategy
from ebbinghaus_reviewer.plumbob import FADING_BELOW, Mood, collection_mood, mood_of
from ebbinghaus_reviewer.retention import TARGET_RETENTION
from tests.conftest import FakeClock

ORDER = list(Mood)


def test_fresh_until_due_then_due(reviewer: Reviewer, clock: FakeClock) -> None:
    item = reviewer.add("x")
    assert item.due_at is not None
    assert mood_of(item, clock.moment) is Mood.FRESH
    assert mood_of(item, item.due_at - timedelta(seconds=1)) is Mood.FRESH
    assert mood_of(item, item.due_at) is Mood.DUE


def test_turns_red_when_recall_falls_below_the_threshold(reviewer: Reviewer) -> None:
    item = reviewer.add("x", strategy=Strategy.SM2)
    last_seen = item.schedule.last_seen_at
    assert last_seen is not None
    # recall = TARGET ** (elapsed / interval), so it reaches FADING_BELOW at:
    limit = item.schedule.interval * (math.log(FADING_BELOW) / math.log(TARGET_RETENTION))
    assert mood_of(item, last_seen + limit - timedelta(minutes=1)) is Mood.DUE
    assert mood_of(item, last_seen + limit + timedelta(minutes=1)) is Mood.FADING


def test_mastered_items_stay_fresh(reviewer: Reviewer, clock: FakeClock) -> None:
    item = reviewer.add("x")
    reviewer.grade(item.id, Grade.EASY)
    item = reviewer.grade(item.id, Grade.EASY)
    assert item.mastered
    assert mood_of(item, clock.moment + timedelta(days=3650)) is Mood.FRESH


def test_the_collection_shows_its_worst_item(reviewer: Reviewer, clock: FakeClock) -> None:
    now = clock.moment
    assert collection_mood([], now) is Mood.FRESH
    fresh = reviewer.add("fresh")
    due = reviewer.add("due", studied_at=now - timedelta(minutes=12))
    fading = reviewer.add("fading", studied_at=now - timedelta(days=1))
    assert [mood_of(item, now) for item in (fresh, due, fading)] == ORDER
    assert collection_mood([fresh], now) is Mood.FRESH
    assert collection_mood([fresh, due], now) is Mood.DUE
    assert collection_mood([fading, due, fresh], now) is Mood.FADING


@given(st.timedeltas(min_value=timedelta(), max_value=timedelta(days=400)))
def test_moods_only_get_worse_as_time_passes(later: timedelta) -> None:
    from ebbinghaus_reviewer import Repository

    with Repository() as repository:
        reviewer = Reviewer(repository, clock=FakeClock())
        item = reviewer.add("x", strategy=Strategy.SM2)
        start: datetime = reviewer.now()
        moods = [mood_of(item, start + later * fraction) for fraction in (0, 0.25, 0.5, 1)]
    assert moods == sorted(moods, key=ORDER.index)


def test_every_mood_has_a_style_and_a_description() -> None:
    assert [mood.style for mood in Mood] == ["green", "yellow", "bold red"]
    for mood in Mood:
        assert mood.description.lower().startswith(mood.value)
    assert f"{FADING_BELOW:.0%}" in Mood.FADING.description
