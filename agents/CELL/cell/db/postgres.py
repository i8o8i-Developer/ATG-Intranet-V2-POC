"""
CELL Postgres layer.
Uses asyncpg directly for performance.
All SQL is explicit — no ORM magic.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import asyncpg
from asyncpg import Pool

from cell.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[Pool] = None


async def get_pool() -> Pool:
    global _pool
    if _pool is None:
        # Strip sqlalchemy prefix for asyncpg
        dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ──────────────────────────────────────────────
# Tasks
# ──────────────────────────────────────────────

async def insert_task(
    project_id: str,
    assignee_id: str,
    title: str,
    priority: str,
    estimated_hours: float,
    due_date: Optional[date],
    status: str,
    source: str,
    source_meeting_id: Optional[str],
    pm_notes: Optional[str],
    bounty_value: float,
    title_embedding: Optional[List[float]] = None,
) -> int:
    pool = await get_pool()
    embedding_str = json.dumps(title_embedding) if title_embedding else None
    row = await pool.fetchrow(
        """
        INSERT INTO tasks (
            project_id, assignee_id, title, title_embedding, priority,
            estimated_hours, due_date, status, source, source_meeting_id,
            pm_notes, bounty_value, created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4::vector, $5,
            $6, $7, $8, $9, $10,
            $11, $12, NOW(), NOW()
        ) RETURNING id
        """,
        project_id, assignee_id, title, embedding_str, priority,
        estimated_hours, due_date, status, source, source_meeting_id,
        pm_notes, bounty_value,
    )
    return row["id"]


async def update_task_erp_id(task_id: int, erp_task_id: str) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE tasks SET erp_task_id=$1, updated_at=NOW() WHERE id=$2",
        erp_task_id, task_id,
    )


async def update_task_status(task_id: int, status: str, pm_notes: Optional[str] = None) -> None:
    pool = await get_pool()
    if pm_notes is not None:
        await pool.execute(
            "UPDATE tasks SET status=$1, pm_notes=$2, updated_at=NOW() WHERE id=$3",
            status, pm_notes, task_id,
        )
    else:
        await pool.execute(
            "UPDATE tasks SET status=$1, updated_at=NOW() WHERE id=$2",
            status, task_id,
        )


async def update_task_estimated_hours(task_id: int, hours: float) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE tasks SET estimated_hours=$1, updated_at=NOW() WHERE id=$2",
        hours, task_id,
    )


async def update_task_due_date(task_id: int, due_date: date) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE tasks SET due_date=$1, updated_at=NOW() WHERE id=$2",
        due_date, task_id,
    )


async def get_open_tasks_for_assignee(project_id: str, assignee_id: str) -> List[Dict[str, Any]]:
    """Return tasks that are open or in_progress for dedup check."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, erp_task_id, title, title_embedding::text, status, due_date
        FROM tasks
        WHERE project_id=$1
          AND assignee_id=$2
          AND status IN ('open','in_progress','pending_pm_approval')
        """,
        project_id, assignee_id,
    )
    return [dict(r) for r in rows]


async def get_tasks_pending_pm_approval(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    pool = await get_pool()
    if project_id:
        rows = await pool.fetch(
            """
            SELECT id, erp_task_id, project_id, assignee_id, title,
                   priority, estimated_hours, due_date, bounty_value, pm_notes
            FROM tasks WHERE status='pending_pm_approval' AND project_id=$1
            ORDER BY created_at
            """,
            project_id,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT id, erp_task_id, project_id, assignee_id, title,
                   priority, estimated_hours, due_date, bounty_value, pm_notes
            FROM tasks WHERE status='pending_pm_approval'
            ORDER BY created_at
            """
        )
    return [dict(r) for r in rows]


async def get_tasks_for_intern_today(intern_id: str, today: date) -> List[Dict[str, Any]]:
    """Return open/in-progress tasks due today or overdue for an intern's daily DM."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, erp_task_id, title, priority, estimated_hours,
               due_date, bounty_value, status
        FROM tasks
        WHERE assignee_id=$1
          AND status IN ('open','in_progress','blocked')
        ORDER BY
          CASE priority
            WHEN 'urgent' THEN 1
            WHEN 'high' THEN 2
            WHEN 'normal' THEN 3
            WHEN 'low' THEN 4
          END,
          due_date ASC NULLS LAST
        """,
        intern_id,
    )
    return [dict(r) for r in rows]


async def get_completed_tasks_yesterday(yesterday: date) -> List[Dict[str, Any]]:
    """Return tasks marked pending_approval on a specific date."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT t.id, t.erp_task_id, t.assignee_id, t.title, t.project_id
        FROM tasks t
        WHERE t.status='pending_approval'
          AND DATE(t.updated_at AT TIME ZONE 'Asia/Kolkata') = $1
        """,
        yesterday,
    )
    return [dict(r) for r in rows]


async def mark_tasks_deadline_missed(intern_id: str, day: date) -> List[int]:
    """Mark all open tasks for intern as deadline_missed. Return affected task IDs."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        UPDATE tasks
        SET status='deadline_missed', updated_at=NOW()
        WHERE assignee_id=$1
          AND status IN ('open','in_progress','blocked')
        RETURNING id
        """,
        intern_id,
    )
    return [r["id"] for r in rows]


# ──────────────────────────────────────────────
# Bounty Ledger
# ──────────────────────────────────────────────

