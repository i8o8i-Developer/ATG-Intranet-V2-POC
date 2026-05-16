"""
CELL Scheduled Jobs — APScheduler AsyncIOScheduler.

Three daily jobs (all IST):
  08:00 AM — morning_job:  PM digest + intern todo DMs
  11:30 PM — eod_reminder_job: reminder to all interns
  02:00 AM — night_process_job: parse EODs, flag no-shows, process queue

Rationale for APScheduler over Celery:
- Only 3 fixed-time daily jobs — no distributed workers needed.
- AsyncIO-native, integrates cleanly with FastAPI's event loop.
- Celery adds Redis/RabbitMQ dependency with no benefit at this scale.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from cell.config import settings
from cell.scheduler.clock import ist_today, ist_yesterday, format_ist_date
from cell.core.bounty import format_bounty_display

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=IST)
    return _scheduler


def start_scheduler() -> None:
    sched = get_scheduler()
    s = settings

    sched.add_job(
        morning_job,
        CronTrigger(hour=s.schedule_morning_hour, minute=s.schedule_morning_minute, timezone=IST),
        id="morning_job",
        replace_existing=True,
    )
    sched.add_job(
        eod_reminder_job,
        CronTrigger(hour=s.schedule_eod_reminder_hour, minute=s.schedule_eod_reminder_minute, timezone=IST),
        id="eod_reminder_job",
        replace_existing=True,
    )
    sched.add_job(
        night_process_job,
        CronTrigger(hour=s.schedule_night_process_hour, minute=s.schedule_night_process_minute, timezone=IST),
        id="night_process_job",
        replace_existing=True,
    )

    sched.start()
    logger.info("CELL scheduler started (IST). Jobs: morning@08:00, eod@23:30, night@02:00")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("CELL scheduler stopped")


# ──────────────────────────────────────────────────────────────
# Job: Morning (8AM IST)
# ──────────────────────────────────────────────────────────────

async def morning_job() -> None:
    """
    1. Send PM digest (pending approvals + yesterday completions + flags).
    2. Send intern todo DMs (prioritised task list + warnings).
    """
    logger.info("CELL morning_job started")
    from cell.db import postgres
    from cell.slack import sender
    from cell.core.accountability import get_warning_text

    today = ist_today()
    yesterday = ist_yesterday()

    # ── Intern todo DMs ──────────────────────────────────────
    interns = await postgres.get_all_active_interns()
    for intern in interns:
        intern_id = intern["employee_id"]
        slack_id = intern.get("slack_user_id")
        if not slack_id:
            continue

        tasks = await postgres.get_tasks_for_intern_today(intern_id, today)
        if not tasks:
            continue

        # Build warning prefix
        warning = await get_warning_text(intern_id)

        msg = _build_intern_todo_dm(today, tasks, warning)
        await sender.send_dm(slack_id, msg)
        logger.info("Morning todo DM sent to intern %s", intern_id)

    # ── PM Digest ────────────────────────────────────────────
    await _send_pm_digests(today, yesterday)

    logger.info("CELL morning_job complete")


async def _send_pm_digests(today: date, yesterday: date) -> None:
    from cell.db import postgres
    from cell.slack import sender
    from cell.core.accountability import get_warning_text

    # Group pending tasks by project → PM
    pending_tasks = await postgres.get_tasks_pending_pm_approval()
    completed_tasks = await postgres.get_completed_tasks_yesterday(yesterday)

    # Get flags (no-shows, blockers)
    all_interns = await postgres.get_all_active_interns()
    flags: List[str] = []
    for intern in all_interns:
        intern_id = intern["employee_id"]
        warn = await get_warning_text(intern_id)
        if warn:
            flags.append(f"{intern_id}: {warn.splitlines()[0]}")

    # Collect unique project IDs from pending tasks
    project_ids = list({t["project_id"] for t in pending_tasks})
    if not project_ids and not completed_tasks and not flags:
        return

    # For each project's PM, send digest
    sent_pms = set()
    for project_id in project_ids:
        pm = await postgres.get_pm_for_project(project_id)
        if not pm or pm["employee_id"] in sent_pms:
            continue
        pm_slack_id = pm.get("slack_user_id")
        if not pm_slack_id:
            continue

        proj_pending = [t for t in pending_tasks if t["project_id"] == project_id]
        proj_completed = [t for t in completed_tasks if t["project_id"] == project_id]

        msg = _build_pm_digest(today, pm["name"], project_id, proj_pending, proj_completed, flags)
        await sender.send_dm(pm_slack_id, msg)
        sent_pms.add(pm["employee_id"])

        # Record digest for escalation tracking
        pool = await postgres.get_pool()
        await pool.execute(
            "INSERT INTO pm_approval_digests (project_id, pm_id, sent_at) VALUES ($1,$2,NOW())",
            project_id, pm["employee_id"],
        )
        logger.info("PM digest sent to %s for project %s", pm["employee_id"], project_id)


# ──────────────────────────────────────────────────────────────
# Job: EOD Reminder (11:30PM IST)
# ──────────────────────────────────────────────────────────────

async def eod_reminder_job() -> None:
    """Send EOD reminder DMs to ALL active interns regardless of prior submission."""
    logger.info("CELL eod_reminder_job started")
    from cell.db import postgres
    from cell.slack import sender

    today = ist_today()
    interns = await postgres.get_all_active_interns()

    for intern in interns:
        intern_id = intern["employee_id"]
        slack_id = intern.get("slack_user_id")
        if not slack_id:
            continue

        tasks = await postgres.get_tasks_for_intern_today(intern_id, today)
        if not tasks:
            continue

        msg = _build_eod_reminder(tasks)
        await sender.send_dm(slack_id, msg)
        logger.info("EOD reminder sent to intern %s", intern_id)

    logger.info("CELL eod_reminder_job complete")


# ──────────────────────────────────────────────────────────────
# Job: Night Processing (2AM IST)
# ──────────────────────────────────────────────────────────────

async def night_process_job() -> None:
    """
    1. Read all intern DM histories (last 24hrs).
    2. Parse EOD replies.
    3. Update task statuses.
    4. Flag no-shows. Update accountability log. Send escalations.
    5. Process ERP write queue.
    6. Check PM approval escalations (48hr timeout).
    """
    logger.info("CELL night_process_job started")
    from cell.db import postgres
    from cell.slack import reader as slack_reader
    from cell.slack import sender
    from cell.slack.parser import parse_eod_reply
    from cell.core.accountability import process_no_show, process_eod_submitted, send_escalation_notifications
    from cell.erp.client import process_write_queue

    today = ist_today()
    yesterday = ist_yesterday()

    interns = await postgres.get_all_active_interns()

    # Collect all intern messages in batch
    all_messages = await slack_reader.collect_all_intern_messages(interns)

    escalation_map: Dict[str, dict] = {}

    for intern in interns:
        intern_id = intern["employee_id"]
        messages = all_messages.get(intern_id, [])

        # Get today's tasks for this intern
        tasks = await postgres.get_tasks_for_intern_today(intern_id, today)
        if not tasks:
            continue

        task_id_map = {i + 1: t["id"] for i, t in enumerate(tasks)}
        task_erp_map = {i + 1: t.get("erp_task_id") for i, t in enumerate(tasks)}

        # Combine all messages into single text for parsing
        combined = "\n".join(m.get("text", "") for m in messages).strip()

        if not combined:
            # No messages at all → no-show
            missed_ids = await postgres.mark_tasks_deadline_missed(intern_id, today)
            info = await process_no_show(intern_id, today, missed_ids)
            if info.get("escalated_to"):
                escalation_map[intern_id] = info
            continue

        # Parse EOD reply
        submission = parse_eod_reply(intern_id, combined, task_id_map)

        if submission.security_flag:
            # Notify PM about injection attempt
            slack_id = intern.get("slack_user_id", "")
            logger.warning("Security flag raised for intern %s — notifying PM", intern_id)
            # Find PM for any of intern's projects
            if tasks:
                pm = await postgres.get_pm_for_project(tasks[0]["project_id"])
                if pm and pm.get("slack_user_id"):
                    await sender.send_dm(
                        pm["slack_user_id"],
                        f"SECURITY FLAG: Intern {intern_id} sent suspicious message that resembles prompt injection. "
                        f"Please review. Raw: {combined[:300]}",
                    )

        # Apply EOD entries to task statuses
        seen_task_numbers = set()
        for entry in submission.entries:
            n = entry.task_number
            seen_task_numbers.add(n)
            task_db_id = task_id_map.get(n)
            erp_task_id = task_erp_map.get(n)
            if not task_db_id:
                continue

            if entry.status.value == "done":
                await postgres.update_task_status(task_db_id, "pending_approval")
            elif entry.status.value == "blocked":
                await postgres.update_task_status(task_db_id, "blocked", pm_notes=entry.block_reason)
            elif entry.status.value == "carry":
                pass  # status stays open, no penalty

            # Persist EOD submission
            await postgres.insert_eod_submission(
                intern_id=intern_id,
                task_id=task_db_id,
                submission_date=today,
                status=entry.status.value,
                block_reason=entry.block_reason,
                raw_message=combined,
                parse_success=submission.parse_success,
            )

        # Any task not reported → missed
        for n, db_id in task_id_map.items():
            if n not in seen_task_numbers:
                await postgres.update_task_status(db_id, "deadline_missed")
                await postgres.insert_eod_submission(
                    intern_id=intern_id,
                    task_id=db_id,
                    submission_date=today,
                    status="missed",
                    block_reason=None,
                    raw_message=combined,
                    parse_success=False,
                )

        if submission.parse_success and submission.entries:
            await process_eod_submitted(intern_id, today)
        else:
            missed_ids = [task_id_map[n] for n in task_id_map if n not in seen_task_numbers]
            info = await process_no_show(intern_id, today, missed_ids)
            if info.get("escalated_to"):
                escalation_map[intern_id] = info

    # Send escalation DMs
    if escalation_map:
        await send_escalation_notifications(escalation_map, sender)

    # Process ERP write retry queue
    await process_write_queue()

    # PM approval escalation (48hr check)
    await _check_pm_approval_escalations(sender)

    logger.info("CELL night_process_job complete")


async def _check_pm_approval_escalations(sender) -> None:
    """Escalate to dept head if PM hasn't responded to approval digest in 48hrs."""
    from cell.db import postgres
    from cell.scheduler.clock import ist_now
    from datetime import datetime

    pool = await postgres.get_pool()
    now = ist_now()

    overdue = await pool.fetch(
        """
        SELECT d.id, d.project_id, d.pm_id, d.sent_at
        FROM pm_approval_digests d
        WHERE d.responded=FALSE
          AND d.sent_at < NOW() - INTERVAL '48 hours'
        """
    )
    for row in overdue:
        # Notify dept head
        pm = await postgres.get_employee(row["pm_id"])
        if pm and pm.get("dept_head_id"):
            dept_head = await postgres.get_employee(pm["dept_head_id"])
            if dept_head and dept_head.get("slack_user_id"):
                await sender.send_dm(
                    dept_head["slack_user_id"],
                    f"Escalation: PM {row['pm_id']} has not responded to task approval digest "
                    f"for project {row['project_id']} (sent {row['sent_at'].strftime('%Y-%m-%d %H:%M')} IST). "
                    f"Please follow up.",
                )
        # Mark as escalated (avoid repeated pings)
        await pool.execute(
            "UPDATE pm_approval_digests SET responded=TRUE WHERE id=$1", row["id"]
        )
        logger.warning(
            "PM approval escalation for project %s — PM %s", row["project_id"], row["pm_id"]
        )


