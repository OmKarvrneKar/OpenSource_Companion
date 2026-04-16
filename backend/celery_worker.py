# ── celery_worker.py ────────────────────────────────────────────
# Celery worker entry point
# Runs 4 job types:
#   1. process_new_issue          (triggered by webhook)
#   2. check_contribution_status  (every 6h via Beat)
#   3. send_notifications         (every 5min via Beat)
#   4. retrain_classifier         (monthly via Beat)
#
# HOW TO RUN LOCALLY:
#   cd backend
#   celery -A celery_worker worker --loglevel=info --concurrency=4
#
# HOW IT RUNS IN DOCKER:
#   Handled by docker-compose celery_worker service
# ────────────────────────────────────────────────────────────────

from app.celery_app import celery_app  # noqa: F401 — must import to register tasks
from app import tasks                  # noqa: F401 — registers all 4 task types

# Celery discovers tasks automatically via app.celery_app include=["app.tasks"]
# This file just ensures everything is imported correctly

if __name__ == "__main__":
    celery_app.start()
