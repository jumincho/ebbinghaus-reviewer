"""Scheduling strategies: pure functions from (schedule, grade, time) to the next schedule.

Two strategies are provided:

* :class:`LadderScheduler` - the fixed *Ebbinghaus ladder* of the original 2021
  app: review 10 minutes after studying, then 1 day, 1 week and 1 month after
  each successful review. Climbing past the last rung marks the item mastered.
* :class:`SM2Scheduler` - SuperMemo's adaptive SM-2 algorithm (Wozniak, 1990),
  where intervals grow by a per-item *ease factor* learned from your grades.

Both consume the same four-level :class:`Grade`. Nothing here touches a clock,
a database or the network, so every rule is directly unit-testable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import ClassVar, Protocol

from ebbinghaus_reviewer.durations import MONTH

__all__ = [
    "DEFAULT_EASE",
    "DEFAULT_LADDER",
    "MAXIMUM_INTERVAL",
    "MIN_EASE",
    "Grade",
    "LadderScheduler",
    "SM2Scheduler",
    "Schedule",
    "Scheduler",
    "Strategy",
]


class Grade(str, Enum):
    """How well an item was recalled during a review."""

    AGAIN = "again"
    """Forgotten: start over."""
    HARD = "hard"
    """Recalled with serious difficulty."""
    GOOD = "good"
    """Recalled after some thought."""
    EASY = "easy"
    """Recalled effortlessly."""

    @property
    def passed(self) -> bool:
        """``True`` for every grade except :attr:`AGAIN`."""
        return self is not Grade.AGAIN

    @property
    def sm2_quality(self) -> int:
        """The SM-2 response quality (0-5 scale) this grade stands for."""
        return _SM2_QUALITY[self]

    @classmethod
    def parse(cls, text: str) -> Grade:
        """Parse a grade from its name, first letter or 1-4 position (``"g"``, ``"3"``)."""
        key = text.strip().lower()
        for position, grade in enumerate(cls, start=1):
            if key in (grade.value, grade.value[0], str(position)):
                return grade
        raise ValueError(f"unknown grade {text!r}; expected one of again, hard, good, easy")


_SM2_QUALITY = {Grade.AGAIN: 1, Grade.HARD: 3, Grade.GOOD: 4, Grade.EASY: 5}


class Strategy(str, Enum):
    """The scheduling algorithm an item follows."""

    LADDER = "ladder"
    SM2 = "sm2"


DEFAULT_LADDER: tuple[timedelta, ...] = (
    timedelta(minutes=10),
    timedelta(days=1),
    timedelta(weeks=1),
    MONTH,
)
"""The four review checkpoints of the original app: 10 min, 1 day, 1 week, 1 month."""

DEFAULT_EASE = 2.5
"""SM-2 ease factor of a new item."""

MIN_EASE = 1.3
"""SM-2 never lets the ease factor fall below this value."""

MAXIMUM_INTERVAL = timedelta(days=36_500)
"""Longest interval SM-2 will schedule (100 years)."""


@dataclass(frozen=True)
class Schedule:
    """Where an item stands on its review schedule.

    Attributes:
        strategy: The algorithm that produced this schedule.
        step: Ladder: index of the rung being waited on (``len(ladder)`` once
            mastered). SM-2: consecutive successful reviews (``n``).
        ease: SM-2 ease factor (carried unchanged by the ladder).
        interval: Gap between the last study/review and ``due_at``.
        due_at: When the next review is due, or ``None`` once mastered.
    """

    strategy: Strategy
    step: int
    ease: float
    interval: timedelta
    due_at: datetime | None

    @property
    def mastered(self) -> bool:
        """``True`` once a ladder item has climbed past its last rung."""
        return self.due_at is None

    @property
    def last_seen_at(self) -> datetime | None:
        """When the item was last studied or reviewed (``due_at - interval``)."""
        return None if self.due_at is None else self.due_at - self.interval


class Scheduler(Protocol):
    """A scheduling strategy."""

    strategy: ClassVar[Strategy]

    def initial(self, studied_at: datetime) -> Schedule:
        """Schedule the first review of an item studied at ``studied_at``."""
        ...

    def next(self, schedule: Schedule, grade: Grade, reviewed_at: datetime) -> Schedule:
        """Return the schedule after a review graded ``grade`` at ``reviewed_at``."""
        ...


@dataclass(frozen=True)
class LadderScheduler:
    """Fixed expanding intervals - the classic Ebbinghaus review ladder.

    Each rung is the gap between two consecutive reviews:

    * ``AGAIN`` drops back to the first rung (relearn),
    * ``HARD`` repeats the current rung,
    * ``GOOD`` climbs one rung and ``EASY`` climbs two.

    Climbing past the top rung masters the item (no further reviews).
    """

    strategy: ClassVar[Strategy] = Strategy.LADDER

    rungs: tuple[timedelta, ...] = DEFAULT_LADDER

    def __post_init__(self) -> None:
        if not self.rungs:
            raise ValueError("a ladder needs at least one rung")
        if any(rung <= timedelta() for rung in self.rungs):
            raise ValueError("ladder rungs must be positive durations")

    def initial(self, studied_at: datetime) -> Schedule:
        return self._at_rung(0, studied_at, DEFAULT_EASE)

    def next(self, schedule: Schedule, grade: Grade, reviewed_at: datetime) -> Schedule:
        top = len(self.rungs)
        current = min(schedule.step, top)
        if grade is Grade.AGAIN:
            rung = 0
        elif grade is Grade.HARD:
            rung = min(current, top - 1)
        elif grade is Grade.GOOD:
            rung = current + 1
        else:
            rung = current + 2
        if rung >= top:
            return Schedule(Strategy.LADDER, top, schedule.ease, schedule.interval, None)
        return self._at_rung(rung, reviewed_at, schedule.ease)

    def _at_rung(self, rung: int, start: datetime, ease: float) -> Schedule:
        gap = self.rungs[rung]
        return Schedule(Strategy.LADDER, rung, ease, gap, start + gap)


@dataclass(frozen=True)
class SM2Scheduler:
    """SuperMemo SM-2 (P. A. Wozniak, *Optimization of learning*, 1990).

    Grades map to SM-2 qualities as again=1, hard=3, good=4, easy=5. On a
    passing review the repetition count ``n`` grows and the interval becomes
    1 day, then 6 days, then ``ceil(previous * EF)`` days, where ``EF`` is the
    ease factor *before* this review's update. The ease factor then moves by
    ``0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)`` and is floored at 1.3. A
    failed review restarts the repetitions at a 1-day interval and leaves the
    ease factor unchanged, as the specification prescribes.

    A newly studied item is first due one day later, i.e. the study session
    counts as the initial presentation. Intervals are capped at
    ``maximum_interval`` (100 years by default): without a cap a long run of
    easy reviews grows them exponentially past what dates can represent.
    """

    strategy: ClassVar[Strategy] = Strategy.SM2

    first_interval: timedelta = timedelta(days=1)
    second_interval: timedelta = timedelta(days=6)
    maximum_interval: timedelta = MAXIMUM_INTERVAL

    def initial(self, studied_at: datetime) -> Schedule:
        return Schedule(
            Strategy.SM2, 0, DEFAULT_EASE, self.first_interval, studied_at + self.first_interval
        )

    def next(self, schedule: Schedule, grade: Grade, reviewed_at: datetime) -> Schedule:
        quality = grade.sm2_quality
        if quality < 3:
            return Schedule(
                Strategy.SM2,
                0,
                schedule.ease,
                self.first_interval,
                reviewed_at + self.first_interval,
            )
        repetitions = schedule.step + 1
        if repetitions == 1:
            interval = self.first_interval
        elif repetitions == 2:
            interval = self.second_interval
        else:
            previous_days = schedule.interval / timedelta(days=1)
            # "If interval is a fraction, round it up to the nearest integer";
            # rounding to 6 places first keeps float noise from adding a day.
            days = math.ceil(round(previous_days * schedule.ease, 6))
            longest = self.maximum_interval // timedelta(days=1)
            interval = timedelta(days=max(1, min(days, longest)))
        ease = max(MIN_EASE, schedule.ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        return Schedule(Strategy.SM2, repetitions, round(ease, 4), interval, reviewed_at + interval)
