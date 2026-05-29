"""Pure SM-2 spaced-repetition algorithm (Wozniak, 1985).

This module is the heart of the spaced-repetition / Ebbinghaus logic. It is
deliberately free of any I/O, persistence, or clock access: every function is
pure, fully type-hinted, and returns new values rather than mutating state.

The SM-2 algorithm models the Ebbinghaus *forgetting curve*: after each
successful recall the inter-review *interval* grows (so reviews get rarer as a
memory consolidates), and the per-item *ease factor* adapts to how easy the
item is for you. A failed recall (quality below 3) collapses the schedule back
to the start so the item is seen again the next day.

References
----------
P. A. Wozniak, "Optimization of learning", 1990 — the SM-2 specification:
https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
"""

from __future__ import annotations

from dataclasses import dataclass

#: Minimum recall quality (total blackout).
MIN_QUALITY = 0
#: Maximum recall quality (perfect response).
MAX_QUALITY = 5
#: Quality below this value counts as a failed recall and resets the schedule.
PASSING_QUALITY = 3
#: Lower bound on the ease factor; SM-2 never lets an item get harder than this.
MIN_EASE_FACTOR = 1.3
#: Ease factor assigned to a brand-new item.
DEFAULT_EASE_FACTOR = 2.5
#: Interval (in days) after the first successful recall.
FIRST_INTERVAL = 1
#: Interval (in days) after the second successful recall.
SECOND_INTERVAL = 6


@dataclass(frozen=True)
class ReviewState:
    """The mutable-over-time scheduling state of a single study item.

    Instances are immutable (``frozen``); :func:`review` consumes one state and
    returns the next one.

    Attributes:
        repetitions: Number of consecutive successful recalls so far.
        ease_factor: SM-2 ease factor (>= :data:`MIN_EASE_FACTOR`).
        interval: Days until the next review.
    """

    repetitions: int = 0
    ease_factor: float = DEFAULT_EASE_FACTOR
    interval: int = 0


def clamp_quality(quality: int) -> int:
    """Clamp a recall grade into the valid SM-2 range ``0..5``.

    Args:
        quality: Raw recall grade.

    Returns:
        ``quality`` constrained to ``[MIN_QUALITY, MAX_QUALITY]``.
    """
    return max(MIN_QUALITY, min(MAX_QUALITY, quality))


def updated_ease_factor(ease_factor: float, quality: int) -> float:
    """Apply the SM-2 ease-factor update for a given recall grade.

    The canonical SM-2 formula is::

        EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))

    The result is floored at :data:`MIN_EASE_FACTOR`.

    Args:
        ease_factor: Current ease factor.
        quality: Recall grade (will be clamped to ``0..5``).

    Returns:
        The updated ease factor, never below :data:`MIN_EASE_FACTOR`.
    """
    q = clamp_quality(quality)
    delta = 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
    return max(MIN_EASE_FACTOR, ease_factor + delta)


def next_interval(repetitions: int, ease_factor: float, interval: int) -> int:
    """Compute the next inter-review interval in days (SM-2 progression).

    The progression for successful recalls is the textbook one:

    * 1st success  -> :data:`FIRST_INTERVAL` (1 day)
    * 2nd success  -> :data:`SECOND_INTERVAL` (6 days)
    * 3rd+ success -> ``round(previous_interval * ease_factor)``

    Args:
        repetitions: Number of *successful* recalls *after* the current one
            (i.e. the already-incremented repetition count).
        ease_factor: The ease factor to multiply by. Per canonical SM-2 this is
            the ease factor *before* the current review's update (step 3 runs
            before the EF update in step 5).
        interval: The previous interval in days.

    Returns:
        The next interval in whole days (>= 1).
    """
    if repetitions <= 1:
        return FIRST_INTERVAL
    if repetitions == 2:
        return SECOND_INTERVAL
    return max(FIRST_INTERVAL, round(interval * ease_factor))


def review(state: ReviewState, quality: int) -> ReviewState:
    """Advance an item's schedule by one graded review (pure SM-2 step).

    This follows the canonical SM-2 order of operations:

    1. A passing grade (``quality >= PASSING_QUALITY``) increments the
       repetition count and computes the next interval using the *current*
       ease factor (before it is updated).
    2. The ease factor is then updated from the grade and floored at
       :data:`MIN_EASE_FACTOR`.
    3. A failing grade resets repetitions and the interval back to one day and,
       per the SM-2 specification, leaves the ease factor unchanged.

    Args:
        state: The item's current scheduling state.
        quality: Recall grade ``0..5`` (values outside the range are clamped).

    Returns:
        A new :class:`ReviewState` with the updated repetitions, ease factor,
        and interval.
    """
    q = clamp_quality(quality)

    if q < PASSING_QUALITY:
        # Failed recall: restart the curve, keep the E-Factor (SM-2 step 6).
        return ReviewState(repetitions=0, ease_factor=state.ease_factor, interval=FIRST_INTERVAL)

    repetitions = state.repetitions + 1
    # Interval uses the pre-update ease factor (SM-2 step 3 before step 5).
    interval = next_interval(repetitions, state.ease_factor, state.interval)
    ease = updated_ease_factor(state.ease_factor, q)
    return ReviewState(repetitions=repetitions, ease_factor=ease, interval=interval)
