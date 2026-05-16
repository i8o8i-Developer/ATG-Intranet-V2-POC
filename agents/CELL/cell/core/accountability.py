"""
CELL Accountability & Escalation Logic.

- Tracks no-shows (interns who don't submit EOD by 2AM).
- Maintains consecutive miss counter.
- Escalates: 3 misses → APM, 5 misses → Dept Head.
- Warning text injected into next morning's 8AM todo DM.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Dict, List, Optional

from cell.config import settings
from cell.db import postgres

logger = logging.getLogger(__name__)


async def process_no_show(intern_id: str, day: date, missed_task_ids: List[int]) -> dict:
    """
    Called at 2AM for an intern who did NOT submit EOD.
    Returns a dict with escalation info for downstream Slack notification.
    """
    # Get prior consecutive miss count
    prior_count = await postgres.get_consecutive_miss_count(intern_id)
    new_count = prior_count + 1

    # Determine escalation
    escalated_to: Optional[str] = None
    if new_count >= settings.escalate_to_dept_head_after:
        employee = await postgres.get_employee(intern_id)
        if employee:
            escalated_to = employee.get("dept_head_id")
        logger.warning(
            "Escalating %s to dept_head after %d consecutive misses", intern_id, new_count
        )
    elif new_count >= settings.escalate_to_apm_after:
        employee = await postgres.get_employee(intern_id)
        if employee:
            escalated_to = employee.get("apm_id")
        logger.warning(
            "Escalating %s to APM after %d consecutive misses", intern_id, new_count
        )

    await postgres.upsert_accountability(
        intern_id=intern_id,
        day=day,
        eod_submitted=False,
        tasks_missed=len(missed_task_ids),
        consecutive_miss_count=new_count,
        warning_sent=False,   # will be set to True when DM is actually sent
        escalated_to=escalated_to,
    )

    return {
        "intern_id": intern_id,
        "consecutive_misses": new_count,
        "tasks_missed": len(missed_task_ids),
        "escalated_to": escalated_to,
    }


async def process_eod_submitted(intern_id: str, day: date) -> None:
    """Called at 2AM for an intern who DID submit EOD. Resets consecutive miss counter."""
    await postgres.upsert_accountability(
        intern_id=intern_id,
        day=day,
        eod_submitted=True,
        tasks_missed=0,
        consecutive_miss_count=0,
        warning_sent=False,
        escalated_to=None,
    )


async def get_warning_text(intern_id: str) -> Optional[str]:
    """
    Return a warning string to prepend to the morning DM if the intern
    had consecutive misses yesterday.
    Returns None if no warning needed.
    """
    count = await postgres.get_consecutive_miss_count(intern_id)
    if count == 0:
        return None

    if count >= settings.escalate_to_dept_head_after:
        return (
            f"WARNING: You have missed EOD for {count} consecutive days.\n"
            f"Your Dept Head has been notified. Please respond to this DM immediately."
        )
    elif count >= settings.escalate_to_apm_after:
        return (
            f"WARNING: You have missed EOD for {count} consecutive days.\n"
            f"Your APM has been notified."
        )
    else:
        return (
            f"WARNING: You did not submit your EOD report yesterday.\n"
            f"{count} consecutive miss(es). {settings.escalate_to_apm_after - count} more will escalate to your APM."
        )


async def send_escalation_notifications(
    escalation_map: Dict[str, dict],
    slack_sender,
) -> None:
    """
    Send DMs to APMs / dept heads for escalated interns.
    `escalation_map`: {intern_id: {escalated_to: supervisor_id, ...}}
    """
    for intern_id, info in escalation_map.items():
        supervisor_id = info.get("escalated_to")
        if not supervisor_id:
            continue
        count = info.get("consecutive_misses", 0)
        supervisor = await postgres.get_employee(supervisor_id)
        if not supervisor:
            continue
        slack_id = supervisor.get("slack_user_id")
        if not slack_id:
            continue

        level = "APM" if count < settings.escalate_to_dept_head_after else "Dept Head"
        msg = (
            f"Escalation notice ({level}):\n"
            f"Intern {intern_id} has missed EOD for {count} consecutive days.\n"
            f"Please follow up."
        )
        await slack_sender.send_dm(slack_id, msg)
        logger.info("Escalation DM sent to %s (%s) for intern %s", slack_id, level, intern_id)
