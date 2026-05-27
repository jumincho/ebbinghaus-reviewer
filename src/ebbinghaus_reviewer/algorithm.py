"""Spaced-repetition scheduling algorithm.

Implements the SM-2 algorithm by P. A. Wozniak (1985), which is the modern
operationalization of Hermann Ebbinghaus's forgetting curve (1885). Ebbinghaus
showed that retention decays exponentially after learning unless the material is
revisited; SM-2 turns that observation into an actionable interval that adapts
to per-card difficulty via an "ease factor".

The original Ebbinghaus intervals (~20min, 1h, 9h, 1d, 2d, 6d, 31d) inspired
this family of algorithms but assume identical material difficulty. SM-2's
ease factor relaxes that assumption.

Reference: https://super-memo.com/english/ol/sm2.htm
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import IntEnum


class ReviewQuality(IntEnum):
    """User-reported recall quality, per SM-2.

    Values 0-2 indicate a failed recall and reset the repetition count.
    Values 3-5 indicate a successful recall with varying confidence.
    """

    BLACKOUT = 0
    INCORRECT_HARD = 1
    INCORRECT_EASY = 2
    CORRECT_HARD = 3
    CORRECT_HESITANT = 4
    PERFECT = 5

    @property
    def is_pass(self) -> bool:
        return self.value >= 3


@dataclass(frozen=True)
class ScheduleState:
    """Per-card scheduling state, updated after each review.

    Attributes:
        repetition: Count of consecutive successful recalls (resets on failure).
        ease_factor: SM-2 ease factor, lower means harder (floor 1.3).
        interval_days: Days until the next review.
        next_review_at: Absolute timestamp of the next review.
    """

    repetition: int
    ease_factor: float
    interval_days: int
    next_review_at: datetime

    @classmethod
    def initial(cls, now: datetime) -> ScheduleState:
        """Initial state for a newly added card: due immediately."""
        return cls(
            repetition=0,
            ease_factor=2.5,
            interval_days=0,
            next_review_at=now,
        )


MIN_EASE_FACTOR = 1.3
DEFAULT_EASE_FACTOR = 2.5


def _next_interval(repetition: int, prev_interval: int, ease_factor: float) -> int:
    """Compute the next interval in days, per SM-2.

    repetition is the *new* count (already incremented for the current pass).
    """
    if repetition == 1:
        return 1
    if repetition == 2:
        return 6
    return max(1, round(prev_interval * ease_factor))


def _update_ease(ease_factor: float, quality: ReviewQuality) -> float:
    """SM-2 ease-factor update, floored at MIN_EASE_FACTOR.

        EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
    """
    q = quality.value
    delta = 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
    return max(MIN_EASE_FACTOR, ease_factor + delta)


def schedule_next(
    state: ScheduleState,
    quality: ReviewQuality,
    reviewed_at: datetime,
) -> ScheduleState:
    """Apply SM-2 to advance schedule state after a review.

    A failed recall (quality < 3) resets the repetition count and reschedules
    one day out, but still updates the ease factor downward. A successful
    recall increments the repetition count and stretches the interval.
    """
    new_ease = _update_ease(state.ease_factor, quality)

    if not quality.is_pass:
        return ScheduleState(
            repetition=0,
            ease_factor=new_ease,
            interval_days=1,
            next_review_at=reviewed_at + timedelta(days=1),
        )

    new_repetition = state.repetition + 1
    new_interval = _next_interval(new_repetition, state.interval_days, new_ease)
    return ScheduleState(
        repetition=new_repetition,
        ease_factor=new_ease,
        interval_days=new_interval,
        next_review_at=reviewed_at + timedelta(days=new_interval),
    )
