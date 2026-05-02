# ── routers/recommendations.py ──────────────────────────────────
# Recommendation API endpoints
# ────────────────────────────────────────────────────────────────

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.recommendations import RecommendationResponse, RecommendationItem, RepoBrief
from app.services.recommendation_service import get_recommendations

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=RecommendationResponse)
def get_recommendations_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recommended issues for the current user based on skill level and language.
    Uses ML when available, falls back to DB filtering.
    """
    issues = get_recommendations(db, current_user)

    recommendations = []
    for issue in issues:
        recommendations.append(
            RecommendationItem(
                issue_id=issue.id,
                title=issue.title,
                difficulty=issue.difficulty.value if issue.difficulty else "unknown",
                language=issue.language,
                repo=RepoBrief(
                    name=issue.repo.name,
                    owner=issue.repo.owner
                )
            )
        )

    logger.info(f"Returned {len(recommendations)} recommendations for user {current_user.id}")

    return RecommendationResponse(
        message="Recommendations fetched",
        data=recommendations
    )
