# ── test_celery.py ───────────────────────────────────────────────
# Quick smoke test — verifies all 4 Celery tasks can be queued
# and Redis is reachable
#
# USAGE (from backend/ folder):
#   python test_celery.py
#
# EXPECTED OUTPUT:
#   Redis connection OK
#   Task 1 queued: process_new_issue    → task id: xxxx
#   Task 2 queued: check_contribution   → task id: xxxx
#   Task 3 queued: send_notifications   → task id: xxxx
#   Task 4 queued: retrain_classifier   → task id: xxxx
#   All tasks queued successfully!
# ────────────────────────────────────────────────────────────────

import os
import sys
from dotenv import load_dotenv

load_dotenv()


def test_redis_connection():
    """Verify Redis is reachable."""
    import redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print(f"Redis connection OK ({redis_url})")
    except Exception as e:
        print(f"Redis connection FAILED: {e}")
        print("Make sure Redis is running: docker-compose up redis")
        sys.exit(1)


def test_tasks():
    """Queue all 4 Celery tasks and verify they're accepted."""
    from app.tasks import (
        process_new_issue,
        check_contribution_status,
        send_notifications,
        retrain_classifier,
    )

    # Mock issue payload for task 1
    mock_issue_payload = {
        "action": "opened",
        "issue": {
            "id": 999999999,
            "title": "Test issue from test_celery.py",
            "body": "This is a test issue to verify the pipeline works.",
            "state": "open",
            "html_url": "https://github.com/test/repo/issues/1",
            "comments": 0,
        },
        "repository": {
            "id": 888888888,
            "name": "test-repo",
            "full_name": "test/test-repo",
            "owner": {"login": "test"},
            "language": "Python",
            "stargazers_count": 100,
            "description": "Test repository",
        }
    }

    tests = [
        ("process_new_issue",         process_new_issue,         [mock_issue_payload]),
        ("check_contribution_status", check_contribution_status, []),
        ("send_notifications",        send_notifications,        []),
        ("retrain_classifier",        retrain_classifier,        []),
    ]

    all_passed = True
    for name, task, args in tests:
        try:
            result = task.delay(*args)
            print(f"Task queued: {name:35s} → task id: {result.id}")
        except Exception as e:
            print(f"FAILED to queue {name}: {e}")
            all_passed = False

    return all_passed


if __name__ == "__main__":
    print("── Celery Smoke Test ────────────────────────────")

    test_redis_connection()

    print("\nQueuing all tasks...")
    passed = test_tasks()

    if passed:
        print("\nAll tasks queued successfully!")
        print("Check Celery worker terminal — you should see tasks being processed.")
        print("Or visit http://localhost:5555 (Flower dashboard)")
    else:
        print("\nSome tasks failed to queue. Check errors above.")
        sys.exit(1)
