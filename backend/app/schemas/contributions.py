# ── schemas/contributions.py ────────────────────────────────────
# Pydantic models for contribution check requests and responses
# ────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import Optional


class ContributionCheckRequest(BaseModel):
    enrollment_id: int


class ContributionCheckData(BaseModel):
    status: str


class ContributionCheckResponse(BaseModel):
    message: str
    data: ContributionCheckData
