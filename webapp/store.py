"""SQLite-backed storage for user profiles and their learning history.

No real accounts/passwords - see README for why. A profile is identified by
a random id kept in a browser cookie (see app.py's get_current_profile()).
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "webapp" / "app.db"

STATUSES = ("known", "in_progress", "completed", "saved")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                interests_json TEXT NOT NULL,
                skill_level TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profile_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                course_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                added_at TEXT NOT NULL,
                UNIQUE(profile_id, course_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                profile_id TEXT,
                reviewer_name TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_profile(name: str, interests: list[str], skill_level: str | None) -> str:
    profile_id = uuid.uuid4().hex
    with _connect() as conn:
        conn.execute(
            "INSERT INTO profiles (id, name, interests_json, skill_level, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (profile_id, name, json.dumps(interests), skill_level, _now(), _now()),
        )
    return profile_id


def update_profile(profile_id: str, name: str, interests: list[str], skill_level: str | None) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE profiles SET name = ?, interests_json = ?, skill_level = ?, updated_at = ? WHERE id = ?",
            (name, json.dumps(interests), skill_level, _now(), profile_id),
        )
        return cur.rowcount > 0


def get_profile(profile_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "interests": json.loads(row["interests_json"]),
            "skill_level": row["skill_level"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def delete_profile(profile_id: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.execute("DELETE FROM profile_courses WHERE profile_id = ?", (profile_id,))


def set_course_status(profile_id: str, course_id: int, status: str | None) -> None:
    """status=None removes the course from the profile's learning history."""
    with _connect() as conn:
        if status is None:
            conn.execute("DELETE FROM profile_courses WHERE profile_id = ? AND course_id = ?", (profile_id, course_id))
            return
        conn.execute(
            """
            INSERT INTO profile_courses (profile_id, course_id, status, added_at) VALUES (?, ?, ?, ?)
            ON CONFLICT(profile_id, course_id) DO UPDATE SET status = excluded.status
            """,
            (profile_id, course_id, status, _now()),
        )


def get_course_statuses(profile_id: str) -> dict[int, str]:
    """course_id -> status, for every course in this profile's history."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT course_id, status FROM profile_courses WHERE profile_id = ?", (profile_id,)
        ).fetchall()
        return {int(r["course_id"]): r["status"] for r in rows}


def get_courses_by_status(profile_id: str) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {s: [] for s in STATUSES}
    with _connect() as conn:
        rows = conn.execute(
            "SELECT course_id, status FROM profile_courses WHERE profile_id = ? ORDER BY added_at DESC",
            (profile_id,),
        ).fetchall()
    for r in rows:
        out.setdefault(r["status"], []).append(int(r["course_id"]))
    return out


# --------------------------------------------------------------- reviews ----
# Learner-written reviews, local to this site only - never confused with the
# course's real Coursera rating shown elsewhere. Nothing is pre-seeded here;
# a course simply has no reviews until an actual visitor leaves one.

MAX_RATING = 5
MIN_RATING = 1


def add_review(course_id: int, profile_id: str | None, reviewer_name: str, rating: int, comment: str) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO reviews (course_id, profile_id, reviewer_name, rating, comment, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (course_id, profile_id, reviewer_name, rating, comment, _now()),
        )
        return int(cur.lastrowid)


def get_reviews_for_course(course_id: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, reviewer_name, rating, comment, created_at FROM reviews WHERE course_id = ? ORDER BY created_at DESC",
            (course_id,),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "reviewer_name": r["reviewer_name"],
            "rating": int(r["rating"]),
            "comment": r["comment"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
