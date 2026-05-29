"""Web smoke tests via FastAPI's TestClient.

Skipped automatically if the optional web stack (FastAPI / httpx) is not
installed, so the core test suite never depends on it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="web extra not installed")
pytest.importorskip("httpx", reason="TestClient needs httpx")

from fastapi.testclient import TestClient  # noqa: E402

from ebbinghaus_reviewer.web import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    app = create_app(tmp_path / "web.db")
    return TestClient(app)


def test_healthz(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_index_empty(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "caught up" in resp.text


def test_add_card_then_listed(client: TestClient) -> None:
    resp = client.post("/cards", data={"front": "web question", "back": "web answer"})
    assert resp.status_code == 200  # followed the redirect to /cards
    assert "web question" in resp.text
    assert "web answer" in resp.text


def test_add_card_ignores_blank_front(client: TestClient) -> None:
    client.post("/cards", data={"front": "   ", "back": "x"})
    cards = client.get("/cards")
    assert "No cards yet" in cards.text


def test_review_flow(client: TestClient) -> None:
    client.post("/cards", data={"front": "grade me", "back": "ok"})

    review_page = client.get("/review")
    assert review_page.status_code == 200
    assert "grade me" in review_page.text

    submit = client.post("/review/1", data={"quality": "5"})
    assert submit.status_code == 200  # redirected back to /review

    # After grading, the card is scheduled forward and nothing is due.
    after = client.get("/review")
    assert "caught up" in after.text


def test_review_quality_is_clamped(client: TestClient) -> None:
    client.post("/cards", data={"front": "clamp", "back": ""})
    # Out-of-range quality should not 500; it gets clamped to a valid grade.
    resp = client.post("/review/1", data={"quality": "99"})
    assert resp.status_code == 200


def test_review_unknown_id_is_safe(client: TestClient) -> None:
    resp = client.post("/review/999", data={"quality": "5"})
    assert resp.status_code == 200


def test_delete_card(client: TestClient) -> None:
    client.post("/cards", data={"front": "delete me", "back": ""})
    resp = client.post("/cards/1/delete")
    assert resp.status_code == 200
    assert "delete me" not in resp.text


def test_index_shows_due_count(client: TestClient) -> None:
    client.post("/cards", data={"front": "due card", "back": ""})
    resp = client.get("/")
    assert "due card" in resp.text
