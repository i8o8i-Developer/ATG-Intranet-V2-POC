"""
CELL Task Extractor.

Rule-based extraction from IRIS insights.yaml → RawTask list.

Real IRIS output uses a nested, meeting-type-specific schema:
  standup      → insights["standup"]
  hr           → insights["hr"]
  client-call  → insights["client"]
  vendor       → insights["vendor"]
  sales-bd     → insights["sales_bd"]
  sprint-planning → insights["internal"]
  design-review   → insights["design_review"]
  milestone-review → insights["milestone_review"]
  cross-dept      → insights["cross_dept"]
  company-allhands → insights["allhands"]  (no tasks generated)

LLM is used ONLY for:
  - Title normalisation
  - Hours estimation
  - Priority suggestion (when not inferrable from text)

LLM is NOT trusted to create tasks outside defined extraction rules.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from cell.config import settings
from cell.core.models import RawTask, TaskPriority, TaskSource

logger = logging.getLogger(__name__)

_openai: Optional[AsyncOpenAI] = None


def _get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai


# ──────────────────────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────────────────────

_PRIORITY_KEYWORDS = {
    TaskPriority.URGENT: {"urgent", "asap", "critical", "emergency", "blocker", "hotfix", "production"},
    TaskPriority.HIGH:   {"high", "important", "must", "required", "sprint", "milestone", "deadline"},
    TaskPriority.LOW:    {"low", "nice-to-have", "optional", "whenever", "someday", "deferred"},
}


def _infer_priority(text: str) -> TaskPriority:
    lower = text.lower()
    for priority, keywords in _PRIORITY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return priority
    return TaskPriority.NORMAL


def _parse_date(val: Any) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        return date.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None


# ──────────────────────────────────────────────────────────────
# Main extraction dispatcher
# ──────────────────────────────────────────────────────────────

def extract_raw_tasks(
    insights: dict,
    project_id: str,
    meeting_id: str,
    default_assignee_id: str = "UNASSIGNED",
) -> List[RawTask]:
    """
    Extract RawTask objects from a parsed IRIS insights.yaml dict.
    Pure rule-based — no LLM calls here.
    Dispatches to the correct handler based on meeting_type.
    """
    meeting_type: str = insights.get("meeting_type", "standup")

    # Use project_id from YAML if not overridden
    resolved_project_id = insights.get("project_id") or project_id
    resolved_meeting_id = insights.get("meeting_id") or meeting_id

    def _make(
        title: str,
        assignee: str,
        yaml_field: str,
        due: Any = None,
        notes: Optional[str] = None,
        priority_hint: Optional[str] = None,
    ) -> RawTask:
        priority = (
            TaskPriority(priority_hint)
            if priority_hint and priority_hint in [p.value for p in TaskPriority]
            else _infer_priority(title + " " + (notes or ""))
        )
        return RawTask(
            title=title.strip(),
            project_id=resolved_project_id,
            assignee_id=(assignee or default_assignee_id).strip(),
            priority=priority,
            due_date=_parse_date(due),
            source=TaskSource.IRIS,
            source_meeting_id=resolved_meeting_id,
            source_yaml_field=yaml_field,
            notes=notes,
        )

    tasks: List[RawTask] = []

    if meeting_type == "standup":
        tasks = _extract_standup(insights, _make, default_assignee_id)
    elif meeting_type == "hr":
        tasks = _extract_hr(insights, _make, default_assignee_id)
    elif meeting_type == "client-call":
        tasks = _extract_client_call(insights, _make, default_assignee_id)
    elif meeting_type == "vendor":
        tasks = _extract_vendor(insights, _make, default_assignee_id)
    elif meeting_type in ("sales-bd", "sales"):
        tasks = _extract_sales_bd(insights, _make, default_assignee_id)
    elif meeting_type == "sprint-planning":
        tasks = _extract_sprint_planning(insights, _make, default_assignee_id)
    elif meeting_type == "design-review":
        tasks = _extract_design_review(insights, _make, default_assignee_id)
    elif meeting_type == "milestone-review":
        tasks = _extract_milestone_review(insights, _make, default_assignee_id)
    elif meeting_type == "cross-dept":
        tasks = _extract_cross_dept(insights, _make, default_assignee_id)
    elif meeting_type == "company-allhands":
        tasks = []   # no tasks from all-hands; strategic decisions only
    else:
        # Fallback: try generic flat-key extraction for unknown types
        tasks = _extract_generic_fallback(insights, _make, default_assignee_id)

    logger.info(
        "Extracted %d raw tasks from meeting %s (type=%s)",
        len(tasks), resolved_meeting_id, meeting_type,
    )
    return tasks


# ──────────────────────────────────────────────────────────────
# Per-type extractors
# ──────────────────────────────────────────────────────────────

def _extract_standup(insights: dict, _make, default_assignee: str) -> List[RawTask]:
    """
    standup: insights["standup"]
    Sources:
      - blocked_today[]     → blocker-resolution task (assigned to unblocking owner / PM)
      - unplanned_work_mentioned[] → unplanned work task
      - silent_members[]    → follow-up check-in task (assigned to PM / follow_up_owner)
    """
    tasks: List[RawTask] = []
    section = insights.get("standup") or {}
    follow_up_owner = insights.get("follow_up_owner") or default_assignee

    # blocked_today
    for item in section.get("blocked_today", []):
        if not isinstance(item, dict):
            continue
        person = item.get("person_id") or default_assignee
        desc = item.get("desc") or item.get("description") or "Blocked"
        days = item.get("days_carried")
        days_note = f" (carried {days} days)" if days else ""
        blocking_dept = item.get("blocking_dept")
        cross = item.get("cross_team", False)
        # Cross-team blockers go to follow_up_owner (PM), intra-team to person
        assignee = follow_up_owner if cross else person
        notes = f"Blocked: {person}{days_note}"
        if blocking_dept:
            notes += f" | blocking dept: {blocking_dept}"
        priority = TaskPriority.URGENT if days and int(days) >= 2 else TaskPriority.HIGH
        t = _make(
            f"Resolve blocker: {desc}",
            assignee,
            "standup.blocked_today",
            notes=notes,
            priority_hint=priority.value,
        )
        tasks.append(t)

    # unplanned_work_mentioned
    for item in section.get("unplanned_work_mentioned", []):
        if not isinstance(item, dict):
            continue
        desc = item.get("desc") or item.get("description") or "Unplanned work"
        raised_by = item.get("raised_by") or default_assignee
        # Let priority inference run on the description — urgent/hotfix words escalate naturally
        inferred = _infer_priority(desc)
        # Floor at HIGH (unplanned work is never low/normal by default)
        if inferred == TaskPriority.NORMAL or inferred == TaskPriority.LOW:
            inferred = TaskPriority.HIGH
        tasks.append(_make(
            desc,
            raised_by,
            "standup.unplanned_work_mentioned",
            notes="Unplanned work raised in standup",
            priority_hint=inferred.value,
        ))

    # silent_members → check-in task for PM
    for item in section.get("silent_members", []):
        if not isinstance(item, dict):
            continue
        person = item.get("person_id") or "unknown"
        days_silent = item.get("days_silent_in_row", 1)
        if days_silent >= 2:   # only escalate if 2+ days silent
            tasks.append(_make(
                f"Follow up with {person} — absent {days_silent} consecutive standups",
                follow_up_owner,
                "standup.silent_members",
                notes=f"{person} has not participated for {days_silent} standups",
                priority_hint=TaskPriority.HIGH.value,
            ))

    return tasks


def _extract_hr(insights: dict, _make, default_assignee: str) -> List[RawTask]:
    """
    hr: insights["hr"]
    Sources:
      - hr.action_items[]   → HR task (restricted visibility, text field)
      - hr.decisions[]      → decision-execution task (has owner + due)
    """
    tasks: List[RawTask] = []
    section = insights.get("hr") or {}

    for item in section.get("action_items", []):
        if not isinstance(item, dict):
            continue
        title = item.get("text") or item.get("action") or item.get("title") or str(item)
        assignee = item.get("owner") or default_assignee
        t = _make(title, assignee, "hr.action_items", due=item.get("due"))
        t = t.model_copy(update={"notes": "[HR RESTRICTED]"})
        tasks.append(t)

    for item in section.get("decisions", []):
        if not isinstance(item, dict):
            continue
        if item.get("owner") and item.get("due"):
            title = item.get("text") or item.get("decision") or str(item)
            t = _make(
                f"Execute HR decision: {title}",
                item["owner"],
                "hr.decisions",
                due=item["due"],
            )
            t = t.model_copy(update={"notes": "[HR RESTRICTED]"})
            tasks.append(t)

    return tasks


def _extract_client_call(insights: dict, _make, default_assignee: str) -> List[RawTask]:
    """
    client-call: insights["client"]
    Sources:
      - client.commitments[]  where made_by == our-side AND status == open
    """
    tasks: List[RawTask] = []
    section = insights.get("client") or {}

    for item in section.get("commitments", []):
        if not isinstance(item, dict):
            continue
        if item.get("made_by") == "our-side" and item.get("status") == "open":
            title = item.get("text") or item.get("commitment") or str(item)
            assignee = item.get("owner") or default_assignee
            tasks.append(_make(
                title,
                assignee,
                "client.commitments",
                due=item.get("due"),
                notes=f"Client commitment C-ID:{item.get('id','')} | critical_path:{item.get('critical_path', False)}",
                priority_hint=TaskPriority.HIGH.value if item.get("critical_path") else None,
            ))

    return tasks


def _extract_vendor(insights: dict, _make, default_assignee: str) -> List[RawTask]:
    """
    vendor: insights["vendor"]
    Sources:
      - vendor.commitments[] where owner is our-side person (not vendor-side) AND status open
        → identified by owner being an internal person_id (starts with p-) or matching follow_up_owner
    """
    tasks: List[RawTask] = []
    section = insights.get("vendor") or {}
    follow_up_owner = insights.get("follow_up_owner") or default_assignee

    internal_owners = {follow_up_owner, insights.get("organiser_id", "")}

    for item in section.get("commitments", []):
        if not isinstance(item, dict):
            continue
        if item.get("status") != "open":
            continue
        owner = item.get("owner") or ""
        # Internal person IDs start with "p-" in this org
        is_internal = owner.startswith("p-") or owner in internal_owners
        if not is_internal:
            continue
        title = item.get("text") or item.get("commitment") or str(item)
        tasks.append(_make(
            title,
            owner or default_assignee,
            "vendor.commitments",
            due=item.get("due"),
            notes=f"Vendor commitment V-ID:{item.get('id','')}",
        ))

    # next_action (top-level in sales_bd style, also appears in vendor via next_action field)
    na = section.get("next_action") or insights.get("next_action")
    if na and isinstance(na, str):
        na_owner = section.get("next_action_owner") or insights.get("next_action_owner") or follow_up_owner
        na_due = section.get("next_action_due") or insights.get("next_action_due")
        tasks.append(_make(na, na_owner, "vendor.next_action", due=na_due))

    return tasks


def _extract_sales_bd(insights: dict, _make, default_assignee: str) -> List[RawTask]:
    """
    sales-bd: insights["sales_bd"]
    Sources:
      - sales_bd.next_action + next_action_owner + next_action_due
    """
    tasks: List[RawTask] = []
    section = insights.get("sales_bd") or {}
    follow_up_owner = insights.get("follow_up_owner") or default_assignee

    na = section.get("next_action")
    if na and isinstance(na, str):
        na_owner = section.get("next_action_owner") or follow_up_owner
        na_due = section.get("next_action_due")
        tasks.append(_make(
            na,
            na_owner,
            "sales_bd.next_action",
            due=na_due,
            notes=f"Lead stage: {section.get('lead_stage_after', 'unknown')}",
            priority_hint=TaskPriority.HIGH.value,
        ))

    return tasks


def _extract_sprint_planning(insights: dict, _make, default_assignee: str) -> List[RawTask]:
    """
    sprint-planning: insights["internal"]
    Sources:
      - internal.decisions[]  where owner + due present
      - internal.deferred_items[]  → follow-up task
      - internal.cross_dept_dependencies[]  → dependency-resolution task
    """
    tasks: List[RawTask] = []
    section = insights.get("internal") or {}

    for item in section.get("decisions", []):
        if not isinstance(item, dict):
            continue
        if item.get("owner") and item.get("due"):
            title = item.get("text") or item.get("decision") or str(item)
            tasks.append(_make(
                f"Execute decision: {title}",
                item["owner"],
                "internal.decisions",
                due=item["due"],
            ))

    for item in section.get("deferred_items", []):
        if not isinstance(item, dict):
            continue
        title = item.get("text") or item.get("item") or str(item)
        assignee = item.get("owner") or default_assignee
        deferred_count = item.get("deferred_count", 1)
        priority = TaskPriority.HIGH if deferred_count >= 2 else TaskPriority.NORMAL
        tasks.append(_make(
            f"Resolve deferred item: {title}",
            assignee,
            "internal.deferred_items",
            notes=f"Deferred {deferred_count}x. Next sync: {item.get('deferred_to', 'TBD')}",
            priority_hint=priority.value,
        ))

    for item in section.get("cross_dept_dependencies", []):
        if not isinstance(item, dict):
            continue
        dep_item = item.get("item") or "cross-dept dependency"
        blocked_dept = item.get("blocked_dept", "")
        blocking_dept = item.get("blocking_dept", "")
        assignee = item.get("owner") or default_assignee
        tasks.append(_make(
            f"Resolve cross-dept dependency: {dep_item}",
            assignee,
            "internal.cross_dept_dependencies",
            due=item.get("due"),
            notes=f"{blocking_dept} blocking {blocked_dept}",
            priority_hint=TaskPriority.HIGH.value,
        ))

    return tasks


def _extract_design_review(insights: dict, _make, default_assignee: str) -> List[RawTask]:
    """
    design-review: insights["design_review"]
    Sources:
      - design_review.feedback_items[] where severity == major
    """
    tasks: List[RawTask] = []
    section = insights.get("design_review") or {}
    is_blocking = section.get("blocking_development", False)

    for item in section.get("feedback_items", []):
        if not isinstance(item, dict):
            continue
        severity = item.get("severity", "minor")
        if severity not in ("major", "critical"):
            continue
        title = item.get("item") or item.get("feedback") or str(item)
        assignee = item.get("owner") or default_assignee
        priority = TaskPriority.URGENT if is_blocking else TaskPriority.HIGH
        tasks.append(_make(
            f"Design fix: {title}",
            assignee,
            "design_review.feedback_items",
            due=item.get("due"),
            notes=f"Severity: {severity} | blocking_dev: {is_blocking}",
            priority_hint=priority.value,
        ))

    return tasks


def _extract_milestone_review(insights: dict, _make, default_assignee: str) -> List[RawTask]:
    """
    milestone-review: insights["milestone_review"]
    Sources:
      - milestone_review.sign_offs[] where status == rejected → rework task
    """
    tasks: List[RawTask] = []
    section = insights.get("milestone_review") or {}

    for sign_off in section.get("sign_offs", []):
        if not isinstance(sign_off, dict):
            continue
        if sign_off.get("status") == "rejected":
            rework_desc = sign_off.get("rework_requested") or f"Rework {sign_off.get('deliverable', 'deliverable')}"
            assignee = sign_off.get("rework_owner") or default_assignee
            tasks.append(_make(
                f"Rework: {rework_desc}",
                assignee,
                "milestone_review.sign_offs",
                due=sign_off.get("rework_due"),
                notes=f"Milestone: {section.get('milestone_id','?')} | deliverable: {sign_off.get('deliverable','')}",
                priority_hint=TaskPriority.HIGH.value,
            ))

    return tasks


def _extract_cross_dept(insights: dict, _make, default_assignee: str) -> List[RawTask]:
    """
    cross-dept: insights["cross_dept"]
    Sources:
      - cross_dept.unresolved_items[]
      - cross_dept.resolution (if owner + due present and status != resolved)
    """
    tasks: List[RawTask] = []
    section = insights.get("cross_dept") or {}

    for item in section.get("unresolved_items", []):
        if not isinstance(item, dict):
            continue
        title = item.get("text") or item.get("item") or str(item)
        assignee = item.get("owner") or default_assignee
        tasks.append(_make(
            f"Resolve cross-dept: {title}",
            assignee,
            "cross_dept.unresolved_items",
            due=item.get("due"),
        ))

    return tasks


def _extract_generic_fallback(insights: dict, _make, default_assignee: str) -> List[RawTask]:
    """
    Fallback for unknown meeting types: try flat action_items / commitments keys.
    """
    tasks: List[RawTask] = []

    for item in insights.get("action_items", []):
        if not isinstance(item, dict):
            continue
        title = item.get("text") or item.get("action") or item.get("title") or str(item)
        assignee = item.get("owner") or default_assignee
        tasks.append(_make(title, assignee, "action_items", due=item.get("due")))

    for item in insights.get("commitments", []):
        if not isinstance(item, dict):
            continue
        if item.get("made_by") == "our-side" and item.get("status") == "open":
            title = item.get("text") or item.get("commitment") or str(item)
            assignee = item.get("owner") or default_assignee
            tasks.append(_make(title, assignee, "commitments", due=item.get("due")))

    return tasks


# ──────────────────────────────────────────────────────────────
# LLM enrichment (title normalisation + hours estimation)
# ──────────────────────────────────────────────────────────────

_ENRICHMENT_SYSTEM_PROMPT = """You are a structured task enricher for a project management system.
Given a raw task title extracted from meeting notes, you must:
1. Return a clean, concise, action-oriented task title (max 12 words). Do not add details not present.
2. Estimate hours to complete this task (integer or 0.5 steps, between 0.5 and 40).
3. Suggest priority: urgent | high | normal | low

