# ── schemas/users.py ────────────────────────────────────────────
# Pydantic models for user profile and badges responses
# ────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ── Profile ──────────────────────────────────────────────────────

class UserStats(BaseModel):
    completed_contributions: int
    active_enrollments: int
    badges_earned: int


class UserProfileData(BaseModel):
    user_id: int
    username: str
    skill_level: str
    primary_language: Optional[str] = None
    points_total: int
    is_mentor: bool
    stats: UserStats


class UserProfileResponse(BaseModel):
    message: str
    data: UserProfileData


# ── Badges ───────────────────────────────────────────────────────

class UserBadgeItem(BaseModel):
    badge_id: int
    name: str
    description: str
    earned_at: datetime

    class Config:
        from_attributes = True


class UserBadgesResponse(BaseModel):
    message: str
    data: List[UserBadgeItem]
