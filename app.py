"""
app.py
------
Streamlit web UI for the Resume Screening Agent.

This is a thin presentation layer on top of the SAME pipeline the
CLI uses (src/agent.py -> run_screening()). No scoring/parsing logic
lives here - that separation is what lets the CLI, this UI, and the
test suite all rely on one single source of truth for how a resume
gets scored.

Run with:
    streamlit run app.py
"""

import os
import shutil
import tempfile

import streamlit as st

from src.agent import run_screening

st.set_page_config(page_title="Resume Screening Agent", page_icon="📋", layout="wide")

st.title("📋 Resume Screening Agent")
st.caption(
    "Upload a job description and a batch of resumes. The agent parses, "
    "scores, ranks, and explains every candidate — deterministically."
)

with st.sidebar:
    st.header("1. Job Description")
    jd_file = st.file_uploader("Upload JD (.txt)", type=["txt"])
    jd_text_input = st.text_area(
        "...or paste the JD text directly", height=180,
        placeholder="Required Skills: Python, SQL, ...",
    )

    st.header("2. Resumes")
    resume_files = st.file_uploader(
        "Upload resumes (.pdf, .docx, .txt)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

    run_button = st.button("Run Screening", type="primary", use_container_width=True)


def _save_uploads_to_temp(jd_file, jd_text_input, resume_files):
    """Writes uploaded files to a temp folder so the existing
    file-path-based pipeline (run_screening) can be reused unchanged."""
    tmp_dir = tempfile.mkdtemp(prefix="resume_agent_")
    resumes_dir = os.path.join(tmp_dir, "resumes")
    output_dir = os.path.join(tmp_dir, "output")
    os.makedirs(resumes_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    jd_path = os.path.join(tmp_dir, "job_description.txt")
    if jd_file is not None:
        with open(jd_path, "wb") as f:
            f.write(jd_file.getbuffer())
    else:
        with open(jd_path, "w", encoding="utf-8") as f:
            f.write(jd_text_input or "")

    for rf in resume_files:
        dest = os.path.join(resumes_dir, rf.name)
        with open(dest, "wb") as f:
            f.write(rf.getbuffer())

    return tmp_dir, jd_path, resumes_dir, output_dir


if run_button:
    if jd_file is None and not (jd_text_input and jd_text_input.strip()):
        st.error("Please upload a JD file or paste JD text.")
    elif not resume_files:
        st.error("Please upload at least one resume.")
    else:
        tmp_dir, jd_path, resumes_dir, output_dir = _save_uploads_to_temp(
            jd_file, jd_text_input, resume_files
        )

        log_lines = []
        log_box = st.empty()

        def ui_log(msg):
            log_lines.append(str(msg))
            log_box.code("\n".join(log_lines[-12:]))

        with st.spinner("Screening candidates..."):
            try:
                ranked = run_screening(jd_path, resumes_dir, output_dir, verbose_print=ui_log)
            except Exception as e:
                st.error(f"Screening failed: {e}")
                shutil.rmtree(tmp_dir, ignore_errors=True)
                st.stop()

        st.success(f"Screened {len(ranked)} candidate(s).")

        # --- Top 3 highlight ---
        st.subheader("🏆 Top Candidates")
        medals = ["🥇", "🥈", "🥉"]
        cols = st.columns(min(3, len(ranked)))
        for i, c in enumerate(ranked[:3]):
            with cols[i]:
                st.metric(
                    label=f"{medals[i]} {c['candidate']}",
                    value=f"{c['overall_score']:g}/100",
                )
                st.caption(c["reasoning"])

        # --- Score chart ---
        st.subheader("📊 Score Comparison")
        chart_data = {c["candidate"]: c["overall_score"] for c in ranked}
        st.bar_chart(chart_data)

        # --- Full table ---
        st.subheader("📄 Full Ranking")
        table_rows = [
            {
                "Rank": c["rank"],
                "Candidate": c["candidate"],
                "Overall": c["overall_score"],
                "Skills": c["skills_score"],
                "Experience": c["experience_score"],
                "Semantic": c["semantic_score"],
                "Education": c["education_score"],
                "Projects": c["projects_score"],
                "Certifications": c["certifications_score"],
            }
            for c in ranked
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        with st.expander("Reasoning per candidate"):
            for c in ranked:
                st.markdown(f"**#{c['rank']} {c['candidate']}** ({c['overall_score']:g}/100)")
                st.write(c["reasoning"])
                st.caption(
                    f"Matched required: {', '.join(c['matched_required_skills']) or 'none'}  \n"
                    f"Missing required: {', '.join(c['missing_required_skills']) or 'none'}"
                )
                st.divider()

        # --- Downloads ---
        st.subheader("⬇️ Downloads")
        dl_cols = st.columns(3)
        with open(os.path.join(output_dir, "ranked_candidates.csv"), "rb") as f:
            dl_cols[0].download_button("Download CSV", f, file_name="ranked_candidates.csv")
        with open(os.path.join(output_dir, "ranked_candidates.json"), "rb") as f:
            dl_cols[1].download_button("Download JSON", f, file_name="ranked_candidates.json")
        with open(os.path.join(output_dir, "summary_report.html"), "rb") as f:
            dl_cols[2].download_button("Download HTML Report", f, file_name="summary_report.html")

else:
    st.info("Upload a job description and resumes in the sidebar, then click **Run Screening**.")
