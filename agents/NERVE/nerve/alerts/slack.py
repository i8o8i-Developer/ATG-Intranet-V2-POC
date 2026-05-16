import logging
from slack_sdk.web.async_client import AsyncWebClient
from nerve.config import settings

logger = logging.getLogger(__name__)

async def slack_alert(message: str):
    if not settings.slack_bot_token or not settings.slack_admin_channel:
        logger.warning("Slack not configured — alert: %s", message)
        return
    client = AsyncWebClient(token=settings.slack_bot_token)
    try:
        await client.chat_postMessage(
            channel=settings.slack_admin_channel,
            text=f"[NERVE] {message}",
        )
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
