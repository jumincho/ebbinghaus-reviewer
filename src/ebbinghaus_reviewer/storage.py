"""SQLite persistence for cards and reviews.

Single-connection design: all storage operations go through one Storage
instance bound to one SQLite file. This is sufficient for a single-user
study tool — no concurrent writers, no connection pool.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from ebbinghaus_reviewer.models import Card, Review

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    front TEXT NOT NULL,
    back TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    repetition INTEGER NOT NULL DEFAULT 0,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    interval_days INTEGER NOT NULL DEFAULT 0,
    next_review_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cards_next_review_at ON cards(next_review_at);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    reviewed_at TEXT NOT NULL,
    quality INTEGER NOT NULL,
    interval_days_before INTEGER NOT NULL,
    interval_days_after INTEGER NOT NULL,
    ease_factor_after REAL NOT NULL,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reviews_card_id ON reviews(card_id);
CREATE INDEX IF NOT EXISTS idx_reviews_reviewed_at ON reviews(reviewed_at);
"""


def default_db_path() -> Path:
    """Resolve the default SQLite path, honoring EBBINGHAUS_DB_PATH."""
    override = os.environ.get("EBBINGHAUS_DB_PATH")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".ebbinghaus" / "db.sqlite"


def _to_iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _from_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _split_tags(s: str) -> list[str]:
    return [t for t in s.split(",") if t]


def _join_tags(tags: Iterable[str]) -> str:
    return ",".join(t.strip() for t in tags if t.strip())


class Storage:
    """SQLite-backed repository for cards and reviews."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            isolation_level=None,  # autocommit; we manage transactions explicitly
            check_same_thread=False,  # safe: SQLite serializes; we don't share writes across threads
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA_SQL)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Storage:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        self._conn.execute("BEGIN")
        try:
            yield self._conn
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        else:
            self._conn.execute("COMMIT")

    # --- Cards ---------------------------------------------------------

    def add_card(self, card: Card) -> Card:
        with self._transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO cards (front, back, tags, created_at,
                                   repetition, ease_factor, interval_days, next_review_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card.front,
                    card.back,
                    _join_tags(card.tags),
                    _to_iso(card.created_at),
                    card.repetition,
                    card.ease_factor,
                    card.interval_days,
                    _to_iso(card.next_review_at),
                ),
            )
            card.id = cursor.lastrowid
        return card

    def get_card(self, card_id: int) -> Card | None:
        row = self._conn.execute(
            "SELECT * FROM cards WHERE id = ?", (card_id,)
        ).fetchone()
        return _row_to_card(row) if row else None

    def list_cards(self, tag: str | None = None) -> list[Card]:
        if tag:
            rows = self._conn.execute(
                "SELECT * FROM cards WHERE tags LIKE ? ORDER BY id",
                (f"%{tag}%",),
            ).fetchall()
            # tags is a comma-joined string; tighten the LIKE result
            return [c for c in (_row_to_card(r) for r in rows) if tag in c.tags]
        rows = self._conn.execute("SELECT * FROM cards ORDER BY id").fetchall()
        return [_row_to_card(r) for r in rows]

    def due_cards(self, before: datetime) -> list[Card]:
        rows = self._conn.execute(
            "SELECT * FROM cards WHERE next_review_at <= ? ORDER BY next_review_at",
            (_to_iso(before),),
        ).fetchall()
        return [_row_to_card(r) for r in rows]

    def update_card_schedule(
        self,
        card_id: int,
        *,
        repetition: int,
        ease_factor: float,
        interval_days: int,
        next_review_at: datetime,
    ) -> None:
        with self._transaction() as conn:
            conn.execute(
                """
                UPDATE cards
                SET repetition = ?, ease_factor = ?, interval_days = ?, next_review_at = ?
                WHERE id = ?
                """,
                (repetition, ease_factor, interval_days, _to_iso(next_review_at), card_id),
            )

    def delete_card(self, card_id: int) -> bool:
        with self._transaction() as conn:
            cursor = conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        return cursor.rowcount > 0

    # --- Reviews -------------------------------------------------------

    def add_review(self, review: Review) -> Review:
        with self._transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reviews (card_id, reviewed_at, quality,
                                     interval_days_before, interval_days_after,
                                     ease_factor_after)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    review.card_id,
                    _to_iso(review.reviewed_at),
                    review.quality,
                    review.interval_days_before,
                    review.interval_days_after,
                    review.ease_factor_after,
                ),
            )
            review.id = cursor.lastrowid
        return review

    def list_reviews(self, card_id: int | None = None) -> list[Review]:
        if card_id is None:
            rows = self._conn.execute(
                "SELECT * FROM reviews ORDER BY reviewed_at DESC"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM reviews WHERE card_id = ? ORDER BY reviewed_at DESC",
                (card_id,),
            ).fetchall()
        return [_row_to_review(r) for r in rows]

    # --- Stats ---------------------------------------------------------

    def card_count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0])

    def review_count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0])

    def due_count(self, before: datetime) -> int:
        return int(
            self._conn.execute(
                "SELECT COUNT(*) FROM cards WHERE next_review_at <= ?", (_to_iso(before),)
            ).fetchone()[0]
        )


def _row_to_card(row: sqlite3.Row) -> Card:
    return Card(
        id=row["id"],
        front=row["front"],
        back=row["back"],
        tags=_split_tags(row["tags"]),
        created_at=_from_iso(row["created_at"]),
        repetition=row["repetition"],
        ease_factor=row["ease_factor"],
        interval_days=row["interval_days"],
        next_review_at=_from_iso(row["next_review_at"]),
    )


def _row_to_review(row: sqlite3.Row) -> Review:
    return Review(
        id=row["id"],
        card_id=row["card_id"],
        reviewed_at=_from_iso(row["reviewed_at"]),
        quality=row["quality"],
        interval_days_before=row["interval_days_before"],
        interval_days_after=row["interval_days_after"],
        ease_factor_after=row["ease_factor_after"],
    )
