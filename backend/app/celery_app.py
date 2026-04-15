# ── celery_app.py ───────────────────────────────────────────────
# Celery configuration — connects to Redis broker
# Import this in tasks.py and main.py
# ────────────────────────────────────────────────────────────────

from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery(
    "opensource_companion",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]   # auto-discovers all tasks in tasks.py
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Retry settings — dead letter queue after 3 retries
    task_max_retries=3,
    task_acks_late=True,           # only ack after task completes (safer)
    worker_prefetch_multiplier=1,  # one task at a time per worker slot

    # Beat schedule — periodic tasks
    beat_schedule={
        # Check every 6 hours if enrolled users have opened a PR
        "check-contribution-status": {
            "task": "app.tasks.check_contribution_status",
            "schedule": 21600.0,   # 6 hours in seconds
        },
        # Send pending notifications every 5 minutes
        "send-notifications": {
            "task": "app.tasks.send_notifications",
            "schedule": 300.0,     # 5 minutes
        },
        # Retrain classifier every 30 days
        "retrain-classifier": {
            "task": "app.tasks.retrain_classifier",
            "schedule": 2592000.0, # 30 days
        },
    }
)
