from __future__ import annotations

from ebbinghaus_reviewer import Repository, Reviewer
from ebbinghaus_reviewer.demo import SAMPLES, seed_demo
from tests.conftest import KST, START, FakeClock


def test_demo_history_is_consistent(repository: Repository) -> None:
    assert seed_demo(repository, now=START) == len(SAMPLES)
    reviewer = Reviewer(repository, clock=FakeClock(START), tz=KST)
    items = reviewer.items()
    assert len(items) == len(SAMPLES)
    assert sum(item.review_count for item in items) == sum(len(s.reviews) for s in SAMPLES)
    # The sample set is meant to show every state: due, upcoming and mastered.
    stats = reviewer.stats()
    assert stats.due_now > 0
    assert stats.mastered > 0
    assert stats.active > stats.due_now
    for item in items:
        assert item.studied_at <= START
        for review in reviewer.history(item.id):
            assert item.studied_at <= review.reviewed_at <= START
