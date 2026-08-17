"""
test_pipeline.py
-----------------
A handful of focused tests covering the parts most likely to break:
skill extraction, JD parsing, scoring math, and file parsing.

Run with:
    python -m pytest tests/ -v
or simply:
    python tests/test_pipeline.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extractor import extract_skills, extract_experience_years, extract_education, parse_job_description
from src.scorer import calculate_score
from src.parser import extract_text, ParsingError


def test_extract_skills_basic():
    text = "Experienced in Python, React.js and AWS. Also know reactjs and node.js."
    skills = extract_skills(text)
    assert "python" in skills
    assert "react.js" in skills  # both spellings should map to canonical form
    assert "amazon web services" in skills or "aws" in skills
    print("test_extract_skills_basic passed")


def test_extract_skills_no_false_positive():
    # "r" as a language shouldn't match inside "framework" or "for"
    text = "This is a framework for building apps."
    skills = extract_skills(text)
    assert "r" not in skills
    print("test_extract_skills_no_false_positive passed")


def test_extract_experience_years():
    assert extract_experience_years("5+ years of experience") == 5.0
    assert extract_experience_years("2.5 yrs experience, later 4 years") == 4.0
    assert extract_experience_years("no experience mentioned") == 0.0
    print("test_extract_experience_years passed")


def test_extract_education():
    assert extract_education("B.Tech in Computer Science") == "bachelor"
    assert extract_education("Master of Science in Data Science") == "master"
    assert extract_education("No degree mentioned here") == "unspecified"
    print("test_extract_education passed")


def test_parse_job_description_sections():
    jd_text = """
    Required Skills:
    Python, SQL, Git

    Preferred Skills:
    Docker, AWS
    """
    jd_data = parse_job_description(jd_text)
    assert "python" in jd_data["required_skills"]
    assert "docker" in jd_data["preferred_skills"]
    # Docker shouldn't ALSO be counted as required
    assert "docker" not in jd_data["required_skills"]
    print("test_parse_job_description_sections passed")


def test_calculate_score_perfect_match():
    from src.extractor import extract_candidate_data

    jd_text = "Required Skills: Python, SQL, Git\n3+ years of experience.\nBachelor's degree required."
    resume_text = (
        "Skills: Python, SQL, Git\n"
        "5 years of experience as a backend developer.\n"
        "B.Tech in Computer Science.\n"
        "Projects:\nBuilt a REST API.\n"
        "Certifications:\nAWS Certified.\n"
    )
    jd_data = parse_job_description(jd_text)
    resume_data = extract_candidate_data(resume_text)
    score = calculate_score(resume_data, jd_data, resume_text)

    assert score["overall_score"] > 80, f"expected a high score, got {score['overall_score']}"
    assert score["missing_required_skills"] == []
    print("test_calculate_score_perfect_match passed")


def test_calculate_score_weak_match():
    from src.extractor import extract_candidate_data

    jd_text = "Required Skills: Python, SQL, Git, AWS, Docker\n5+ years of experience."
    resume_text = "Skills: Microsoft Excel, PowerPoint\nEducation: B.Com"
    jd_data = parse_job_description(jd_text)
    resume_data = extract_candidate_data(resume_text)
    score = calculate_score(resume_data, jd_data, resume_text)

    assert score["overall_score"] < 40, f"expected a low score, got {score['overall_score']}"
    print("test_calculate_score_weak_match passed")


def test_parser_handles_missing_file():
    try:
        extract_text("resumes/does_not_exist.pdf")
        assert False, "should have raised ParsingError"
    except ParsingError:
        print("test_parser_handles_missing_file passed")


def test_parser_handles_txt():
    # Uses a real sample resume shipped in resumes/
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "resumes", "candidate_01_strong.txt")
    if os.path.exists(path):
        text = extract_text(path)
        assert len(text) > 50
        print("test_parser_handles_txt passed")
    else:
        print("test_parser_handles_txt skipped (sample resume not found)")


if __name__ == "__main__":
    test_extract_skills_basic()
    test_extract_skills_no_false_positive()
    test_extract_experience_years()
    test_extract_education()
    test_parse_job_description_sections()
    test_calculate_score_perfect_match()
    test_calculate_score_weak_match()
    test_parser_handles_missing_file()
    test_parser_handles_txt()
    print("\nAll tests passed.")