# ──────────────────────────────────────────────────────────────
# Message builders
# ──────────────────────────────────────────────────────────────

_PRIORITY_LABEL = {
    "urgent": "[URGENT]",
    "high":   "[HIGH]  ",
    "normal": "[NORMAL]",
    "low":    "[LOW]   ",
}


def _build_intern_todo_dm(today: date, tasks: list, warning: Optional[str] = None) -> str:
    lines = []
    if warning:
        lines.append(warning)
        lines.append("")
    lines.append(f"Good morning! Here are your tasks for today — {format_ist_date(today)}.")
    lines.append("")
    for i, task in enumerate(tasks, start=1):
        priority = task.get("priority", "normal").lower()
        label = _PRIORITY_LABEL.get(priority, "[NORMAL]")
        title = task.get("title", "")
        due = task.get("due_date")
        due_str = f"due {due.strftime('%-d %b')}" if due else "no due date"
        hours = task.get("estimated_hours", 4)
        bounty = task.get("bounty_value", 0)

        lines.append(f"{label} {title} — {due_str}")
        lines.append(f"         Est. {hours}hrs | Bounty: {format_bounty_display(bounty)}")
        lines.append(f"         Reply: done {i} / blocked {i} <reason> / carry {i}")
        lines.append("")
    lines.append("Reply in this format at EOD. One line per task.")
    return "\n".join(lines)


