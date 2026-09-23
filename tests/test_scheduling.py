from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ebbinghaus_reviewer.scheduling import (
    DEFAULT_EASE,
    DEFAULT_LADDER,
    MAXIMUM_INTERVAL,
    MIN_EASE,
    Grade,
    LadderScheduler,
    Schedule,
    SM2Scheduler,
    Strategy,
)

T0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
DAY = timedelta(days=1)


class TestGrade:
    @pytest.mark.parametrize(
        ("text", "grade"),
        [
            ("again", Grade.AGAIN),
            ("A", Grade.AGAIN),
            ("1", Grade.AGAIN),
            ("hard", Grade.HARD),
            ("h", Grade.HARD),
            ("good", Grade.GOOD),
            (" g ", Grade.GOOD),
            ("3", Grade.GOOD),
            ("Easy", Grade.EASY),
            ("4", Grade.EASY),
        ],
    )
    def test_parse(self, text: str, grade: Grade) -> None:
        assert Grade.parse(text) is grade

    @pytest.mark.parametrize("text", ["", "x", "5", "0", "ok"])
    def test_parse_rejects_unknown(self, text: str) -> None:
        with pytest.raises(ValueError, match="unknown grade"):
            Grade.parse(text)

    def test_only_again_fails(self) -> None:
        assert [grade.passed for grade in Grade] == [False, True, True, True]

    def test_sm2_quality_mapping(self) -> None:
        assert [grade.sm2_quality for grade in Grade] == [1, 3, 4, 5]


class TestLadder:
    ladder = LadderScheduler()

    def test_default_rungs_match_the_original_app(self) -> None:
        assert (timedelta(minutes=10), DAY, 7 * DAY, 30 * DAY) == DEFAULT_LADDER

    def test_first_review_is_ten_minutes_after_studying(self) -> None:
        schedule = self.ladder.initial(T0)
        assert schedule == Schedule(
            Strategy.LADDER, 0, DEFAULT_EASE, timedelta(minutes=10), T0 + timedelta(minutes=10)
        )
        assert schedule.last_seen_at == T0

    def test_good_reviews_climb_the_ladder_until_mastered(self) -> None:
        schedule = self.ladder.initial(T0)
        moment = T0
        seen = []
        for _ in DEFAULT_LADDER:
            assert schedule.due_at is not None
            moment = schedule.due_at
            schedule = self.ladder.next(schedule, Grade.GOOD, moment)
            seen.append(schedule.interval)
        assert seen[:3] == [DAY, 7 * DAY, 30 * DAY]
        assert schedule.mastered
        assert schedule.step == len(DEFAULT_LADDER)
        assert schedule.last_seen_at is None

    def test_intervals_are_measured_from_the_actual_review(self) -> None:
        late = T0 + 3 * DAY  # reviewed long after the 10-minute rung was due
        schedule = self.ladder.next(self.ladder.initial(T0), Grade.GOOD, late)
        assert schedule.due_at == late + DAY

    def test_again_restarts_from_the_first_rung(self) -> None:
        schedule = Schedule(Strategy.LADDER, 2, DEFAULT_EASE, 7 * DAY, T0)
        after = self.ladder.next(schedule, Grade.AGAIN, T0)
        assert (after.step, after.interval, after.due_at) == (
            0,
            timedelta(minutes=10),
            T0 + timedelta(minutes=10),
        )

    def test_hard_repeats_the_current_rung(self) -> None:
        schedule = Schedule(Strategy.LADDER, 2, DEFAULT_EASE, 7 * DAY, T0)
        after = self.ladder.next(schedule, Grade.HARD, T0)
        assert (after.step, after.interval) == (2, 7 * DAY)

    def test_easy_skips_a_rung(self) -> None:
        schedule = Schedule(Strategy.LADDER, 1, DEFAULT_EASE, DAY, T0)
        after = self.ladder.next(schedule, Grade.EASY, T0)
        assert (after.step, after.interval) == (3, 30 * DAY)

    def test_easy_on_the_top_rung_masters(self) -> None:
        schedule = Schedule(Strategy.LADDER, 3, DEFAULT_EASE, 30 * DAY, T0)
        assert self.ladder.next(schedule, Grade.EASY, T0).mastered

    def test_grading_a_mastered_item(self) -> None:
        mastered = Schedule(Strategy.LADDER, 4, DEFAULT_EASE, 30 * DAY, None)
        assert self.ladder.next(mastered, Grade.GOOD, T0).mastered
        assert self.ladder.next(mastered, Grade.HARD, T0).due_at == T0 + 30 * DAY
        assert self.ladder.next(mastered, Grade.AGAIN, T0).step == 0

    def test_custom_rungs(self) -> None:
        ladder = LadderScheduler((DAY, 3 * DAY))
        schedule = ladder.next(ladder.initial(T0), Grade.GOOD, T0 + DAY)
        assert schedule.interval == 3 * DAY
        assert ladder.next(schedule, Grade.GOOD, T0 + 4 * DAY).mastered

    @pytest.mark.parametrize("rungs", [(), (DAY, timedelta()), (-DAY,)])
    def test_invalid_rungs(self, rungs: tuple[timedelta, ...]) -> None:
        with pytest.raises(ValueError, match="rung"):
            LadderScheduler(rungs)


