"""A realistic sample collection for trying the app (``ebbinghaus demo``).

The history is produced by replaying study sessions and reviews through the
real :class:`~ebbinghaus_reviewer.service.Reviewer` with a clock that travels
back in time, so every schedule is exactly what the algorithms would produce.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ebbinghaus_reviewer.scheduling import Grade, Strategy
from ebbinghaus_reviewer.service import Reviewer
from ebbinghaus_reviewer.storage import Repository

__all__ = ["SAMPLES", "Sample", "seed_demo"]

_M = timedelta(minutes=1)
_H = timedelta(hours=1)
_D = timedelta(days=1)


@dataclass(frozen=True)
class Sample:
    """One sample item: when it was studied and how each review went.

    Times are offsets back from "now".
    """

    title: str
    notes: str
    subject: str
    strategy: Strategy
    studied_ago: timedelta
    reviews: tuple[tuple[timedelta, Grade], ...] = ()


SAMPLES: tuple[Sample, ...] = (
    Sample(
        "Ebbinghaus (1885): forgetting is fastest right after learning",
        "Savings fall steeply within the first hour and then level off; "
        "well-timed reviews flatten the curve.",
        "Psychology",
        Strategy.LADDER,
        40 * _D,
        (
            (40 * _D - 10 * _M, Grade.GOOD),
            (39 * _D, Grade.GOOD),
            (32 * _D, Grade.GOOD),
            (2 * _D, Grade.GOOD),
        ),
    ),
    Sample(
        "Krebs cycle: the eight intermediates in order",
        "Citrate, isocitrate, alpha-ketoglutarate, succinyl-CoA, succinate, fumarate, "
        "malate, oxaloacetate.",
        "Biology",
        Strategy.LADDER,
        9 * _D,
        ((9 * _D - 10 * _M, Grade.GOOD), (8 * _D, Grade.GOOD)),
    ),
    Sample(
        "Binary heap: cost of push and pop",
        "O(log n) each; building a heap from a list (heapify) is O(n).",
        "Algorithms",
        Strategy.SM2,
        8 * _D,
        ((7 * _D, Grade.GOOD), (6 * _D + 2 * _H, Grade.GOOD)),
    ),
    Sample(
        "SM-2: lowest possible ease factor",
        "1.3 - an item never gets 'harder' than that.",
        "Learning science",
        Strategy.SM2,
        30 * _D,
        ((29 * _D, Grade.GOOD), (28 * _D, Grade.EASY), (12 * _D, Grade.GOOD)),
    ),
    Sample(
        "Treaty of Westphalia",
        "1648 - ended the Thirty Years' War; origin of the sovereign-state system.",
        "History",
        Strategy.SM2,
        15 * _D,
        (
            (14 * _D, Grade.GOOD),
            (13 * _D, Grade.AGAIN),
            (12 * _D, Grade.GOOD),
            (4 * _D, Grade.HARD),
        ),
    ),
    Sample(
        "Avogadro constant",
        "6.022 x 10^23 per mole.",
        "Chemistry",
        Strategy.LADDER,
        3 * _D,
        ((3 * _D - 10 * _M, Grade.GOOD), (2 * _D, Grade.GOOD)),
    ),
    Sample(
        "Korean spelling: 되 vs 돼",
        "돼 is the contraction of 되어 - if 되어 fits, write 돼.",
        "Korean",
        Strategy.LADDER,
        3 * _D,
        ((3 * _D - 10 * _M, Grade.GOOD),),
    ),
    Sample(
        "French: 'être' in the passé simple",
        "je fus, tu fus, il fut, nous fûmes, vous fûtes, ils furent",
        "French",
        Strategy.LADDER,
        5 * _M,
    ),
)


class _TravellingClock:
    """A clock whose current time can be set explicitly."""

    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment


def seed_demo(repository: Repository, *, now: datetime) -> int:
    """Add :data:`SAMPLES` with their review histories; return how many items were added."""
    clock = _TravellingClock(now)
    reviewer = Reviewer(repository, clock=clock)
    for sample in SAMPLES:
        clock.moment = now - sample.studied_ago
        item = reviewer.add(
            sample.title, notes=sample.notes, subject=sample.subject, strategy=sample.strategy
        )
        for ago, grade in sample.reviews:
            clock.moment = now - ago
            reviewer.grade(item.id, grade)
    return len(SAMPLES)
