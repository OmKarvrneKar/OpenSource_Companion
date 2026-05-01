# ── schemas/recommendations.py ──────────────────────────────────
# Pydantic models for recommendation responses
# ────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import List, Optional


class RepoBrief(BaseModel):
    name: str
    owner: str

    class Config:
        from_attributes = True


class RecommendationItem(BaseModel):
    issue_id: int
    title: str
    difficulty: str
    language: Optional[str] = None
    repo: RepoBrief

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    message: str
    data: List[RecommendationItem]
