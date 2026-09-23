from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ebbinghaus_reviewer.durations import format_interval, format_relative, parse_duration


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("10m", timedelta(minutes=10)),
        ("10min", timedelta(minutes=10)),
        ("1h30m", timedelta(hours=1, minutes=30)),
        ("2 h", timedelta(hours=2)),
        ("1d", timedelta(days=1)),
        ("2w", timedelta(weeks=2)),
        ("1mo", timedelta(days=30)),
        ("1D", timedelta(days=1)),
        ("45s", timedelta(seconds=45)),
    ],
)
def test_parse_duration(text: str, expected: timedelta) -> None:
    assert parse_duration(text) == expected


@pytest.mark.parametrize("text", ["", "10", "m", "-1d", "0m", "1 fortnight", "1mon", "1.5h"])
def test_parse_duration_rejects_invalid_input(text: str) -> None:
    with pytest.raises(ValueError, match="duration"):
        parse_duration(text)


@pytest.mark.parametrize(
    ("interval", "expected"),
    [
        (timedelta(seconds=20), "1 min"),
        (timedelta(minutes=10), "10 min"),
        (timedelta(hours=5), "5 h"),
        (timedelta(days=1), "1 day"),
        (timedelta(days=6), "6 days"),
        (timedelta(weeks=1), "1 week"),
        (timedelta(weeks=2), "2 weeks"),
        (timedelta(days=16), "16 days"),
        (timedelta(days=30), "1 month"),
        (timedelta(days=60), "2 months"),
        (timedelta(days=43), "43 days"),
    ],
)
def test_format_interval(interval: timedelta, expected: str) -> None:
    assert format_interval(interval) == expected


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (timedelta(seconds=30), "now"),
        (timedelta(seconds=-30), "now"),
        (timedelta(minutes=5), "in 5 min"),
        (timedelta(minutes=-50), "50 min ago"),
        (timedelta(hours=3), "in 3 h"),
        (timedelta(hours=23, minutes=50), "in 1 day"),
        (timedelta(days=-2), "2 days ago"),
    ],
)
def test_format_relative(offset: timedelta, expected: str) -> None:
    assert format_relative(NOW + offset, NOW) == expected
