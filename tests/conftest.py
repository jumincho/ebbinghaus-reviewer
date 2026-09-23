"""Shared fixtures: a controllable clock and a fresh in-memory collection."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest

from ebbinghaus_reviewer import Repository, Reviewer

KST = timezone(timedelta(hours=9), "KST")
"""A fixed-offset zone (no DST) so "today" is deterministic in every test."""

START = datetime(2026, 3, 2, 9, 0, tzinfo=KST)
"""Monday 2 March 2026, 09:00 in Seoul."""


class FakeClock:
    """A clock that only moves when told to."""

    def __init__(self, moment: datetime = START) -> None:
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment

    def advance(self, delta: timedelta) -> None:
        self.moment += delta

    def set(self, moment: datetime) -> None:
        self.moment = moment


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def repository() -> Iterator[Repository]:
    with Repository() as repo:
        yield repo


@pytest.fixture
def reviewer(repository: Repository, clock: FakeClock) -> Reviewer:
    return Reviewer(repository, clock=clock, tz=KST)
