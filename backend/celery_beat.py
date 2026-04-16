# ── celery_beat.py ──────────────────────────────────────────────
# Celery Beat — periodic task scheduler
# Triggers scheduled tasks at fixed intervals:
#
#   check_contribution_status  → every 6 hours
#   send_notifications         → every 5 minutes
#   retrain_classifier         → every 30 days
#
# IMPORTANT: Run ONLY ONE Beat instance at a time.
# Running multiple Beat instances causes duplicate task execution.
#
# HOW TO RUN LOCALLY (separate terminal from worker):
#   cd backend
#   celery -A celery_beat beat --loglevel=info
#
# HOW IT RUNS IN DOCKER:
#   Handled by docker-compose celery_beat service
# ────────────────────────────────────────────────────────────────

from app.celery_app import celery_app  # noqa: F401
from app import tasks                  # noqa: F401

if __name__ == "__main__":
    celery_app.start()
