"""Mock ML service for OpenSource Companion.

This module is intentionally importable from FastAPI as:
    from ml.ml_service import classify_issue, get_recommendations, predict_pr_success

Stage 1 delivers deterministic mock behavior so the backend can run before the
real models are trained and wired in.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

__all__ = ["classify_issue", "get_recommendations", "predict_pr_success"]

_MOCK_DIFFICULTY = "Beginner"
_MOCK_SUCCESS_PROBABILITY = 0.5


def classify_issue(title: str, body: str, labels: list[str]) -> str:
    """Return a deterministic placeholder difficulty label."""
    return _MOCK_DIFFICULTY


def get_recommendations(
    user_id: int,
    user_profile: dict,
    candidate_issues: list[dict],
    top_k: int = 10,
) -> list[dict]:
    """Return the first ``top_k`` issues with a mock match score."""
    if top_k <= 0:
        return []

    recommendations: list[dict] = []
    for issue in candidate_issues[:top_k]:
        ranked_issue = deepcopy(issue)
        ranked_issue["match_score"] = 0.5
        recommendations.append(ranked_issue)

    return recommendations


def predict_pr_success(user_profile: dict, issue: dict) -> float:
    """Return a placeholder PR success probability."""
    return _MOCK_SUCCESS_PROBABILITY
