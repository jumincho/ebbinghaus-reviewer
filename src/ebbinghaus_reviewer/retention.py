"""A simple forgetting-curve model used to *visualise* memory strength.

Ebbinghaus found that retention decays roughly exponentially after learning.
We model recall probability as ``R(t) = exp(-t / S)`` and choose the
stability ``S`` so that ``R`` has fallen to :data:`TARGET_RETENTION` exactly
when the item is due, i.e. ``R(t) = TARGET_RETENTION ** (t / interval)``.

This is a display heuristic that assumes the schedule is well calibrated; it
does not change how items are scheduled.
"""

from __future__ import annotations

from datetime import timedelta

__all__ = ["TARGET_RETENTION", "curve", "estimated_retention"]

TARGET_RETENTION = 0.9
"""Assumed probability of recall at the moment an item becomes due."""


def estimated_retention(elapsed: timedelta, interval: timedelta) -> float:
    """Estimated probability of recall ``elapsed`` after the last review.

    Args:
        elapsed: Time since the item was last studied or reviewed.
        interval: The scheduled gap between that review and the due time.

    Returns:
        A probability in ``(0, 1]``; ``1.0`` for non-positive ``elapsed``.
    """
    if interval <= timedelta():
        raise ValueError("interval must be positive")
    if elapsed <= timedelta():
        return 1.0
    return float(TARGET_RETENTION ** (elapsed / interval))


def curve(
    interval: timedelta, *, horizon: float = 3.0, points: int = 61
) -> list[tuple[float, float]]:
    """Sample the forgetting curve as ``(t / interval, retention)`` pairs.

    Args:
        interval: The scheduled interval that anchors the curve.
        horizon: How many intervals to sample, starting from the last review.
        points: Number of samples (at least 2).
    """
    if points < 2:
        raise ValueError("points must be at least 2")
    return [
        (x, estimated_retention(interval * x, interval))
        for x in (horizon * i / (points - 1) for i in range(points))
    ]
