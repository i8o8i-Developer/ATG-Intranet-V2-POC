"""
CELL Slack Reader.
Scheduled pull only — NOT a live listener.
Called once at 2AM IST to read the last 24hrs of DMs from each intern.

Required Slack scopes: im:history, im:write, chat:write, users:read
"""
from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from cell.config import settings
from cell.scheduler.clock import ist_now, day_window_start_ts

logger = logging.getLogger(__name__)

_client: Optional[AsyncWebClient] = None


def _get_client() -> AsyncWebClient:
    global _client
    if _client is None:
        if settings.mock_mode:
            _client = AsyncWebClient(
                token=settings.slack_bot_token,
                base_url=f"{settings.mock_slack_url}/api/",
            )
        else:
            _client = AsyncWebClient(token=settings.slack_bot_token)
    return _client


async def get_dm_channel_id(slack_user_id: str) -> Optional[str]:
    """Open (or retrieve) the DM channel with a user."""
    client = _get_client()
    try:
        resp = await client.conversations_open(users=slack_user_id)
        return resp["channel"]["id"]
    except SlackApiError as exc:
        logger.error("Cannot open DM for user %s: %s", slack_user_id, exc.response["error"])
        return None


async def read_intern_messages(slack_user_id: str) -> List[Dict]:
    """
    Pull all messages from a DM channel over the last 24hrs (the current day window).
    Day window: 2AM today → 1:59AM tomorrow (i.e., from the last 2AM IST tick).

    Returns list of message dicts sorted oldest-first.
    """
    channel_id = await get_dm_channel_id(slack_user_id)
    if not channel_id:
        return []

    client = _get_client()
    oldest_ts = day_window_start_ts()   # Unix timestamp of today's 2AM IST

    messages = []
    cursor = None

    try:
        while True:
            kwargs: Dict = {
                "channel": channel_id,
                "oldest": str(oldest_ts),
                "limit": 200,
            }
            if cursor:
                kwargs["cursor"] = cursor

            resp = await client.conversations_history(**kwargs)
            messages.extend(resp.get("messages", []))

            next_cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not next_cursor:
                break
            cursor = next_cursor

    except SlackApiError as exc:
        logger.error("conversations.history failed for %s: %s", slack_user_id, exc.response["error"])

    # Sort oldest-first, exclude bot messages
    user_messages = [m for m in messages if m.get("user") == slack_user_id]
    user_messages.sort(key=lambda m: float(m.get("ts", 0)))
    return user_messages


async def collect_all_intern_messages(interns: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Fetch messages for all interns concurrently.
    Returns {intern_id: [messages]} mapping.
    """
    import asyncio
    results = {}

    async def _fetch(intern: Dict) -> None:
        intern_id = intern["employee_id"]
        slack_user_id = intern.get("slack_user_id")
        if not slack_user_id:
            logger.warning("No Slack user ID for intern %s — skipping", intern_id)
            results[intern_id] = []
            return
        msgs = await read_intern_messages(slack_user_id)
        results[intern_id] = msgs

    await asyncio.gather(*[_fetch(i) for i in interns])
    return results
