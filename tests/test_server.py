"""Tests for the FastAPI web UI."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ebbinghaus_reviewer.storage import Storage
from ebbinghaus_reviewer.web.server import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    storage = Storage(tmp_path / "web.sqlite")
    app = create_app(storage=storage)
    with TestClient(app) as c:
        yield c
    storage.close()


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_index_empty(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "caught up" in r.text.lower()


def test_create_and_list_card(client: TestClient) -> None:
    r = client.post(
        "/cards",
        data={"front": "What is the Ebbinghaus curve?", "back": "Memory decays.", "tags": "psych, memory"},
        follow_redirects=False,
    )
    # Redirect response with HX-Redirect header.
    assert r.status_code == 303

    listing = client.get("/cards")
    assert listing.status_code == 200
    assert "Ebbinghaus curve" in listing.text
    assert "psych" in listing.text


def test_create_card_requires_front(client: TestClient) -> None:
    r = client.post("/cards", data={"front": "", "back": "", "tags": ""}, follow_redirects=False)
    assert r.status_code == 400


def test_review_flow(client: TestClient) -> None:
    client.post("/cards", data={"front": "Q?", "back": "A.", "tags": ""}, follow_redirects=False)

    page = client.get("/cards/1/review")
    assert page.status_code == 200
    assert "Q?" in page.text
    assert "A." in page.text

    done = client.post("/cards/1/review", data={"quality": "5"})
    assert done.status_code == 200
    assert "saved" in done.text.lower()


def test_review_invalid_quality(client: TestClient) -> None:
    client.post("/cards", data={"front": "Q?"}, follow_redirects=False)
    r = client.post("/cards/1/review", data={"quality": "9"})
    assert r.status_code == 400


def test_review_missing_card(client: TestClient) -> None:
    r = client.get("/cards/9999/review")
    assert r.status_code == 404


def test_delete_card(client: TestClient) -> None:
    client.post("/cards", data={"front": "Q?"}, follow_redirects=False)
    r = client.post("/cards/1/delete", follow_redirects=False)
    assert r.status_code == 303

    listing = client.get("/cards")
    assert "Q?" not in listing.text


def test_delete_missing_card(client: TestClient) -> None:
    r = client.post("/cards/9999/delete", follow_redirects=False)
    assert r.status_code == 404


def test_stats(client: TestClient) -> None:
    client.post("/cards", data={"front": "Q1"}, follow_redirects=False)
    client.post("/cards", data={"front": "Q2"}, follow_redirects=False)
    r = client.get("/stats")
    assert r.status_code == 200
    assert "Total cards" in r.text
    assert ">2<" in r.text  # Rendered as the big number


def test_index_shows_due_card(client: TestClient) -> None:
    client.post("/cards", data={"front": "Due Q"}, follow_redirects=False)
    r = client.get("/")
    assert r.status_code == 200
    assert "Due Q" in r.text
    assert "Review" in r.text


def test_filter_cards_by_tag(client: TestClient) -> None:
    client.post("/cards", data={"front": "P", "tags": "psych"}, follow_redirects=False)
    client.post("/cards", data={"front": "A", "tags": "algo"}, follow_redirects=False)
    r = client.get("/cards", params={"tag": "psych"})
    assert r.status_code == 200
    assert "P" in r.text
    # The algo card should not appear in the table.
    assert "<td class=\"px-4 py-2 font-medium\">A</td>" not in r.text
