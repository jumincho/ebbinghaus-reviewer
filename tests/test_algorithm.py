"""Tests for the SM-2 spaced-repetition algorithm."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ebbinghaus_reviewer.algorithm import (
    DEFAULT_EASE_FACTOR,
    MIN_EASE_FACTOR,
    ReviewQuality,
    ScheduleState,
    schedule_next,
)

T0 = datetime(2026, 1, 1, 12, 0, 0)


def initial() -> ScheduleState:
    return ScheduleState.initial(T0)


# --- Initial state -------------------------------------------------------


def test_initial_state_is_due_now() -> None:
    s = initial()
    assert s.repetition == 0
    assert s.ease_factor == DEFAULT_EASE_FACTOR
    assert s.interval_days == 0
    assert s.next_review_at == T0


# --- Quality enum --------------------------------------------------------


@pytest.mark.parametrize(
    "quality,is_pass",
    [
        (ReviewQuality.BLACKOUT, False),
        (ReviewQuality.INCORRECT_HARD, False),
        (ReviewQuality.INCORRECT_EASY, False),
        (ReviewQuality.CORRECT_HARD, True),
        (ReviewQuality.CORRECT_HESITANT, True),
        (ReviewQuality.PERFECT, True),
    ],
)
def test_quality_pass_threshold(quality: ReviewQuality, is_pass: bool) -> None:
    assert quality.is_pass is is_pass


# --- First successful review -------------------------------------------


def test_first_pass_schedules_one_day_out() -> None:
    s = schedule_next(initial(), ReviewQuality.PERFECT, T0)
    assert s.repetition == 1
    assert s.interval_days == 1
    assert s.next_review_at == T0 + timedelta(days=1)


def test_second_pass_schedules_six_days_out() -> None:
    s = schedule_next(initial(), ReviewQuality.PERFECT, T0)
    s = schedule_next(s, ReviewQuality.PERFECT, s.next_review_at)
    assert s.repetition == 2
    assert s.interval_days == 6


def test_third_pass_uses_ease_factor() -> None:
    """After the third pass, interval = prev_interval * ease_factor."""
    s = schedule_next(initial(), ReviewQuality.PERFECT, T0)
    s = schedule_next(s, ReviewQuality.PERFECT, s.next_review_at)
    prev_interval = s.interval_days
    s = schedule_next(s, ReviewQuality.PERFECT, s.next_review_at)
    assert s.repetition == 3
    # PERFECT (q=5) bumps EF, so this is > 6 * 2.5 with the new EF
    expected = round(prev_interval * s.ease_factor)
    assert s.interval_days == expected
    assert s.interval_days >= 15  # 6 * 2.5 ≈ 15


# --- Failure resets repetitions ---------------------------------------


def test_failure_resets_repetition_and_schedules_one_day() -> None:
    s = schedule_next(initial(), ReviewQuality.PERFECT, T0)
    s = schedule_next(s, ReviewQuality.PERFECT, s.next_review_at)
    s = schedule_next(s, ReviewQuality.PERFECT, s.next_review_at)
    assert s.repetition == 3

    failed = schedule_next(s, ReviewQuality.BLACKOUT, s.next_review_at)
    assert failed.repetition == 0
    assert failed.interval_days == 1
    assert failed.next_review_at == s.next_review_at + timedelta(days=1)


def test_failure_still_drops_ease_factor() -> None:
    s = schedule_next(initial(), ReviewQuality.PERFECT, T0)
    initial_ef = s.ease_factor
    failed = schedule_next(s, ReviewQuality.BLACKOUT, s.next_review_at)
    assert failed.ease_factor < initial_ef


# --- Ease factor math -------------------------------------------------


def test_perfect_increases_ease_factor() -> None:
    s = schedule_next(initial(), ReviewQuality.PERFECT, T0)
    assert s.ease_factor > DEFAULT_EASE_FACTOR


def test_correct_hard_decreases_ease_factor_slightly() -> None:
    s = schedule_next(initial(), ReviewQuality.CORRECT_HARD, T0)
    # quality 3 reduces EF by ~0.14
    assert s.ease_factor < DEFAULT_EASE_FACTOR


def test_ease_factor_floor() -> None:
    """Repeated failures should never drive ease factor below 1.3."""
    s = initial()
    for _ in range(20):
        s = schedule_next(s, ReviewQuality.BLACKOUT, s.next_review_at)
    assert s.ease_factor == pytest.approx(MIN_EASE_FACTOR)


# --- Boundary edge cases ----------------------------------------------


def test_correct_hesitant_keeps_ease_factor_roughly_stable() -> None:
    """Quality 4 leaves EF roughly unchanged (delta ≈ 0)."""
    s = schedule_next(initial(), ReviewQuality.CORRECT_HESITANT, T0)
    # delta = 0.1 - 1 * (0.08 + 1*0.02) = 0
    assert s.ease_factor == pytest.approx(DEFAULT_EASE_FACTOR, abs=0.001)


def test_passing_review_advances_clock_to_reviewed_at() -> None:
    """Next review is computed from reviewed_at, not original schedule."""
    s = initial()
    late = T0 + timedelta(days=10)  # reviewed 10 days late
    s = schedule_next(s, ReviewQuality.PERFECT, late)
    assert s.next_review_at == late + timedelta(days=1)
