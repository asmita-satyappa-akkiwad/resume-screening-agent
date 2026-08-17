# Resume Screening Agent

![Tests](https://github.com/asmita-satyappa-akkiwad/resume-screening-agent/actions/workflows/test.yml/badge.svg)

*(Replace `YOUR_USERNAME/YOUR_REPO` above with your actual GitHub path once you push — the badge will automatically show a green "passing" once Actions runs.)*

An AI agent that takes a Job Description and a folder of resumes (PDF/DOCX/TXT),
scores every candidate against the JD using a transparent, reproducible scoring
system, and produces a ranked shortlist with explanations — as CLI output, CSV,
and JSON.

Built for a 24-Hour AI Agent Challenge (Junior AI Research Associate round).

## Problem Statement

Manually screening dozens of resumes against a job description is slow and
inconsistent — different reviewers weigh things differently, and it's easy to
lose track of *why* a candidate was ranked where they were. This project
automates the first pass: parse, score, rank, and explain — consistently,
every time.

## Solution

The agent runs a pipeline: parse each resume → extract structured info
(skills, experience, education, projects, certifications) → compute a
deterministic 0–100 score against the JD → generate a short explanation →
rank everyone → write CSV/JSON.

## Features

- Parses **PDF, DOCX, and TXT** resumes
- Extracts skills, experience (years), education level, projects, certifications
- Transparent **0–100 point scoring formula** (fully documented below)
- **Semantic similarity** via sentence embeddings (`all-MiniLM-L6-v2`), with
  automatic fallback to TF-IDF if the embedding model can't be loaded (e.g. no
  internet) — the app never crashes because of this
- Short **AI-generated reasoning** per candidate (LLM), with a rule-based
  template fallback if no API key is configured
- Handles 10+ resumes per run, skips unreadable files gracefully
- Outputs **CSV**, **JSON**, and a styled, self-contained **HTML summary report**
  (top-3 highlight cards + full ranked table)
- **Streamlit web UI** (`app.py`) — upload JD + resumes, see rankings, a score
  chart, and per-candidate reasoning in the browser; same pipeline as the CLI
- Ignores protected/irrelevant personal characteristics (see Fairness below)

## Architecture

```
JD (.txt) ──► parse_job_description() ──► JD requirements (skills, exp, edu)
                                                    │
Resumes/ ──► extract_text() ──► clean_text() ──► extract_candidate_data()
  (pdf/docx/txt)                                    │
                                                     ▼
                                    calculate_score(candidate, jd)
                                    - skills match (embedding/TF-IDF too)
                                    - experience match
                                    - education match
                                    - projects / certifications presence
                                                     │
                                                     ▼
                                    generate_reasoning() (LLM or template)
                                                     │
                                                     ▼
                                    rank_candidates() ──► CSV + JSON
```

## Tech Stack

| Purpose | Library | Why |
|---|---|---|
| PDF parsing | PyMuPDF (`fitz`) | Fast, reliable, simple API |
| DOCX parsing | `python-docx` | Standard for `.docx`, reads tables too |
| Skill/entity extraction | Custom keyword matcher (`skills_db.py`) | Deterministic, free, fast, explainable |
| Semantic similarity | `sentence-transformers` (`all-MiniLM-L6-v2`) | Small (~80MB), free, local, understands meaning beyond keywords |
| Similarity fallback | `scikit-learn` TF-IDF + cosine similarity | Works fully offline, no model download needed |
| Reasoning | Anthropic API (optional) | Turns numeric scores into a readable explanation |
| Output | `csv` / `json` (stdlib) | No extra dependency needed |
| Interface | CLI (`main.py`) | Fast to build, zero deployment risk |

## How It Works

1. **Parsing** (`src/parser.py`) — `extract_text(file_path)` detects the file
   type by extension and routes to the right library, returning plain text.
2. **Extraction** (`src/extractor.py`) — regex + keyword matching pulls out
   skills (against a curated list in `skills_db.py`), years of experience,
   education level, a "Projects" section, and certification mentions. The
   *same* functions parse the JD, so comparisons are apples-to-apples.
3. **Similarity** (`src/similarity.py`) — embeds resume text and JD text with
   `all-MiniLM-L6-v2` and computes cosine similarity (0–1). Falls back to
   TF-IDF + cosine similarity automatically if the embedding model can't load.
4. **Scoring** (`src/scorer.py`) — combines skill match, experience match,
   semantic similarity, education match, and project/cert presence into one
   0–100 score (formula below).
5. **Reasoning** (`src/reasoning.py`) — an optional LLM call turns the score
   breakdown into 2–3 readable sentences. Falls back to a template if no API
   key is set.
6. **Ranking** (`src/ranker.py`) — sorts candidates by score, assigns ranks.
7. **Output** (`src/output_writer.py`) — writes `ranked_candidates.csv` and
   `ranked_candidates.json`.

## Project Structure

