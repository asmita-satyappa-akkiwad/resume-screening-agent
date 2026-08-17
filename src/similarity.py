"""
similarity.py
-------------
Computes a 0-1 semantic similarity score between a resume's text
and the job description's text.

WHAT ARE EMBEDDINGS?
An embedding turns a piece of text into a list of numbers (a
"vector") that captures its MEANING, not just its exact words.
Texts with similar meaning end up as vectors that point in similar
directions - even if they don't share the same words. Example:
"built REST APIs with Flask" and "backend development experience"
use almost no common words, but a good embedding model places
their vectors close together because they mean similar things.

WHAT IS COSINE SIMILARITY?
It's a way to measure how similar two vectors' DIRECTIONS are,
ignoring their length. It ranges from -1 (opposite) to 1 (identical
direction). For text embeddings it's almost always between 0 and 1
in practice. We use it because it's the standard, well-understood
way to compare embedding vectors, and it's cheap to compute.

WHY A FALLBACK?
The primary model (all-MiniLM-L6-v2) needs to be downloaded from
the internet the first time it's used (~80MB). If that download
isn't possible (no internet, firewall, offline grading environment),
the whole app shouldn't crash. So we fall back to TF-IDF + cosine
similarity, which uses only scikit-learn (already required) and
works fully offline. This is a real, defensible engineering
decision to mention in an interview: "graceful degradation instead
of a hard dependency."
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine_similarity
import numpy as np

_model = None
_model_load_attempted = False
_model_load_error = None


def _get_embedding_model():
    """
    Lazily loads the sentence-transformers model on first use, so
    the app doesn't pay the (slow) import/download cost unless the
    similarity function is actually called. Returns None if loading
    fails for any reason (e.g. no internet).
    """
    global _model, _model_load_attempted, _model_load_error

    if _model_load_attempted:
        return _model

    _model_load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        _model_load_error = str(e)
        _model = None

    return _model


def _embedding_similarity(text_a: str, text_b: str) -> float:
    model = _get_embedding_model()
    if model is None:
        return None

    vectors = model.encode([text_a, text_b])
    score = sk_cosine_similarity([vectors[0]], [vectors[1]])[0][0]
    return float(np.clip(score, 0.0, 1.0))


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
    except ValueError:
        # Happens if both texts are empty / all-stopwords after cleaning
        return 0.0
    score = sk_cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return float(np.clip(score, 0.0, 1.0))


def semantic_similarity(resume_text: str, jd_text: str) -> dict:
    """
    Returns {"score": float 0-1, "method": "embeddings" | "tfidf"}

    Tries sentence embeddings first (better quality, understands
    meaning). Falls back to TF-IDF automatically if the embedding
    model can't be loaded.
    """
    score = _embedding_similarity(resume_text, jd_text)
    if score is not None:
        return {"score": score, "method": "embeddings"}

    score = _tfidf_similarity(resume_text, jd_text)
    return {"score": score, "method": "tfidf"}
