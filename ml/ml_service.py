"""
ml_service.py
Importable ML module for OpenSource Companion.

Exposes three functions:
    classify_issue(title, body, labels)         → "Beginner" | "Intermediate" | "Advanced"
    get_recommendations(user_id, user_profile,  → list[dict]
                        candidate_issues, top_k)
    predict_pr_success(user_profile, issue)     → float

Models are loaded ONCE at import time. If model files are missing,
each function falls back to safe defaults so the backend never crashes.
"""

import os
import re
import logging

import joblib
import numpy as np

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────

_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR = os.path.join(_BASE_DIR, "..", "models")

def _model_path(filename: str) -> str:
    return os.path.join(_MODELS_DIR, filename)

# ══════════════════════════════════════════════════════════════════════════════
# ── 1. Load Classifier at import time ────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

_classifier       = None
_tfidf_vectorizer = None
_label_encoder    = None
_classifier_ready = False

def _load_classifier():
    global _classifier, _tfidf_vectorizer, _label_encoder, _classifier_ready
    try:
        _classifier       = joblib.load(_model_path("classifier.pkl"))
        _tfidf_vectorizer = joblib.load(_model_path("tfidf_vectorizer.pkl"))
        _label_encoder    = joblib.load(_model_path("label_encoder.pkl"))
        _classifier_ready = True
        logger.info("✅ Classifier models loaded successfully.")
    except FileNotFoundError:
        logger.warning(
            "⚠️  Classifier model files not found in models/. "
            "classify_issue() will return 'Beginner' as fallback. "
            "Run ml/train_classifier.py to train the models."
        )
    except Exception as e:
        logger.error(f"❌ Failed to load classifier models: {e}")

_load_classifier()

