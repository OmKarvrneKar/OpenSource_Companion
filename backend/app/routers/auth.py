# ── routers/auth.py ─────────────────────────────────────────────
# Auth endpoints — GitHub OAuth callback, token refresh, logout
# All responses follow the { message, data } envelope contract
# ────────────────────────────────────────────────────────────────

import logging
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.auth import (
    AuthResponse,
    GitHubCallbackRequest,
    LoginData,
    LogoutRequest,
    RefreshData,
    RefreshTokenRequest,
    UserResponse,
)
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    exchange_github_code,
    fetch_github_user,
    upsert_user,
    verify_token,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── POST /auth/github/callback ──────────────────────────────────

@router.post("/github/callback", response_model=AuthResponse, status_code=200)
async def github_callback(
    body: GitHubCallbackRequest,
    db: Session = Depends(get_db),
):
    """
    Exchange a GitHub OAuth authorization code for JWT tokens.
    Creates the user on first login, updates profile on subsequent logins.
    """
    # 1. Exchange code for GitHub access token
    try:
        github_access_token = await exchange_github_code(body.code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # 2. Fetch user profile from GitHub
    try:
        github_user = await fetch_github_user(github_access_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # 3. Upsert user into PostgreSQL
    try:
        user = upsert_user(db, github_user)
    except Exception as e:
        logger.error(f"User upsert failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create or update user record",
        )

    # 4. Generate JWT tokens
    user_id = cast(int, user.id)
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    logger.info(f"Login successful: {user.github_username} (id={user.id})")

    return AuthResponse(
        message="Login successful",
        data=LoginData(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        ),
    )


# ── POST /auth/refresh ──────────────────────────────────────────

@router.post("/refresh", response_model=AuthResponse, status_code=200)
def refresh_token(body: RefreshTokenRequest):
    """
    Issue a new access token using a valid refresh token.
    The refresh token itself is NOT rotated — it stays valid until expiry.
    """
    user_id = verify_token(body.refresh_token, expected_type="refresh")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    new_access_token = create_access_token(user_id)

    return AuthResponse(
        message="Token refreshed",
        data=RefreshData(access_token=new_access_token),
    )


# ── POST /auth/logout ───────────────────────────────────────────

@router.post("/logout", response_model=AuthResponse, status_code=200)
def logout(
    body: LogoutRequest,
    _current_user: User = Depends(get_current_user),
):
    """
    Logout the current user.
    Currently a no-op on the server side — the frontend discards tokens.
    Token blacklisting can be added later via Redis.
    """
    # Future: blacklist body.refresh_token in Redis with TTL = remaining expiry
    logger.info(f"User logged out: {_current_user.github_username}")

    return AuthResponse(
        message="Logged out successfully",
        data=None,
    )
