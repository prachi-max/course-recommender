"""Content-based course recommender.

Approach (deliberately the classic, explainable one - see README.md):
  1. Build one "content soup" string per course out of its title, skills,
     category, level, and description (title and skills repeated so they
     count for more than incidental words in the description).
  2. Fit a single TfidfVectorizer across every course's soup. Each course
     becomes a sparse vector in that shared vocabulary space.
  3. To recommend for a user: turn their chosen interests (and, if they have
     any, the courses they've already completed/are taking) into a vector in
     that SAME space, then rank every course by cosine similarity to it.
  4. To find "similar courses" on a course's own page: cosine similarity
     between that one course's vector and every other course's vector.

No neural network, no external API call - just TF-IDF + cosine similarity,
which is exactly what the brief for this project asked for. It is fast
enough to rebuild from scratch on every process start (a few hundred courses
fits in memory trivially), so there's no separate "training" step to run by hand.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
COURSES_PATH = ROOT / "data" / "courses.csv"


def _content_soup(row: pd.Series) -> str:
    # Repeat title and skills so they weigh more than the free-text
    # description in the resulting TF-IDF vector - the description alone
    # would otherwise dominate just by being the longest field.
    parts = [
        row["title"], row["title"],
        row["skills"].replace(";", " "), row["skills"].replace(";", " "),
        row["category"],
        row["level"],
        row["description"],
    ]
    return " ".join(parts)


@dataclass
class CourseIndex:
    courses: pd.DataFrame          # one row per course, original columns + soup
    vectorizer: TfidfVectorizer
    matrix: np.ndarray              # sparse TF-IDF matrix, one row per course
    similarity: np.ndarray          # dense course-to-course cosine similarity
    id_to_pos: dict                 # course_id -> row position in `courses`/`matrix`

    def course_row(self, course_id: int) -> pd.Series:
        return self.courses.iloc[self.id_to_pos[course_id]]

    def similar_courses(self, course_id: int, top_n: int = 6, exclude_ids: set[int] | None = None) -> list[dict]:
        if course_id not in self.id_to_pos:
            return []
        pos = self.id_to_pos[course_id]
        scores = self.similarity[pos]
        exclude_ids = (exclude_ids or set()) | {course_id}
        ranked = sorted(
            ((i, s) for i, s in enumerate(scores) if int(self.courses.iloc[i]["course_id"]) not in exclude_ids),
            key=lambda t: t[1], reverse=True,
        )[:top_n]
        out = []
        for i, score in ranked:
            row = self.courses.iloc[i]
            out.append({**_course_to_dict(row), "match_pct": round(float(score) * 100, 1)})
        return out

    def recommend_for_profile(
        self,
        interests: list[str],
        skill_level: str | None,
        known_course_ids: list[int],
        top_n: int = 12,
    ) -> list[dict]:
        interest_text = " ".join(interests * 3)  # weight interests heavily - they're the explicit signal
        vectors = []
        if interest_text.strip():
            vectors.append(np.asarray(self.vectorizer.transform([interest_text]).todense()))
        known_positions = [self.id_to_pos[cid] for cid in known_course_ids if cid in self.id_to_pos]
        if known_positions:
            known_vec = np.asarray(self.matrix[known_positions].mean(axis=0))
            vectors.append(known_vec)

        if not vectors:
            # No signal at all yet - fall back to the site's most popular/highest rated courses.
            fallback = self.courses.sort_values(["rating", "students"], ascending=False).head(top_n)
            return [{**_course_to_dict(r), "match_pct": None, "why": "Popular on the platform"} for _, r in fallback.iterrows()]

        user_vector = sum(vectors) / len(vectors)  # dense (1, n_features)
        scores = cosine_similarity(user_vector, self.matrix).ravel()

        exclude = set(known_course_ids)
        feature_names = self.vectorizer.get_feature_names_out()

        # Relevance (the TF-IDF/cosine score) stays the primary sort key -
        # a matching skill level only nudges otherwise-close courses ahead of
        # each other, it never promotes an irrelevant course over a relevant one.
        LEVEL_BONUS = 0.05
        candidates = []
        for i, s in enumerate(scores):
            if int(self.courses.iloc[i]["course_id"]) in exclude:
                continue
            bonus = LEVEL_BONUS if (skill_level and self.courses.iloc[i]["level"] == skill_level) else 0.0
            candidates.append((i, float(s), float(s) + bonus))

        # Only keep courses that actually share some content with the user's
        # profile - padding the list with 0%-similarity courses just to hit
        # top_n would be misleading, not helpful.
        relevant = [c for c in candidates if c[1] > 0.01]
        relevant.sort(key=lambda t: t[2], reverse=True)
        ranked = relevant[:top_n]

        out = []
        user_row = user_vector[0]
        for i, raw_score, _ in ranked:
            row = self.courses.iloc[i]
            why = _explain(user_row, self.matrix[i].toarray().ravel(), feature_names)
            out.append({**_course_to_dict(row), "match_pct": round(raw_score * 100, 1), "why": why})

        if len(out) < min(6, top_n):
            # Not enough personalized signal to fill the page - top up with
            # popular courses the user doesn't already know, clearly labeled.
            have = {r["course_id"] for r in out} | exclude
            fallback = self.courses[~self.courses["course_id"].isin(have)].sort_values(
                ["rating", "students"], ascending=False
            ).head(top_n - len(out))
            for _, row in fallback.iterrows():
                out.append({**_course_to_dict(row), "match_pct": None, "why": "Popular on the platform"})

        return out


def _explain(user_vec: np.ndarray, course_vec: np.ndarray, feature_names: np.ndarray, top_k: int = 4) -> str:
    user_vec = np.asarray(user_vec).ravel()
    overlap = user_vec * course_vec
    if overlap.max(initial=0) <= 0:
        return ""
    top_idx = overlap.argsort()[::-1][:top_k]
    terms = [feature_names[i] for i in top_idx if overlap[i] > 0]
    return ", ".join(terms)


def _course_to_dict(row: pd.Series) -> dict:
    return {
        "course_id": int(row["course_id"]),
        "title": row["title"],
        "category": row["category"],
        "level": row["level"],
        "skills": [s.strip() for s in row["skills"].split(";")],
        "duration_hours": int(row["duration_hours"]),
        "rating": float(row["rating"]),
        "students": int(row["students"]),
        "instructor": row["instructor"],
        "description": row["description"],
    }


_INDEX: CourseIndex | None = None


def get_index() -> CourseIndex:
    """Build (once) and cache the TF-IDF index for the whole process."""
    global _INDEX
    if _INDEX is not None:
        return _INDEX

    courses = pd.read_csv(COURSES_PATH)
    courses["soup"] = courses.apply(_content_soup, axis=1)

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1, max_features=6000)
    matrix = vectorizer.fit_transform(courses["soup"])
    similarity = cosine_similarity(matrix)
    id_to_pos = {int(cid): pos for pos, cid in enumerate(courses["course_id"])}

    _INDEX = CourseIndex(courses=courses, vectorizer=vectorizer, matrix=matrix, similarity=similarity, id_to_pos=id_to_pos)
    return _INDEX


def all_courses_as_dicts() -> list[dict]:
    idx = get_index()
    return [_course_to_dict(r) for _, r in idx.courses.iterrows()]


def get_course(course_id: int) -> dict | None:
    idx = get_index()
    if course_id not in idx.id_to_pos:
        return None
    return _course_to_dict(idx.course_row(course_id))


def all_categories() -> list[str]:
    idx = get_index()
    return sorted(idx.courses["category"].unique().tolist())


def all_skills() -> list[str]:
    idx = get_index()
    skills = set()
    for s in idx.courses["skills"]:
        skills.update(x.strip() for x in s.split(";"))
    return sorted(skills)
