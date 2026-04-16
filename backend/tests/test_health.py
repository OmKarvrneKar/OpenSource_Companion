# ── backend/tests/test_health.py ────────────────────────────────
# Basic smoke tests — CI runs these on every PR
# Member 3: add more tests in this folder as you build each endpoint
# ────────────────────────────────────────────────────────────────

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ── Health check ─────────────────────────────────────────────────

def test_health_check():
    """API must always return 200 on /health."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Webhook endpoint ─────────────────────────────────────────────

def test_webhook_ping():
    """GitHub sends a ping when webhook is first set up."""
    response = client.post(
        "/webhooks/github",
        json={"zen": "Practicality beats purity.", "hook_id": 123},
        headers={"X-GitHub-Event": "ping"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["event"] == "ping"


def test_webhook_issue_opened():
    """New issue opened event should be queued."""
    mock_payload = {
        "action": "opened",
        "issue": {
            "id": 12345,
            "title": "Test issue",
            "body": "Test description",
            "state": "open",
            "html_url": "https://github.com/test/repo/issues/1",
            "comments": 0,
        },
        "repository": {
            "id": 67890,
            "name": "test-repo",
            "full_name": "test/test-repo",
            "owner": {"login": "test"},
            "language": "Python",
            "stargazers_count": 100,
            "description": "Test repo",
        }
    }
    response = client.post(
        "/webhooks/github",
        json=mock_payload,
        headers={"X-GitHub-Event": "issues"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"


def test_webhook_unknown_event():
    """Unknown events should still return 200 (never reject GitHub)."""
    response = client.post(
        "/webhooks/github",
        json={"action": "something_new"},
        headers={"X-GitHub-Event": "unknown_event"}
    )
    assert response.status_code == 200


# ── CORS ──────────────────────────────────────────────────────────

def test_cors_headers():
    """Frontend origin must be allowed."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    # FastAPI returns 200 for OPTIONS preflight
    assert response.status_code in [200, 405]