class TestSM2:
    sm2 = SM2Scheduler()

    def test_first_review_is_one_day_after_studying(self) -> None:
        schedule = self.sm2.initial(T0)
        assert (schedule.step, schedule.ease, schedule.interval, schedule.due_at) == (
            0,
            DEFAULT_EASE,
            DAY,
            T0 + DAY,
        )

    def test_worked_example(self) -> None:
        """The sequence documented in docs/algorithm.md."""
        expected = [
            (Grade.EASY, 1, 2.6, 1),
            (Grade.EASY, 2, 2.7, 6),
            (Grade.GOOD, 3, 2.7, 17),  # ceil(6 * 2.7) = ceil(16.2)
            (Grade.HARD, 4, 2.56, 46),  # ceil(17 * 2.7) = ceil(45.9)
            (Grade.AGAIN, 0, 2.56, 1),  # reset, ease unchanged
            (Grade.GOOD, 1, 2.56, 1),
        ]
        schedule = self.sm2.initial(T0)
        moment = T0
        for grade, repetitions, ease, days in expected:
            assert schedule.due_at is not None
            moment = schedule.due_at
            schedule = self.sm2.next(schedule, grade, moment)
            assert schedule.step == repetitions
            assert schedule.ease == pytest.approx(ease)
            assert schedule.interval == timedelta(days=days)
            assert schedule.due_at == moment + schedule.interval

    def test_interval_uses_the_ease_before_the_update(self) -> None:
        schedule = Schedule(Strategy.SM2, 2, 2.5, 6 * DAY, T0)
        after = self.sm2.next(schedule, Grade.HARD, T0)
        assert after.interval == 15 * DAY  # 6 * 2.5, not 6 * 2.36
        assert after.ease == pytest.approx(2.36)

    def test_exact_products_are_not_rounded_up(self) -> None:
        schedule = Schedule(Strategy.SM2, 2, 2.5, 6 * DAY, T0)
        assert self.sm2.next(schedule, Grade.GOOD, T0).interval == 15 * DAY

    def test_intervals_are_capped(self) -> None:
        schedule = self.sm2.initial(T0)
        for _ in range(60):
            schedule = self.sm2.next(schedule, Grade.EASY, T0)
        assert schedule.interval == MAXIMUM_INTERVAL
        assert schedule.ease == pytest.approx(DEFAULT_EASE + 6.0)

    def test_ease_is_floored(self) -> None:
        schedule = Schedule(Strategy.SM2, 5, 1.35, 10 * DAY, T0)
        assert self.sm2.next(schedule, Grade.HARD, T0).ease == MIN_EASE

    @given(
        grades=st.lists(st.sampled_from(list(Grade)), max_size=40),
        gaps=st.lists(st.integers(min_value=0, max_value=90 * 24 * 60), min_size=40, max_size=40),
    )
    def test_invariants(self, grades: list[Grade], gaps: list[int]) -> None:
        schedule = self.sm2.initial(T0)
        moment = T0
        for grade, gap in zip(grades, gaps, strict=False):
            moment += timedelta(minutes=gap)
            after = self.sm2.next(schedule, grade, moment)
            assert after.ease >= MIN_EASE
            assert DAY <= after.interval <= MAXIMUM_INTERVAL
            assert after.due_at == moment + after.interval
            assert after.step == (schedule.step + 1 if grade.passed else 0)
            if not grade.passed:
                assert after.ease == schedule.ease
            schedule = after


@given(
    grades=st.lists(st.sampled_from(list(Grade)), max_size=30),
    gap=st.integers(min_value=0, max_value=100_000),
)
def test_ladder_invariants(grades: list[Grade], gap: int) -> None:
    ladder = LadderScheduler()
    schedule = ladder.initial(T0)
    moment = T0
    for grade in grades:
        moment += timedelta(minutes=gap)
        schedule = ladder.next(schedule, grade, moment)
        assert 0 <= schedule.step <= len(DEFAULT_LADDER)
        if schedule.mastered:
            assert schedule.step == len(DEFAULT_LADDER)
        else:
            assert schedule.interval == DEFAULT_LADDER[schedule.step]
            assert schedule.due_at == moment + schedule.interval
