"""
scorer.py
---------
Combines everything (skills, experience, education, projects,
certifications, semantic similarity) into ONE transparent 0-100 score.

SCORING FORMULA (out of 100):
- Skills match:            40 pts  (30 required + 10 preferred)
- Experience relevance:    25 pts
- Semantic similarity:     15 pts  (embedding/TF-IDF cosine score)
- Education:               10 pts
- Projects:                 7 pts
- Certifications:           3 pts

Every sub-score is calculated with a plain formula (no randomness,
no LLM) so the SAME resume + JD always produces the SAME score.
That reproducibility is what makes the system defensible: you can
always explain exactly why a candidate got the number they got.
"""

import json
import os

from src.similarity import semantic_similarity

# Default weights - used if config.json is missing, unreadable, or doesn't
# override a particular key. These are the SAME numbers the app has always
# used, so behavior is unchanged unless someone deliberately edits
# config.json in the project root.
_DEFAULT_WEIGHTS = {
    "required_skills": 30,
    "preferred_skills": 10,
    "experience": 25,
    "semantic": 15,
    "education": 10,
    "projects": 7,
    "certifications": 3,
}

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


def _load_weights() -> dict:
    """
    Reads scoring weights from config.json in the project root, falling
    back to the built-in defaults for any key that's missing or if the
    file itself can't be read/parsed. This means:
      - No config.json at all -> works exactly as before.
      - A partial config.json (e.g. only overrides "experience") -> only
        that value changes, everything else stays default.
      - A broken/invalid config.json -> silently falls back to defaults
        instead of crashing the whole pipeline.
    """
    weights = dict(_DEFAULT_WEIGHTS)
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            overrides = json.load(f)
        for key in weights:
            if key in overrides:
                weights[key] = overrides[key]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return weights


WEIGHTS = _load_weights()

EDUCATION_RANK = {
    "phd": 5,
    "master": 4,
    "bachelor": 3,
    "diploma": 2,
    "high_school": 1,
    "unspecified": 0,
}


def _score_skills(candidate_skills: set, required: set, preferred: set) -> dict:
    """
    Required skills matter more than preferred ones, so they get 3x
    the weight per-skill by default (30 pts across "required" vs
    10 pts across "preferred"). If the JD lists zero required/preferred
    skills (parsing edge case), we give full marks for that component
    rather than unfairly zeroing every candidate out.
    """
    if required:
        matched_required = candidate_skills & required
        required_score = (len(matched_required) / len(required)) * WEIGHTS["required_skills"]
    else:
        matched_required = set()
        required_score = WEIGHTS["required_skills"]

    if preferred:
        matched_preferred = candidate_skills & preferred
        preferred_score = (len(matched_preferred) / len(preferred)) * WEIGHTS["preferred_skills"]
    else:
        matched_preferred = set()
        preferred_score = WEIGHTS["preferred_skills"]

    return {
        "score": round(required_score + preferred_score, 2),
        "matched_required": sorted(matched_required),
        "missing_required": sorted(required - candidate_skills),
        "matched_preferred": sorted(matched_preferred),
    }


def _score_experience(candidate_years: float, min_years: float) -> float:
    """
    Full marks if the candidate meets or exceeds the JD's minimum
    experience. Partial credit scales linearly below that. If the JD
    doesn't specify a minimum (min_years == 0), we treat any
    experience as fully sufficient and score on a light curve instead
    of unfairly punishing every candidate for a JD parsing gap.
    """
    if min_years <= 0:
        # No explicit requirement -> reward having *some* relevant
        # experience, capped at full marks by 4 years.
        return round(min(candidate_years / 4, 1.0) * WEIGHTS["experience"], 2)

    ratio = min(candidate_years / min_years, 1.0)
    return round(ratio * WEIGHTS["experience"], 2)


def _score_education(candidate_level: str, jd_level: str) -> float:
    """
    Full marks if candidate's education is >= what the JD asks for.
    Partial credit if one level below. This avoids being overly
    strict (a Bachelor's candidate isn't zeroed out for a JD that
    didn't clearly specify a degree).
    """
    jd_rank = EDUCATION_RANK.get(jd_level, 0)
    cand_rank = EDUCATION_RANK.get(candidate_level, 0)

    if jd_rank == 0:
        # JD didn't specify -> any stated education gets full credit,
        # unspecified gets half credit rather than zero.
        return WEIGHTS["education"] if cand_rank > 0 else WEIGHTS["education"] * 0.5

    if cand_rank >= jd_rank:
        return float(WEIGHTS["education"])
    if cand_rank == jd_rank - 1:
        return round(WEIGHTS["education"] * 0.6, 2)
    return 0.0


def calculate_score(resume_data: dict, jd_data: dict, resume_text: str) -> dict:
    """
    The main entry point: takes the extracted resume data + JD data,
    computes every sub-score, and returns a full breakdown.

    Args:
        resume_data: dict from extractor.extract_candidate_data()
        jd_data: dict from extractor.parse_job_description()
        resume_text: cleaned raw resume text (needed for similarity)

    Returns:
        dict with overall_score plus every sub-score and the
        matched/missing skill details (used later for reasoning).
    """
    skills_result = _score_skills(
        resume_data["skills"], jd_data["required_skills"], jd_data["preferred_skills"]
    )
    experience_score = _score_experience(
        resume_data["experience_years"], jd_data["min_experience_years"]
    )
    education_score = _score_education(resume_data["education"], jd_data["education"])

    projects_score = WEIGHTS["projects"] if resume_data["has_projects"] else 0.0
    certifications_score = (
        WEIGHTS["certifications"] if resume_data["certifications"] else 0.0
    )

    sim_result = semantic_similarity(resume_text, jd_data["raw_text"])
    semantic_score = round(sim_result["score"] * WEIGHTS["semantic"], 2)

    overall = (
        skills_result["score"]
        + experience_score
        + semantic_score
        + education_score
        + projects_score
        + certifications_score
    )
    overall = round(min(overall, 100.0), 2)

    return {
        "overall_score": overall,
        "skills_score": skills_result["score"],
        "experience_score": experience_score,
        "semantic_score": semantic_score,
        "education_score": education_score,
        "projects_score": projects_score,
        "certifications_score": certifications_score,
        "matched_required_skills": skills_result["matched_required"],
        "missing_required_skills": skills_result["missing_required"],
        "matched_preferred_skills": skills_result["matched_preferred"],
        "similarity_method": sim_result["method"],
        "candidate_experience_years": resume_data["experience_years"],
        "candidate_education": resume_data["education"],
    }
