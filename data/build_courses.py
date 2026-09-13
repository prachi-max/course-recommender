"""Builds data/courses.csv from REAL course data.

Source: a public scrape of ~890 Coursera course listings, mirrored on GitHub
by Siddharth1698 (github.com/Siddharth1698/Coursera-Course-Dataset), originally
sourced from Kaggle ("Coursera Course Dataset"). A local copy is kept at
data/sources/coursera_raw.csv so this script is reproducible offline.

What's real, straight from the source file, for every course below:
  - title              (real Coursera course title)
  - instructor field   (the real offering organization/university, e.g. "Google Cloud")
  - level              (the real difficulty label Coursera assigned)
  - rating             (the real average rating)
  - students           (the real enrollment count)

What this script adds on top (the source file has no category/skills/
description/duration columns at all):
  - category    assigned by keyword-matching the real title into one of the
                app's 10 tracks
  - skills      short tags extracted from keywords found in the real title
  - description a one-line auto-generated summary (title + org + level) -
                NOT scraped text, since Coursera's dataset doesn't include one
  - duration_hours  estimated from the course's real certificate type
                (COURSE / SPECIALIZATION / PROFESSIONAL CERTIFICATE), since
                the source has no duration field

Run once:  python data/build_courses.py
"""
from __future__ import annotations

import csv
import random
import re
from pathlib import Path

random.seed(42)

SRC_PATH = Path(__file__).resolve().parent / "sources" / "coursera_raw.csv"
OUT_PATH = Path(__file__).resolve().parent / "courses.csv"

# Ordered keyword -> category rules. First match wins, checked in this order
# so more specific tracks (DevOps, Databases, Mobile...) are tested before
# broad ones, avoiding e.g. "Kubernetes" landing in Cloud Computing instead
# of DevOps & SRE.
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Mobile Development", [
        "android", "ios development", "ios app", "swift 5", "swift programming",
        "kotlin for", "flutter", "react native", "building applications for ios",
    ]),
    ("DevOps & SRE", [
        "devops", "docker", "kubernetes", "site reliability", "continuous delivery",
        "continuous integration", "version control with git", "linux system",
        "linux administration", "google it automation", "ansible", "terraform",
    ]),
    ("Cybersecurity", [
        "cyber security", "cybersecurity", "ethical hacking", "penetration testing",
        "network security", "cryptography", "information security",
        "security operations", "malware", "security fundamentals",
    ]),
    ("Databases & Data Engineering", [
        "sql", "database", "databases", "big data", "apache spark", "hadoop",
        "data warehousing", "nosql", "mongodb", "using databases",
    ]),
    ("Machine Learning & AI", [
        "machine learning", "deep learning", "neural network", "artificial intelligence",
        "tensorflow", "natural language processing", " nlp ", "computer vision",
        "reinforcement learning", "generative adversarial",
    ]),
    ("Data Science", [
        "data science", "data analysis", "data analytics", "data visualization",
        "tableau", "excel", "r programming", "statistics for", "business analytics",
        "data scientist", "introduction to statistics", "probability",
    ]),
    ("Web Development", [
        "html", "css", "javascript", "web development", "frontend", "front-end",
        r"\breact\b", "angular", "vue.js", "node.js", "full stack", "full-stack",
        "php", "wordpress", "web design", "web programming", "web application",
        "responsive web", "web applications for everybody",
    ]),
    ("Cloud Computing", [
        "google cloud", "gcp", "aws", "amazon web services", "microsoft azure",
        " azure", "cloud computing", "cloud architecture", "cloud platform",
        "serverless", "cloud engineer",
    ]),
    ("UI/UX Design", [
        "user experience", "ux design", "ui design", "user interface",
        "interaction design", "graphic design", "design thinking", " ux ", " ui ",
        "visual design", "design principles",
    ]),
    ("Business & Product Management", [
        "product management", "business strategy", "entrepreneurship", "agile",
        "scrum", "project management", "marketing", "leadership", "negotiation",
        "finance for", "strategic management", "innovation management", "startup",
    ]),
]

