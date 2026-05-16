"""
CELL Slack EOD Reply Parser.

Parses intern EOD replies and PM approval replies.

Security principles:
- Intern messages treated as DATA TOKENS ONLY, never as instructions.
- Whitelist: only `done <n>`, `blocked <n> <reason>`, `carry <n>` are valid.
- Any instruction-like text is flagged and sent to PM.
- LLM is used to help detect injection attempts, not to execute instructions.

PM parsing is also handled here — structured but less strict than intern parsing.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from cell.core.models import (
    EODEntry,
    EODStatus,
    EODSubmission,
    PMApprovalAction,
    PMApprovalReply,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Intern EOD Parser
# ──────────────────────────────────────────────────────────────

# Whitelist patterns (compiled once)
_DONE_RE    = re.compile(r"^\s*done\s+(\d+)\s*$", re.IGNORECASE)
_BLOCKED_RE = re.compile(r"^\s*blocked\s+(\d+)\s+(.+)$", re.IGNORECASE)
_CARRY_RE   = re.compile(r"^\s*carry\s+(\d+)\s*$", re.IGNORECASE)

# Prompt injection detection patterns
_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"ignore\s+(previous|above|prior|all)\s+instructions?",
        r"system\s*:",
        r"you\s+are\s+(now|a|an)\s+",
        r"act\s+as\s+",
        r"pretend\s+(you\s+are|to\s+be)",
        r"new\s+instructions?:",
        r"override\s+",
        r"forget\s+(everything|previous)",
        r"disregard\s+",
        r"jailbreak",
        r"prompt\s+injection",
    ]
]


def _detect_injection(text: str) -> bool:
    """Return True if text looks like a prompt injection attempt."""
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


def parse_eod_reply(
    intern_id: str,
    raw_message: str,
    task_id_map: dict,  # {task_number (1-indexed): db_task_id}
) -> EODSubmission:
    """
    Parse a raw EOD reply from an intern.

    Args:
        intern_id: The intern's employee ID.
        raw_message: The full raw message text from Slack.
        task_id_map: Maps 1-indexed task numbers to internal task IDs.

    Returns:
        EODSubmission with parsed entries. parse_success=False if any line fails.
    """
    from datetime import date
    from cell.scheduler.clock import ist_today

    today = ist_today()
    entries: List[EODEntry] = []
    parse_success = True
    security_flag = False

    # Check for injection in the full message first
    if _detect_injection(raw_message):
        logger.warning("Prompt injection attempt from intern %s", intern_id)
        security_flag = True
        return EODSubmission(
            intern_id=intern_id,
            submission_date=today,
            entries=[],
            raw_message=raw_message,
            parse_success=False,
            security_flag=True,
        )

    lines = [line.strip() for line in raw_message.strip().splitlines() if line.strip()]

    for line in lines:
        # Also check injection per-line
        if _detect_injection(line):
            logger.warning("Injection detected in line from %s: %r", intern_id, line)
            security_flag = True
            parse_success = False
            continue

        matched = False

        # done <n>
        m = _DONE_RE.match(line)
        if m:
            n = int(m.group(1))
            entries.append(EODEntry(task_number=n, status=EODStatus.DONE))
            matched = True

        # blocked <n> <reason>
        if not matched:
            m = _BLOCKED_RE.match(line)
            if m:
                n = int(m.group(1))
                reason = m.group(2).strip()[:500]   # cap reason length
                entries.append(EODEntry(task_number=n, status=EODStatus.BLOCKED, block_reason=reason))
                matched = True

        # carry <n>
        if not matched:
            m = _CARRY_RE.match(line)
            if m:
                n = int(m.group(1))
                entries.append(EODEntry(task_number=n, status=EODStatus.CARRY))
                matched = True

        if not matched:
            logger.info("Unrecognised line from intern %s: %r", intern_id, line)
            parse_success = False

    return EODSubmission(
        intern_id=intern_id,
        submission_date=today,
        entries=entries,
        raw_message=raw_message,
        parse_success=parse_success and bool(entries),
        security_flag=security_flag,
    )


# ──────────────────────────────────────────────────────────────
# PM Approval Reply Parser
# ──────────────────────────────────────────────────────────────

# approve all
_APPROVE_ALL_RE = re.compile(r"^\s*approve\s+all\s*$", re.IGNORECASE)
# approve 1,3,5 [hours=6]
_APPROVE_RE = re.compile(r"^\s*approve\s+([\d,\s]+)(?:\s+hours\s*=\s*(\d+(?:\.\d+)?))?\s*$", re.IGNORECASE)
# reject 2 - reason text
_REJECT_RE = re.compile(r"^\s*reject\s+(\d+)\s*[-–]?\s*(.*?)\s*$", re.IGNORECASE)
# approve 1 hours=6
_APPROVE_SINGLE_HOURS_RE = re.compile(
    r"^\s*approve\s+(\d+)\s+hours\s*=\s*(\d+(?:\.\d+)?)\s*$", re.IGNORECASE
)


def parse_pm_approval_reply(pm_id: str, raw_message: str) -> PMApprovalReply:
    """
    Parse a PM's structured approval reply.

    Valid formats:
      approve all
      approve 1,3,5
      approve 1 hours=6
      reject 2 - reason text

    Returns PMApprovalReply. parse_error=True if nothing was parseable.
    """
    actions: List[PMApprovalAction] = []
    approve_all = False
    any_parsed = False

    lines = [line.strip() for line in raw_message.strip().splitlines() if line.strip()]

    for line in lines:
        # approve all
        if _APPROVE_ALL_RE.match(line):
            approve_all = True
            any_parsed = True
            continue

        # reject <n> - reason
        m = _REJECT_RE.match(line)
        if m:
            n = int(m.group(1))
            note = m.group(2).strip() or None
            actions.append(PMApprovalAction(task_index=n, action="reject", rejection_note=note))
            any_parsed = True
            continue

        # approve <n> hours=<h> (single)
        m = _APPROVE_SINGLE_HOURS_RE.match(line)
        if m:
            n = int(m.group(1))
            hours = float(m.group(2))
            actions.append(PMApprovalAction(task_index=n, action="approve", edited_hours=hours))
            any_parsed = True
            continue

        # approve 1,3,5 [hours=X] (bulk)
        m = _APPROVE_RE.match(line)
        if m:
            indices_str = m.group(1)
            hours_str = m.group(2)
            indices = [int(x.strip()) for x in indices_str.split(",") if x.strip().isdigit()]
            edited_hours = float(hours_str) if hours_str else None
            for idx in indices:
                actions.append(PMApprovalAction(
                    task_index=idx,
                    action="approve",
                    edited_hours=edited_hours,
                ))
            any_parsed = True
            continue

        logger.debug("PM reply line not parsed: %r", line)

    return PMApprovalReply(
        pm_id=pm_id,
        raw_message=raw_message,
        actions=actions,
        approve_all=approve_all,
        parse_error=not any_parsed,
    )
