# ── routers/webhooks.py ─────────────────────────────────────────
# FastAPI webhook endpoint
# Receives GitHub events → validates signature → pushes to Redis queue
# Must respond to GitHub in under 3 seconds — all heavy work in Celery
# ────────────────────────────────────────────────────────────────

import hashlib
import hmac
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request

from app.tasks import process_new_issue, process_pr_merged

logger = logging.getLogger(__name__)
router = APIRouter()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def verify_signature(payload_body: bytes, signature: str) -> bool:
    """
    Verify the X-Hub-Signature-256 header GitHub sends with every webhook.
    If this fails → reject the request (could be a spoofed webhook).
    """
    if not WEBHOOK_SECRET:
        logger.warning("GITHUB_WEBHOOK_SECRET not set — skipping signature verification")
        return True

    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@router.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_hub_signature_256: str = Header(default="")
):
    """
    Main webhook receiver.
    GitHub sends events here when:
      - An issue is opened/closed/edited
      - A PR is opened/merged/closed
      - A push happens
      - An issue comment is created

    This endpoint ONLY:
      1. Validates the signature
      2. Pushes a Celery task to Redis
      3. Returns 200 immediately

    All heavy processing happens in Celery workers.
    """
    # Read raw body for signature verification
    body = await request.body()

    # Verify webhook signature
    if x_hub_signature_256 and not verify_signature(body, x_hub_signature_256):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = x_github_event
    action = payload.get("action", "")

    logger.info(f"Received GitHub event: {event}.{action}")

    # ── Route events to correct Celery tasks ──────────────────────

    if event == "issues":
        if action in ("opened", "edited", "reopened"):
            process_new_issue.delay(payload)
            logger.info(f"Queued process_new_issue for: {payload.get('issue', {}).get('title', '')[:60]}")

        elif action == "closed":
            # Update issue state to closed in DB
            process_new_issue.delay(payload)

    elif event == "pull_request":
        if action == "closed" and payload.get("pull_request", {}).get("merged"):
            process_pr_merged.delay(payload)
            logger.info("Queued process_pr_merged")

    elif event == "push":
        # Push events tracked for future features (commit analysis)
        logger.info(f"Push event received for repo: {payload.get('repository', {}).get('full_name', '')}")

    elif event == "issue_comment":
        if action == "created":
            # Update comment count on the issue
            logger.info("Issue comment event received")

    elif event == "ping":
        # GitHub sends this when you first set up the webhook
        logger.info("GitHub webhook ping received — connection established!")

    # Always respond 200 immediately — never make GitHub wait
    return {"status": "queued", "event": event, "action": action}