# Tags pulled out of the title text itself, per category. Fallback tag is
# used (and always included) when nothing more specific matches.
SKILL_RULES: dict[str, list[tuple[str, str]]] = {
    "Web Development": [("html", "html"), ("css", "css"), ("javascript", "javascript"),
                         (r"\breact\b", "react"), ("bootstrap", "bootstrap"),
                         ("responsive", "responsive design"), ("node.js", "node.js"),
                         ("full stack", "full stack"), ("full-stack", "full stack")],
    "Cloud Computing": [("google cloud", "gcp"), ("gcp", "gcp"), ("aws", "aws"),
                         ("amazon web services", "aws"), ("azure", "azure"),
                         ("serverless", "serverless"), ("architecture", "cloud architecture")],
    "DevOps & SRE": [("docker", "docker"), ("kubernetes", "kubernetes"), ("devops", "devops"),
                      ("site reliability", "sre"), ("git", "git"), ("automation", "automation"),
                      ("continuous", "ci/cd"), ("linux", "linux"), ("python", "python")],
    "Cybersecurity": [("ethical hacking", "ethical hacking"), ("penetration", "penetration testing"),
                       ("network security", "network security"), ("cryptography", "cryptography"),
                       ("malware", "malware analysis"), ("security", "security fundamentals")],
    "Machine Learning & AI": [("deep learning", "deep learning"), ("neural network", "neural networks"),
                               ("tensorflow", "tensorflow"), ("natural language", "nlp"),
                               ("computer vision", "computer vision"),
                               ("reinforcement learning", "reinforcement learning"),
                               ("python", "python"),
                               ("machine learning", "machine learning")],
    "Data Science": [("data analysis", "data analysis"), ("data visualization", "data visualization"),
                      ("tableau", "tableau"), ("excel", "excel"), ("r programming", "r"),
                      ("statistics", "statistics"), ("probability", "probability"),
                      ("python", "python")],
    "Databases & Data Engineering": [("sql", "sql"), ("database", "databases"), ("big data", "big data"),
                                      ("spark", "apache spark"), ("hadoop", "hadoop"),
                                      ("nosql", "nosql"), ("mongodb", "mongodb"),
                                      ("python", "python")],
    "Mobile Development": [("android", "android"), ("ios", "ios"), ("swift", "swift"),
                            ("kotlin", "kotlin"), ("flutter", "flutter"),
                            ("react native", "react native")],
    "UI/UX Design": [("user experience", "ux"), ("ux", "ux"), ("user interface", "ui design"),
                      ("graphic design", "graphic design"), ("design thinking", "design thinking"),
                      ("interaction design", "interaction design")],
    "Business & Product Management": [("product management", "product management"),
                                       ("agile", "agile"), ("scrum", "scrum"),
                                       ("project management", "project management"),
                                       ("marketing", "marketing"),
                                       ("entrepreneurship", "entrepreneurship"),
                                       ("leadership", "leadership"),
                                       ("negotiation", "negotiation"),
                                       ("strateg", "business strategy")],
}
FALLBACK_TAG = {
    "Web Development": "web development", "Cloud Computing": "cloud computing",
    "DevOps & SRE": "devops", "Cybersecurity": "cybersecurity",
    "Machine Learning & AI": "machine learning", "Data Science": "data science",
    "Databases & Data Engineering": "databases", "Mobile Development": "mobile development",
    "UI/UX Design": "ui/ux", "Business & Product Management": "business",
}

# Non-Latin scripts, and accented-Latin (Spanish/Portuguese/French translated
# title variants), sometimes show up in this scrape - skip anything that
# isn't essentially plain English text.
BAD_RANGES = [(0x3000, 0xA6FF), (0x0400, 0x04FF), (0x0600, 0x06FF), (0xAC00, 0xD7FF),
              (0x00C0, 0x024F)]



# A handful of translated titles in the source use plain (unaccented) Latin
# letters, so the unicode-range check above won't catch them - a small set
# of connector words that are essentially never legitimate English course
# titles' own words, checked separately below.
NON_ENGLISH_WORDS = {
    "de", "para", "en", "con", "los", "las", "el", "la", "das", "der", "die",
    "und", "für", "avec", "le", "les", "du", "des", "che", "del", "al",
}