```
resume-screening-agent/
├── resumes/              # sample resumes (pdf/docx/txt, 11 files)
├── data/
│   └── job_description.txt
├── output/
│   ├── ranked_candidates.csv
│   ├── ranked_candidates.json
│   └── summary_report.html
├── src/
│   ├── parser.py          # file -> raw text
│   ├── skills_db.py        # curated skill/synonym list
│   ├── extractor.py        # text -> structured data (skills, exp, edu...)
│   ├── similarity.py       # embeddings + TF-IDF fallback
│   ├── scorer.py           # structured data -> 0-100 score
│   ├── reasoning.py        # score -> explanation (LLM + fallback)
│   ├── ranker.py           # sorts candidates
│   ├── output_writer.py    # CSV/JSON writers
│   ├── report_generator.py # builds the HTML summary report
│   └── agent.py            # orchestrates the whole pipeline
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
├── main.py                 # CLI entry point
└── app.py                  # Streamlit web UI
```

## Installation

```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and add your Anthropic API key if you want
LLM-generated reasoning text:

```
ANTHROPIC_API_KEY=your_key_here
```

**The app runs fine without this.** Without a key, it falls back to a
rule-based reasoning template built directly from the score breakdown.

## How to Run

Interactive:
```bash
python main.py
```
You'll be prompted for the JD path and resumes folder (defaults shown in brackets).

Non-interactive:
```bash
python main.py --jd data/job_description.txt --resumes resumes --output output
```

Expected console output:
```
Processing resumes...

Job description loaded. Found 9 required skill(s) and 5 preferred skill(s).
11 resume(s) found.

Analyzing candidate_01_strong.txt...
...
Ranking candidates...

Results:

1. candidate_01_strong — 82.78/100
2. candidate_08_strong_alt — 76.78/100
...

