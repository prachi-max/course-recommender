"""Tests for the content-based recommender (src/recommender.py)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.recommender import get_index  # noqa: E402


def test_catalog_loads_real_courses():
    idx = get_index()
    assert len(idx.courses) > 100


def test_similar_courses_excludes_itself():
    idx = get_index()
    web_dev_id = next(c["course_id"] for c in idx.courses.to_dict("records") if c["category"] == "Web Development")
    similar = idx.similar_courses(web_dev_id, top_n=5)
    assert all(c["course_id"] != web_dev_id for c in similar)
    assert len(similar) == 5


def test_similar_courses_are_topically_related():
    idx = get_index()
    web_dev_id = next(c["course_id"] for c in idx.courses.to_dict("records") if c["category"] == "Web Development")
    similar = idx.similar_courses(web_dev_id, top_n=3)
    # At least one of the top matches should also be a web-flavored course.
    categories = [c["category"] for c in similar]
    assert any(cat in ("Web Development", "Cloud Computing", "DevOps & SRE") for cat in categories)


def test_recommend_for_interests_ranks_relevant_courses_first():
    idx = get_index()
    recs = idx.recommend_for_profile(interests=["cybersecurity"], skill_level=None, known_course_ids=[])
    assert recs, "expected at least one recommendation"
    assert recs[0]["category"] == "Cybersecurity"
    assert recs[0]["match_pct"] > 0


def test_recommend_excludes_known_courses():
    idx = get_index()
    recs = idx.recommend_for_profile(interests=["python"], skill_level=None, known_course_ids=[25])
    assert all(r["course_id"] != 25 for r in recs)


def test_recommend_with_no_signal_falls_back_to_popular():
    idx = get_index()
    recs = idx.recommend_for_profile(interests=[], skill_level=None, known_course_ids=[])
    assert recs
    assert all(r["match_pct"] is None for r in recs)
    assert all(r["why"] == "Popular on the platform" for r in recs)
