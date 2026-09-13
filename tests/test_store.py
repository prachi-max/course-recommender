"""Tests for the SQLite-backed profile store (webapp/store.py)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from webapp import store  # noqa: E402


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "test.db")
    store.init_db()
    yield


def test_create_and_get_profile(temp_db):
    pid = store.create_profile("Alex", ["python", "Data Science"], "Beginner")
    profile = store.get_profile(pid)
    assert profile["name"] == "Alex"
    assert profile["interests"] == ["python", "Data Science"]
    assert profile["skill_level"] == "Beginner"


def test_set_and_get_course_status(temp_db):
    pid = store.create_profile("Alex", ["python"], None)
    store.set_course_status(pid, 5, "known")
    store.set_course_status(pid, 6, "in_progress")
    statuses = store.get_course_statuses(pid)
    assert statuses == {5: "known", 6: "in_progress"}


def test_set_course_status_upserts(temp_db):
    pid = store.create_profile("Alex", ["python"], None)
    store.set_course_status(pid, 5, "known")
    store.set_course_status(pid, 5, "completed")  # change status, same course
    statuses = store.get_course_statuses(pid)
    assert statuses == {5: "completed"}


def test_set_course_status_none_removes(temp_db):
    pid = store.create_profile("Alex", ["python"], None)
    store.set_course_status(pid, 5, "known")
    store.set_course_status(pid, 5, None)
    assert store.get_course_statuses(pid) == {}


def test_delete_profile_cascades_courses(temp_db):
    pid = store.create_profile("Alex", ["python"], None)
    store.set_course_status(pid, 5, "known")
    store.delete_profile(pid)
    assert store.get_profile(pid) is None
    assert store.get_course_statuses(pid) == {}


def test_add_and_get_reviews(temp_db):
    store.add_review(5, None, "Alex", 5, "Really clear explanations.")
    store.add_review(5, None, "Sam", 3, "Decent, a bit slow paced.")
    reviews = store.get_reviews_for_course(5)
    assert len(reviews) == 2
    assert {r["reviewer_name"] for r in reviews} == {"Alex", "Sam"}
    assert all(1 <= r["rating"] <= 5 for r in reviews)


def test_reviews_are_scoped_to_their_course(temp_db):
    store.add_review(5, None, "Alex", 5, "Great course.")
    store.add_review(6, None, "Sam", 4, "Also good.")
    assert len(store.get_reviews_for_course(5)) == 1
    assert len(store.get_reviews_for_course(6)) == 1
