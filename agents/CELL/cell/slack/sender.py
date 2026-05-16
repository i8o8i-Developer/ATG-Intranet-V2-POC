"""
CELL Slack Sender.
DM-only. Never posts to channels.
Uses slack-sdk AsyncWebClient.
In MOCK_MODE, posts to mock Slack server (port 8004).
"""
from __future__ import annotations

import logging
from typing import Optional

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from cell.config import settings

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


async def send_dm(slack_user_id: str, text: str) -> bool:
    """
    Send a DM to a Slack user by their user ID.
    Opens a DM channel first (conversations.open), then posts.
    Returns True on success, False on failure.
    """
    client = _get_client()
    try:
        # Open or reuse existing DM channel
        open_resp = await client.conversations_open(users=slack_user_id)
        channel_id = open_resp["channel"]["id"]

        await client.chat_postMessage(channel=channel_id, text=text)
        logger.info("DM sent to %s", slack_user_id)
        return True

    except SlackApiError as exc:
        logger.error("Slack DM failed for user %s: %s", slack_user_id, exc.response["error"])
        return False
    except Exception as exc:
        logger.exception("Unexpected error sending DM to %s: %s", slack_user_id, exc)
        return False
