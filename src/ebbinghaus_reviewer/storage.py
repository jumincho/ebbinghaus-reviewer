"""SQLite persistence for items and their review history.

A :class:`Repository` owns one connection to one database file (or a private
in-memory database). The schema is versioned with ``PRAGMA user_version`` and
upgraded by forward-only migrations when a database is opened.

Timestamps are stored as ISO-8601 UTC strings with second precision
(``2026-09-23T07:30:00+00:00``), which also makes them sort correctly as text.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import TracebackType

from ebbinghaus_reviewer.models import Item, Review
from ebbinghaus_reviewer.scheduling import Grade, Schedule, Strategy

__all__ = ["MEMORY", "SCHEMA_VERSION", "DatabaseError", "Repository"]

MEMORY = ":memory:"
"""Pass as the path to get a private, in-memory database."""

_MIGRATIONS: tuple[str, ...] = (
    """
    CREATE TABLE items (
        id               INTEGER PRIMARY KEY,
        title            TEXT    NOT NULL CHECK (length(trim(title)) > 0),
        notes            TEXT    NOT NULL DEFAULT '',
        subject          TEXT,
        strategy         TEXT    NOT NULL CHECK (strategy IN ('ladder', 'sm2')),
        step             INTEGER NOT NULL CHECK (step >= 0),
        ease             REAL    NOT NULL,
        interval_seconds INTEGER NOT NULL CHECK (interval_seconds > 0),
        due_at           TEXT,
        studied_at       TEXT    NOT NULL,
        last_reviewed_at TEXT,
        created_at       TEXT    NOT NULL,
        updated_at       TEXT    NOT NULL
    );
    CREATE INDEX items_due_at ON items (due_at);
    CREATE INDEX items_subject ON items (subject);

    CREATE TABLE reviews (
        id               INTEGER PRIMARY KEY,
        item_id          INTEGER NOT NULL REFERENCES items (id) ON DELETE CASCADE,
        reviewed_at      TEXT    NOT NULL,
        grade            TEXT    NOT NULL CHECK (grade IN ('again', 'hard', 'good', 'easy')),
        scheduled_for    TEXT,
        interval_seconds INTEGER NOT NULL CHECK (interval_seconds > 0)
    );
    CREATE INDEX reviews_item ON reviews (item_id, reviewed_at);
    CREATE INDEX reviews_reviewed_at ON reviews (reviewed_at);
    """,
)

SCHEMA_VERSION = len(_MIGRATIONS)
"""The schema version this release reads and writes."""

_ITEM_SELECT = """
    SELECT items.*,
           (SELECT COUNT(*) FROM reviews WHERE reviews.item_id = items.id) AS review_count,
           (SELECT COUNT(*) FROM reviews
             WHERE reviews.item_id = items.id AND reviews.grade = 'again') AS lapse_count
      FROM items
