"""
extractor.py
------------
Turns raw resume/JD TEXT into STRUCTURED data:
skills, years of experience, education level, projects, certifications.

This is the "Agent extracts important candidate information" and
"Agent extracts important requirements" steps of the pipeline. The
same functions are reused for both resumes and the job description,
so a candidate's skill list and the JD's skill list are extracted
the exact same way -> fair, consistent comparison.
"""

import re
from src.skills_db import SKILLS, SYNONYMS
from src.utils import safe_lower, find_section

# Build one flat lookup: every synonym/spelling -> its "canonical" skill name.
_SKILL_LOOKUP = {}
for skill in SKILLS:
    _SKILL_LOOKUP[skill] = skill
for canonical, synonyms in SYNONYMS.items():
    for syn in synonyms:
        _SKILL_LOOKUP[syn] = canonical

# Degree keywords, ordered from highest to lowest so we can also
# report the "highest" education level found.
EDUCATION_LEVELS = [
    ("phd", ["phd", "ph.d", "doctorate"]),
    ("master", ["m.tech", "mtech", "m.e ", "me ", "msc", "m.sc",
                "mca", "master of", "master's", "mba"]),
    ("bachelor", ["b.tech", "btech", "b.e ", "be ", "bsc", "b.sc",
                  "bca", "bachelor of", "bachelor's", "b.com"]),
    ("diploma", ["diploma"]),
    ("high_school", ["high school", "12th", "hsc", "10th", "ssc"]),
]

CERT_KEYWORDS = [
    "certified", "certification", "certificate",
    "aws certified", "azure certified", "pmp", "coursera", "udemy",
    "google certified", "microsoft certified", "oracle certified",
]


def extract_skills(text: str) -> set:
    """
    Finds every known skill (from skills_db.py) mentioned in the text.
    Uses word-boundary matching so "r" doesn't match inside "framework",
    and returns the *canonical* skill name (so "reactjs" and "react.js"
    both count as "react.js").
    """
    lowered = safe_lower(text)
    found = set()

    for term, canonical in _SKILL_LOOKUP.items():
        # Escape special regex characters like "." and "+" in things
        # like "c++" or "node.js", then require word boundaries so we
        # don't match substrings inside unrelated words.
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(term) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, lowered):
            found.add(canonical)

    return found


def extract_experience_years(text: str) -> float:
    """
    Looks for patterns like "3 years", "5+ years of experience",
    "2 yrs" and returns the LARGEST number found, on the assumption
    that resumes/JDs usually state total experience at least once.
    Returns 0 if nothing is found (e.g. fresher resume).
    """
    lowered = safe_lower(text)
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs|yr)\b", lowered)
    if not matches:
        return 0.0
    return max(float(m) for m in matches)


def extract_education(text: str) -> str:
    """
    Returns the highest education level mentioned in the text, as one
    of: "phd", "master", "bachelor", "diploma", "high_school", or
    "unspecified" if nothing matched.
    """
    lowered = safe_lower(text)
    for level, keywords in EDUCATION_LEVELS:
        for kw in keywords:
            if kw in lowered:
                return level
    return "unspecified"


def extract_projects_text(text: str) -> str:
    """Grabs the 'Projects' section of a resume, if one exists."""
    return find_section(
        text,
        section_names=["projects", "project experience", "academic projects"],
        next_section_names=[
            "certifications", "certificate", "education", "experience",
            "work experience", "skills", "achievements", "extracurricular",
        ],
    )


def extract_certifications(text: str) -> list:
    """
    Returns short snippets (lines) mentioning certification keywords.
    We keep this simple: a resume either shows evidence of
    certifications or it doesn't - the exact cert names aren't
    critical to the score, just presence.
    """
    lowered_lines = text.split("\n")
    hits = []
    for line in lowered_lines:
        low = line.lower()
        if any(kw in low for kw in CERT_KEYWORDS):
            cleaned = line.strip()
            if cleaned and cleaned not in hits:
                hits.append(cleaned)
    return hits[:10]  # cap so one messy resume can't dominate output


def extract_candidate_data(text: str) -> dict:
    """
    Runs ALL extractors and bundles the results into one dict.
    This is the "candidate profile" the scorer.py will compare
    against the JD profile.
    """
    return {
        "skills": extract_skills(text),
        "experience_years": extract_experience_years(text),
        "education": extract_education(text),
        "projects_text": extract_projects_text(text),
        "has_projects": bool(extract_projects_text(text)),
        "certifications": extract_certifications(text),
    }


# --- Job description specific parsing -------------------------------

REQUIRED_MARKERS = [
    "required skills", "must have", "requirements", "required qualifications",
    "minimum qualifications",
]
PREFERRED_MARKERS = [
    "preferred skills", "nice to have", "good to have", "preferred qualifications",
    "bonus", "plus",
]


def parse_job_description(text: str) -> dict:
    """
    Extracts structured requirements from a Job Description.

    Strategy (kept intentionally simple for a 24-hour build):
    1. Try to find an explicit "required" section and a "preferred"
       section using common header phrases.
    2. Extract skills mentioned in each section separately.
    3. If no explicit sections are found, treat every skill mentioned
       anywhere in the JD as "required" (safe default).
    4. Also extract minimum experience years and education level,
       reusing the same extractors used for resumes.
    """
    required_section = find_section(
        text, REQUIRED_MARKERS, next_section_names=PREFERRED_MARKERS + ["responsibilities"]
    )
    preferred_section = find_section(
        text, PREFERRED_MARKERS, next_section_names=["responsibilities", "about"]
    )

    if required_section:
        required_skills = extract_skills(required_section)
    else:
        # No explicit section header found -> use all skills mentioned
        # in the whole JD as "required" (a safe, simple default).
        required_skills = extract_skills(text)

    preferred_skills = extract_skills(preferred_section) if preferred_section else set()
    # Don't double count a skill as both required and preferred
    preferred_skills -= required_skills

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "min_experience_years": extract_experience_years(text),
        "education": extract_education(text),
        "raw_text": text,
    }
