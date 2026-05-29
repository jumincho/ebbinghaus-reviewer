"""SQLite persistence for study items.

A thin, dependency-free repository over a single SQLite file. The database path
is injectable (no module-level globals, no implicit "current" database), which
keeps the layer easy to test and lets the CLI and the web server share one file.

The schema stores both the content of a card (``front``/``back``) and its SM-2
scheduling state (``repetitions``, ``ease_factor``, ``interval``, ``due_date``)
plus light bookkeeping timestamps.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .algorithm import DEFAULT_EASE_FACTOR, ReviewState

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    front         TEXT    NOT NULL,
    back          TEXT    NOT NULL DEFAULT '',
    repetitions   INTEGER NOT NULL DEFAULT 0,
    ease_factor   REAL    NOT NULL DEFAULT 2.5,
    interval      INTEGER NOT NULL DEFAULT 0,
    due_date      TEXT    NOT NULL,
    created_at    TEXT    NOT NULL,
    last_reviewed TEXT
);
"""

#: Sentinel path that opens a private, in-memory database (handy for tests).
MEMORY = ":memory:"


@dataclass
class StudyItem:
    """A single study card and its scheduling state.

    Attributes:
        front: The prompt / question / subject shown first.
        back: The answer / note revealed on recall (may be empty).
        repetitions: Consecutive successful recalls (SM-2).
        ease_factor: SM-2 ease factor.
        interval: Days between the last review and ``due_date``.
        due_date: The date this item is next due for review.
        created_at: When the item was first added.
        last_reviewed: When the item was last graded, or ``None`` if never.
        id: Database primary key, or ``None`` before insertion.
    """

    front: str
    back: str = ""
    repetitions: int = 0
    ease_factor: float = DEFAULT_EASE_FACTOR
    interval: int = 0
    due_date: date = None  # type: ignore[assignment]
    created_at: datetime = None  # type: ignore[assignment]
    last_reviewed: datetime | None = None
    id: int | None = None

    @property
    def state(self) -> ReviewState:
        """Return the SM-2 :class:`ReviewState` view of this item."""
        return ReviewState(
            repetitions=self.repetitions,
            ease_factor=self.ease_factor,
            interval=self.interval,
        )


def _row_to_item(row: sqlite3.Row) -> StudyItem:
    """Map a database row to a :class:`StudyItem`."""
    last = row["last_reviewed"]
    return StudyItem(
        id=row["id"],
        front=row["front"],
        back=row["back"],
        repetitions=row["repetitions"],
        ease_factor=row["ease_factor"],
        interval=row["interval"],
        due_date=date.fromisoformat(row["due_date"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        last_reviewed=datetime.fromisoformat(last) if last else None,
    )


class Storage:
    """A SQLite-backed repository of :class:`StudyItem` records.

    Args:
        path: Filesystem path to the SQLite database. Use :data:`MEMORY` for a
            private in-memory database (the connection is kept open for the
            lifetime of the instance so the data survives between calls).
    """

    def __init__(self, path: str | Path = MEMORY) -> None:
        self._path = str(path)
        self._shared: sqlite3.Connection | None = None
        if self._path == MEMORY:
            # An in-memory DB only lives as long as its connection; hold one open.
            self._shared = self._connect()
            self._init_schema(self._shared)
        else:
            db_path = Path(self._path)
            if db_path.parent and not db_path.parent.exists():
                db_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connection() as conn:
                self._init_schema(conn)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _init_schema(conn: sqlite3.Connection) -> None:
        conn.executescript(_SCHEMA)
        conn.commit()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection, committing on success.

        For an in-memory database the single shared connection is reused; for a
        file database a fresh connection is opened and closed per operation.
        """
        if self._shared is not None:
            yield self._shared
            self._shared.commit()
            return
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def add(self, item: StudyItem) -> StudyItem:
        """Insert ``item`` and return it with its assigned ``id``.

        ``created_at`` and ``due_date`` are filled in with sensible defaults
        (now / today) when not already set.
        """
        if item.created_at is None:
            item.created_at = datetime.now()
        if item.due_date is None:
            item.due_date = item.created_at.date()
        with self._connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO items
                    (front, back, repetitions, ease_factor, interval,
                     due_date, created_at, last_reviewed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.front,
                    item.back,
                    item.repetitions,
                    item.ease_factor,
                    item.interval,
                    item.due_date.isoformat(),
                    item.created_at.isoformat(),
                    item.last_reviewed.isoformat() if item.last_reviewed else None,
                ),
            )
            item.id = int(cur.lastrowid or 0)
        return item

    def get(self, item_id: int) -> StudyItem | None:
        """Return the item with ``item_id``, or ``None`` if it does not exist."""
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return _row_to_item(row) if row else None

    def list_all(self) -> list[StudyItem]:
        """Return every item ordered by due date then id."""
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM items ORDER BY due_date ASC, id ASC").fetchall()
        return [_row_to_item(r) for r in rows]

    def list_due(self, on: date | None = None) -> list[StudyItem]:
        """Return items due on or before ``on`` (default: today).

        Args:
            on: The reference date; defaults to ``date.today()``.
        """
        on = on or date.today()
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM items WHERE due_date <= ? ORDER BY due_date ASC, id ASC",
                (on.isoformat(),),
            ).fetchall()
        return [_row_to_item(r) for r in rows]

    def update(self, item: StudyItem) -> None:
        """Persist changes to an existing (already-inserted) ``item``.

        Raises:
            ValueError: If ``item.id`` is ``None``.
        """
        if item.id is None:
            raise ValueError("cannot update an item without an id")
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE items
                   SET front = ?, back = ?, repetitions = ?, ease_factor = ?,
                       interval = ?, due_date = ?, last_reviewed = ?
                 WHERE id = ?
                """,
                (
                    item.front,
                    item.back,
                    item.repetitions,
                    item.ease_factor,
                    item.interval,
                    item.due_date.isoformat(),
                    item.last_reviewed.isoformat() if item.last_reviewed else None,
                    item.id,
                ),
            )

    def delete(self, item_id: int) -> bool:
        """Delete the item with ``item_id``.

        Returns:
            ``True`` if a row was deleted, ``False`` if no such item existed.
        """
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        return cur.rowcount > 0

    def count(self) -> int:
        """Return the total number of stored items."""
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM items").fetchone()
        return int(row["n"])

    def close(self) -> None:
        """Close the shared in-memory connection, if any."""
        if self._shared is not None:
            self._shared.close()
            self._shared = None
