"""Flask frontend for the Course Recommendation System.

Run with:
    python -m webapp.app
from the project root. Open http://127.0.0.1:5057
"""
from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.recommender import (  # noqa: E402
    all_categories,
    all_courses_as_dicts,
    get_course,
    get_index,
)
from webapp import store  # noqa: E402
from webapp.icons import CATEGORY_ICON, icon_svg  # noqa: E402

app = Flask(__name__)
app.jinja_env.globals["icon"] = icon_svg
store.init_db()

# A curated, manageable set of specific skills for the onboarding chip
# picker - all_skills() alone returns 150+ near-duplicate variations
# (one course's skills column split apart), too many to show as chips.
POPULAR_SKILLS = [
    "python", "javascript", "sql", "react", "html", "css",
    "aws", "gcp", "cloud computing", "kubernetes", "devops", "git",
    "machine learning", "deep learning", "tensorflow", "data analysis",
    "ui/ux", "product management", "agile", "project management",
    "cybersecurity", "android", "ios", "excel",
]

PROFILE_COOKIE = "profile_id"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year

# Curated career tracks for the Career Path / skill-gap tool. Skills listed
# are drawn only from tags that actually appear in the real course catalog
# (see all_skills()), so every "missing skill" below is guaranteed to have
# at least one real course that can close the gap.
CAREER_TRACKS = {
    "Frontend Developer": {"icon": CATEGORY_ICON["Web Development"], "category": "Web Development",
                            "skills": ["html", "css", "javascript", "react", "responsive design"]},
    "Data Analyst": {"icon": CATEGORY_ICON["Data Science"], "category": "Data Science",
                      "skills": ["sql", "data analysis", "excel", "data science", "databases"]},
    "Machine Learning Engineer": {"icon": CATEGORY_ICON["Machine Learning & AI"], "category": "Machine Learning & AI",
                                   "skills": ["python", "machine learning", "deep learning", "tensorflow", "neural networks"]},
    "Cloud Engineer": {"icon": CATEGORY_ICON["Cloud Computing"], "category": "Cloud Computing",
                        "skills": ["aws", "gcp", "cloud computing", "serverless", "devops"]},
    "Cybersecurity Analyst": {"icon": CATEGORY_ICON["Cybersecurity"], "category": "Cybersecurity",
                               "skills": ["cybersecurity", "security fundamentals"]},
    "Mobile App Developer": {"icon": CATEGORY_ICON["Mobile Development"], "category": "Mobile Development",
                              "skills": ["android", "ios", "swift", "kotlin", "mobile development"]},
    "DevOps Engineer": {"icon": CATEGORY_ICON["DevOps & SRE"], "category": "DevOps & SRE",
                         "skills": ["devops", "kubernetes", "ci/cd", "git", "automation", "sre"]},
    "Product Manager": {"icon": CATEGORY_ICON["Business & Product Management"], "category": "Business & Product Management",
                         "skills": ["product management", "agile", "project management", "business strategy"]},
    "UX/UI Designer": {"icon": CATEGORY_ICON["UI/UX Design"], "category": "UI/UX Design",
                        "skills": ["ui/ux", "ux", "ui design", "design thinking", "interaction design"]},
}


# ------------------------------------------------------------- profile ----

def get_current_profile() -> dict | None:
    pid = request.cookies.get(PROFILE_COOKIE)
    if not pid:
        return None
    return store.get_profile(pid)


@app.context_processor
def inject_profile():
    return {"current_profile": get_current_profile()}


def _attach_status(course: dict, statuses: dict[int, str]) -> dict:
    return {**course, "status": statuses.get(course["course_id"])}


# ---------------------------------------------------------------- pages ----

