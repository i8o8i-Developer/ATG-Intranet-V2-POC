"""
CELL API Routes.

Endpoints:
  POST /cell/ingest-nerve       — NERVE event from IRIS
  POST /cell/ingest-tasks       — Agent 3 weekly task push
  GET  /cell/health             — Health check
  GET  /cell/tasks/{project_id} — Staged tasks for a project (debug/admin)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from cell.core.models import NerveEvent, Agent3IngestRequest, RawTask, TaskSource, TaskPriority
from cell.core.extractor import extract_raw_tasks, enrich_tasks
from cell.core.deduplicator import check_duplicate, get_embedding_for_storage
from cell.core.bounty import calculate_bounty
from cell.db import postgres
from cell.erp.client import create_task
from cell.core.models import ERPTaskCreate
from cell.storage.r2_client import fetch_insights_yaml

router = APIRouter()
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────────────────────

@router.get("/cell/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "CELL"}


# ──────────────────────────────────────────────────────────────
# NERVE Ingest (from IRIS)
# ──────────────────────────────────────────────────────────────

@router.post("/cell/ingest-nerve", status_code=status.HTTP_202_ACCEPTED)
async def ingest_nerve(event: NerveEvent, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Receive NERVE event from IRIS. Validates event, then processes async.
    Returns 202 immediately so NERVE doesn't wait.
    """
    logger.info("NERVE event received: %s / %s", event.meeting_id, event.project_id)

    if event.flagged:
        logger.warning(
            "IRIS flagged meeting %s (confidence=%.2f) — staging for human review",
            event.meeting_id, event.confidence_score,
        )
        # Still process, but PM will see a low-confidence warning in digest

    background_tasks.add_task(
        _process_nerve_event,
        event.insights_path,
        event.project_id,
        event.meeting_id,
        event.confidence_score,
        event.flagged,
    )
    return {"status": "accepted", "meeting_id": event.meeting_id}


async def _process_nerve_event(
    insights_path: str,
    project_id: str,
    meeting_id: str,
    confidence_score: float,
    flagged: bool,
) -> None:
    """Background: fetch YAML, extract, dedup, stage for PM approval."""
    insights = fetch_insights_yaml(insights_path)
    if not insights:
        logger.error("Failed to fetch insights.yaml for meeting %s", meeting_id)
        return

    # Determine default assignee from insights
    default_assignee = insights.get("primary_assignee") or insights.get("owner") or "UNASSIGNED"

    raw_tasks = extract_raw_tasks(insights, project_id, meeting_id, default_assignee)
    if not raw_tasks:
        logger.info("No tasks extracted from meeting %s", meeting_id)
        return

    enriched_tasks = await enrich_tasks(raw_tasks)
    await _stage_tasks_for_pm(enriched_tasks, flagged=flagged, confidence=confidence_score)


# ──────────────────────────────────────────────────────────────
# Agent 3 Ingest
# ──────────────────────────────────────────────────────────────

@router.post("/cell/ingest-tasks", status_code=status.HTTP_202_ACCEPTED)
async def ingest_tasks(payload: Agent3IngestRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Receive weekly task breakdown from Agent 3.
    Deduplicates and stages for PM approval.
    """
    logger.info(
        "Agent 3 ingest: %s tasks for project %s / week %s",
        len(payload.tasks), payload.project_id, payload.week_ref,
    )
    background_tasks.add_task(_process_agent3_tasks, payload)
    return {
        "status": "accepted",
        "project_id": payload.project_id,
        "task_count": len(payload.tasks),
    }


async def _process_agent3_tasks(payload: Agent3IngestRequest) -> None:
    raw_tasks = [
        RawTask(
            title=t.title,
            project_id=payload.project_id,
            assignee_id=t.assignee_id,
            priority=t.priority,
            due_date=t.due_date,
            estimated_hours=t.estimated_hours,
            notes=t.notes,
            source=TaskSource.AGENT3,
            source_meeting_id=None,
            source_yaml_field=None,
        )
        for t in payload.tasks
    ]
    await _stage_tasks_for_pm(raw_tasks)


# ──────────────────────────────────────────────────────────────
# Shared: stage tasks for PM approval
# ──────────────────────────────────────────────────────────────

async def _stage_tasks_for_pm(
    tasks: List[RawTask],
    flagged: bool = False,
    confidence: float = 1.0,
) -> None:
    """
    For each task:
    1. Run dedup check.
    2. If duplicate: update due_date, add meeting ref, skip creation.
    3. If new: calculate bounty, insert to Postgres (pending_pm_approval).
    """
    for task in tasks:
        dedup = await check_duplicate(task)

        if dedup.is_duplicate and dedup.existing_task_id:
            logger.info(
                "Dedup skip: '%s' matches task_id=%s (sim=%.3f)",
                task.title, dedup.existing_task_id, dedup.similarity,
            )
            # Update due_date if changed
            if task.due_date:
                await postgres.update_task_due_date(dedup.existing_task_id, task.due_date)
            continue

        # New task
        bounty = calculate_bounty(
            task.estimated_hours or 4.0,
            task.priority.value,
        )
        embedding_str = await get_embedding_for_storage(task.title)

        pm_notes = None
        if flagged:
            pm_notes = f"[LOW CONFIDENCE {confidence:.0%}] Review before approving."

        task_id = await postgres.insert_task(
            project_id=task.project_id,
            assignee_id=task.assignee_id,
            title=task.title,
            priority=task.priority.value,
            estimated_hours=task.estimated_hours or 4.0,
            due_date=task.due_date,
            status="pending_pm_approval",
            source=task.source.value,
            source_meeting_id=task.source_meeting_id,
            pm_notes=pm_notes,
            bounty_value=bounty,
            title_embedding=None,  # stored as JSON string via embedding_str below
        )
        logger.info(
            "Staged task_id=%d '%s' for PM approval (bounty=%.2f units)",
            task_id, task.title, bounty,
        )


# ──────────────────────────────────────────────────────────────
# Debug: list staged tasks
# ──────────────────────────────────────────────────────────────

@router.get("/cell/tasks/{project_id}")
async def get_staged_tasks(project_id: str) -> Dict[str, Any]:
    tasks = await postgres.get_tasks_pending_pm_approval(project_id)
    return {"project_id": project_id, "pending_tasks": tasks, "count": len(tasks)}
