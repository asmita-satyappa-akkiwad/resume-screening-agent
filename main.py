"""
main.py
-------
Command-line entry point for the Resume Screening Agent.

Usage (interactive):
    python main.py

Usage (non-interactive, useful for testing/automation):
    python main.py --jd data/job_description.txt --resumes resumes --output output
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from src.agent import run_screening

load_dotenv()  # loads ANTHROPIC_API_KEY from .env if present


def main():
    parser = argparse.ArgumentParser(description="AI Resume Screening Agent")
    parser.add_argument("--jd", help="Path to the job description .txt file")
    parser.add_argument("--resumes", help="Path to the folder containing resumes")
    parser.add_argument("--output", default="output", help="Folder to write CSV/JSON results")
    args = parser.parse_args()

    jd_path = args.jd or input(
        "Enter path to Job Description [data/job_description.txt]: "
    ).strip() or "data/job_description.txt"

    resumes_folder = args.resumes or input(
        "Enter path to resumes folder [resumes]: "
    ).strip() or "resumes"

    output_folder = args.output

    if not os.path.exists(jd_path):
        print(f"Error: job description file not found at '{jd_path}'")
        sys.exit(1)
    if not os.path.isdir(resumes_folder):
        print(f"Error: resumes folder not found at '{resumes_folder}'")
        sys.exit(1)

    print("\nProcessing resumes...\n")

    try:
        ranked = run_screening(jd_path, resumes_folder, output_folder)
    except Exception as e:
        print(f"\nAgent failed: {e}")
        sys.exit(1)

    print("\nResults:\n")
    for c in ranked:
        print(f"{c['rank']}. {c['candidate']} — {c['overall_score']}/100")

    print(f"\nDone. See '{output_folder}/ranked_candidates.csv' and "
          f"'{output_folder}/ranked_candidates.json' for full details.")


if __name__ == "__main__":
    main()