# ══════════════════════════════════════════════════════════════════════════════
# ── 2. classify_issue ────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _clean_text(text: str) -> str:
    """Same preprocessing as training — MUST be identical."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"```[\s\S]*?```", " code ", text)
    text = re.sub(r"[^a-z0-9\s\-_]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classify_issue(title: str, body: str, labels: list[str]) -> str:
    """
    Classify a GitHub issue into Beginner / Intermediate / Advanced.

    Args:
        title  : Issue title string.
        body   : Issue body/description string.
        labels : List of GitHub label name strings (e.g. ["bug", "good first issue"]).

    Returns:
        One of: "Beginner", "Intermediate", "Advanced"
    """
    if not _classifier_ready:
        logger.warning("classify_issue: model not loaded, returning fallback 'Beginner'.")
        return "Beginner"

    try:
        # ── Build text exactly as done during training ──
        clean_title = _clean_text(title)
        clean_body  = _clean_text(body)[:500]   # truncate to 500 chars
        # Title repeated 3x to match training weight
        combined = f"{clean_title} {clean_title} {clean_title} {clean_body}".strip()

        if not combined:
            return "Beginner"

        # ── TF-IDF transform ──
        X = _tfidf_vectorizer.transform([combined])

        # ── Predict ──
        encoded_pred = _classifier.predict(X)[0]
        label        = _label_encoder.inverse_transform([encoded_pred])[0]

        return str(label)

    except Exception as e:
        logger.error(f"classify_issue error: {e}")
        return "Beginner"


# ══════════════════════════════════════════════════════════════════════════════
# ── 3. get_recommendations  (MOCK — replaced in Phase 2) ─────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def get_recommendations(
    user_id: int,
    user_profile: dict,
    candidate_issues: list[dict],
    top_k: int = 10,
) -> list[dict]:
    """
    Return top_k issues ranked by relevance to the user profile.

    Currently returns candidate_issues[:top_k] with a mock match_score.
    Will be replaced with SBERT + FAISS in Phase 2.

    Args:
        user_id          : DB user ID.
        user_profile     : Dict with keys: skill_level, preferred_languages,
                           enrolled_issue_ids, merged_pr_count,
                           enrolled_issue_texts (list[str]).
        candidate_issues : List of issue dicts (already filtered by backend
                           for skill level, language, not enrolled).
        top_k            : Number of results to return.

    Returns:
        List of issue dicts with "match_score" field added (float 0–1).
    """
    if not candidate_issues:
        return []

    # Mock: return first top_k with a placeholder score
    results = []
    for issue in candidate_issues[:top_k]:
        scored = dict(issue)
        scored["match_score"] = round(0.75, 4)
        results.append(scored)

    logger.info(
        f"get_recommendations (mock): returning {len(results)} issues for user {user_id}."
    )
    return results


# ══════════════════════════════════════════════════════════════════════════════
# ── 4. predict_pr_success  (MOCK — replaced in Phase 3) ──────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def predict_pr_success(user_profile: dict, issue: dict) -> float:
    """
    Predict probability (0.0 – 1.0) that a PR will be merged.

    Currently returns 0.75 as an optimistic default.
    Will be replaced with a Random Forest model in Phase 3.

    Args:
        user_profile : Dict with user info (skill_level, merged_pr_count, etc.)
        issue        : Dict with issue info (difficulty, language, labels, etc.)

    Returns:
        Float probability between 0.0 and 1.0.
    """
    logger.debug("predict_pr_success (mock): returning 0.75")
    return 0.75


# ══════════════════════════════════════════════════════════════════════════════
# ── Quick self-test (run as script) ──────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n── classify_issue tests ──")

    tests = [
        {
            "title": "Fix typo in README",
            "body": "There is a spelling mistake in the README file on line 12. Easy fix for newcomers.",
            "labels": ["good first issue", "documentation"],
            "expected": "Beginner",
        },
        {
            "title": "Add pagination support to REST API",
            "body": "We need to implement cursor-based pagination for the /users endpoint. Should handle edge cases.",
            "labels": ["help wanted", "enhancement"],
            "expected": "Intermediate",
        },
        {
            "title": "Optimize CUDA kernel for transformer attention mechanism",
            "body": "The current FlashAttention implementation has suboptimal memory bandwidth utilization on A100 GPUs. We need to rewrite the backward pass kernel.",
            "labels": ["performance", "cuda"],
            "expected": "Advanced",
        },
    ]

    all_passed = True
    for t in tests:
        result = classify_issue(t["title"], t["body"], t["labels"])
        status = "✅" if result == t["expected"] else "⚠️ "
        if result != t["expected"]:
            all_passed = False
        print(f"  {status} '{t['title'][:50]}...'")
        print(f"     Expected: {t['expected']}  |  Got: {result}")

    print()
    if not _classifier_ready:
        print("ℹ️  Running with MOCK (model files not found). Train first:")
        print("   python ml/train_classifier.py")
    elif all_passed:
        print("✅ All classify_issue tests passed.")
    else:
        print("⚠️  Some tests failed — check model quality or training data.")

    print("\n── get_recommendations test ──")
    sample_issues = [
        {"issue_id": 1, "title": "Fix button alignment", "body": "...", "labels": ["bug"], "language": "JavaScript", "difficulty": "Beginner"},
        {"issue_id": 2, "title": "Add dark mode", "body": "...", "labels": ["enhancement"], "language": "CSS", "difficulty": "Intermediate"},
    ]
    recs = get_recommendations(
        user_id=42,
        user_profile={"skill_level": "Beginner", "preferred_languages": ["JavaScript"], "enrolled_issue_ids": [], "merged_pr_count": 0, "enrolled_issue_texts": []},
        candidate_issues=sample_issues,
        top_k=5,
    )
    print(f"  Returned {len(recs)} recommendations. match_score: {recs[0]['match_score']}")

    print("\n── predict_pr_success test ──")
    prob = predict_pr_success(
        user_profile={"skill_level": "Beginner", "merged_pr_count": 1},
        issue={"difficulty": "Beginner", "language": "Python", "labels": ["good first issue"]},
    )
    print(f"  PR success probability: {prob}")
    print("\nDone.")