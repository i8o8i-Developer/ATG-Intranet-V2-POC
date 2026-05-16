"""
CELL Core Pydantic Models.
All data flowing through CELL is typed here.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class TaskStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_PM_APPROVAL = "pending_pm_approval"
    PENDING_APPROVAL = "pending_approval"   # intern marked done, awaiting PM
    APPROVED = "approved"
    REJECTED = "rejected"
    DEADLINE_MISSED = "deadline_missed"
    BLOCKED = "blocked"
    CLOSED = "closed"


class TaskPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class BountyStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TaskSource(str, Enum):
    IRIS = "iris"
    AGENT3 = "agent3"
    MANUAL = "manual"


class EODStatus(str, Enum):
    DONE = "done"
    BLOCKED = "blocked"
    CARRY = "carry"
    MISSED = "missed"


# ──────────────────────────────────────────────
# NERVE Event (from IRIS)
# ──────────────────────────────────────────────

class NerveEvent(BaseModel):
    event: str
    meeting_id: str
    project_id: str
    confidence_score: float
    flagged: bool = False
    insights_path: str
    timestamp: datetime


# ──────────────────────────────────────────────
# Agent 3 Ingest
# ──────────────────────────────────────────────

class Agent3Task(BaseModel):
    title: str
    assignee_id: str
    estimated_hours: float
    priority: TaskPriority = TaskPriority.NORMAL
    due_date: date
    notes: Optional[str] = None


class Agent3IngestRequest(BaseModel):
    source: str = "agent3"
    project_id: str
    week_ref: str
    tasks: List[Agent3Task]


# ──────────────────────────────────────────────
# Raw Extracted Task (pre-ERP)
# ──────────────────────────────────────────────

class RawTask(BaseModel):
    """Task as extracted from YAML / Agent 3 before dedup + ERP write."""
    title: str
    project_id: str
    assignee_id: str
    priority: TaskPriority = TaskPriority.NORMAL
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    notes: Optional[str] = None
    source: TaskSource = TaskSource.IRIS
    source_meeting_id: Optional[str] = None
    source_yaml_field: Optional[str] = None


# ──────────────────────────────────────────────
# ERP Task (write contract)
# ──────────────────────────────────────────────

class ERPTaskCreate(BaseModel):
    title: str
    project_id: str
    assignee_id: str
    priority: str
    due_date: Optional[str] = None     # ISO date string
    estimated_hours: float
    bounty_value: float                # bounty units (not INR); accountant × ₹100 = payout
    status: str = "open"
    source_meeting_id: Optional[str] = None
    source_yaml_field: Optional[str] = None
    notes: Optional[str] = None
    subtasks: List[Any] = Field(default_factory=list)


class ERPTaskResponse(BaseModel):
    erp_task_id: str
    title: str
    project_id: str
    assignee_id: str
    status: str
    created_at: Optional[datetime] = None


# ──────────────────────────────────────────────
# Postgres Task (internal state)
# ──────────────────────────────────────────────

class TaskRecord(BaseModel):
    id: Optional[int] = None
    erp_task_id: Optional[str] = None
    project_id: str
    assignee_id: str
    title: str
    priority: Optional[str] = None
    estimated_hours: Optional[float] = None
    due_date: Optional[date] = None
    status: str = TaskStatus.OPEN
    source: str = TaskSource.IRIS
    source_meeting_id: Optional[str] = None
    pm_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    bounty_value: Optional[float] = None   # bounty units (not INR)


# ──────────────────────────────────────────────
# Bounty
# ──────────────────────────────────────────────

class BountyRecord(BaseModel):
    id: Optional[int] = None
    task_erp_id: str
    intern_id: str
    project_id: str
    estimated_hours: float
    priority: str
    bounty_value: float                # bounty units (not INR); accountant × ₹100 = payout
    status: BountyStatus = BountyStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ──────────────────────────────────────────────
# EOD Submission
# ──────────────────────────────────────────────

class EODEntry(BaseModel):
    task_number: int
    status: EODStatus
    block_reason: Optional[str] = None


class EODSubmission(BaseModel):
    intern_id: str
    submission_date: date
    entries: List[EODEntry]
    raw_message: str
    parse_success: bool
    security_flag: bool = False


# ──────────────────────────────────────────────
# PM Approval Reply
# ──────────────────────────────────────────────

class PMApprovalAction(BaseModel):
    task_index: int           # 1-based index from digest
    action: str               # "approve" | "reject"
    edited_hours: Optional[float] = None
    rejection_note: Optional[str] = None


class PMApprovalReply(BaseModel):
    pm_id: str
    raw_message: str
    actions: List[PMApprovalAction]
    approve_all: bool = False
    parse_error: bool = False


# ──────────────────────────────────────────────
# Accountability
# ──────────────────────────────────────────────

class AccountabilityRecord(BaseModel):
    id: Optional[int] = None
    intern_id: str
    date: date
    eod_submitted: bool = False
    tasks_missed: int = 0
    consecutive_miss_count: int = 0
    warning_sent: bool = False
    escalated_to: Optional[str] = None
    created_at: Optional[datetime] = None


# ──────────────────────────────────────────────
# ERP Write Queue (retry / dead-letter)
# ──────────────────────────────────────────────

class ERPWriteQueueRecord(BaseModel):
    id: Optional[int] = None
    task_id: int
    payload: dict
    attempt_count: int = 0
    last_error: Optional[str] = None
    status: str = "pending"   # pending | success | dead_letter
    next_retry_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
