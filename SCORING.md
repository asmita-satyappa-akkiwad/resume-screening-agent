# Scoring Methodology

Every candidate is scored out of 100 using six deterministic components.
The same resume + job description will always produce the same score —
there is no randomness and the LLM never influences the score, only the
written explanation.

## Components

### 1. Required Skills Match — 30 points

```
required_score = (matched_required_skills / total_required_skills) * 30
```

If the JD lists 9 required skills and a candidate's resume mentions 6 of
them, they get `(6/9) * 30 = 20` points here.

*Edge case:* if the JD parser can't find any required skills (rare parsing
gap), every candidate gets full marks for this component rather than being
unfairly zeroed out.

### 2. Preferred Skills Match — 10 points

Same formula as above, applied to the JD's "preferred/nice-to-have" skills.
A skill already counted as "required" is never double-counted as
"preferred."

### 3. Experience Relevance — 25 points

```
if min_years_required > 0:
    experience_score = min(candidate_years / min_years_required, 1.0) * 25
else:
    experience_score = min(candidate_years / 4, 1.0) * 25
```

Meeting or exceeding the JD's stated minimum experience gives full marks.
Below that, credit scales linearly (e.g. 1 year of a 2-year requirement =
half credit). If the JD doesn't state a minimum, we reward any experience
found, capped at full marks by 4 years.

### 4. Semantic Similarity — 15 points

```
similarity_score = cosine_similarity(resume_embedding, jd_embedding) * 15
```

Uses sentence embeddings (`all-MiniLM-L6-v2`) to catch conceptual overlap
that keyword matching misses (e.g. "shipped REST endpoints" vs. "API
development experience"). Falls back to TF-IDF cosine similarity if the
embedding model is unavailable.

This component is weighted lower (15 vs 30+10 for explicit skills) because
it's a "soft" signal meant to complement, not replace, explicit skill
matching — it's what makes the difference between two similarly
skills-matched resumes.

### 5. Education Match — 10 points

Education is ranked: PhD > Master's > Bachelor's > Diploma > High School.

- Candidate's level ≥ JD's required level → full 10 points
- Candidate's level is exactly one tier below → 6 points (60%)
- Candidate's level is more than one tier below → 0 points
- JD doesn't specify education → 10 points if candidate lists any
  education, 5 points if none is found

### 6. Projects & Certifications — 7 + 3 points

- **Projects (7 pts):** full marks if a "Projects" section was found in the
  resume, 0 otherwise. Kept as presence/absence rather than trying to score
  project *quality*, which would require subjective judgment.
- **Certifications (3 pts):** full marks if any certification-related text
  was found, 0 otherwise.

## Why these weights?

Required skills (30) and experience (25) carry the most weight because
they're the strongest, most direct signals of whether a candidate can do
the job — this mirrors how most human reviewers actually weigh a resume.
Semantic similarity (15) is a meaningful but secondary signal since it can
be a soft, sometimes noisy measure of overlap. Education (10) matters but
is often a minimum bar rather than a differentiator. Projects (7) and
certifications (3) are the smallest components because they're presence
checks, not depth checks — useful signal, but weaker than direct skill and
experience matches.

## Why this is defensible in an interview

Every point on a candidate's score can be traced back to a specific,
inspectable piece of resume text (the matched/missing skill lists, years
found by regex, education keyword found, etc.) — nothing is a "black box."
You can always answer "why did they get 84?" by walking through these six
numbers.
