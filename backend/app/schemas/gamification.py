# ── schemas/gamification.py ─────────────────────────────────────
# Pydantic models for gamification responses
# ────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import List


class LeaderboardEntry(BaseModel):
    user_id: int
    username: str
    points_total: int

    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    message: str
    data: List[LeaderboardEntry]