@app.route("/")
def browse():
    category = request.args.get("category") or ""
    level = request.args.get("level") or ""
    q = request.args.get("q") or ""
    courses = _filter_courses(category, level, q)

    profile = get_current_profile()
    statuses = store.get_course_statuses(profile["id"]) if profile else {}
    courses = [_attach_status(c, statuses) for c in courses]

    all_courses = all_courses_as_dicts()

    # "Explore by Category" module - real per-category counts from the catalog.
    counts_by_cat: dict[str, int] = {}
    for c in all_courses:
        counts_by_cat[c["category"]] = counts_by_cat.get(c["category"], 0) + 1
    category_counts = sorted(
        ({"category": c, "count": counts_by_cat.get(c, 0)} for c in all_categories()),
        key=lambda r: -r["count"],
    )

    # "Recommended for You" home teaser - reuses the same TF-IDF ranking as
    # the /recommendations page when a profile exists; otherwise falls back
    # to the catalog's real top-rated courses (no invented match score).
    home_why = None
    if profile:
        idx = get_index()
        known_ids = list(statuses.keys())
        home_recs = idx.recommend_for_profile(
            interests=profile["interests"],
            skill_level=profile["skill_level"],
            known_course_ids=known_ids,
            top_n=4,
        )
        home_recs = [_attach_status(r, statuses) for r in home_recs]
        if profile["interests"] or profile["skill_level"]:
            home_why = {"interests": profile["interests"][:6], "skill_level": profile["skill_level"]}
    else:
        home_recs = sorted(all_courses, key=lambda c: (-c["rating"], -c["students"]))[:4]

    # "Continue Learning" teaser - real status data, most recently touched
    # in-progress / saved courses first. No fabricated completion percentage.
    continue_items = []
    if profile:
        by_status = store.get_courses_by_status(profile["id"])
        continue_ids = (by_status.get("in_progress", []) + by_status.get("saved", []))[:4]
        for cid in continue_ids:
            c = get_course(cid)
            if c:
                continue_items.append({**c, "status": statuses.get(cid)})

    # "Skills in Your Recommendations" dashboard module - a real tally of how
    # often each skill shows up across the courses just recommended above
    # (or, with no profile yet, across the whole catalog). Bar length is
    # literally that count relative to the top skill's count - not a
    # simulated mastery percentage.
    skill_counts: dict[str, int] = {}
    skill_source = home_recs if profile else all_courses
    for c in skill_source:
        for s in c.get("skills", []):
            skill_counts[s] = skill_counts.get(s, 0) + 1
    top_skills = sorted(
        ({"skill": s, "count": n} for s, n in skill_counts.items()),
        key=lambda r: -r["count"],
    )[:5]
    max_skill_count = top_skills[0]["count"] if top_skills else 0
    total_skill_count = len(skill_counts)

    return render_template(
        "browse.html",
        active_page="browse",
        courses=courses,
        categories=all_categories(),
        filters={"category": category, "level": level, "q": q},
        total_courses=len(all_courses),
        category_counts=category_counts,
        home_recs=home_recs,
        home_why=home_why,
        continue_items=continue_items,
        top_skills=top_skills,
        max_skill_count=max_skill_count,
        total_skill_count=total_skill_count,
    )


@app.route("/course/<int:course_id>")
def course_detail(course_id: int):
    course = get_course(course_id)
    if course is None:
        return render_template("not_found.html", active_page=""), 404

    idx = get_index()
    profile = get_current_profile()
    statuses = store.get_course_statuses(profile["id"]) if profile else {}
    exclude = set(statuses.keys())
    similar = idx.similar_courses(course_id, top_n=6, exclude_ids=exclude)
    similar = [_attach_status(c, statuses) for c in similar]
    reviews = store.get_reviews_for_course(course_id)

    return render_template(
        "course_detail.html",
        active_page="browse",
        course=_attach_status(course, statuses),
        similar=similar,
        reviews=reviews,
        profile=profile,
    )


@app.route("/onboarding", methods=["GET"])
def onboarding():
    profile = get_current_profile()
    known_ids = store.get_courses_by_status(profile["id"])["known"] if profile else []
    return render_template(
        "onboarding.html",
        active_page="",
        categories=all_categories(),
        skills=POPULAR_SKILLS,
        courses=all_courses_as_dicts(),
        profile=profile,
        known_ids=known_ids,
        is_edit=False,
    )


@app.route("/recommendations")
def recommendations_page():
    profile = get_current_profile()
    if profile is None:
        return redirect(url_for("onboarding"))

    idx = get_index()
    statuses = store.get_course_statuses(profile["id"])
    known_ids = list(statuses.keys())
    recs = idx.recommend_for_profile(
        interests=profile["interests"],
        skill_level=profile["skill_level"],
        known_course_ids=known_ids,
        top_n=12,
    )
    recs = [_attach_status(r, statuses) for r in recs]

    return render_template("recommendations.html", active_page="recommendations", recommendations=recs, profile=profile)


@app.route("/my-learning")
def my_learning():
    profile = get_current_profile()
    if profile is None:
        return redirect(url_for("onboarding"))

    by_status = store.get_courses_by_status(profile["id"])
    sections = {}
    total_hours = 0
    for status, ids in by_status.items():
        items = [get_course(cid) for cid in ids]
        items = [{**c, "status": status} for c in items if c is not None]
        sections[status] = items
        if status == "completed":
            total_hours = sum(c["duration_hours"] for c in items)

    return render_template(
        "my_learning.html",
        active_page="my-learning",
        sections=sections,
        total_hours=total_hours,
        profile=profile,
    )