Respond ONLY in this exact JSON format, nothing else:
{"title": "...", "estimated_hours": 4, "priority": "normal"}
"""


async def enrich_task_with_llm(task: RawTask) -> RawTask:
    """
    Call LLM to normalise title, estimate hours, suggest priority.
    Returns a new RawTask with enriched fields.
    On any LLM failure → returns original task unchanged.
    """
    import json as _json

    client = _get_openai()
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _ENRICHMENT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Raw title: {task.title}\nContext: {task.notes or ''}"},
            ],
            temperature=0,
            max_tokens=100,
        )
        raw = response.choices[0].message.content.strip()
        data = _json.loads(raw)

        enriched = task.model_copy(deep=True)
        enriched.title = data.get("title", task.title)
        enriched.estimated_hours = float(data.get("estimated_hours", task.estimated_hours or 4.0))

        # Only use LLM priority if YAML didn't already give a strong signal
        if task.priority == TaskPriority.NORMAL and "priority" in data:
            try:
                enriched.priority = TaskPriority(data["priority"])
            except ValueError:
                pass

        return enriched

    except Exception as exc:
        logger.warning("LLM enrichment failed for task '%s': %s", task.title, exc)
        if task.estimated_hours is None:
            task.estimated_hours = 4.0
        return task


async def enrich_tasks(tasks: List[RawTask]) -> List[RawTask]:
    """Enrich all tasks via LLM concurrently."""
    import asyncio
    return await asyncio.gather(*[enrich_task_with_llm(t) for t in tasks])
