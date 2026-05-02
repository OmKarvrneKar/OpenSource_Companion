# ── services/user_service.py ────────────────────────────────────
# User profile and badge queries
# ────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session

from app.models import User, Enrollment, EnrollmentStatus, UserBadge, Badge


def get_user_profile_data(db: Session, user_id: int) -> dict:
    """
    Build profile data dict with computed stats.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    completed = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == EnrollmentStatus.completed
    ).count()

    active = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == EnrollmentStatus.enrolled
    ).count()

    badges_count = db.query(UserBadge).filter(
        UserBadge.user_id == user_id
    ).count()

    return {
        "user_id": user.id,
        "username": user.github_username,
        "skill_level": user.skill_level.value,
        "primary_language": user.primary_language,
        "points_total": user.points_total,
        "is_mentor": user.is_mentor,
        "stats": {
            "completed_contributions": completed,
            "active_enrollments": active,
            "badges_earned": badges_count,
        }
    }


def get_user_badges_list(db: Session, user_id: int) -> list:
    """
    Fetch all badges earned by user, ordered by most recent first.
    """
    results = (
        db.query(UserBadge, Badge)
        .join(Badge, UserBadge.badge_id == Badge.id)
        .filter(UserBadge.user_id == user_id)
        .order_by(UserBadge.earned_at.desc())
        .all()
    )

    return [
        {
            "badge_id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "earned_at": user_badge.earned_at,
        }
        for user_badge, badge in results
    ]
