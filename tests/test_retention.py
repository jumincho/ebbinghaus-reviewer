from __future__ import annotations

from datetime import timedelta

import pytest

from ebbinghaus_reviewer.retention import TARGET_RETENTION, curve, estimated_retention

WEEK = timedelta(weeks=1)


def test_full_recall_right_after_review() -> None:
    assert estimated_retention(timedelta(), WEEK) == 1.0
    assert estimated_retention(-timedelta(hours=1), WEEK) == 1.0


def test_target_retention_is_reached_exactly_when_due() -> None:
    assert estimated_retention(WEEK, WEEK) == pytest.approx(TARGET_RETENTION)


def test_decay_is_exponential() -> None:
    assert estimated_retention(2 * WEEK, WEEK) == pytest.approx(TARGET_RETENTION**2)
    assert estimated_retention(WEEK / 2, WEEK) == pytest.approx(TARGET_RETENTION**0.5)


def test_longer_intervals_decay_more_slowly() -> None:
    day = timedelta(days=1)
    assert estimated_retention(3 * day, WEEK) > estimated_retention(3 * day, day)


def test_rejects_non_positive_interval() -> None:
    with pytest.raises(ValueError, match="positive"):
        estimated_retention(WEEK, timedelta())


def test_curve_samples() -> None:
    points = curve(WEEK, horizon=2.0, points=5)
    assert [x for x, _ in points] == [0.0, 0.5, 1.0, 1.5, 2.0]
    assert points[0][1] == 1.0
    assert points[2][1] == pytest.approx(TARGET_RETENTION)
    retentions = [r for _, r in points]
    assert retentions == sorted(retentions, reverse=True)


def test_curve_needs_two_points() -> None:
    with pytest.raises(ValueError, match="points"):
        curve(WEEK, points=1)
