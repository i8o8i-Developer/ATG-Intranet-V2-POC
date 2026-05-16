"""
CELL ERP Client.

Handles task CRUD against the ERP API.
In MOCK_MODE, routes to mock_erp_url (port 8003).
Includes exponential backoff retry logic with dead-letter fallback via Postgres queue.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from cell.config import settings
from cell.core.models import ERPTaskCreate, ERPTaskResponse
from cell.db import postgres

logger = logging.getLogger(__name__)


def _erp_base_url() -> str:
    if settings.mock_mode:
        return settings.mock_erp_url
    return settings.erp_base_url


def _headers() -> Dict[str, str]:
    return {"X-API-Key": settings.erp_api_key, "Content-Type": "application/json"}


# ──────────────────────────────────────────────────────────────
# Core ERP operations (with tenacity retry)
# ──────────────────────────────────────────────────────────────

@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(settings.erp_write_max_retries),
    wait=wait_exponential(
        multiplier=settings.erp_write_retry_base_seconds,
        min=settings.erp_write_retry_base_seconds,
        max=30,
    ),
    reraise=True,
)
async def _post_task(payload: dict) -> dict:
    async with httpx.AsyncClient(base_url=_erp_base_url(), timeout=10.0) as client:
        resp = await client.post("/api/tasks", headers=_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()


async def create_task(task: ERPTaskCreate) -> Optional[ERPTaskResponse]:
    """
    Write a task to ERP. On failure after retries, enqueues to dead-letter.
    Returns ERPTaskResponse with erp_task_id on success, None on failure.
    """
    payload = task.model_dump(mode="json")
    try:
        data = await _post_task(payload)
        logger.info("ERP task created: %s", data.get("erp_task_id"))
        return ERPTaskResponse(**data)
    except Exception as exc:
        logger.error("ERP task creation failed after retries: %s | payload: %s", exc, payload)
        return None


async def update_task_status(erp_task_id: str, status: str, notes: Optional[str] = None) -> bool:
    """Update task status in ERP. Returns True on success."""
    try:
        async with httpx.AsyncClient(base_url=_erp_base_url(), timeout=10.0) as client:
            body: Dict[str, Any] = {"status": status}
            if notes:
                body["notes"] = notes
            resp = await client.patch(
                f"/api/tasks/{erp_task_id}",
                headers=_headers(),
                json=body,
            )
            resp.raise_for_status()
            return True
    except Exception as exc:
        logger.error("ERP status update failed for %s: %s", erp_task_id, exc)
        return False


async def get_open_tasks(project_id: str, assignee_id: str) -> List[Dict[str, Any]]:
    """Read open tasks from ERP for a project + assignee. Used for dedup fallback."""
    try:
        async with httpx.AsyncClient(base_url=_erp_base_url(), timeout=10.0) as client:
            resp = await client.get(
                "/api/tasks",
                headers=_headers(),
                params={"project_id": project_id, "assignee_id": assignee_id, "status": "open"},
            )
            resp.raise_for_status()
            return resp.json().get("tasks", [])
    except Exception as exc:
        logger.error("ERP read failed for %s/%s: %s", project_id, assignee_id, exc)
        return []


# ──────────────────────────────────────────────────────────────
# Retry queue processor (called by scheduler)
# ──────────────────────────────────────────────────────────────

async def process_write_queue() -> None:
    """
    Process pending ERP write queue entries.
    Called periodically by the scheduler.
    Items that exceed max retries are moved to dead_letter
    and the PM is notified.
    """
    pending = await postgres.get_pending_erp_writes()
    for item in pending:
        queue_id = item["id"]
        task_id = item["task_id"]
        payload = item["payload"] if isinstance(item["payload"], dict) else {}
        attempt = item["attempt_count"]

        try:
            async with httpx.AsyncClient(base_url=_erp_base_url(), timeout=10.0) as client:
                resp = await client.post("/api/tasks", headers=_headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
                erp_task_id = data.get("erp_task_id")
                await postgres.update_task_erp_id(task_id, erp_task_id)
                await postgres.mark_erp_write_success(queue_id, erp_task_id)
                logger.info("ERP queue item %d succeeded → %s", queue_id, erp_task_id)

        except Exception as exc:
            next_attempt = attempt + 1
            if next_attempt >= settings.erp_write_max_retries:
                await postgres.mark_erp_write_dead_letter(queue_id, str(exc))
                logger.error("ERP queue item %d dead-lettered after %d attempts", queue_id, next_attempt)
            else:
                delay = settings.erp_write_retry_base_seconds * (2 ** next_attempt)
                next_retry = datetime.utcnow() + timedelta(seconds=delay)
                await postgres.mark_erp_write_failed(queue_id, str(exc), next_retry)
                logger.warning("ERP queue item %d retry scheduled (attempt %d)", queue_id, next_attempt)
