"""
Seed script: Simulate IRIS → NERVE → CELL pipeline.

This script:
1. Uploads a sample insights.yaml to mock R2 (or local file)
2. Sends a NERVE event to CELL
3. Polls CELL for staged tasks

Usage:
  python scripts/seed_nerve_event.py
  python scripts/seed_nerve_event.py --meeting-type standup
  python scripts/seed_nerve_event.py --meeting-type sales
  python scripts/seed_nerve_event.py --meeting-type hr
  python scripts/seed_nerve_event.py --flagged
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import datetime, timezone

import httpx

CELL_URL = "http://localhost:8002"

# ── Sample insights.yaml payloads per meeting type ────────────

STANDUP_INSIGHTS = {
    "meeting_type": "standup",
    "primary_assignee": "p-arjun-001",
    "action_items": [
        {"action": "Fix token refresh edge case in auth module", "owner": "p-arjun-001", "due": "2025-05-09"},
        {"action": "Update architecture diagram", "owner": "p-arjun-001", "due": "2025-05-12"},
    ],
    "commitments": [
        {"commitment": "Deliver API gateway spike by Friday", "made_by": "our-side", "status": "open", "owner": "p-rohit-002", "due": "2025-05-10"},
        {"commitment": "Client to provide test credentials", "made_by": "client-side", "status": "open"},
    ],
    "unresolved_items": [
        {"item": "Credential handover from vendor still pending", "owner": "p-rohit-002"},
    ],
    "blocked_today": [
        {"description": "Cannot access staging DB", "blocked_person": "p-arjun-001", "unblocking_owner": "p-rohit-002"},
    ],
    "decisions": [
        {"decision": "Use Redis for caching layer", "owner": "p-arjun-001", "due": "2025-05-11"},
    ],
    "rework_requested": None,
    "next_action": None,
}

SALES_INSIGHTS = {
    "meeting_type": "sales",
    "primary_assignee": "p-sales-001",
    "action_items": [
        {"action": "Send revised proposal to client", "owner": "p-sales-001", "due": "2025-05-08"},
    ],
    "commitments": [
        {"commitment": "Provide live demo by next Tuesday", "made_by": "our-side", "status": "open", "owner": "p-sales-001", "due": "2025-05-13"},
    ],
    "next_action": {"action": "Follow up with procurement team", "owner": "p-sales-001", "due": "2025-05-09"},
    "unresolved_items": [],
    "blocked_today": [],
    "decisions": [],
}

HR_INSIGHTS = {
    "meeting_type": "hr",
    "primary_assignee": "p-hr-001",
    "action_items": [],
    "hr": {
        "action_items": [
            {"action": "Issue warning letter to p-dev-003", "owner": "p-hr-001", "due": "2025-05-09"},
            {"action": "Schedule performance review for p-arjun-001", "owner": "p-hr-001", "due": "2025-05-15"},
        ]
    },
    "commitments": [],
    "unresolved_items": [],
    "blocked_today": [],
    "decisions": [],
}

MEETING_TYPE_MAP = {
    "standup": STANDUP_INSIGHTS,
    "sales": SALES_INSIGHTS,
    "hr": HR_INSIGHTS,
}


async def seed(meeting_type: str, flagged: bool) -> None:
    insights = MEETING_TYPE_MAP.get(meeting_type, STANDUP_INSIGHTS)
    meeting_id = f"meet-{meeting_type}-seed-{int(time.time())}"
    project_id = "PROJ-CRM-0014"

    # In mock mode, CELL's _process_nerve_event will try to fetch from R2.
    # For seeding, we inject insights directly via a special test endpoint
    # OR we stub R2 with a local file. Here we use the ingest-tasks endpoint
    # to bypass R2 and test the full pipeline from extracted tasks.

    print(f"\nSeeding NERVE event: meeting_type={meeting_type}, flagged={flagged}")
    print(f"Meeting ID: {meeting_id}")
    print(f"Insights payload:")
    print(json.dumps(insights, indent=2))

    # For local testing without R2, use /cell/ingest-tasks with pre-extracted tasks
    # (simulating what CELL would produce from the YAML above)
    from_insights = _insights_to_agent3_format(insights, project_id)

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{CELL_URL}/cell/ingest-tasks",
            json=from_insights,
        )
        print(f"\nIngest response: {resp.status_code}")
        print(resp.json())

        # Wait a moment for background processing
        await asyncio.sleep(2)

        # Check staged tasks
        resp2 = await client.get(f"{CELL_URL}/cell/tasks/{project_id}")
        print(f"\nStaged tasks for {project_id}:")
        print(json.dumps(resp2.json(), indent=2, default=str))


def _insights_to_agent3_format(insights: dict, project_id: str) -> dict:
    """Convert sample insights to Agent3 ingest format for bypass testing."""
    tasks = []
    for item in insights.get("action_items", []):
        tasks.append({
            "title": item.get("action", ""),
            "assignee_id": item.get("owner", "p-default-001"),
            "estimated_hours": 4,
            "priority": "normal",
            "due_date": item.get("due", "2025-12-31"),
        })
    for item in insights.get("commitments", []):
        if item.get("made_by") == "our-side" and item.get("status") == "open":
            tasks.append({
                "title": item.get("commitment", ""),
                "assignee_id": item.get("owner", "p-default-001"),
                "estimated_hours": 4,
                "priority": "high",
                "due_date": item.get("due", "2025-12-31"),
            })
    return {
        "source": "agent3",
        "project_id": project_id,
        "week_ref": "2025-W19",
        "tasks": tasks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed NERVE event to CELL")
    parser.add_argument("--meeting-type", choices=["standup", "sales", "hr"], default="standup")
    parser.add_argument("--flagged", action="store_true")
    args = parser.parse_args()
    asyncio.run(seed(args.meeting_type, args.flagged))


if __name__ == "__main__":
    main()
