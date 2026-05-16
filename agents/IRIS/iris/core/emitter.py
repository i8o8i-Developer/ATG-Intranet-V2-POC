"""
NERVE event emitter.
Posts iris.extraction.complete events to the NERVE webhook endpoint.
"""

import httpx
import logging
from datetime import datetime, timezone

from iris.config import settings
from iris.core.models import IRISEvent

logger = logging.getLogger(__name__)


def emit_extraction_complete(
    meeting_id: str,
    project_id: str,
    confidence_score: float,
    flagged: bool,
    insights_path: str,
    provider: str,
) -> IRISEvent:
    """
    Build and emit the iris.extraction.complete event to NERVE.
    Returns the event payload (useful for logging and test assertions).
    """
    event = IRISEvent(
        event="iris.extraction.complete",
        meeting_id=meeting_id,
        project_id=project_id,
        confidence_score=confidence_score,
        flagged=flagged,
        insights_path=insights_path,
        timestamp=datetime.now(timezone.utc),
        provider=provider,
    )

    payload = event.model_dump(mode="json")

    try:
        response = httpx.post(
            settings.nerve_webhook_url,
            json=payload,
            headers={"X-API-Key": settings.nerve_api_key},
            timeout=5.0,
        )
        if response.status_code in (200, 202):
            logger.info(
                f"[{meeting_id}] Event emitted to NERVE — flagged={flagged}, "
                f"confidence={confidence_score:.2f}"
            )
        else:
            logger.warning(
                f"[{meeting_id}] NERVE returned {response.status_code}: {response.text}"
            )
    except (httpx.RequestError, httpx.TimeoutException) as e:
        # Non-fatal: log and continue. In production, add to a retry queue.
        logger.error(
            f"[{meeting_id}] Failed to emit event to NERVE: {e}. "
            "Event was not delivered but extraction is complete."
        )

    return event
