# ── schemas/auth.py ─────────────────────────────────────────────
# Pydantic models for auth request / response validation
# Aligned with docs/api_contract.md
# ────────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Requests ─────────────────────────────────────────────────────

class GitHubCallbackRequest(BaseModel):
    code: str = Field(..., min_length=1, description="GitHub OAuth authorization code")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="JWT refresh token")


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="JWT refresh token to invalidate")


# ── Response sub-models ──────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    github_username: str
    avatar_url: Optional[str] = None
    skill_level: str
    points_total: int
    is_mentor: bool

    model_config = {"from_attributes": True}


class LoginData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshData(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Envelope responses ───────────────────────────────────────────

class AuthResponse(BaseModel):
    """Standard envelope for all auth endpoints."""
    message: str
    data: Optional[LoginData | RefreshData] = None
