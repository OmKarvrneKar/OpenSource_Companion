# ── models.py ───────────────────────────────────────────────────
# All 9 PostgreSQL tables defined as SQLAlchemy ORM models
# Member 3: import these in your service files
# Member 2: issues.embedding_id links to FAISS index
# ────────────────────────────────────────────────────────────────

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean,
    DateTime, Float, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


# ── Enums ────────────────────────────────────────────────────────

class SkillLevel(str, enum.Enum):
    beginner     = "beginner"
    intermediate = "intermediate"
    advanced     = "advanced"


class Difficulty(str, enum.Enum):
    beginner     = "beginner"
    intermediate = "intermediate"
    advanced     = "advanced"


class IssueState(str, enum.Enum):
    open   = "open"
    closed = "closed"


class EnrollmentStatus(str, enum.Enum):
    enrolled  = "enrolled"
    completed = "completed"
    dropped   = "dropped"
    stale     = "stale"


# ── Table 1: users ───────────────────────────────────────────────

class User(Base):
    """
    Every person who logs in via GitHub OAuth.
    Created automatically on first login by the auth service.
    """
    __tablename__ = "users"

    id                = Column(Integer, primary_key=True, index=True)
    github_username   = Column(String(100), unique=True, nullable=False, index=True)
    github_id         = Column(BigInteger, unique=True, nullable=False)
    email             = Column(String(255), nullable=True)
    avatar_url        = Column(String(500), nullable=True)
    skill_level       = Column(SAEnum(SkillLevel), default=SkillLevel.beginner, nullable=False)
    primary_language  = Column(String(50), nullable=True)
    points_total      = Column(Integer, default=0, nullable=False)
    is_mentor         = Column(Boolean, default=False, nullable=False)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    enrollments        = relationship("Enrollment", back_populates="user")
    points_log         = relationship("PointsLog", back_populates="user")
    user_badges        = relationship("UserBadge", back_populates="user")
    gamification_events = relationship("GamificationEvent", back_populates="user")
    notifications      = relationship("Notification", back_populates="user")


# ── Table 2: repos ───────────────────────────────────────────────

class Repo(Base):
    """
    GitHub repositories we track and pull issues from.
    Populated by the data pipeline (Member 1's Celery worker).
    """
    __tablename__ = "repos"

    id              = Column(Integer, primary_key=True, index=True)
    github_repo_id  = Column(BigInteger, unique=True, nullable=False, index=True)
    owner           = Column(String(100), nullable=False)
    name            = Column(String(100), nullable=False)
    full_name       = Column(String(200), nullable=False)   # owner/name
    language        = Column(String(50), nullable=True)
    stars           = Column(Integer, default=0)
    description     = Column(Text, nullable=True)
    last_synced_at  = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    issues = relationship("Issue", back_populates="repo")


# ── Table 3: issues ──────────────────────────────────────────────

class Issue(Base):
    """
    GitHub issues pulled from tracked repos.
    difficulty   → set by ML difficulty classifier (Member 2)
    embedding_id → FAISS index ID for semantic search (Member 2)
    """
    __tablename__ = "issues"

    id              = Column(Integer, primary_key=True, index=True)
    github_issue_id = Column(BigInteger, unique=True, nullable=False, index=True)
    repo_id         = Column(Integer, ForeignKey("repos.id"), nullable=False)
    title           = Column(String(500), nullable=False)
    description     = Column(Text, nullable=True)
    difficulty      = Column(SAEnum(Difficulty), nullable=True)     # set by classifier
    language        = Column(String(50), nullable=True)
    state           = Column(SAEnum(IssueState), default=IssueState.open)
    embedding_id    = Column(Integer, nullable=True, index=True)    # FAISS vector ID
    github_url      = Column(String(500), nullable=True)
    comment_count   = Column(Integer, default=0)
    days_open       = Column(Integer, default=0)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    repo        = relationship("Repo", back_populates="issues")
    enrollments = relationship("Enrollment", back_populates="issue")


# ── Table 4: enrollments ─────────────────────────────────────────

class Enrollment(Base):
    """
    Tracks which user is working on which issue.
    status transitions:
      enrolled → completed  (PR merged)
      enrolled → stale      (no activity for 14 days)
      enrolled → dropped    (user withdrew)
    """
    __tablename__ = "enrollments"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    issue_id     = Column(Integer, ForeignKey("issues.id"), nullable=False)
    status       = Column(SAEnum(EnrollmentStatus), default=EnrollmentStatus.enrolled)
    pr_url       = Column(String(500), nullable=True)   # filled when PR is opened
    enrolled_at  = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user  = relationship("User", back_populates="enrollments")
    issue = relationship("Issue", back_populates="enrollments")


# ── Table 5: points_log ──────────────────────────────────────────

class PointsLog(Base):
    """
    Every points transaction ever made — append only, never update.
    reason examples:
      "first_contribution", "merged_pr", "helped_mentee", "weekly_streak"
    """
    __tablename__ = "points_log"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    points      = Column(Integer, nullable=False)           # can be negative
    reason      = Column(String(100), nullable=False)
    extra_data  = Column(JSON, nullable=True)               # extra context (renamed: 'metadata' is reserved in SQLAlchemy)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="points_log")


# ── Table 6: badges ──────────────────────────────────────────────

class Badge(Base):
    """
    Master list of all badges that can be earned.
    trigger_condition examples:
      "first_pr_merged", "10_prs_merged", "mentor_promoted", "7_day_streak"
    Seed this table with INSERT on first deploy.
    """
    __tablename__ = "badges"

    id                = Column(Integer, primary_key=True, index=True)
    name              = Column(String(100), unique=True, nullable=False)
    description       = Column(Text, nullable=False)
    trigger_condition = Column(String(100), unique=True, nullable=False)
    icon_url          = Column(String(500), nullable=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge")


# ── Table 7: user_badges ─────────────────────────────────────────

class UserBadge(Base):
    """
    Junction table — which user earned which badge and when.
    """
    __tablename__ = "user_badges"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id   = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at  = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user  = relationship("User", back_populates="user_badges")
    badge = relationship("Badge", back_populates="user_badges")


# ── Table 8: gamification_events ─────────────────────────────────

class GamificationEvent(Base):
    """
    Raw event log — every gamification trigger gets recorded here.
    event_type examples:
      "contribution_completed", "badge_earned", "mentor_promoted", "streak_achieved"
    metadata: flexible JSON for event-specific data
    """
    __tablename__ = "gamification_events"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type  = Column(String(100), nullable=False, index=True)
    extra_data  = Column(JSON, nullable=True)               # renamed: 'metadata' is reserved in SQLAlchemy
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="gamification_events")


# ── Table 9: notifications ───────────────────────────────────────

class Notification(Base):
    """
    Queued messages to users.
    Sent by Celery send_notifications worker.
    is_read flipped to True when user opens notification.
    """
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    message    = Column(Text, nullable=False)
    is_read    = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")
