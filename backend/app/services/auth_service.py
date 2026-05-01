# ── services/auth_service.py ────────────────────────────────────
# All auth business logic — GitHub OAuth, JWT, user upsert
# Called by routers/auth.py — never imported by other services
# ────────────────────────────────────────────────────────────────

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User

logger = logging.getLogger(__name__)

settings = get_settings()

# ── GitHub OAuth URLs ────────────────────────────────────────────
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


# ── GitHub OAuth ─────────────────────────────────────────────────

async def exchange_github_code(code: str) -> str:
    """
    Exchange the OAuth authorization code for a GitHub access token.
    Raises ValueError on failure.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
            timeout=10.0,
        )

    if response.status_code != 200:
        logger.error(f"GitHub token exchange failed: HTTP {response.status_code}")
        raise ValueError("Failed to exchange code with GitHub")

    data = response.json()

    if "error" in data:
        logger.error(f"GitHub OAuth error: {data.get('error_description', data['error'])}")
        raise ValueError(data.get("error_description", "GitHub rejected the authorization code"))

    access_token = data.get("access_token")
    if not access_token:
        raise ValueError("No access_token in GitHub response")

    return access_token


async def fetch_github_user(github_access_token: str) -> dict:
    """
    Fetch authenticated user profile from GitHub API.
    Returns dict with: id, login, email, avatar_url.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10.0,
        )

    if response.status_code != 200:
        logger.error(f"GitHub user fetch failed: HTTP {response.status_code}")
        raise ValueError("Failed to fetch user data from GitHub")

    data = response.json()
    return {
        "github_id": data["id"],
        "github_username": data["login"],
        "email": data.get("email"),
        "avatar_url": data.get("avatar_url"),
    }


# ── User Upsert ──────────────────────────────────────────────────

def upsert_user(db: Session, github_user: dict) -> User:
    """
    Insert or update a user based on github_id.
    On first login → creates user with beginner skill level.
    On subsequent logins → updates username, email, avatar.
    """
    user = db.query(User).filter(
        User.github_id == github_user["github_id"]
    ).first()

    if user:
        # Update mutable profile fields from GitHub
        user.github_username = github_user["github_username"]
        user.email = github_user.get("email") or user.email
        user.avatar_url = github_user.get("avatar_url") or user.avatar_url
        logger.info(f"Updated existing user: {user.github_username}")
    else:
        user = User(
            github_id=github_user["github_id"],
            github_username=github_user["github_username"],
            email=github_user.get("email"),
            avatar_url=github_user.get("avatar_url"),
        )
        db.add(user)
        logger.info(f"Created new user: {user.github_username}")

    db.commit()
    db.refresh(user)
    return user


# ── JWT Token Creation ───────────────────────────────────────────

def create_access_token(user_id: int) -> str:
    """Short-lived access token (15 min default)."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Long-lived refresh token (7 days default)."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ── JWT Verification ─────────────────────────────────────────────

def verify_token(token: str, expected_type: str = "access") -> Optional[int]:
    """
    Decode and validate a JWT token.
    Returns user_id (int) on success, None on failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Validate token type (access vs refresh)
        token_type = payload.get("type")
        if token_type != expected_type:
            logger.warning(f"Token type mismatch: expected {expected_type}, got {token_type}")
            return None

        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None

        return int(user_id_str)

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
    except (ValueError, TypeError):
        return None
