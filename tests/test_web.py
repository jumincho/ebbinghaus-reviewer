from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from ebbinghaus_reviewer import Grade, Repository, Reviewer, __version__
from ebbinghaus_reviewer.web import create_app
from tests.conftest import KST, FakeClock


@pytest.fixture
def db(tmp_path: Path) -> Path:
    return tmp_path / "web.sqlite3"


@pytest.fixture
def client(db: Path, clock: FakeClock) -> TestClient:
    return TestClient(create_app(db, clock=clock, tz=KST))


@pytest.fixture
def reviewer(db: Path, clock: FakeClock) -> Iterator[Reviewer]:
    """A second connection to the served database, for arranging and asserting."""
    with Repository(db) as repository:
        yield Reviewer(repository, clock=clock, tz=KST)


def test_health_and_static_assets(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok", "version": __version__}
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/icon.svg").headers["content-type"].startswith("image/svg")


def test_empty_pages(client: TestClient) -> None:
    today = client.get("/")
    assert today.status_code == 200
    assert "All caught up." in today.text
    assert "Nothing is scheduled yet." in client.get("/review").text
    assert "No items" in client.get("/items").text
    assert "Nothing scheduled in this period." in client.get("/agenda").text


def test_add_review_and_grade(client: TestClient, clock: FakeClock) -> None:
    added = client.post(
        "/items", data={"title": "Krebs cycle", "notes": "eight steps", "subject": "Biology"}
    )
    assert added.status_code == 200  # redirected to /items
    assert "Krebs cycle" in added.text
    assert "Next review:" in client.get("/").text

    clock.advance(timedelta(minutes=10))
    page = client.get("/review")
    assert "Krebs cycle" in page.text
    assert "eight steps" in page.text
    for grade in Grade:
        assert f'value="{grade.value}"' in page.text

    graded = client.post("/items/1/grade", data={"grade": "good"}, follow_redirects=False)
    assert graded.status_code == 303
    assert graded.headers["location"] == "/review"
    assert "All caught up" in client.get("/review").text


def test_review_can_be_limited_to_a_subject(
    client: TestClient, reviewer: Reviewer, clock: FakeClock
) -> None:
    reviewer.add("biology item", subject="Biology", studied_at=clock.moment - timedelta(hours=1))
    reviewer.add("history item", subject="History", studied_at=clock.moment - timedelta(hours=1))
    page = client.get("/review", params={"subject": "History"})
    assert "history item" in page.text
    assert "biology item" not in page.text
    assert 'value="/review?subject=History"' in page.text


def test_grade_redirects_only_to_local_paths(client: TestClient, reviewer: Reviewer) -> None:
    reviewer.add("x")
    for target in ("https://example.com", "//example.com", "/\\example.com"):
        response = client.post(
            "/items/1/grade", data={"grade": "good", "next": target}, follow_redirects=False
        )
        assert response.headers["location"] == "/review"
    response = client.post(
        "/items/1/grade", data={"grade": "good", "next": "/items/1"}, follow_redirects=False
    )
    assert response.headers["location"] == "/items/1"


def test_invalid_input(client: TestClient) -> None:
    blank = client.post("/items", data={"title": "   ", "notes": "kept"})
    assert blank.status_code == 400
    assert "title must not be empty" in blank.text
    assert "kept" in blank.text  # the draft is preserved
    assert client.post("/items/1/grade", data={"grade": "perfect"}).status_code == 422
    missing = client.get("/items/99")
    assert missing.status_code == 404
    assert "There is no item #99." in missing.text
    assert client.post("/items/99/grade", data={"grade": "good"}).status_code == 404


def test_item_page_edit_restart_delete(
    client: TestClient, reviewer: Reviewer, clock: FakeClock
) -> None:
    item = reviewer.add("Treaty", subject="History")
    clock.advance(timedelta(minutes=10))
    reviewer.grade(item.id, Grade.GOOD)

    page = client.get(f"/items/{item.id}")
    assert page.status_code == 200
    assert "<svg" in page.text
    assert "Estimated recall is 100% now" in page.text
    assert "ladder · step 2 of 4" in page.text

    edited = client.post(
        f"/items/{item.id}", data={"title": "Treaty of Westphalia", "notes": "1648", "subject": ""}
    )
    assert "Treaty of Westphalia" in edited.text
    assert reviewer.get(item.id).subject is None
    bad_edit = client.post(f"/items/{item.id}", data={"title": " "})
    assert bad_edit.status_code == 400

    client.post(f"/items/{item.id}/restart", data={"strategy": "sm2"})
    assert reviewer.get(item.id).schedule.strategy.value == "sm2"
    client.post(f"/items/{item.id}/restart", data={"strategy": ""})
    assert reviewer.get(item.id).schedule.strategy.value == "sm2"

    deleted = client.post(f"/items/{item.id}/delete", follow_redirects=False)
    assert deleted.headers["location"] == "/items"
    assert reviewer.items() == []


def test_mastered_item_has_no_chart(client: TestClient, reviewer: Reviewer) -> None:
    item = reviewer.add("done")
    reviewer.grade(item.id, Grade.EASY)
    reviewer.grade(item.id, Grade.EASY)
    page = client.get(f"/items/{item.id}")
    assert "mastered" in page.text
    assert "<svg" not in page.text


def test_lists_and_agenda(client: TestClient, reviewer: Reviewer, clock: FakeClock) -> None:
    reviewer.add("overdue", subject="A", studied_at=clock.moment - timedelta(days=1))
    reviewer.add("later", subject="B")
    today = client.get("/")
    assert "1 item due for review." in today.text
    assert "overdue" in today.text
    filtered = client.get("/items", params={"subject": "B"})
    assert "later" in filtered.text
    assert "overdue" not in filtered.text.split("<tbody>")[1]
    agenda = client.get("/agenda", params={"days": 3})
    assert "Today" in agenda.text
    assert "overdue" in agenda.text
    assert client.get("/agenda", params={"days": 0}).status_code == 422
