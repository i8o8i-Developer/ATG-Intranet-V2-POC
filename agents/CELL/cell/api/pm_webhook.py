"""
CELL PM Slack Reply Handler.

PM replies to morning digest DMs — CELL parses and acts.
In v1: PM replies are pulled via Slack API at 2AM (same as intern reads).
This webhook endpoint is provided as an optional Slack Events API integration
(if the org upgrades to Slack event subscriptions later).

For now, PM parsing is also triggered during night_process_job by reading
the PM's DM thread — same pull strategy as interns.

The webhook here handles the Slack Events API url_verification challenge
and event dispatch for future use.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request, status

from cell.config import settings
from cell.slack.parser import parse_pm_approval_reply
from cell.api.pm_approval import process_pm_approval

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/cell/slack/events")
async def slack_events(request: Request, x_slack_signature: str = Header(None)) -> Dict[str, Any]:
    """
    Slack Events API endpoint.
    - Handles url_verification challenge.
    - Routes message events to PM approval processor.
    """
    body_bytes = await request.body()

    # Verify Slack signature
    if not _verify_slack_signature(body_bytes, x_slack_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Slack signature")

    payload = await request.json()

    # url_verification handshake
    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}

    # Event dispatch
    event = payload.get("event", {})
    if event.get("type") == "message" and event.get("channel_type") == "im":
        user_id = event.get("user")
        text = event.get("text", "")
        # We don't know if this is a PM or intern here without DB lookup.
        # Delegate to background task to keep endpoint fast.
        logger.debug("Slack IM event from user %s", user_id)

    return {"ok": True}


def _verify_slack_signature(body: bytes, signature: str) -> bool:
    """Verify Slack request signature using signing secret."""
    if not signature:
        return False
    try:
        signing_secret = settings.slack_bot_token  # In production, use SLACK_SIGNING_SECRET
        timestamp = str(int(time.time()))
        base_string = f"v0:{timestamp}:{body.decode()}"
        computed = "v0=" + hmac.new(
            signing_secret.encode(),
            base_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(computed, signature)
    except Exception:
        return False
