"""Tests for the pure SM-2 algorithm."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ebbinghaus_reviewer.algorithm import (
    DEFAULT_EASE_FACTOR,
    FIRST_INTERVAL,
    MIN_EASE_FACTOR,
    SECOND_INTERVAL,
    ReviewState,
    clamp_quality,
    next_interval,
    review,
    updated_ease_factor,
)


def test_default_state() -> None:
    state = ReviewState()
    assert state.repetitions == 0
    assert state.ease_factor == DEFAULT_EASE_FACTOR
    assert state.interval == 0


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(-5, 0), (0, 0), (3, 3), (5, 5), (9, 5)],
)
def test_clamp_quality(raw: int, expected: int) -> None:
    assert clamp_quality(raw) == expected


def test_canonical_interval_progression() -> None:
    """The textbook progression: 1 -> 6 -> round(6 * EF), all q=5."""
    state = ReviewState()

    state = review(state, 5)
    assert state.repetitions == 1
    assert state.interval == FIRST_INTERVAL == 1

    state = review(state, 5)
    assert state.repetitions == 2
    assert state.interval == SECOND_INTERVAL == 6

    prev_interval = state.interval
    ef_before_third = state.ease_factor  # 2.7 after two q=5 reviews
    state = review(state, 5)
    assert state.repetitions == 3
    # Canonical SM-2 multiplies by the ease factor *before* this review's update.
    assert state.interval == round(prev_interval * ef_before_third)
    # interval = round(6 * 2.7) = 16; EF then climbs to 2.8.
    assert ef_before_third == pytest.approx(2.7)
    assert state.interval == 16
    assert state.ease_factor == pytest.approx(2.8)


def test_failure_resets_repetitions_and_interval() -> None:
    """A grade below 3 collapses the schedule back to one day."""
    state = ReviewState(repetitions=5, ease_factor=2.6, interval=40)
    after = review(state, 2)
    assert after.repetitions == 0
    assert after.interval == FIRST_INTERVAL == 1


@pytest.mark.parametrize("quality", [0, 1, 2])
def test_all_failing_grades_reset(quality: int) -> None:
    state = ReviewState(repetitions=3, ease_factor=2.5, interval=15)
    after = review(state, quality)
    assert after.repetitions == 0
    assert after.interval == 1


@pytest.mark.parametrize("quality", [3, 4, 5])
def test_passing_grades_increment(quality: int) -> None:
    state = ReviewState()
    after = review(state, quality)
    assert after.repetitions == 1
    assert after.interval == FIRST_INTERVAL


def test_ease_floor_never_below_minimum() -> None:
    """Repeated hard-but-passing grades cannot push EF under 1.3."""
    state = ReviewState()
    for _ in range(50):
        state = review(state, 3)  # q=3 nudges EF downward each time
    assert state.ease_factor == pytest.approx(MIN_EASE_FACTOR)
    assert state.ease_factor >= MIN_EASE_FACTOR


def test_ease_floor_on_repeated_failures() -> None:
    ef = DEFAULT_EASE_FACTOR
    for _ in range(20):
        ef = updated_ease_factor(ef, 0)
    assert ef == pytest.approx(MIN_EASE_FACTOR)


def test_quality_five_increases_ease() -> None:
    assert updated_ease_factor(2.5, 5) == pytest.approx(2.6)


def test_quality_four_keeps_ease_constant() -> None:
    # SM-2: q=4 leaves EF essentially unchanged (delta == 0).
    assert updated_ease_factor(2.5, 4) == pytest.approx(2.5)


def test_quality_three_decreases_ease() -> None:
    assert updated_ease_factor(2.5, 3) == pytest.approx(2.36)


def test_ease_factor_formula_matches_reference() -> None:
    # EF' = EF + (0.1 - (5-q)(0.08 + (5-q)*0.02))
    for q in range(0, 6):
        delta = 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
        assert updated_ease_factor(3.0, q) == pytest.approx(3.0 + delta)


def test_next_interval_rules() -> None:
    assert next_interval(1, 2.5, 0) == FIRST_INTERVAL
    assert next_interval(2, 2.5, 1) == SECOND_INTERVAL
    assert next_interval(3, 2.5, 6) == round(6 * 2.5)
    assert next_interval(4, 2.0, 15) == round(15 * 2.0)


def test_next_interval_never_below_one() -> None:
    assert next_interval(3, 1.3, 0) >= 1


def test_state_is_immutable() -> None:
    state = ReviewState()
    with pytest.raises(FrozenInstanceError):
        state.repetitions = 99  # type: ignore[misc]


def test_quality_out_of_range_is_clamped_in_review() -> None:
    # Passing huge quality behaves like q=5 (passing); negative like q=0 (fail).
    passing = review(ReviewState(), 99)
    assert passing.repetitions == 1
    failing = review(ReviewState(repetitions=4, interval=30), -10)
    assert failing.repetitions == 0
