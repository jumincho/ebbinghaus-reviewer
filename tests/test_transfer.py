from __future__ import annotations

from typing import Any

import pytest

from ebbinghaus_reviewer import transfer
from ebbinghaus_reviewer.scheduling import Grade, Strategy


def document(**item_overrides: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "title": "Title",
        "notes": None,
        "subject": "  Subject  ",
        "strategy": "sm2",
        "step": 2,
        "ease": 2.5,
        "interval_seconds": 518_400,
        "due_at": "2026-01-10T09:00:00+00:00",
        "studied_at": "2026-01-01T09:00:00+00:00",
        "last_reviewed_at": "2026-01-04T09:00:00+00:00",
        "created_at": "2026-01-01T09:00:00+00:00",
        "reviews": [
            {
                "reviewed_at": "2026-01-02T09:00:00+00:00",
                "grade": "good",
                "scheduled_for": None,
                "interval_seconds": 86_400,
            }
        ],
    }
    item.update(item_overrides)
    return {"format": transfer.FORMAT, "version": transfer.VERSION, "items": [item]}


def test_load_valid_document() -> None:
    [item] = transfer.load(document())
    assert (item.title, item.notes, item.subject) == ("Title", "", "Subject")
    assert item.schedule.strategy is Strategy.SM2
    assert item.schedule.interval.days == 6
    assert item.reviews[0].grade is Grade.GOOD
    assert item.reviews[0].scheduled_for is None


@pytest.mark.parametrize(
    ("doc", "message"),
    [
        ([], "JSON object"),
        ({"format": "anki"}, "not an ebbinghaus-reviewer export"),
        ({"format": transfer.FORMAT, "version": 99}, "unsupported export version"),
        ({"format": transfer.FORMAT, "version": 1, "items": {}}, "'items' must be a list"),
        ({"format": transfer.FORMAT, "version": 1, "items": [1]}, r"items\[0\] must be an object"),
    ],
)
def test_load_rejects_bad_envelopes(doc: Any, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        transfer.load(doc)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"title": "  "}, "'title' must not be empty"),
        ({"title": 3}, "'title' must be a string"),
        ({"strategy": "leitner"}, "'strategy' must be one of ladder, sm2"),
        ({"step": -1}, "'step' must be an integer >= 0"),
        ({"step": True}, "'step' must be an integer"),
        ({"ease": "high"}, "'ease' must be a number"),
        ({"interval_seconds": 0}, "'interval_seconds' must be an integer >= 1"),
        ({"due_at": "tomorrow"}, "'due_at' must be an ISO-8601 timestamp"),
        ({"studied_at": "2026-01-01T09:00:00"}, "'studied_at' must include a UTC offset"),
        ({"reviews": "none"}, "'reviews' must be a list"),
        ({"reviews": [1]}, r"reviews\[0\] must be an object"),
        (
            {"reviews": [{"reviewed_at": "2026-01-02T09:00:00+00:00", "grade": "meh"}]},
            r"items\[0\].reviews\[0\]: 'grade' must be one of",
        ),
    ],
)
def test_load_rejects_bad_items(overrides: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        transfer.load(document(**overrides))