Done. See 'output/ranked_candidates.csv' and 'output/ranked_candidates.json' for full details.
```

Every run also writes `output/summary_report.html` — a self-contained, styled report with the top 3 candidates highlighted and a full ranked table. Open it directly in any browser, no server needed.

## Web UI (Streamlit)

For an interactive, visual version of the same pipeline:
```bash
streamlit run app.py
```
This opens a browser tab where you can upload (or paste) a JD, upload multiple resumes, and click **Run Screening**. It shows a 🥇🥈🥉 top-3 highlight, a bar chart comparing every candidate's score, a full sortable table, per-candidate reasoning, and download buttons for the CSV/JSON/HTML report — all powered by the exact same `run_screening()` function the CLI uses, so results are identical either way.

## Sample Job Description

See [`data/job_description.txt`](data/job_description.txt) — a Junior AI
Research Associate role requiring Python, ML/NLP, REST APIs, SQL, and Git,
with Docker/AWS/Flask listed as preferred.

## Sample Resumes

`resumes/` contains 11 sample resumes covering: a strong match, a medium
match, a weak/irrelevant-field match, a candidate missing key required
skills, an unusually formatted resume, a fresher with only projects, a
resume with personal/irrelevant info included, a `.docx` file, a `.pdf`
file, and one deliberately empty file (to test graceful error handling).

## Sample Output

See [`output/ranked_candidates.csv`](output/ranked_candidates.csv) and
[`output/ranked_candidates.json`](output/ranked_candidates.json) for a real
run's output (generated against the sample JD and resumes above).

## Scoring Methodology

Every resume gets a score out of 100, built from six deterministic
components — see [`SCORING.md`](SCORING.md) for the full breakdown with
formulas and reasoning for each weight.

Summary:

| Component | Points |
|---|---|
| Required skills match | 30 |
| Preferred skills match | 10 |
| Experience relevance | 25 |
| Semantic similarity (embeddings/TF-IDF) | 15 |
| Education match | 10 |
| Projects present | 7 |
| Certifications present | 3 |

These weights live in [`config.json`](config.json) at the project root rather
than being hardcoded, so they can be tuned per role (e.g. weighting
experience higher for a senior position) without touching any Python code.
If `config.json` is missing or a key is left out, `src/scorer.py` falls back
to these same default values, so removing the file never breaks anything.

**The score is fully deterministic** — the same resume + JD always produces
the same score. No randomness, and the LLM never touches the score, only the
explanation text.

## NLP Methodology

- **Skill extraction**: keyword/synonym matching against a curated skill
  list (`skills_db.py`), with word-boundary regex so short terms (e.g. "r",
  "c") don't match inside unrelated words.
- **Semantic similarity**: sentence embeddings from `all-MiniLM-L6-v2`
  (a small, free, local sentence-transformer model) compared via cosine
  similarity. This catches conceptual matches that keyword matching misses —
  e.g. "built REST APIs with Flask" scoring well against "backend
  development experience" even without exact keyword overlap.
- **Fallback**: if the embedding model can't load (no internet, restricted
  environment), the system automatically switches to TF-IDF + cosine
  similarity using `scikit-learn`, which needs no download.

## AI/LLM Usage

An LLM (Claude, via the Anthropic API) is used **only** to generate the
2–3 sentence human-readable explanation for each candidate's score — never
to compute the score itself. This is a deliberate design choice: LLM output
for a raw numeric score would be inconsistent across runs and hard to
defend in an interview ("why did they get 84 and not 85?"). Deterministic
scoring + LLM explanation gives us both reproducibility and readability.

If no API key is set, or the call fails for any reason, a template-based
explanation is generated instead from the same score breakdown data — the
pipeline never blocks or crashes on this step.

## Design Decisions

- **Deterministic scoring, LLM only for explanation** — reproducibility over
  novelty.
- **Curated skill list over free-form NER** — faster, cheaper, and far
  easier to explain and defend than training/using a named-entity model for
  a 24-hour build.
- **Embeddings with automatic TF-IDF fallback** — best available quality,
  but never a hard dependency on internet access.
- **CLI as the primary interface, with an optional Streamlit UI on top** —
  the CLI stays the reliable, scriptable path; the UI (`app.py`) is a thin
  presentation layer over the exact same `run_screening()` pipeline, so
  there's one single source of truth for scoring either way.

## Fairness Considerations

The extractors deliberately only look for **job-relevant qualifications**
(skills, experience, education, projects, certifications). The system does
not look for, extract, or score based on gender, age, date of birth,
religion, caste, race, marital status, photographs, or home address, even
if such information appears on a resume (see `candidate_07_irrelevant_info.txt`
in the samples, which includes this kind of data and is scored purely on
technical qualifications). This is a design constraint, not just a
post-hoc filter — the scoring formula has no component that could weight
any protected characteristic.

## Limitations

- Skill extraction is keyword-based, so skills phrased in ways not covered
  by `skills_db.py`/`SYNONYMS` won't be picked up. Extending the list is
  straightforward but manual.
- Section detection (Projects, Education, etc.) relies on common header
  phrasing; heavily unconventional resume layouts may extract less cleanly.
- Experience-years extraction looks for explicit "X years" phrasing; resumes
  that only list dates (e.g. "2021–2023") without stating years won't be
  picked up.
- Scanned/image-only PDFs produce no extractable text and are skipped
  (no OCR in this version).
- LLM reasoning cost/security: API calls send resume-derived text (skills,
  years, education level — not full resume text) to the Anthropic API. No
  API key is ever hardcoded; it's read from `.env`, which is gitignored.

## Tradeoffs

- **Why Python?** Best library support for parsing and NLP, and the
  fastest path to a working solution in 24 hours.
- **Why PyMuPDF over other PDF libraries?** Fast, actively maintained,
  simple text-extraction API.
- **Why embeddings over pure TF-IDF?** Embeddings capture meaning, not just
  word overlap — better matches for resumes phrased differently than the
  JD. TF-IDF is kept as a free, offline-friendly fallback rather than the
  primary method, since it's weaker at catching paraphrased skills.
- **Why not fine-tune a model?** No labeled training data, and totally
  unnecessary for a keyword + embedding similarity approach that already
  meets the requirements — fine-tuning would burn most of the 24 hours for
  uncertain benefit.
- **Why not a vector database?** At most a few dozen resumes per run — an
  in-memory list and a couple of cosine similarity calls is simpler, faster
  to build, and just as fast to run at this scale. A vector DB would only
  earn its complexity at much higher volume (see "scaling" below).
- **Why deterministic scoring?** Reproducibility and defensibility — you can
  always explain exactly why a score is what it is.
- **Why an LLM at all, then?** Explanations in natural language are more
  useful to a human reviewer than a table of numbers, and this is genuinely
  a task LLMs are good at, used in the right place (text generation, not
  numeric judgment).
- **Why CLI instead of a frontend?** Zero deployment risk, faster to build
  and test within 24 hours. A UI is presentation, not the core hard problem.

## Future Improvements

- OCR support for scanned/image-only PDFs
- Expandable/editable skill list via a config file instead of hardcoded list
- Batch LLM calls (single request for multiple candidates) to reduce API
  calls and cost at higher volume
- Confidence indicators when a resume's structure couldn't be reliably
  parsed (e.g. no clear sections found)

## Example Execution

```bash
python main.py --jd data/job_description.txt --resumes resumes --output output
```
See "How to Run" above for full sample console output.

## Challenge Requirements Satisfied

- [x] Parses PDF, DOCX, TXT resumes
- [x] Extracts skills, experience, education, projects, certifications
- [x] NLP-based similarity/relevance method (embeddings + TF-IDF fallback)
- [x] Relevance score per candidate (0-100)
- [x] Ranks candidates highest to lowest
- [x] Reasoning explaining each score
- [x] Handles 10+ resumes in a single run (11 sample resumes included)
- [x] Machine-readable output: CSV and JSON
- [x] JD, sample resumes, ranked output, scoring explanation, README, tradeoffs all included
