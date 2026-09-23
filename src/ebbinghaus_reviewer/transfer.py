"""Versioned JSON export/import of a whole collection, including review history."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, TypeVar

from ebbinghaus_reviewer.models import Item, Review
from ebbinghaus_reviewer.scheduling import Grade, Schedule, Strategy

__all__ = ["FORMAT", "VERSION", "ImportedItem", "ImportedReview", "dump", "load"]

FORMAT = "ebbinghaus-reviewer"
VERSION = 1


@dataclass(frozen=True)
class ImportedReview:
    """A review read from an export file."""

    reviewed_at: datetime
    grade: Grade
    scheduled_for: datetime | None
    interval: timedelta


@dataclass(frozen=True)
class ImportedItem:
    """An item (and its history) read from an export file."""

    title: str
    notes: str
    subject: str | None
    schedule: Schedule
    studied_at: datetime
    last_reviewed_at: datetime | None
    created_at: datetime
    reviews: tuple[ImportedReview, ...]


def _stamp(moment: datetime | None) -> str | None:
    return None if moment is None else moment.astimezone(timezone.utc).isoformat()


def dump(
    entries: Sequence[tuple[Item, Sequence[Review]]], *, exported_at: datetime
) -> dict[str, Any]:
    """Serialise items with their reviews into a JSON-compatible document."""
    return {
        "format": FORMAT,
        "version": VERSION,
        "exported_at": _stamp(exported_at),
        "items": [
            {
                "title": item.title,
                "notes": item.notes,
                "subject": item.subject,
                "strategy": item.schedule.strategy.value,
                "step": item.schedule.step,
                "ease": item.schedule.ease,
                "interval_seconds": round(item.schedule.interval.total_seconds()),
                "due_at": _stamp(item.schedule.due_at),
                "studied_at": _stamp(item.studied_at),
                "last_reviewed_at": _stamp(item.last_reviewed_at),
                "created_at": _stamp(item.created_at),
                "reviews": [
                    {
                        "reviewed_at": _stamp(review.reviewed_at),
                        "grade": review.grade.value,
                        "scheduled_for": _stamp(review.scheduled_for),
                        "interval_seconds": round(review.interval.total_seconds()),
                    }
                    for review in reviews
                ],
            }
            for item, reviews in entries
        ],
    }


_E = TypeVar("_E", Strategy, Grade)


class _Reader:
    """Typed accessors that turn malformed input into precise ``ValueError``s."""

    def __init__(self, data: Mapping[str, Any], where: str) -> None:
        self.data = data
        self.where = where

    def fail(self, message: str) -> ValueError:
        return ValueError(f"{self.where}: {message}")

    def text(self, key: str) -> str:
        value = self.data.get(key)
        if not isinstance(value, str):
            raise self.fail(f"'{key}' must be a string")
        return value

    def optional_text(self, key: str) -> str | None:
        return None if self.data.get(key) is None else self.text(key)

    def integer(self, key: str, *, minimum: int) -> int:
        value = self.data.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise self.fail(f"'{key}' must be an integer >= {minimum}")
        return value

    def number(self, key: str) -> float:
        value = self.data.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise self.fail(f"'{key}' must be a number")
        return float(value)

    def moment(self, key: str) -> datetime:
        try:
            moment = datetime.fromisoformat(self.text(key))
        except ValueError:
            raise self.fail(f"'{key}' must be an ISO-8601 timestamp") from None
        if moment.tzinfo is None:
            raise self.fail(f"'{key}' must include a UTC offset")
        return moment

    def optional_moment(self, key: str) -> datetime | None:
        return None if self.data.get(key) is None else self.moment(key)

    def choice(self, key: str, enum: type[_E]) -> _E:
        value = self.text(key)
        try:
            return enum(value)
        except ValueError:
            allowed = ", ".join(member.value for member in enum)
            raise self.fail(f"'{key}' must be one of {allowed}") from None


def load(document: Any) -> list[ImportedItem]:
    """Validate an export document and return its items.

    Raises:
        ValueError: If the document is not a compatible export.
    """
    if not isinstance(document, Mapping):
        raise ValueError("export must be a JSON object")
    if document.get("format") != FORMAT:
        raise ValueError(f"not an {FORMAT} export (missing or wrong 'format')")
    if document.get("version") != VERSION:
        raise ValueError(f"unsupported export version {document.get('version')!r}")
    raw_items = document.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("'items' must be a list")

    items: list[ImportedItem] = []
    for index, raw in enumerate(raw_items):
        if not isinstance(raw, Mapping):
            raise ValueError(f"items[{index}] must be an object")
        read = _Reader(raw, f"items[{index}]")
        title = read.text("title").strip()
        if not title:
            raise read.fail("'title' must not be empty")
        raw_reviews = raw.get("reviews", [])
        if not isinstance(raw_reviews, list):
            raise read.fail("'reviews' must be a list")
        reviews: list[ImportedReview] = []
        for position, raw_review in enumerate(raw_reviews):
            if not isinstance(raw_review, Mapping):
                raise read.fail(f"reviews[{position}] must be an object")
            review = _Reader(raw_review, f"items[{index}].reviews[{position}]")
            reviews.append(
                ImportedReview(
                    reviewed_at=review.moment("reviewed_at"),
                    grade=review.choice("grade", Grade),
                    scheduled_for=review.optional_moment("scheduled_for"),
                    interval=timedelta(seconds=review.integer("interval_seconds", minimum=1)),
                )
            )
        items.append(
            ImportedItem(
                title=title,
                notes=read.optional_text("notes") or "",
                subject=(read.optional_text("subject") or "").strip() or None,
                schedule=Schedule(
                    strategy=read.choice("strategy", Strategy),
                    step=read.integer("step", minimum=0),
                    ease=read.number("ease"),
                    interval=timedelta(seconds=read.integer("interval_seconds", minimum=1)),
                    due_at=read.optional_moment("due_at"),
                ),
                studied_at=read.moment("studied_at"),
                last_reviewed_at=read.optional_moment("last_reviewed_at"),
                created_at=read.moment("created_at"),
                reviews=tuple(reviews),
            )
        )
    return items
