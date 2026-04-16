"""
backend/app/routers/auth.py
GitHub OAuth flow:
  GET /auth/github   → redirect user to GitHub to authorize
  GET /auth/callback → GitHub redirects back here with code, exchange for JWT
  POST /auth/refresh → refresh an expiring JWT
"""

import os
import httpx
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from jose import jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Config ────────────────────────────────────────────────────────

GITHUB_CLIENT_ID     = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://localhost:3000")

JWT_SECRET_KEY              = os.getenv("JWT_SECRET_KEY", "changeme")
JWT_ALGORITHM               = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ── Helpers ───────────────────────────────────────────────────────

def _create_jwt(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _get_or_create_user(github_user: dict, db: Session) -> tuple[User, bool]:
    """Returns (user, is_new_user)."""
    github_id = github_user["id"]
    user = db.query(User).filter(User.github_id == github_id).first()

    if user:
        # Update mutable fields on every login
        user.avatar_url = github_user.get("avatar_url")
        user.email      = github_user.get("email")
        db.commit()
        return user, False

    # First login — create the user
    new_user = User(
        github_id       = github_id,
        github_username = github_user.get("login", ""),
        email           = github_user.get("email"),
        avatar_url      = github_user.get("avatar_url"),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user, True


# ── Routes ────────────────────────────────────────────────────────

@router.get("/github")
def github_login():
    """
    Step 1: Redirect the user to GitHub's OAuth authorization page.
    """
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID not configured")

    github_oauth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        "&scope=user:email"
    )
    return RedirectResponse(url=github_oauth_url)


@router.get("/callback")
def github_callback(
    code: str = Query(..., description="Temporary code from GitHub"),
    db:   Session = Depends(get_db),
):
    """
    Step 2: GitHub redirects here after the user authorises.
    Exchange the code for an access token, fetch the user profile,
    upsert the User row, then redirect the frontend with a JWT.
    """
    # Exchange code for GitHub access token
    token_resp = httpx.post(
        "https://github.com/login/oauth/access_token",
        json={
            "client_id":     GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code":          code,
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )

    token_data = token_resp.json()
    access_token = token_data.get("access_token")

    if not access_token:
        logger.error(f"GitHub token exchange failed: {token_data}")
        return RedirectResponse(url=f"{FRONTEND_URL}/?error=oauth_failed")

    # Fetch GitHub user profile
    user_resp = httpx.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept":        "application/vnd.github+json",
        },
        timeout=10,
    )

    if user_resp.status_code != 200:
        logger.error(f"GitHub /user fetch failed: {user_resp.text}")
        return RedirectResponse(url=f"{FRONTEND_URL}/?error=github_api_failed")

    github_user = user_resp.json()

    # Upsert user in DB
    try:
        user, is_new = _get_or_create_user(github_user, db)
    except Exception as exc:
        logger.error(f"DB upsert failed: {exc}")
        return RedirectResponse(url=f"{FRONTEND_URL}/?error=db_error")

    # Issue JWT
    jwt_token = _create_jwt(user.id)

    # Redirect back to frontend — frontend stores the token in localStorage
    redirect_url = (
        f"{FRONTEND_URL}/auth/callback"
        f"?token={jwt_token}"
        f"&new_user={'true' if is_new else 'false'}"
    )
    return RedirectResponse(url=redirect_url)


@router.post("/refresh")
def refresh_token(
    token: str,
    db:    Session = Depends(get_db),
):
    """
    Step 3 (optional): Refresh an expiring access token.
    Expects the current JWT in the request body.
    """
    try:
        payload  = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id  = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {"access_token": _create_jwt(user.id), "token_type": "bearer"}
