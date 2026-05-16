"""
CELL PM Approval Processor.

Parses PM's approval reply, applies approve/reject actions,
writes approved tasks to ERP, credits bounties.
"""
from __future__ import annotations

import logging
from typing import List

from cell.core.models import PMApprovalReply
from cell.db import postgres
from cell.erp import client as erp_client
from cell.core.models import ERPTaskCreate
from cell.core.bounty import calculate_bounty

logger = logging.getLogger(__name__)


async def process_pm_approval(reply: PMApprovalReply, project_id: str) -> dict:
    """
    Apply PM approval/rejection actions to staged tasks.

    If approve_all: approve every pending task for the project.
    Otherwise apply per-task actions from reply.actions.

    Returns summary of actions taken.
    """
    pending = await postgres.get_tasks_pending_pm_approval(project_id)
    if not pending:
        return {"approved": 0, "rejected": 0, "error": "No pending tasks"}

    # Build 1-indexed map matching the digest order
    task_index_map = {i + 1: t for i, t in enumerate(pending)}

    approved_count = 0
    rejected_count = 0

    if reply.approve_all:
        for idx, task in task_index_map.items():
            await _approve_task(task, reply.pm_id, edited_hours=None)
            approved_count += 1
    else:
        acted_indices = set()
        for action in reply.actions:
            idx = action.task_index
            task = task_index_map.get(idx)
            if not task:
                logger.warning("PM referenced task index %d but only %d tasks pending", idx, len(pending))
                continue
            acted_indices.add(idx)

            if action.action == "approve":
                await _approve_task(task, reply.pm_id, edited_hours=action.edited_hours)
                approved_count += 1
            elif action.action == "reject":
                await _reject_task(task, reply.pm_id, note=action.rejection_note)
                rejected_count += 1

    return {"approved": approved_count, "rejected": rejected_count}


async def _approve_task(task: dict, pm_id: str, edited_hours=None) -> None:
    task_id = task["id"]
    hours = edited_hours if edited_hours is not None else task.get("estimated_hours", 4.0)
    priority = task.get("priority", "normal")

    # Recalculate bounty if hours edited
    bounty = calculate_bounty(hours, priority)

    if edited_hours is not None:
        await postgres.update_task_estimated_hours(task_id, hours)

    # Write to ERP
    erp_payload = ERPTaskCreate(
        title=task["title"],
        project_id=task["project_id"],
        assignee_id=task["assignee_id"],
        priority=priority,
        due_date=str(task["due_date"]) if task.get("due_date") else None,
        estimated_hours=hours,
        bounty_value=bounty,
        status="open",
        source_meeting_id=None,
        notes=task.get("pm_notes"),
    )
    erp_resp = await erp_client.create_task(erp_payload)

    if erp_resp and erp_resp.erp_task_id:
        await postgres.update_task_erp_id(task_id, erp_resp.erp_task_id)
        await postgres.update_task_status(task_id, "open")

        # Credit bounty
        await postgres.insert_bounty(
            task_erp_id=erp_resp.erp_task_id,
            intern_id=task["assignee_id"],
            project_id=task["project_id"],
            estimated_hours=hours,
            priority=priority,
            bounty_value=bounty,
        )
        logger.info(
            "Task approved: %s → ERP %s (bounty=%.2f units, approved_by=%s)",
            task["title"], erp_resp.erp_task_id, bounty, pm_id,
        )
    else:
        # ERP write failed — enqueue for retry
        await postgres.enqueue_erp_write(task_id, erp_payload.model_dump(mode="json"))
        logger.error("ERP write failed for task_id=%d — queued for retry", task_id)


async def _reject_task(task: dict, pm_id: str, note=None) -> None:
    task_id = task["id"]
    pm_note = f"Rejected by {pm_id}"
    if note:
        pm_note += f": {note}"
    # Set status to open (surfaces in next standup digest) with rejection note
    await postgres.update_task_status(task_id, "open", pm_notes=pm_note)
    logger.info("Task rejected: %s (task_id=%d, note=%s)", task["title"], task_id, note)
