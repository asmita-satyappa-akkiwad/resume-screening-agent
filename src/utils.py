"""
utils.py
--------
Small, reusable helper functions used across the project.
Keeping these separate avoids repeating the same code in
parser.py, extractor.py, and scorer.py.
"""

import re


def clean_text(text: str) -> str:
    """
    Normalize raw extracted text so downstream steps (skill
    matching, similarity, etc.) don't get tripped up by PDF/DOCX
    extraction artifacts.

    What it does:
    - Collapses multiple spaces/newlines into single spaces
    - Removes weird control characters PDFs sometimes leave behind
    - Strips leading/trailing whitespace

    We deliberately do NOT lowercase or strip punctuation here,
    because some downstream extractors (e.g. email/phone regex,
    section headers like "Projects:") rely on case and punctuation.
    Lowercasing happens only where it's needed (e.g. skill matching).
    """
    if not text:
        return ""

    # Remove non-printable / control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)

    # Collapse multiple whitespace/newlines into a single space,
    # but keep single newlines so section detection still works.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def safe_lower(text: str) -> str:
    """Lowercase helper that won't blow up on None."""
    return (text or "").lower()


def read_text_file(path: str) -> str:
    """
    Read a .txt file, trying a couple of encodings since resumes
    are sometimes saved with Windows encodings that aren't UTF-8.
    """
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"Could not decode text file: {path}")


def find_section(text: str, section_names, next_section_names=None, max_chars=1200):
    """
    Very lightweight "section finder" for resumes.

    Resumes aren't structured documents (no guaranteed tags), so we
    look for a line that looks like a section header (e.g. "Projects",
    "PROJECTS:", "Work Experience") and grab the text that follows it,
    up until the next likely section header or a character limit.

    Args:
        text: full resume text
        section_names: list of possible header names to search for
        next_section_names: list of header names that mark the END
                             of this section (so we don't over-grab)
        max_chars: hard cap so one giant paragraph can't swallow
                   the rest of the resume

    Returns:
        The section text (str), or "" if no matching header was found.
    """
    lines = text.split("\n")
    start_idx = None

    for i, line in enumerate(lines):
        stripped = line.strip().strip(":").strip()
        for name in section_names:
            if stripped.lower() == name.lower() or (
                len(stripped) < 40 and name.lower() in stripped.lower()
            ):
                start_idx = i
                break
        if start_idx is not None:
            break

    if start_idx is None:
        return ""

    end_idx = len(lines)
    if next_section_names:
        for j in range(start_idx + 1, len(lines)):
            stripped = lines[j].strip().strip(":").strip()
            for name in next_section_names:
                if stripped.lower() == name.lower() or (
                    len(stripped) < 40 and name.lower() in stripped.lower()
                ):
                    end_idx = j
                    break
            if end_idx != len(lines):
                break

    section_text = "\n".join(lines[start_idx + 1 : end_idx]).strip()
    return section_text[:max_chars]
