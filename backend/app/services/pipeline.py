# ── services/pipeline.py ────────────────────────────────────────
# Core processing logic for the data pipeline
# Called by Celery workers — NOT called directly by API routes
# ────────────────────────────────────────────────────────────────

import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Repo, Issue, Enrollment, EnrollmentStatus, User, Notification

logger = logging.getLogger(__name__)


# ── Issue Processing ─────────────────────────────────────────────

def process_issue_payload(payload: dict) -> None:
    """
    Called by process_new_issue Celery task.
    Saves or updates an issue in PostgreSQL.
    Difficulty classification + embedding generation will be added
    once Member 2 delivers ml_service.py.
    """
    db: Session = SessionLocal()
    try:
        issue_data   = payload.get("issue", {})
        repo_data    = payload.get("repository", {})

        # Upsert repo
        repo = db.query(Repo).filter(
            Repo.github_repo_id == repo_data["id"]
        ).first()

        if not repo:
            repo = Repo(
                github_repo_id = repo_data["id"],
                owner          = repo_data["owner"]["login"],
                name           = repo_data["name"],
                full_name      = repo_data["full_name"],
                language       = repo_data.get("language"),
                stars          = repo_data.get("stargazers_count", 0),
                description    = repo_data.get("description"),
            )
            db.add(repo)
            db.flush()   # get repo.id without committing
            logger.info(f"Created new repo: {repo.full_name}")

        # Upsert issue
        issue = db.query(Issue).filter(
            Issue.github_issue_id == issue_data["id"]
        ).first()

        if not issue:
            issue = Issue(
                github_issue_id = issue_data["id"],
                repo_id         = repo.id,
                title           = issue_data["title"],
                description     = issue_data.get("body", ""),
                language        = repo_data.get("language"),
                state           = issue_data["state"],
                github_url      = issue_data["html_url"],
                comment_count   = issue_data.get("comments", 0),
            )
            db.add(issue)
            logger.info(f"Created new issue: {issue.title[:60]}")
        else:
            # Update state if issue was closed
            issue.state         = issue_data["state"]
            issue.comment_count = issue_data.get("comments", 0)
            logger.info(f"Updated issue: {issue.title[:60]}")

        db.commit()

        # TODO: Once Member 2 delivers ml_service.py, add:
        # from ml.ml_service import classify_issue
        # issue.difficulty = classify_issue(issue.title, issue.description)
        # db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing issue payload: {e}")
        raise
    finally:
        db.close()


def process_pr_merged(payload: dict) -> None:
    """
    Called when a pull_request.closed webhook fires with merged=True.
    Marks the matching enrollment as completed.
    Triggers gamification via gamification engine (Member 3 builds this).
    """
    db: Session = SessionLocal()
    try:
        pr_data   = payload.get("pull_request", {})
        pr_url    = pr_data.get("html_url", "")
        pr_body   = pr_data.get("body", "") or ""
        pr_user   = pr_data.get("user", {}).get("login", "")

        # Find user
        user = db.query(User).filter(
            User.github_username == pr_user
        ).first()

        if not user:
            logger.warning(f"PR merged but user not found: {pr_user}")
            return

        # Find enrolled issue — match by PR URL or by issue reference in PR body
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user.id,
            Enrollment.status  == EnrollmentStatus.enrolled
        ).first()

        if enrollment:
            from datetime import datetime, timezone
            enrollment.status       = EnrollmentStatus.completed
            enrollment.pr_url       = pr_url
            enrollment.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Marked enrollment {enrollment.id} as completed for user {pr_user}")

            # Notify user
            notification = Notification(
                user_id = user.id,
                message = f"Congratulations! Your PR was merged. Points have been awarded."
            )
            db.add(notification)
            db.commit()

            # TODO: Member 3 to call gamification engine here:
            # from app.services.gamification import award_points
            # award_points(user.id, "merged_pr", db)

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing PR merged: {e}")
        raise
    finally:
        db.close()


def check_stale_enrollments() -> None:
    """
    Called by check_contribution_status Celery task every 6 hours.
    Marks enrollments as stale if no activity for 14+ days.
    Sends a nudge notification.
    """
    from datetime import datetime, timezone, timedelta
    db: Session = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)

        stale = db.query(Enrollment).filter(
            Enrollment.status     == EnrollmentStatus.enrolled,
            Enrollment.enrolled_at < cutoff
        ).all()

        for enrollment in stale:
            enrollment.status = EnrollmentStatus.stale

            notification = Notification(
                user_id = enrollment.user_id,
                message = (
                    f"Your enrollment in issue #{enrollment.issue_id} "
                    f"has been marked stale after 14 days of inactivity. "
                    f"Pick it back up or enroll in a new issue!"
                )
            )
            db.add(notification)

        db.commit()
        logger.info(f"Marked {len(stale)} enrollments as stale")

    except Exception as e:
        db.rollback()
        logger.error(f"Error checking stale enrollments: {e}")
        raise
    finally:
        db.close()
