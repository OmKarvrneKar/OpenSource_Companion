# ── services/gamification_service.py ────────────────────────────
# Points engine + badge evaluation
# Called after contribution events — never called from routers directly
# ────────────────────────────────────────────────────────────────

import logging
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    User, PointsLog, Badge, UserBadge,
    GamificationEvent, Enrollment, EnrollmentStatus,
)

logger = logging.getLogger(__name__)

# ── Points rules ─────────────────────────────────────────────────

POINTS_MAP = {
    "merged_pr":          100,
    "first_contribution":  50,
    "streak":              20,
}


# ── Main entry point ────────────────────────────────────────────

def award_points(db: Session, user_id: int, event_type: str) -> None:
    """
    Award points for an event and check for badge eligibility.
    Wrapped in error handling — gamification failures should never
    break the contribution flow.
    """
    try:
        points = POINTS_MAP.get(event_type, 0)
        if points == 0:
            logger.warning(f"Unknown event type: {event_type}")
            return

        # Check for first_contribution bonus (only awarded once)
        if event_type == "merged_pr":
            first_time = _is_first_completed_pr(db, user_id)
            if first_time:
                _insert_points(db, user_id, POINTS_MAP["first_contribution"], "first_contribution")
                _log_event(db, user_id, "first_contribution")
                logger.info(f"First contribution bonus awarded to user {user_id}")

        # Award the main event points
        _insert_points(db, user_id, points, event_type)
        _log_event(db, user_id, event_type)

        # Recalculate user total from points_log for accuracy
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            total = db.query(func.coalesce(func.sum(PointsLog.points), 0)).filter(
                PointsLog.user_id == user_id
            ).scalar()
            user.points_total = total
            db.commit()

        # Check badges
        check_badges(db, user_id)

        logger.info(f"Awarded {points} pts to user {user_id} for '{event_type}' (total: {user.points_total if user else 'N/A'})")

    except Exception as e:
        db.rollback()
        logger.error(f"Gamification error for user {user_id}: {e}")
        # Do NOT re-raise — gamification errors should not break the main flow


# ── Badge evaluation ────────────────────────────────────────────

def check_badges(db: Session, user_id: int) -> None:
    """
    Evaluate badge conditions and award any newly earned badges.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        completed_count = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.status == EnrollmentStatus.completed
        ).count()

        # ── First Merge: first completed PR ──────────────────────
        if completed_count >= 1:
            _award_badge_if_new(db, user_id, "first_pr_merged")

        # ── On a Roll: 5 merged PRs ─────────────────────────────
        if completed_count >= 5:
            _award_badge_if_new(db, user_id, "5_prs_merged")

        # ── Open Source Hero: 10 merged PRs ──────────────────────
        if completed_count >= 10:
            _award_badge_if_new(db, user_id, "10_prs_merged")

        # ── Mentor: 500+ points AND 10+ merged PRs ──────────────
        if user.points_total >= 500 and completed_count >= 10:
            _award_badge_if_new(db, user_id, "mentor_promoted")
            if not user.is_mentor:
                user.is_mentor = True
                db.commit()
                logger.info(f"User {user_id} promoted to mentor")

    except Exception as e:
        db.rollback()
        logger.error(f"Badge evaluation error for user {user_id}: {e}")


# ── Internal helpers ─────────────────────────────────────────────

def _is_first_completed_pr(db: Session, user_id: int) -> bool:
    """Check if this is the user's first ever completed enrollment."""
    count = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == EnrollmentStatus.completed
    ).count()
    return count == 1


def _insert_points(db: Session, user_id: int, points: int, reason: str) -> None:
    """Append a row to points_log."""
    log = PointsLog(
        user_id=user_id,
        points=points,
        reason=reason,
    )
    db.add(log)
    db.commit()
    logger.debug(f"Points log: user={user_id}, points={points}, reason={reason}")


def _log_event(db: Session, user_id: int, event_type: str) -> None:
    """Append a row to gamification_events."""
    event = GamificationEvent(
        user_id=user_id,
        event_type=event_type,
    )
    db.add(event)
    db.commit()


def _award_badge_if_new(db: Session, user_id: int, trigger_condition: str) -> None:
    """Award a badge only if the user hasn't earned it yet."""
    badge = db.query(Badge).filter(
        Badge.trigger_condition == trigger_condition
    ).first()

    if not badge:
        logger.warning(f"Badge with trigger '{trigger_condition}' not found in DB — run seed_badges.py")
        return

    already_earned = db.query(UserBadge).filter(
        UserBadge.user_id == user_id,
        UserBadge.badge_id == badge.id
    ).first()

    if already_earned:
        return

    user_badge = UserBadge(
        user_id=user_id,
        badge_id=badge.id,
    )
    db.add(user_badge)
    db.commit()

    _log_event(db, user_id, "badge_earned")
    logger.info(f"Badge '{badge.name}' awarded to user {user_id}")
