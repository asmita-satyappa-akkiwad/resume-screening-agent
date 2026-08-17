"""
reasoning.py
------------
Generates a short, human-readable explanation of WHY a candidate got
their score.

IMPORTANT DESIGN DECISION:
The LLM does NOT decide the score - scorer.py already computed that
deterministically. The LLM only turns numbers we already trust into
a readable sentence. This keeps the system reproducible (same score
every time) while still giving a nice natural-language summary.

If no ANTHROPIC_API_KEY is set (or the API call fails for any
reason - offline, rate limit, etc.), we fall back to a template-based
explanation built directly from the score breakdown. The app never
crashes or blocks just because reasoning-generation failed.
"""

import os

_client = None
_client_init_attempted = False


def _get_client():
    global _client, _client_init_attempted
    if _client_init_attempted:
        return _client

    _client_init_attempted = True
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
        _client = anthropic.Anthropic(api_key=api_key)
    except Exception:
        _client = None

    return _client


def _template_reasoning(candidate_name: str, score_data: dict) -> str:
    """Rule-based fallback explanation, built purely from the score breakdown."""
    matched = score_data["matched_required_skills"]
    missing = score_data["missing_required_skills"]
    years = score_data["candidate_experience_years"]

    parts = []
    if matched:
        parts.append(f"has relevant skills including {', '.join(matched[:5])}")
    if years:
        parts.append(f"shows {years:g} years of experience")
    if score_data["projects_score"] > 0:
        parts.append("includes relevant project work")
    if score_data["certifications_score"] > 0:
        parts.append("lists relevant certifications")

    strengths = "; ".join(parts) if parts else "shows limited overlap with the JD"

    gap = ""
    if missing:
        gap = f" Missing required skills: {', '.join(missing[:5])}."

    return f"{candidate_name} {strengths}.{gap}".strip()


def generate_reasoning(candidate_name: str, score_data: dict) -> str:
    """
    Returns a 1-3 sentence explanation for a candidate's score.
    Tries the LLM first, falls back to a template if unavailable.
    """
    client = _get_client()
    fallback = _template_reasoning(candidate_name, score_data)

    if client is None:
        return fallback

    prompt = (
        "You are helping summarize a resume-screening result. Given the "
        "score breakdown below, write ONE short, factual paragraph (2-3 "
        "sentences max) explaining why this candidate received this score. "
        "Be specific about matched and missing skills. Do not invent facts "
        "not present in the data. Do not mention the raw point totals.\n\n"
        f"Candidate: {candidate_name}\n"
        f"Overall score: {score_data['overall_score']}/100\n"
        f"Matched required skills: {score_data['matched_required_skills']}\n"
        f"Missing required skills: {score_data['missing_required_skills']}\n"
        f"Matched preferred skills: {score_data['matched_preferred_skills']}\n"
        f"Years of experience: {score_data['candidate_experience_years']}\n"
        f"Education level: {score_data['candidate_education']}\n"
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        ).strip()
        return text if text else fallback
    except Exception:
        return fallback