"""


class DatabaseError(RuntimeError):
    """The database cannot be used by this version of Ebbinghaus Reviewer."""


def _to_text(moment: datetime) -> str:
    if moment.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")


def _optional_text(moment: datetime | None) -> str | None:
    return None if moment is None else _to_text(moment)


def _from_text(text: str) -> datetime:
    return datetime.fromisoformat(text)


def _optional_datetime(text: str | None) -> datetime | None:
    return None if text is None else _from_text(text)


def _seconds(interval: timedelta) -> int:
    return round(interval.total_seconds())


def _row_to_item(row: sqlite3.Row) -> Item:
    return Item(
        id=row["id"],
        title=row["title"],
        notes=row["notes"],
        subject=row["subject"],
        schedule=Schedule(
            strategy=Strategy(row["strategy"]),
            step=row["step"],
            ease=row["ease"],
            interval=timedelta(seconds=row["interval_seconds"]),
            due_at=_optional_datetime(row["due_at"]),
        ),
        studied_at=_from_text(row["studied_at"]),
        last_reviewed_at=_optional_datetime(row["last_reviewed_at"]),
        created_at=_from_text(row["created_at"]),
        updated_at=_from_text(row["updated_at"]),
        review_count=row["review_count"],
        lapse_count=row["lapse_count"],
    )


def _row_to_review(row: sqlite3.Row) -> Review:
    return Review(
        id=row["id"],
        item_id=row["item_id"],
        reviewed_at=_from_text(row["reviewed_at"]),
        grade=Grade(row["grade"]),
        scheduled_for=_optional_datetime(row["scheduled_for"]),
        interval=timedelta(seconds=row["interval_seconds"]),
    )


class Repository:
    """Items and reviews stored in one SQLite database.

    Args:
        path: Database file (parent directories are created) or
            :data:`MEMORY`. Use the repository as a context manager, or call
            :meth:`close`, to release the connection.

    Raises:
        DatabaseError: If the file cannot be opened or is not a compatible database.
    """

    def __init__(self, path: str | os.PathLike[str] = MEMORY) -> None:
        self.path = MEMORY if os.fspath(path) == MEMORY else os.fspath(Path(path).expanduser())
        try:
            if self.path != MEMORY:
                Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            # Autocommit mode: transactions are opened explicitly by transaction().
            # Connections may be handed between threads (e.g. by the web server),
            # but each repository is only ever used by one request at a time.
            self._conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        except (OSError, sqlite3.Error) as exc:
            raise DatabaseError(f"cannot open {self.path}: {exc}") from exc
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA busy_timeout = 5000")
        try:
            self._migrate()
        except DatabaseError:
            self._conn.close()
            raise
        except sqlite3.DatabaseError as exc:
            self._conn.close()
            raise DatabaseError(
                f"{self.path} is not an Ebbinghaus Reviewer database: {exc}"
            ) from exc

    def _migrate(self) -> None:
        version = int(self._conn.execute("PRAGMA user_version").fetchone()[0])
        if version > SCHEMA_VERSION:
            raise DatabaseError(
                f"{self.path} uses schema version {version}, but this release only "
                f"understands up to {SCHEMA_VERSION}; please upgrade ebbinghaus-reviewer"
            )
        for target, script in enumerate(_MIGRATIONS[version:], start=version + 1):
            # executescript() runs outside the implicit transaction machinery, so
            # the migration and its version bump are committed atomically here.
            self._conn.executescript(f"BEGIN; {script}; PRAGMA user_version = {target}; COMMIT;")

    # -- lifecycle -----------------------------------------------------------

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()

    def __enter__(self) -> Repository:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Run a block atomically; nested blocks join the outer transaction."""
        if self._conn.in_transaction:
            yield
            return
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        self._conn.execute("COMMIT")

    @property
    def schema_version(self) -> int:
        """The schema version of the open database."""
        return int(self._conn.execute("PRAGMA user_version").fetchone()[0])

    # -- items ---------------------------------------------------------------

    def insert_item(
        self,
        *,
        title: str,
        notes: str,
        subject: str | None,
        schedule: Schedule,
        studied_at: datetime,
        created_at: datetime,
        last_reviewed_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> Item:
        """Insert an item and return it with its new id."""
        cursor = self._conn.execute(
            """
            INSERT INTO items (title, notes, subject, strategy, step, ease, interval_seconds,
                               due_at, studied_at, last_reviewed_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                notes,
                subject,
                schedule.strategy.value,
                schedule.step,
                schedule.ease,
                _seconds(schedule.interval),
                _optional_text(schedule.due_at),
                _to_text(studied_at),
                _optional_text(last_reviewed_at),
                _to_text(created_at),
                _to_text(updated_at or created_at),
            ),
        )
        return self._require_item(int(cursor.lastrowid or 0))

    def update_item(self, item: Item, *, updated_at: datetime) -> Item:
        """Persist every mutable field of ``item`` and return the stored version."""
        cursor = self._conn.execute(
            """
            UPDATE items
               SET title = ?, notes = ?, subject = ?, strategy = ?, step = ?, ease = ?,
                   interval_seconds = ?, due_at = ?, studied_at = ?, last_reviewed_at = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                item.title,
                item.notes,
                item.subject,
                item.schedule.strategy.value,
                item.schedule.step,
                item.schedule.ease,
                _seconds(item.schedule.interval),
                _optional_text(item.schedule.due_at),
                _to_text(item.studied_at),
                _optional_text(item.last_reviewed_at),
                _to_text(updated_at),
                item.id,
            ),
        )
        if cursor.rowcount == 0:
            raise LookupError(f"no item with id {item.id}")
        return self._require_item(item.id)

    def delete_item(self, item_id: int) -> bool:
        """Delete an item and its reviews; return whether it existed."""
        cursor = self._conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        return cursor.rowcount > 0

    def get_item(self, item_id: int) -> Item | None:
        """Return the item with ``item_id``, or ``None``."""
        row = self._conn.execute(f"{_ITEM_SELECT} WHERE items.id = ?", (item_id,)).fetchone()
        return None if row is None else _row_to_item(row)

    def _require_item(self, item_id: int) -> Item:
        item = self.get_item(item_id)
        if item is None:  # pragma: no cover - only reachable through a race
            raise LookupError(f"no item with id {item_id}")
        return item

    def list_items(
        self, *, subject: str | None = None, include_mastered: bool = True
    ) -> list[Item]:
        """Return items ordered by due time (mastered items last)."""
        clauses: list[str] = []
        params: list[object] = []
        if subject is not None:
            clauses.append("items.subject = ?")
            params.append(subject)
        if not include_mastered:
            clauses.append("items.due_at IS NOT NULL")
        return self._select_items(clauses, params, order="items.due_at IS NULL, items.due_at")

    def items_due_before(
        self, moment: datetime, *, subject: str | None = None, inclusive: bool = True
    ) -> list[Item]:
        """Return items due at or before ``moment`` (or strictly before), earliest first."""
        clauses = ["items.due_at IS NOT NULL", f"items.due_at {'<=' if inclusive else '<'} ?"]
        params: list[object] = [_to_text(moment)]
        if subject is not None:
            clauses.append("items.subject = ?")
            params.append(subject)
        return self._select_items(clauses, params, order="items.due_at")

    def _select_items(
        self, clauses: Sequence[str], params: Sequence[object], *, order: str
    ) -> list[Item]:
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._conn.execute(f"{_ITEM_SELECT}{where} ORDER BY {order}, items.id", params)
        return [_row_to_item(row) for row in rows]

    def subjects(self) -> list[str]:
        """Return the distinct subjects in use, alphabetically."""
        rows = self._conn.execute(
            "SELECT DISTINCT subject FROM items WHERE subject IS NOT NULL "
            "ORDER BY subject COLLATE NOCASE"
        )
        return [row["subject"] for row in rows]

    # -- reviews -------------------------------------------------------------

    def insert_review(
        self,
        *,
        item_id: int,
        reviewed_at: datetime,
        grade: Grade,
        scheduled_for: datetime | None,
        interval: timedelta,
    ) -> Review:
        """Record a review and return it with its new id."""
        cursor = self._conn.execute(
            """
            INSERT INTO reviews (item_id, reviewed_at, grade, scheduled_for, interval_seconds)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                item_id,
                _to_text(reviewed_at),
                grade.value,
                _optional_text(scheduled_for),
                _seconds(interval),
            ),
        )
        row = self._conn.execute(
            "SELECT * FROM reviews WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return _row_to_review(row)

    def reviews_for(self, item_id: int) -> list[Review]:
        """Return the review history of an item, oldest first."""
        rows = self._conn.execute(
            "SELECT * FROM reviews WHERE item_id = ? ORDER BY reviewed_at, id", (item_id,)
        )
        return [_row_to_review(row) for row in rows]

    def reviews_since(self, moment: datetime) -> list[Review]:
        """Return every review at or after ``moment``, oldest first."""
        rows = self._conn.execute(
            "SELECT * FROM reviews WHERE reviewed_at >= ? ORDER BY reviewed_at, id",
            (_to_text(moment),),
        )
        return [_row_to_review(row) for row in rows]

    def review_times(self) -> list[datetime]:
        """Return the timestamp of every review, oldest first."""
        rows = self._conn.execute("SELECT reviewed_at FROM reviews ORDER BY reviewed_at")
        return [_from_text(row["reviewed_at"]) for row in rows]