def is_english(title: str) -> bool:
    if any(any(lo <= ord(ch) <= hi for lo, hi in BAD_RANGES) for ch in title):
        return False
    words = set(re.findall(r"[a-zA-Z]+", title.lower()))
    return not (words & NON_ENGLISH_WORDS)


def _matches(t: str, kw: str) -> bool:
    # A keyword starting with a raw regex escape (currently only \b-wrapped
    # entries, for short words like "react" that are also substrings of
    # unrelated words such as "Reactions") is matched as regex; everything
    # else is a plain substring check.
    if kw.startswith(r"\b"):
        return re.search(kw, t) is not None
    return kw in t


def categorize(title: str) -> str | None:
    t = title.lower()
    for cat, keywords in CATEGORY_RULES:
        if any(_matches(t, kw) for kw in keywords):
            return cat
    return None


def extract_skills(title: str, category: str) -> list[str]:
    t = title.lower()
    tags: list[str] = []
    for kw, tag in SKILL_RULES.get(category, []):
        if _matches(t, kw) and tag not in tags:
            tags.append(tag)
    fallback = FALLBACK_TAG[category]
    if fallback not in tags:
        tags.append(fallback)
    return tags[:4]


def parse_students(raw: str) -> int:
    s = raw.strip().lower()
    try:
        if s.endswith("k"):
            return int(float(s[:-1]) * 1_000)
        if s.endswith("m"):
            return int(float(s[:-1]) * 1_000_000)
        return int(float(s))
    except ValueError:
        return 0


DURATION_RANGES = {
    "COURSE": (4, 15),
    "SPECIALIZATION": (15, 45),
    "PROFESSIONAL CERTIFICATE": (30, 90),
}


def build_description(title: str, org: str, level: str, category: str) -> str:
    article = "An" if level[0].lower() in "aeiou" else "A"
    return f"{article} {level.lower()}-level {category.lower()} course offered by {org}, covering {title.rstrip('.')}."


def main() -> None:
    with SRC_PATH.open(encoding="utf-8") as f:
        source_rows = list(csv.DictReader(f))

    seen_titles: set[str] = set()
    candidates = []
    for row in source_rows:
        title = row["course_title"].strip()
        if not title or title in seen_titles or not is_english(title):
            continue
        category = categorize(title)
        if category is None:
            continue
        difficulty = row["course_difficulty"]
        level = "Intermediate" if difficulty == "Mixed" else difficulty
        if level not in ("Beginner", "Intermediate", "Advanced"):
            continue
        try:
            rating = float(row["course_rating"])
        except ValueError:
            continue
        students = parse_students(row["course_students_enrolled"])
        if students <= 0:
            continue
        seen_titles.add(title)
        candidates.append({
            "title": title,
            "org": row["course_organization"].strip(),
            "cert": row["course_Certificate_type"].strip(),
            "level": level,
            "rating": rating,
            "students": students,
            "category": category,
        })

    # Cap each category at 20 courses, favoring the most-enrolled real
    # courses first, so popular/well-known ones make the cut.
    by_category: dict[str, list[dict]] = {}
    for c in candidates:
        by_category.setdefault(c["category"], []).append(c)
    rows = []
    course_id = 1
    for category, _keywords in CATEGORY_RULES:
        items = sorted(by_category.get(category, []), key=lambda c: -c["students"])[:20]
        for c in items:
            lo, hi = DURATION_RANGES.get(c["cert"], (8, 20))
            duration = random.randint(lo, hi)
            skills = extract_skills(c["title"], category)
            description = build_description(c["title"], c["org"], c["level"], category)
            rows.append({
                "course_id": course_id,
                "title": c["title"],
                "category": category,
                "level": c["level"],
                "skills": "; ".join(skills),
                "duration_hours": duration,
                "rating": round(c["rating"], 1),
                "students": c["students"],
                "instructor": c["org"],
                "description": description,
            })
            course_id += 1

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real courses to {OUT_PATH}")
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    for cat, _ in CATEGORY_RULES:
        print(f"  {cat}: {counts.get(cat, 0)}")


if __name__ == "__main__":
    main()