@app.route("/profile", methods=["GET"])
def profile_page():
    profile = get_current_profile()
    if profile is None:
        return redirect(url_for("onboarding"))
    known_ids = store.get_courses_by_status(profile["id"])["known"]
    return render_template(
        "onboarding.html",
        active_page="profile",
        categories=all_categories(),
        skills=POPULAR_SKILLS,
        courses=all_courses_as_dicts(),
        profile=profile,
        known_ids=known_ids,
        is_edit=True,
    )


@app.route("/learning-path")
def learning_path():
    category = request.args.get("category") or ""
    profile = get_current_profile()
    statuses = store.get_course_statuses(profile["id"]) if profile else {}

    grouped = {"Beginner": [], "Intermediate": [], "Advanced": []}
    if category:
        courses = [c for c in all_courses_as_dicts() if c["category"] == category]
        courses = [_attach_status(c, statuses) for c in courses]
        for level in grouped:
            grouped[level] = sorted(
                [c for c in courses if c["level"] == level],
                key=lambda c: (-c["rating"], -c["students"]),
            )

    return render_template(
        "learning_path.html",
        active_page="learning-path",
        categories=all_categories(),
        selected_category=category,
        grouped=grouped,
    )


@app.route("/compare")
def compare():
    return render_template(
        "compare.html",
        active_page="compare",
        courses=all_courses_as_dicts(),
    )


@app.route("/insights")
def insights():
    courses = all_courses_as_dicts()
    total = len(courses)

    by_cat: dict[str, list[dict]] = {}
    for c in courses:
        by_cat.setdefault(c["category"], []).append(c)

    category_stats = []
    for cat in all_categories():
        items = by_cat.get(cat, [])
        avg_rating = (sum(c["rating"] for c in items) / len(items)) if items else 0.0
        category_stats.append({
            "category": cat,
            "count": len(items),
            "pct": round(len(items) / total * 100, 1) if total else 0,
            "avg_rating": round(avg_rating, 2),
        })
    category_stats.sort(key=lambda c: -c["count"])
    max_count = max((c["count"] for c in category_stats), default=1)

    top_rated = sorted(courses, key=lambda c: (-c["rating"], -c["students"]))[:6]
    most_popular = sorted(courses, key=lambda c: -c["students"])[:6]
    overall_avg_rating = round(sum(c["rating"] for c in courses) / total, 2) if total else 0
    total_students = sum(c["students"] for c in courses)

    profile = get_current_profile()
    skill_coverage = None
    if profile:
        statuses = store.get_course_statuses(profile["id"])
        have_ids = [cid for cid, s in statuses.items() if s in ("known", "completed")]
        known_skills: set[str] = set()
        for cid in have_ids:
            c = get_course(cid)
            if c:
                known_skills.update(c["skills"])
        all_skills_set: set[str] = set()
        for c in courses:
            all_skills_set.update(c["skills"])
        skill_coverage = {
            "known_count": len(known_skills),
            "total_count": len(all_skills_set),
            "pct": round(len(known_skills) / len(all_skills_set) * 100, 1) if all_skills_set else 0,
            "known_skills": sorted(known_skills),
        }

    return render_template(
        "insights.html",
        active_page="insights",
        total=total,
        category_stats=category_stats,
        max_count=max_count,
        top_rated=top_rated,
        most_popular=most_popular,
        skill_coverage=skill_coverage,
        profile=profile,
        overall_avg_rating=overall_avg_rating,
        total_students=total_students,
    )


@app.route("/career-path")
def career_path():
    profile = get_current_profile()
    if profile is None:
        return redirect(url_for("onboarding"))

    role = request.args.get("role") or ""
    statuses = store.get_course_statuses(profile["id"])
    have_ids = [cid for cid, s in statuses.items() if s in ("known", "completed")]
    known_skills: set[str] = set()
    for cid in have_ids:
        c = get_course(cid)
        if c:
            known_skills.update(c["skills"])

    role_data = None
    have_skills: list[str] = []
    missing_skills: list[str] = []
    recommended: list[dict] = []
    if role and role in CAREER_TRACKS:
        role_data = CAREER_TRACKS[role]
        have_skills = [s for s in role_data["skills"] if s in known_skills]
        missing_skills = [s for s in role_data["skills"] if s not in known_skills]

        if missing_skills:
            exclude = set(statuses.keys())
            scored = []
            for c in all_courses_as_dicts():
                if c["course_id"] in exclude:
                    continue
                overlap = len(set(c["skills"]) & set(missing_skills))
                if overlap > 0:
                    scored.append((overlap, c))
            scored.sort(key=lambda t: (-t[0], -t[1]["rating"]))
            recommended = [_attach_status(c, statuses) for _, c in scored[:8]]

    return render_template(
        "career_path.html",
        active_page="career-path",
        tracks=CAREER_TRACKS,
        selected_role=role,
        role_data=role_data,
        have_skills=have_skills,
        missing_skills=missing_skills,
        recommended=recommended,
        profile=profile,
    )