def _build_eod_reminder(tasks: list) -> str:
    lines = [
        "EOD check-in reminder — please reply before 2AM.",
        "",
        "Format for each task:",
        "  done <task_number>",
        "  blocked <task_number> <reason>",
        "  carry <task_number>",
        "",
        "Your open tasks today:",
    ]
    for i, task in enumerate(tasks, start=1):
        lines.append(f"  {i}. {task.get('title', '')}")
    lines.append("")
    lines.append("Reply now or your tasks will be marked as deadline missed.")
    return "\n".join(lines)


def _build_pm_digest(
    today: date,
    pm_name: str,
    project_id: str,
    pending_tasks: list,
    completed_tasks: list,
    flags: List[str],
) -> str:
    lines = [f"Good morning {pm_name} — {format_ist_date(today)} summary for {project_id}.", ""]

    if pending_tasks:
        lines.append("━━ PENDING YOUR APPROVAL ━━")
        lines.append(f"{len(pending_tasks)} new task(s) generated:")
        for i, task in enumerate(pending_tasks, start=1):
            priority = task.get("priority", "normal").upper()
            title = task.get("title", "")
            assignee = task.get("assignee_id", "")
            hours = task.get("estimated_hours", 4)
            bounty = task.get("bounty_value", 0)
            lines.append(f"  {i}. [{priority}]  {title} — {assignee} — Est. {hours}hrs — {format_bounty_display(bounty)}")
        lines.append("")
        lines.append("Reply: approve all / approve 1,3 / reject 2 - <reason>")
        lines.append("You can also edit hours: approve 1 hours=6")
        lines.append("")

    if completed_tasks:
        lines.append("━━ YESTERDAY'S COMPLETIONS ━━")
        lines.append(f"{len(completed_tasks)} task(s) marked done by interns:")
        for t in completed_tasks[:5]:
            lines.append(f"  ✓ {t.get('assignee_id')} — {t.get('title')}")
        if len(completed_tasks) > 5:
            lines.append(f"  ... ({len(completed_tasks) - 5} more)")
        lines.append("")

    if flags:
        lines.append("━━ FLAGS ━━")
        for flag in flags:
            lines.append(f"  ⚠ {flag}")

    return "\n".join(lines)
