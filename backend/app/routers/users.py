# ── routers/users.py ────────────────────────────────────────────
# User profile and badges endpoints
# ────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.users import (
    UserProfileResponse,
    UserProfileData,
    UserStats,
    UserBadgesResponse,
    UserBadgeItem,
)
from app.services.user_service import get_user_profile_data, get_user_badges_list

router = APIRouter()


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
def get_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user profile with contribution stats.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this profile"
        )

    profile = get_user_profile_data(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserProfileResponse(
        message="Profile fetched",
        data=UserProfileData(
            user_id=profile["user_id"],
            username=profile["username"],
            skill_level=profile["skill_level"],
            primary_language=profile["primary_language"],
            points_total=profile["points_total"],
            is_mentor=profile["is_mentor"],
            stats=UserStats(**profile["stats"]),
        )
    )


@router.get("/{user_id}/badges", response_model=UserBadgesResponse)
def get_badges(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all badges earned by a user.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view these badges"
        )

    badges = get_user_badges_list(db, user_id)

    return UserBadgesResponse(
        message="Badges fetched",
        data=[UserBadgeItem(**b) for b in badges],
    )
