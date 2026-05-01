# ── routers/gamification.py ─────────────────────────────────────
# Gamification endpoints — leaderboard
# ────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.gamification import (
    LeaderboardResponse,
    LeaderboardEntry,
)

router = APIRouter()


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Return top 10 users ranked by points_total.
    """
    top_users = db.query(User).order_by(
        User.points_total.desc()
    ).limit(10).all()

    entries = [
        LeaderboardEntry(
            user_id=u.id,
            username=u.github_username,
            points_total=u.points_total,
        )
        for u in top_users
    ]

    return LeaderboardResponse(
        message="Leaderboard fetched",
        data=entries,
    )