@app.errorhandler(404)
def not_found(_e):
    return render_template("not_found.html", active_page=""), 404


# ------------------------------------------------------------------ api ----

def _filter_courses(category: str, level: str, q: str) -> list[dict]:
    courses = all_courses_as_dicts()
    if category:
        courses = [c for c in courses if c["category"] == category]
    if level:
        courses = [c for c in courses if c["level"] == level]
    if q:
        needle = q.lower().strip()
        courses = [
            c for c in courses
            if needle in c["title"].lower()
            or needle in c["description"].lower()
            or any(needle in s.lower() for s in c["skills"])
        ]
    return courses


@app.route("/api/courses")
def api_courses():
    category = request.args.get("category") or ""
    level = request.args.get("level") or ""
    q = request.args.get("q") or ""
    courses = _filter_courses(category, level, q)
    profile = get_current_profile()
    statuses = store.get_course_statuses(profile["id"]) if profile else {}
    courses = [_attach_status(c, statuses) for c in courses]
    return jsonify(courses)


@app.route("/api/profile", methods=["POST"])
def api_profile_save():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name") or "Learner").strip()[:60] or "Learner"
    interests = [str(s).strip() for s in payload.get("interests", []) if str(s).strip()][:20]
    skill_level = payload.get("skill_level") or None
    known_course_ids = [int(cid) for cid in payload.get("known_course_ids", []) if str(cid).isdigit()]

    if not interests and not known_course_ids:
        return jsonify({"error": "bad_request", "message": "Pick at least one interest, or one course you already know."}), 400

    existing = get_current_profile()
    if existing:
        store.update_profile(existing["id"], name, interests, skill_level)
        profile_id = existing["id"]
        # Reconcile the "known" set: add newly-checked courses, and remove
        # ones the user unchecked (without touching in_progress/completed/saved).
        previously_known = set(store.get_courses_by_status(profile_id)["known"])
        now_known = set(known_course_ids)
        for cid in previously_known - now_known:
            store.set_course_status(profile_id, cid, None)
    else:
        profile_id = store.create_profile(name, interests, skill_level)

    for cid in known_course_ids:
        store.set_course_status(profile_id, cid, "known")

    resp = jsonify({"profile_id": profile_id})
    resp.set_cookie(PROFILE_COOKIE, profile_id, max_age=COOKIE_MAX_AGE, httponly=True, samesite="Lax")
    return resp


@app.route("/api/profile/reset", methods=["POST"])
def api_profile_reset():
    profile = get_current_profile()
    if profile:
        store.delete_profile(profile["id"])
    resp = jsonify({"ok": True})
    resp.delete_cookie(PROFILE_COOKIE)
    return resp


@app.route("/api/my-learning/<int:course_id>", methods=["POST"])
def api_my_learning_set(course_id: int):
    profile = get_current_profile()
    if profile is None:
        return jsonify({"error": "no_profile", "message": "Set up your profile first."}), 400
    if get_course(course_id) is None:
        return jsonify({"error": "not_found", "message": "No such course."}), 404

    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    if status is not None and status not in store.STATUSES:
        return jsonify({"error": "bad_request", "message": "Invalid status."}), 400

    store.set_course_status(profile["id"], course_id, status)
    return jsonify({"ok": True, "course_id": course_id, "status": status})


@app.route("/api/courses/<int:course_id>/reviews", methods=["POST"])
def api_add_review(course_id: int):
    if get_course(course_id) is None:
        return jsonify({"error": "not_found", "message": "No such course."}), 404

    payload = request.get_json(silent=True) or {}
    try:
        rating = int(payload.get("rating"))
    except (TypeError, ValueError):
        rating = None
    if rating is None or not (store.MIN_RATING <= rating <= store.MAX_RATING):
        return jsonify({"error": "bad_request", "message": "Pick a rating from 1 to 5."}), 400

    comment = str(payload.get("comment") or "").strip()
    if not comment:
        return jsonify({"error": "bad_request", "message": "Write a short comment."}), 400
    comment = comment[:600]

    profile = get_current_profile()
    reviewer_name = (profile["name"] if profile else str(payload.get("reviewer_name") or "").strip()) or "Anonymous"
    reviewer_name = reviewer_name[:60]

    review_id = store.add_review(course_id, profile["id"] if profile else None, reviewer_name, rating, comment)
    return jsonify({"ok": True, "review_id": review_id})


if __name__ == "__main__":
    app.run(debug=True, port=5057)
