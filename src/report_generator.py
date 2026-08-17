"""
report_generator.py
--------------------
Builds a single, self-contained HTML summary report from the ranked
results: a highlighted "Top 3" section followed by a full ranked
table. No external dependencies (no matplotlib, no internet) - pure
Python string templating - so it can't break the core pipeline if
something's missing.

This is a REPORTING layer only. It reads the same `ranked` list that
already gets written to CSV/JSON in output_writer.py - it doesn't
recompute anything, so the numbers always match.
"""

import html
import os

MEDALS = ["🥇", "🥈", "🥉"]


def _skill_badges(skills: list, css_class: str) -> str:
    if not skills:
        return "<span class='muted'>none</span>"
    return "".join(
        f"<span class='badge {css_class}'>{html.escape(s)}</span>" for s in skills
    )


def _score_bar(label: str, score: float, max_score: float) -> str:
    pct = 0 if max_score == 0 else round((score / max_score) * 100)
    return f"""
    <div class="bar-row">
      <span class="bar-label">{html.escape(label)}</span>
      <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
      <span class="bar-value">{score:g}/{max_score:g}</span>
    </div>"""


def _candidate_card(rank: int, c: dict, is_top: bool) -> str:
    medal = MEDALS[rank - 1] if is_top and rank <= 3 else ""
    card_class = "card top-card" if is_top else "card"

    bars = "".join([
        _score_bar("Skills", c["skills_score"], 40),
        _score_bar("Experience", c["experience_score"], 25),
        _score_bar("Semantic similarity", c["semantic_score"], 15),
        _score_bar("Education", c["education_score"], 10),
        _score_bar("Projects", c["projects_score"], 7),
        _score_bar("Certifications", c["certifications_score"], 3),
    ])

    return f"""
    <div class="{card_class}">
      <div class="card-header">
        <div>
          <span class="rank">{medal} #{rank}</span>
          <span class="name">{html.escape(c['candidate'])}</span>
        </div>
        <div class="overall-score">{c['overall_score']:g}<span class="out-of">/100</span></div>
      </div>
      <div class="bars">{bars}</div>
      <div class="skills-row">
        <div><strong>Matched required:</strong> {_skill_badges(c['matched_required_skills'], 'matched')}</div>
        <div><strong>Missing required:</strong> {_skill_badges(c['missing_required_skills'], 'missing')}</div>
      </div>
      <p class="reasoning">{html.escape(c['reasoning'])}</p>
      <p class="meta">similarity method: {html.escape(c['similarity_method'])} · file: {html.escape(c['file'])}</p>
    </div>"""


def _table_rows(ranked: list) -> str:
    rows = []
    for c in ranked:
        rows.append(f"""
        <tr>
          <td>{c['rank']}</td>
          <td>{html.escape(c['candidate'])}</td>
          <td class="score-cell">{c['overall_score']:g}</td>
          <td>{c['skills_score']:g}</td>
          <td>{c['experience_score']:g}</td>
          <td>{c['semantic_score']:g}</td>
          <td>{c['education_score']:g}</td>
          <td>{c['projects_score']:g}</td>
          <td>{c['certifications_score']:g}</td>
        </tr>""")
    return "".join(rows)


CSS = """
:root {
  --bg: #0f1420; --panel: #171d2e; --panel-2: #1e2740; --border: #2a3350;
  --text: #e7ebf5; --muted: #93a0c2; --accent: #6ea8fe; --good: #37c17a;
  --bad: #e2694d; --gold: #ffd166;
}
* { box-sizing: border-box; }
body {
  background: var(--bg); color: var(--text); font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  margin: 0; padding: 32px 16px 64px;
}
.wrap { max-width: 880px; margin: 0 auto; }
h1 { font-size: 24px; margin-bottom: 4px; }
.subtitle { color: var(--muted); margin-top: 0; margin-bottom: 32px; font-size: 14px; }
h2.section-title { font-size: 16px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--accent); margin: 40px 0 16px; }
.card {
  background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
  padding: 18px 20px; margin-bottom: 14px;
}
.top-card { border-color: var(--gold); box-shadow: 0 0 0 1px rgba(255,209,102,0.25); }
.card-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.rank { color: var(--muted); font-size: 13px; margin-right: 10px; }
.name { font-size: 17px; font-weight: 600; }
.overall-score { font-size: 26px; font-weight: 700; color: var(--accent); }
.out-of { font-size: 14px; color: var(--muted); font-weight: 400; }
.bars { margin: 10px 0 14px; }
.bar-row { display: grid; grid-template-columns: 130px 1fr 60px; align-items: center; gap: 10px; margin-bottom: 6px; font-size: 12px; }
.bar-label { color: var(--muted); }
.bar-track { background: var(--panel-2); border-radius: 6px; height: 8px; overflow: hidden; }
.bar-fill { background: var(--accent); height: 100%; border-radius: 6px; }
.bar-value { text-align: right; color: var(--muted); }
.skills-row { font-size: 13px; margin-bottom: 10px; display: flex; flex-direction: column; gap: 6px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; margin: 2px 4px 2px 0; }
.badge.matched { background: rgba(55,193,122,0.15); color: var(--good); border: 1px solid rgba(55,193,122,0.4); }
.badge.missing { background: rgba(226,105,77,0.15); color: var(--bad); border: 1px solid rgba(226,105,77,0.4); }
.muted { color: var(--muted); font-size: 12px; }
.reasoning { font-size: 13px; color: var(--text); line-height: 1.5; margin: 8px 0; }
.meta { font-size: 11px; color: var(--muted); margin: 0; }
table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }
th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.04em; }
.score-cell { color: var(--accent); font-weight: 700; }
tr:hover td { background: var(--panel-2); }
footer { color: var(--muted); font-size: 12px; margin-top: 40px; text-align: center; }
"""


def generate_html_report(ranked: list, jd_title: str = "Job Description") -> str:
    """
    Args:
        ranked: the same list produced by ranker.rank_candidates() /
                already written to CSV/JSON (each dict has rank,
                candidate, overall_score, sub-scores, reasoning, etc.)
        jd_title: optional label shown in the report header

    Returns:
        A complete, self-contained HTML document (string).
    """
    top = ranked[:3]
    rest = ranked[3:]

    top_cards = "".join(
        _candidate_card(c["rank"], c, is_top=True) for c in top
    )

    full_table = f"""
    <table>
      <thead>
        <tr>
          <th>Rank</th><th>Candidate</th><th>Overall</th><th>Skills</th>
          <th>Experience</th><th>Semantic</th><th>Education</th>
          <th>Projects</th><th>Certs</th>
        </tr>
      </thead>
      <tbody>{_table_rows(ranked)}</tbody>
    </table>"""

    avg_score = round(sum(c["overall_score"] for c in ranked) / len(ranked), 1) if ranked else 0

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Resume Screening Report</title>
<style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    <h1>Resume Screening Report</h1>
    <p class="subtitle">{html.escape(jd_title)} · {len(ranked)} candidate(s) screened · average score {avg_score}/100</p>

    <h2 class="section-title">Top {len(top)} Candidates</h2>
    {top_cards if top_cards else "<p class='muted'>No candidates to show.</p>"}

    <h2 class="section-title">Full Ranking ({len(ranked)})</h2>
    {full_table}

    <footer>Generated by the Resume Screening Agent · scores are computed deterministically from a transparent, documented formula.</footer>
  </div>
</body>
</html>"""


def write_html_report(ranked: list, path: str, jd_title: str = "Job Description"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    html_content = generate_html_report(ranked, jd_title)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return path
