# ── schemas/enrollments.py ──────────────────────────────────────
# Pydantic models for enrollment requests and responses
# ────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ── Requests ─────────────────────────────────────────────────────

class EnrollmentCreateRequest(BaseModel):
    issue_id: int


# ── Response sub-models ──────────────────────────────────────────

class IssueBrief(BaseModel):
    id: int
    title: str
    difficulty: str

    class Config:
        from_attributes = True


class EnrollmentItem(BaseModel):
    enrollment_id: int
    status: str
    issue: IssueBrief

    class Config:
        from_attributes = True


class EnrollmentCreatedData(BaseModel):
    enrollment_id: int


# ── Envelope responses ───────────────────────────────────────────

class EnrollmentCreatedResponse(BaseModel):
    message: str
    data: EnrollmentCreatedData


class EnrollmentListResponse(BaseModel):
    message: str
    data: List[EnrollmentItem]
