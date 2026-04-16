"""
backend/app/celery_app.py
Celery application instance and configuration.
"""

import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "opensource_companion",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.workers.sync_issues",
        "app.workers.compute_embeddings",
        "app.workers.award_badges",
        "app.workers.send_notifications",
    ],
)

# Alias so that `from app.celery_app import celery_app` works everywhere
celery_app = celery

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,                    # re-queue if worker crashes mid-task
    worker_prefetch_multiplier=1,           # one task at a time per worker
    result_expires=3600,                    # results kept for 1 hour
    beat_schedule={
        # Auto-sync all repos every 6 hours
        "sync-all-repos-every-6h": {
            "task": "app.workers.sync_issues.sync_all_repos",
            "schedule": 6 * 60 * 60,
        },
    },
)
