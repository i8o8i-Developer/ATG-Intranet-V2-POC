"""
CELL Test Configuration.
Provides fixtures for unit tests that don't require live DB/Slack/ERP.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

# ── Set env vars before importing CELL modules ───────────────
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_cell")
os.environ.setdefault("R2_ENDPOINT_URL", "https://mock.r2.dev")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test")
os.environ.setdefault("MOCK_MODE", "true")

SAMPLES_DIR = Path(__file__).parent.parent / "sample_outputs"


# ── Real YAML fixtures ────────────────────────────────────────

@pytest.fixture
def standup_yaml() -> Dict[str, Any]:
    with open(SAMPLES_DIR / "insights_standup.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def hr_yaml() -> Dict[str, Any]:
    with open(SAMPLES_DIR / "insights_hr.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def client_call_yaml() -> Dict[str, Any]:
    with open(SAMPLES_DIR / "insights_client_call.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def vendor_yaml() -> Dict[str, Any]:
    with open(SAMPLES_DIR / "insights_vendor.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sales_bd_yaml() -> Dict[str, Any]:
    with open(SAMPLES_DIR / "insights_sales_bd.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sprint_planning_yaml() -> Dict[str, Any]:
    with open(SAMPLES_DIR / "insights_sprint_planning.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def design_review_yaml() -> Dict[str, Any]:
    with open(SAMPLES_DIR / "insights_design_review.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def milestone_review_yaml() -> Dict[str, Any]:
    with open(SAMPLES_DIR / "insights_milestone_review.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def cross_dept_yaml() -> Dict[str, Any]:
    with open(SAMPLES_DIR / "insights_cross_dept.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def allhands_yaml() -> Dict[str, Any]:
    with open(SAMPLES_DIR / "insights_company_allhands.yaml") as f:
        return yaml.safe_load(f)


# ── Sample YAML fixtures ──────────────────────────────────────

@pytest.fixture
def standup_insights() -> Dict[str, Any]:
    return {
        "meeting_type": "standup",
        "primary_assignee": "p-arjun-001",
        "action_items": [
            {"action": "Fix token refresh edge case", "owner": "p-arjun-001", "due": "2025-05-09"},
            {"action": "Update architecture diagram", "owner": "p-arjun-001"},
        ],
        "commitments": [
            {
                "commitment": "Deliver API gateway spike by Friday",
                "made_by": "our-side",
                "status": "open",
                "owner": "p-rohit-002",
                "due": "2025-05-10",
            },
            {
                "commitment": "Client to provide test credentials",
                "made_by": "client-side",
                "status": "open",
            },
        ],
        "unresolved_items": [
            {"item": "Credential handover from vendor pending", "owner": "p-rohit-002"},
        ],
        "blocked_today": [
            {
                "description": "Cannot access staging DB",
                "blocked_person": "p-arjun-001",
                "unblocking_owner": "p-rohit-002",
            }
        ],
        "decisions": [
            {"decision": "Use Redis for caching", "owner": "p-arjun-001", "due": "2025-05-11"},
        ],
        "rework_requested": "Redo the auth module tests with proper mocking",
        "next_action": None,
        "hr": {},
    }


@pytest.fixture
def sales_insights() -> Dict[str, Any]:
    return {
        "meeting_type": "sales",
        "primary_assignee": "p-sales-001",
        "action_items": [
            {"action": "Send revised proposal", "owner": "p-sales-001", "due": "2025-05-08"},
        ],
        "commitments": [
            {
                "commitment": "Live demo by next Tuesday",
                "made_by": "our-side",
                "status": "open",
                "owner": "p-sales-001",
                "due": "2025-05-13",
            }
        ],
        "next_action": {
            "action": "Follow up with procurement team",
            "owner": "p-sales-001",
            "due": "2025-05-09",
        },
        "unresolved_items": [],
        "blocked_today": [],
        "decisions": [],
        "rework_requested": None,
        "hr": {},
    }


@pytest.fixture
def hr_insights() -> Dict[str, Any]:
    return {
        "meeting_type": "hr",
        "primary_assignee": "p-hr-001",
        "action_items": [],
        "hr": {
            "action_items": [
                {"action": "Issue warning letter", "owner": "p-hr-001", "due": "2025-05-09"},
                {"action": "Schedule performance review", "owner": "p-hr-001", "due": "2025-05-15"},
            ]
        },
        "commitments": [],
        "unresolved_items": [],
        "blocked_today": [],
        "decisions": [],
        "rework_requested": None,
        "next_action": None,
    }


@pytest.fixture
def sample_tasks_for_intern() -> List[Dict[str, Any]]:
    return [
        {
            "id": 1,
            "erp_task_id": "ERP-001",
            "title": "Fix token refresh edge case",
            "priority": "urgent",
            "estimated_hours": 4.0,
            "due_date": date(2025, 5, 9),
            "bounty_value": 1.5,   # 4h urgent = 1.5 bounty units
            "status": "open",
        },
        {
            "id": 2,
            "erp_task_id": "ERP-002",
            "title": "API schema v2 endpoint",
            "priority": "high",
            "estimated_hours": 6.0,
            "due_date": date(2025, 5, 10),
            "bounty_value": 1.75,  # 6h high = 1.75 bounty units
            "status": "open",
        },
        {
            "id": 3,
            "erp_task_id": "ERP-003",
            "title": "Update architecture diagram",
            "priority": "normal",
            "estimated_hours": 3.0,
            "due_date": date(2025, 5, 12),
            "bounty_value": 0.75,  # 3h normal = 0.75 bounty units
            "status": "open",
        },
    ]
