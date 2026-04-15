# ── tasks.py ────────────────────────────────────────────────────
# All 4 Celery background job types:
#   1. process_new_issue          — classify + embed + save
#   2. check_contribution_status  — poll PRs every 6h
#   3. send_notifications         — badge alerts, nudges
#   4. retrain_classifier         — monthly batch retraining
# ────────────────────────────────────────────────────────────────

import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


# ── Task 1: Process new issue ────────────────────────────────────

@celery_app.task(
    name="app.tasks.process_new_issue",
    bind=True,
    max_retries=3,
    default_retry_delay=60   # wait 60s before retry
)
def process_new_issue(self, payload: dict):
    """
    Triggered by webhook when a new issue is opened or edited.
    Flow: save to DB → classify difficulty → generate embedding → save FAISS id
    """
    try:
        from app.services.pipeline import process_issue_payload
        logger.info(f"Processing issue: {payload.get('issue', {}).get('title', 'unknown')[:60]}")
        process_issue_payload(payload)
        logger.info("Issue processed successfully")

    except Exception as exc:
        logger.error(f"process_new_issue failed: {exc}")
        raise self.retry(exc=exc)


# ── Task 2: Check contribution status ────────────────────────────

@celery_app.task(
    name="app.tasks.check_contribution_status",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def check_contribution_status(self):
    """
    Runs every 6 hours via Celery Beat.
    Checks all active enrollments:
      - Has user opened a PR referencing this issue? → mark completed
      - 14+ days with no activity? → mark stale, send nudge
    """
    try:
        from app.services.pipeline import check_stale_enrollments
        logger.info("Running contribution status check")
        check_stale_enrollments()
        logger.info("Contribution status check complete")

    except Exception as exc:
        logger.error(f"check_contribution_status failed: {exc}")
        raise self.retry(exc=exc)


# ── Task 3: Send notifications ───────────────────────────────────

@celery_app.task(
    name="app.tasks.send_notifications",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_notifications(self):
    """
    Runs every 5 minutes via Celery Beat.
    Processes queued notifications from the notifications table.
    Currently logs them — extend to email/push in production.
    """
    try:
        from app.database import SessionLocal
        from app.models import Notification

        db = SessionLocal()
        try:
            unread = db.query(Notification).filter(
                Notification.is_read == False
            ).limit(100).all()

            for notification in unread:
                # TODO: extend with email/push notification service
                logger.info(
                    f"Notification for user {notification.user_id}: "
                    f"{notification.message[:80]}"
                )

            logger.info(f"Processed {len(unread)} pending notifications")
        finally:
            db.close()

    except Exception as exc:
        logger.error(f"send_notifications failed: {exc}")
        raise self.retry(exc=exc)


# ── Task 4: Retrain classifier ───────────────────────────────────

@celery_app.task(
    name="app.tasks.retrain_classifier",
    bind=True,
    max_retries=1,
    default_retry_delay=3600  # wait 1hr before retry
)
def retrain_classifier(self):
    """
    Runs monthly via Celery Beat.
    Triggers Member 2's ML retraining pipeline.
    Stub — Member 2 fills in the actual retraining logic.
    """
    try:
        logger.info("Starting monthly classifier retraining...")

        # TODO: Member 2 to implement:
        # from ml.ml_service import retrain
        # retrain()

        logger.info("Classifier retraining complete")

    except Exception as exc:
        logger.error(f"retrain_classifier failed: {exc}")
        raise self.retry(exc=exc)


# ── Task: Process PR merged ──────────────────────────────────────

@celery_app.task(
    name="app.tasks.process_pr_merged",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_pr_merged(self, payload: dict):
    """
    Triggered by webhook when a PR is merged.
    Marks enrollment completed + triggers gamification.
    """
    try:
        from app.services.pipeline import process_pr_merged as _process_pr_merged
        logger.info(f"Processing merged PR from: {payload.get('pull_request', {}).get('user', {}).get('login', 'unknown')}")
        _process_pr_merged(payload)

    except Exception as exc:
        logger.error(f"process_pr_merged failed: {exc}")
        raise self.retry(exc=exc)
