"""
agent.py
--------
The orchestrator. This is the "brain" that runs every step of the
pipeline in order and ties all the other modules together:

  load JD -> for each resume: parse -> extract -> score -> reason
  -> rank everyone -> write CSV/JSON

Keeping this separate from main.py means the CLI (main.py) stays
tiny and focused on user interaction (prompts/printing), while all
the actual pipeline logic lives here and could be reused by a future
UI (e.g. Streamlit) without duplicating anything.
"""

import os
from src.parser import extract_text, ParsingError
from src.extractor import extract_candidate_data, parse_job_description
from src.scorer import calculate_score
from src.reasoning import generate_reasoning
from src.ranker import rank_candidates
from src.output_writer import write_csv, write_json
from src.report_generator import write_html_report
from src.utils import read_text_file, clean_text

SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".txt")


def run_screening(jd_path: str, resumes_folder: str, output_folder: str, verbose_print=print):
    """
    Runs the full pipeline and returns the ranked list of results.
    `verbose_print` defaults to print() but can be swapped out (e.g.
    for a Streamlit callback) without changing this function's logic.
    """
    # --- Load & parse JD -------------------------------------------------
    jd_raw = clean_text(read_text_file(jd_path))
    jd_data = parse_job_description(jd_raw)
    verbose_print(
        f"Job description loaded. Found {len(jd_data['required_skills'])} required "
        f"skill(s) and {len(jd_data['preferred_skills'])} preferred skill(s)."
    )

    # --- Discover resumes --------------------------------------------------
    resume_files = sorted(
        f for f in os.listdir(resumes_folder)
        if f.lower().endswith(SUPPORTED_EXTENSIONS)
    )
    if not resume_files:
        raise FileNotFoundError(f"No .pdf/.docx/.txt resumes found in {resumes_folder}")

    verbose_print(f"{len(resume_files)} resume(s) found.\n")

    results = []
    skipped = []

    for filename in resume_files:
        file_path = os.path.join(resumes_folder, filename)
        candidate_name = os.path.splitext(filename)[0]

        try:
            verbose_print(f"Analyzing {filename}...")
            resume_text = extract_text(file_path)
            resume_data = extract_candidate_data(resume_text)
            score_data = calculate_score(resume_data, jd_data, resume_text)
            reasoning = generate_reasoning(candidate_name, score_data)

            results.append({
                "candidate": candidate_name,
                "file": filename,
                "overall_score": score_data["overall_score"],
                "skills_score": score_data["skills_score"],
                "experience_score": score_data["experience_score"],
                "semantic_score": score_data["semantic_score"],
                "education_score": score_data["education_score"],
                "projects_score": score_data["projects_score"],
                "certifications_score": score_data["certifications_score"],
                "matched_required_skills": score_data["matched_required_skills"],
                "missing_required_skills": score_data["missing_required_skills"],
                "matched_preferred_skills": score_data["matched_preferred_skills"],
                "similarity_method": score_data["similarity_method"],
                "reasoning": reasoning,
            })
        except ParsingError as e:
            verbose_print(f"  Skipped ({e})")
            skipped.append({"file": filename, "reason": str(e)})

    if not results:
        raise RuntimeError("No resumes could be successfully processed.")

    verbose_print("\nRanking candidates...")
    ranked = rank_candidates(results)

    csv_path = os.path.join(output_folder, "ranked_candidates.csv")
    json_path = os.path.join(output_folder, "ranked_candidates.json")
    report_path = os.path.join(output_folder, "summary_report.html")
    write_csv(ranked, csv_path)
    write_json({"results": ranked, "skipped": skipped}, json_path)
    write_html_report(ranked, report_path, jd_title=os.path.basename(jd_path))

    verbose_print(f"\nResults written to:\n  {csv_path}\n  {json_path}\n  {report_path}")
    if skipped:
        verbose_print(f"\n{len(skipped)} file(s) were skipped due to parsing errors:")
        for s in skipped:
            verbose_print(f"  - {s['file']}: {s['reason']}")

    return ranked
