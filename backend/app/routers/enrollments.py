# ── routers/enrollments.py ──────────────────────────────────────
# Enrollment API endpoints
# ────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.enrollments import (
    EnrollmentCreateRequest, 
    EnrollmentCreatedResponse, 
    EnrollmentCreatedData,
    EnrollmentListResponse,
    EnrollmentItem,
    IssueBrief
)
from app.services.enrollment_service import create_enrollment, get_user_enrollments

router = APIRouter()


@router.post("", response_model=EnrollmentCreatedResponse, status_code=status.HTTP_201_CREATED)
def enroll_in_issue(
    body: EnrollmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enroll the current user in a specific issue.
    """
    enrollment = create_enrollment(db, current_user.id, body.issue_id)
    
    return EnrollmentCreatedResponse(
        message="Enrolled successfully",
        data=EnrollmentCreatedData(enrollment_id=enrollment.id)
    )


@router.get("/{user_id}", response_model=EnrollmentListResponse)
def get_enrollments(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all enrollments for a specific user.
    Security: Users can only view their own enrollments.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view these enrollments"
        )
        
    enrollments = get_user_enrollments(db, user_id)
    
    # Map to schema
    items = [
        EnrollmentItem(
            enrollment_id=e.id,
            status=e.status.value,
            issue=IssueBrief(
                id=e.issue.id,
                title=e.issue.title,
                difficulty=e.issue.difficulty.value
            )
        )
        for e in enrollments
    ]
    
    return EnrollmentListResponse(
        message="Enrollments fetched",
        data=items
    )
