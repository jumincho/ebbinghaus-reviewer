"""Tests for SQLite-backed persistence."""

from __future__ import annotations

from datetime import datetime, timedelta

from ebbinghaus_reviewer.models import Card, Review
from ebbinghaus_reviewer.storage import Storage, default_db_path


def make_card(front: str = "Q?", **kw: object) -> Card:
    now = datetime(2026, 1, 1, 12, 0, 0)
    base = dict(
        id=None,
        front=front,
        back="A.",
        tags=["psych"],
        created_at=now,
        repetition=0,
        ease_factor=2.5,
        interval_days=0,
        next_review_at=now,
    )
    base.update(kw)  # type: ignore[arg-type]
    return Card(**base)  # type: ignore[arg-type]


# --- Cards CRUD --------------------------------------------------------


def test_add_card_assigns_id(storage: Storage) -> None:
    card = storage.add_card(make_card())
    assert card.id is not None and card.id > 0


def test_get_card_round_trip(storage: Storage) -> None:
    saved = storage.add_card(make_card(front="What?"))
    fetched = storage.get_card(saved.id)  # type: ignore[arg-type]
    assert fetched is not None
    assert fetched.front == "What?"
    assert fetched.tags == ["psych"]
    assert fetched.ease_factor == 2.5


def test_get_card_missing(storage: Storage) -> None:
    assert storage.get_card(9999) is None


def test_list_cards_orders_by_id(storage: Storage) -> None:
    a = storage.add_card(make_card(front="A"))
    b = storage.add_card(make_card(front="B"))
    cards = storage.list_cards()
    assert [c.id for c in cards] == [a.id, b.id]


def test_list_cards_filter_by_tag(storage: Storage) -> None:
    storage.add_card(make_card(front="psych card", tags=["psych"]))
    storage.add_card(make_card(front="algo card", tags=["algo"]))
    storage.add_card(make_card(front="both", tags=["psych", "algo"]))

    psych = storage.list_cards(tag="psych")
    algo = storage.list_cards(tag="algo")
    assert {c.front for c in psych} == {"psych card", "both"}
    assert {c.front for c in algo} == {"algo card", "both"}


def test_list_cards_tag_filter_does_not_substring_match(storage: Storage) -> None:
    """tag='al' must NOT match tag 'algo' to avoid false positives."""
    storage.add_card(make_card(tags=["algo"]))
    storage.add_card(make_card(tags=["al"]))
    cards = storage.list_cards(tag="al")
    assert len(cards) == 1
    assert cards[0].tags == ["al"]


def test_delete_card_removes_it(storage: Storage) -> None:
    card = storage.add_card(make_card())
    assert storage.delete_card(card.id) is True  # type: ignore[arg-type]
    assert storage.get_card(card.id) is None  # type: ignore[arg-type]


def test_delete_card_missing_returns_false(storage: Storage) -> None:
    assert storage.delete_card(9999) is False


def test_delete_card_cascades_reviews(storage: Storage) -> None:
    card = storage.add_card(make_card())
    storage.add_review(
        Review(
            id=None,
            card_id=card.id,  # type: ignore[arg-type]
            reviewed_at=datetime(2026, 1, 2, 12, 0, 0),
            quality=5,
            interval_days_before=0,
            interval_days_after=1,
            ease_factor_after=2.6,
        )
    )
    assert storage.review_count() == 1
    storage.delete_card(card.id)  # type: ignore[arg-type]
    assert storage.review_count() == 0


# --- Schedule updates ---------------------------------------------------


def test_update_card_schedule(storage: Storage) -> None:
    card = storage.add_card(make_card())
    next_at = datetime(2026, 1, 8, 12, 0, 0)
    storage.update_card_schedule(
        card.id,  # type: ignore[arg-type]
        repetition=2,
        ease_factor=2.6,
        interval_days=6,
        next_review_at=next_at,
    )
    refreshed = storage.get_card(card.id)  # type: ignore[arg-type]
    assert refreshed is not None
    assert refreshed.repetition == 2
    assert refreshed.ease_factor == 2.6
    assert refreshed.interval_days == 6
    assert refreshed.next_review_at == next_at


# --- Due query ----------------------------------------------------------


def test_due_cards_returns_only_past_due(storage: Storage) -> None:
    now = datetime(2026, 1, 5, 12, 0, 0)
    due_card = storage.add_card(make_card(front="due", next_review_at=now - timedelta(hours=1)))
    future_card = storage.add_card(
        make_card(front="future", next_review_at=now + timedelta(days=3))
    )
    due = storage.due_cards(before=now)
    assert [c.id for c in due] == [due_card.id]
    assert future_card.id not in [c.id for c in due]


# --- Reviews -----------------------------------------------------------


def test_add_review_assigns_id_and_lists(storage: Storage) -> None:
    card = storage.add_card(make_card())
    review = storage.add_review(
        Review(
            id=None,
            card_id=card.id,  # type: ignore[arg-type]
            reviewed_at=datetime(2026, 1, 2, 12, 0, 0),
            quality=4,
            interval_days_before=0,
            interval_days_after=1,
            ease_factor_after=2.5,
        )
    )
    assert review.id is not None
    listed = storage.list_reviews(card_id=card.id)  # type: ignore[arg-type]
    assert len(listed) == 1
    assert listed[0].quality == 4


# --- Counts -----------------------------------------------------------


def test_counts(storage: Storage) -> None:
    assert storage.card_count() == 0
    assert storage.review_count() == 0
    assert storage.due_count(datetime(2026, 1, 1)) == 0

    card = storage.add_card(make_card())
    assert storage.card_count() == 1
    assert storage.due_count(datetime(2026, 1, 2)) == 1

    storage.add_review(
        Review(
            id=None,
            card_id=card.id,  # type: ignore[arg-type]
            reviewed_at=datetime(2026, 1, 2),
            quality=5,
            interval_days_before=0,
            interval_days_after=1,
            ease_factor_after=2.6,
        )
    )
    assert storage.review_count() == 1


# --- Env-var path override --------------------------------------------


def test_default_db_path_env_override(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "elsewhere" / "x.sqlite"
    monkeypatch.setenv("EBBINGHAUS_DB_PATH", str(target))
    assert default_db_path() == target


def test_default_db_path_without_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("EBBINGHAUS_DB_PATH", raising=False)
    p = default_db_path()
    assert p.name == "db.sqlite"
    assert p.parent.name == ".ebbinghaus"
