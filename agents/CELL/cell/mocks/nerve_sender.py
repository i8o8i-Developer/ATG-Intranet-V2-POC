"""
Mock NERVE Event Emitter.
Simulates IRIS completing extraction and sending a NERVE event to CELL.
Used for local testing — not for production.

Usage:
  python -m cell.mocks.nerve_sender
  python -m cell.mocks.nerve_sender --meeting-id meet-standup-002
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone

import httpx

CELL_URL = "http://localhost:8002"

SAMPLE_EVENT = {
    "event": "iris.extraction.complete",
    "meeting_id": "meet-standup-001",
    "project_id": "PROJ-CRM-0014",
    "confidence_score": 0.88,
    "flagged": False,
    "insights_path": "/projects/PROJ-CRM-0014/2025-05-06_meet-standup-001/insights.yaml",
    "timestamp": datetime.now(timezone.utc).isoformat(),
}


async def send_nerve_event(event: dict) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{CELL_URL}/cell/ingest-nerve", json=event)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock NERVE event sender")
    parser.add_argument("--meeting-id", default=SAMPLE_EVENT["meeting_id"])
    parser.add_argument("--project-id", default=SAMPLE_EVENT["project_id"])
    parser.add_argument("--confidence", type=float, default=0.88)
    parser.add_argument("--flagged", action="store_true")
    parser.add_argument("--insights-path", default=SAMPLE_EVENT["insights_path"])
    args = parser.parse_args()

    event = {
        **SAMPLE_EVENT,
        "meeting_id": args.meeting_id,
        "project_id": args.project_id,
        "confidence_score": args.confidence,
        "flagged": args.flagged,
        "insights_path": args.insights_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    print("Sending NERVE event:")
    print(json.dumps(event, indent=2))
    asyncio.run(send_nerve_event(event))


if __name__ == "__main__":
    main()
