"""Domain models for cards and reviews."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Card:
    """A study item with a front (prompt) and optional back (answer)."""

    id: int | None
    front: str
    back: str
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Schedule state (mirrors algorithm.ScheduleState; flattened for storage).
    repetition: int = 0
    ease_factor: float = 2.5
    interval_days: int = 0
    next_review_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Review:
    """One review event recorded against a card."""

    id: int | None
    card_id: int
    reviewed_at: datetime
    quality: int
    interval_days_before: int
    interval_days_after: int
    ease_factor_after: float
