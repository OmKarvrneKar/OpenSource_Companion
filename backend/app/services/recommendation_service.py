# ── services/recommendation_service.py ──────────────────────────
# Recommendation engine — DB filtering with ML integration hook
# ────────────────────────────────────────────────────────────────

import logging
from sqlalchemy.orm import Session
from app.models import Issue, User, Enrollment, IssueState
from typing import List

logger = logging.getLogger(__name__)


def get_recommendations(db: Session, user: User) -> List[Issue]:
    """
    Primary recommendation function.
    Attempts ML-powered recommendations first, falls back to DB filtering.
    """
    # ── ML integration hook ──────────────────────────────────────
    try:
        from ml.ml_service import get_ml_recommendations
        issues = get_ml_recommendations(db, user)
        if issues:
            logger.info(f"ML recommendations returned {len(issues)} results for user {user.id}")
            return issues
    except ImportError:
        logger.debug("ML service not available — using DB filtering fallback")
    except Exception as e:
        logger.warning(f"ML recommendation failed, falling back to DB: {e}")

    # ── DB fallback ──────────────────────────────────────────────
    return _get_db_recommendations(db, user)


def _get_db_recommendations(db: Session, user: User) -> List[Issue]:
    """
    Database-driven recommendation fallback.
    Filters by skill level and language, excludes already-enrolled issues.
    """
    # 1. Get IDs of issues the user is already enrolled in
    enrolled_issue_ids = [
        r[0] for r in db.query(Enrollment.issue_id).filter(
            Enrollment.user_id == user.id
        ).all()
    ]

    # 2. Build query — open issues matching skill level
    query = db.query(Issue).filter(
        Issue.state == IssueState.open,
        Issue.difficulty == user.skill_level,
    )

    # 3. Exclude already-enrolled issues
    if enrolled_issue_ids:
        query = query.filter(Issue.id.not_in(enrolled_issue_ids))

    # 4. Filter by language if set
    if user.primary_language:
        query = query.filter(Issue.language == user.primary_language)

    results = query.limit(10).all()

    # 5. If language filter returns nothing, try without it
    if not results and user.primary_language:
        query = db.query(Issue).filter(
            Issue.state == IssueState.open,
            Issue.difficulty == user.skill_level,
        )
        if enrolled_issue_ids:
            query = query.filter(Issue.id.not_in(enrolled_issue_ids))
        results = query.limit(10).all()
        logger.info(f"No results for language '{user.primary_language}', broadened search")

    logger.info(f"DB recommendations returned {len(results)} results for user {user.id}")
    return results