async def insert_bounty(
    task_erp_id: str,
    intern_id: str,
    project_id: str,
    estimated_hours: float,
    priority: str,
    bounty_value: float,
) -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO bounty_ledger (
            task_erp_id, intern_id, project_id,
            estimated_hours, priority, bounty_value,
            status, created_at
        ) VALUES ($1,$2,$3,$4,$5,$6,'pending',NOW())
        RETURNING id
        """,
        task_erp_id, intern_id, project_id, estimated_hours, priority, bounty_value,
    )
    return row["id"]


async def approve_bounty(bounty_id: int, approved_by: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE bounty_ledger
        SET status='approved', approved_by=$1, approved_at=NOW()
        WHERE id=$2
        """,
        approved_by, bounty_id,
    )


async def reject_bounty(bounty_id: int, approved_by: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE bounty_ledger
        SET status='rejected', approved_by=$1, approved_at=NOW()
        WHERE id=$2
        """,
        approved_by, bounty_id,
    )


async def get_bounty_by_erp_task(erp_task_id: str) -> Optional[Dict[str, Any]]:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM bounty_ledger WHERE task_erp_id=$1", erp_task_id
    )
    return dict(row) if row else None


# ──────────────────────────────────────────────
# EOD Submissions
# ──────────────────────────────────────────────

async def insert_eod_submission(
    intern_id: str,
    task_id: int,
    submission_date: date,
    status: str,
    block_reason: Optional[str],
    raw_message: str,
    parse_success: bool,
) -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO eod_submissions (
            intern_id, task_id, submission_date,
            status, block_reason, raw_message, parse_success, created_at
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,NOW())
        RETURNING id
        """,
        intern_id, task_id, submission_date, status, block_reason, raw_message, parse_success,
    )
    return row["id"]


# ──────────────────────────────────────────────
# Accountability Log
# ──────────────────────────────────────────────

async def get_accountability_record(intern_id: str, day: date) -> Optional[Dict[str, Any]]:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM accountability_log WHERE intern_id=$1 AND date=$2",
        intern_id, day,
    )
    return dict(row) if row else None


async def upsert_accountability(
    intern_id: str,
    day: date,
    eod_submitted: bool,
    tasks_missed: int,
    consecutive_miss_count: int,
    warning_sent: bool,
    escalated_to: Optional[str],
) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO accountability_log (
            intern_id, date, eod_submitted, tasks_missed,
            consecutive_miss_count, warning_sent, escalated_to, created_at
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,NOW())
        ON CONFLICT (intern_id, date) DO UPDATE SET
            eod_submitted=EXCLUDED.eod_submitted,
            tasks_missed=EXCLUDED.tasks_missed,
            consecutive_miss_count=EXCLUDED.consecutive_miss_count,
            warning_sent=EXCLUDED.warning_sent,
            escalated_to=EXCLUDED.escalated_to
        """,
        intern_id, day, eod_submitted, tasks_missed,
        consecutive_miss_count, warning_sent, escalated_to,
    )


async def get_consecutive_miss_count(intern_id: str) -> int:
    """Return the most recent consecutive_miss_count for an intern."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT consecutive_miss_count FROM accountability_log
        WHERE intern_id=$1
        ORDER BY date DESC LIMIT 1
        """,
        intern_id,
    )
    return row["consecutive_miss_count"] if row else 0


# ──────────────────────────────────────────────
# ERP Write Queue
# ──────────────────────────────────────────────

async def enqueue_erp_write(task_id: int, payload: dict) -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO erp_write_queue (task_id, payload, attempt_count, status, next_retry_at, created_at)
        VALUES ($1, $2::jsonb, 0, 'pending', NOW(), NOW())
        RETURNING id
        """,
        task_id, json.dumps(payload),
    )
    return row["id"]


async def get_pending_erp_writes() -> List[Dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, task_id, payload, attempt_count, last_error
        FROM erp_write_queue
        WHERE status='pending' AND next_retry_at <= NOW()
        ORDER BY created_at
        """
    )
    return [dict(r) for r in rows]


async def mark_erp_write_success(queue_id: int, erp_task_id: str) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE erp_write_queue SET status='success' WHERE id=$1", queue_id
    )


async def mark_erp_write_failed(queue_id: int, error: str, next_retry_at: datetime) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE erp_write_queue
        SET attempt_count=attempt_count+1, last_error=$1, next_retry_at=$2
        WHERE id=$3
        """,
        error, next_retry_at, queue_id,
    )


async def mark_erp_write_dead_letter(queue_id: int, error: str) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE erp_write_queue SET status='dead_letter', last_error=$1 WHERE id=$2",
        error, queue_id,
    )


# ──────────────────────────────────────────────
# Employee / Intern helpers
# ──────────────────────────────────────────────

async def get_all_active_interns() -> List[Dict[str, Any]]:
    """Return all interns (role='intern') with their Slack user IDs."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT employee_id, slack_user_id, name, apm_id, dept_head_id
        FROM employees
        WHERE role='intern' AND active=true
        """
    )
    return [dict(r) for r in rows]


async def get_employee(employee_id: str) -> Optional[Dict[str, Any]]:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM employees WHERE employee_id=$1", employee_id
    )
    return dict(row) if row else None


async def get_pm_for_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Return the PM (tech lead / APM) assigned to a project."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT e.employee_id, e.slack_user_id, e.name
        FROM project_members pm
        JOIN employees e ON e.employee_id = pm.employee_id
        WHERE pm.project_id=$1 AND pm.role='pm'
        LIMIT 1
        """,
        project_id,
    )
    return dict(row) if row else None
