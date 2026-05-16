"""
Seed script: Simulate Agent 3 weekly task push to CELL.

Usage:
  python scripts/seed_agent3_tasks.py
  python scripts/seed_agent3_tasks.py --project-id PROJ-CRM-0014 --week 2025-W20
"""
from __future__ import annotations

import argparse
import asyncio
import json

import httpx

CELL_URL = "http://localhost:8002"

SAMPLE_PAYLOAD = {
    "source": "agent3",
    "project_id": "PROJ-CRM-0014",
    "week_ref": "2025-W19",
    "tasks": [
        {
            "title": "Complete API gateway spike",
            "assignee_id": "p-arjun-001",
            "estimated_hours": 8,
            "priority": "high",
            "due_date": "2025-05-10",
            "notes": "Understand scope complexity before sprint planning",
        },
        {
            "title": "Set up staging environment",
            "assignee_id": "p-rohit-002",
            "estimated_hours": 4,
            "priority": "normal",
            "due_date": "2025-05-09",
            "notes": None,
        },
        {
            "title": "Write unit tests for auth module",
            "assignee_id": "p-arjun-001",
            "estimated_hours": 6,
            "priority": "high",
            "due_date": "2025-05-11",
            "notes": "Cover token refresh and session expiry paths",
        },
        {
            "title": "Document API endpoints",
            "assignee_id": "p-dev-003",
            "estimated_hours": 3,
            "priority": "low",
            "due_date": "2025-05-12",
            "notes": None,
        },
    ],
}


async def seed(project_id: str, week_ref: str) -> None:
    payload = {**SAMPLE_PAYLOAD, "project_id": project_id, "week_ref": week_ref}
    print("Sending Agent 3 task push:")
    print(json.dumps(payload, indent=2))

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(f"{CELL_URL}/cell/ingest-tasks", json=payload)
        print(f"\nIngest response: {resp.status_code}")
        print(resp.json())

        await asyncio.sleep(2)

        # Check staged tasks
        resp2 = await client.get(f"{CELL_URL}/cell/tasks/{project_id}")
        print(f"\nStaged tasks for {project_id}:")
        print(json.dumps(resp2.json(), indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Agent 3 tasks to CELL")
    parser.add_argument("--project-id", default="PROJ-CRM-0014")
    parser.add_argument("--week", default="2025-W19")
    args = parser.parse_args()
    asyncio.run(seed(args.project_id, args.week))


if __name__ == "__main__":
    main()
