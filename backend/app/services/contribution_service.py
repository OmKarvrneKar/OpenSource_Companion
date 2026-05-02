# ── services/contribution_service.py ────────────────────────────
# Contribution verification logic
# Currently mocks the PR check — real GitHub polling added later
# ────────────────────────────────────────────────────────────────

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Enrollment, EnrollmentStatus
from app.services.gamification_service import award_points

logger = logging.getLogger(__name__)


def check_contribution(db: Session, user_id: int, enrollment_id: int) -> Enrollment:
    """
    Verify that a PR was merged for the given enrollment.
    Currently mocked — always treats PR as merged.
    """
    # 1. Fetch enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.id == enrollment_id
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )

    # 2. Security: verify ownership
    if enrollment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to check this enrollment"
        )

    # 3. Must be in enrolled status
    if enrollment.status != EnrollmentStatus.enrolled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Enrollment is already '{enrollment.status.value}', cannot check"
        )

    # 4. Simulate PR merged check (always True for now)
    #    TODO: Replace with real GitHub PR check via PyGithub
    pr_merged = True
    logger.info(f"PR check for enrollment {enrollment_id}: merged={pr_merged} (mocked)")

    if not pr_merged:
        return enrollment

    # 5. Mark enrollment as completed
    try:
        enrollment.status = EnrollmentStatus.completed
        enrollment.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(enrollment)
        logger.info(f"Enrollment {enrollment_id} marked completed for user {user_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update enrollment {enrollment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update enrollment status"
        )

    # 6. Trigger gamification (errors handled internally — won't break this flow)
    award_points(db, user_id, "merged_pr")

    return enrollment
