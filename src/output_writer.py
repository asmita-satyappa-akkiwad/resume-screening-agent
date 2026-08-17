"""
output_writer.py
-----------------
Writes the final ranked results to CSV and JSON files, as required
by the challenge ("machine-readable output: CSV, JSON").
"""

import csv
import json
import os

CSV_COLUMNS = [
    "rank", "candidate", "file", "overall_score", "skills_score",
    "experience_score", "semantic_score", "education_score",
    "projects_score", "certifications_score", "reasoning",
]


def write_csv(results: list, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in results:
            writer.writerow({col: r.get(col, "") for col in CSV_COLUMNS})


def write_json(results: list, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
