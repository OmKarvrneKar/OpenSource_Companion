# ── services/enrollment_service.py ──────────────────────────────
# Enrollment lifecycle management
# ────────────────────────────────────────────────────────────────

import logging
from sqlalchemy.orm import Session
from app.models import Enrollment, EnrollmentStatus, Issue, IssueState
from fastapi import HTTPException, status
from typing import List

logger = logging.getLogger(__name__)


def create_enrollment(db: Session, user_id: int, issue_id: int) -> Enrollment:
    """
    Creates a new enrollment for a user.
    Validates: no active enrollment, issue exists, issue is open.
    """
    # 1. Check if user already has an active enrollment
    active_enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == EnrollmentStatus.enrolled
    ).first()

    if active_enrollment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has an active enrollment"
        )

    # 2. Check if issue exists
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )

    # 3. Check if issue is open
    if issue.state != IssueState.open:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enroll in a closed issue"
        )

    # 4. Create enrollment
    try:
        new_enrollment = Enrollment(
            user_id=user_id,
            issue_id=issue_id,
            status=EnrollmentStatus.enrolled
        )
        db.add(new_enrollment)
        db.commit()
        db.refresh(new_enrollment)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create enrollment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create enrollment"
        )

    logger.info(f"Enrollment created: user={user_id}, issue={issue_id}, id={new_enrollment.id}")
    return new_enrollment


def get_user_enrollments(db: Session, user_id: int) -> List[Enrollment]:
    """
    Returns all enrollments for a specific user, most recent first.
    """
    return db.query(Enrollment).filter(
        Enrollment.user_id == user_id
    ).order_by(Enrollment.enrolled_at.desc()).all()
