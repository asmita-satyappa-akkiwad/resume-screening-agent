"""
ranker.py
---------
Takes the list of scored candidates and sorts them highest-to-lowest,
assigning a rank number to each. Deliberately tiny - sorting is a
one-line job and doesn't deserve a complicated abstraction.
"""


def rank_candidates(candidates: list) -> list:
    """
    Args:
        candidates: list of dicts, each with at least "overall_score"

    Returns:
        The same list, sorted by overall_score descending, with a
        "rank" key added to each dict (1 = best).
    """
    sorted_candidates = sorted(
        candidates, key=lambda c: c["overall_score"], reverse=True
    )
    for i, c in enumerate(sorted_candidates, start=1):
        c["rank"] = i
    return sorted_candidates
