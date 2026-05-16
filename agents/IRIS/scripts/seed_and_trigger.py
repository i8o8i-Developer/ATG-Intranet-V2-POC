#!/usr/bin/env python3
"""
Quick test script — seeds a meeting into mock R2 and fires the IRIS trigger.
Usage:
    python scripts/seed_and_trigger.py --type client-call --provider anthropic
    python scripts/seed_and_trigger.py --type standup --provider openai
    python scripts/seed_and_trigger.py --type all --provider anthropic
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iris.storage.r2_client import R2Client
from iris.config import settings

FIXTURE_MAP = {
    "standup":          ("tests.fixtures.meetings.standup",         "standup"),
    "client-call":      ("tests.fixtures.meetings.client_call",     "client-call"),
    "sprint-planning":  ("tests.fixtures.meetings.sprint_planning", "sprint-planning"),
    "milestone-review": ("tests.fixtures.meetings.milestone_review","milestone-review"),
    "cross-dept":       ("tests.fixtures.meetings.cross_dept",      "cross-dept"),
    "design-review":    ("tests.fixtures.meetings.design_review",   "design-review"),
    "sales-bd":         ("tests.fixtures.meetings.sales_bd",        "sales-bd"),
    "hr":               ("tests.fixtures.meetings.hr_meeting",      "hr"),
    "company-allhands": ("tests.fixtures.meetings.allhands",        "company-allhands"),
    "vendor":           ("tests.fixtures.meetings.vendor_meeting",  "vendor"),
}


def seed_meeting(meeting_type: str, r2: R2Client) -> tuple[str, dict]:
    module_path, _ = FIXTURE_MAP[meeting_type]
    import importlib
    mod = importlib.import_module(module_path)
    meta = mod.METADATA
    r2_path = f"/projects/{meta['project_id']}/{meta['date']}_{meta['meeting_id']}"
    r2.seed_meeting(r2_path, meta, mod.ATTENDEES, mod.TRANSCRIPT)
    print(f"  Seeded: {r2_path}")
    return r2_path, meta


def trigger(r2_path: str, meta: dict, provider: str):
    import httpx
    from datetime import datetime

    payload = {
        "meeting_id": meta["meeting_id"],
        "project_id": meta["project_id"],
        "r2_path": r2_path,
        "transcript_status": "completed",
        "triggered_at": datetime.utcnow().isoformat(),
    }

    url = f"http://localhost:{settings.iris_port}/iris/trigger?provider={provider}"
    print(f"  POSTing to {url}")

    response = httpx.post(url, json=payload, timeout=120.0)
    if response.status_code == 200:
        event = response.json()
        print(f"  OK — confidence={event['confidence_score']:.2f}, flagged={event['flagged']}, provider={event['provider']}")
        print(f"  insights_path={event['insights_path']}")
    else:
        print(f"  ERROR {response.status_code}: {response.text}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default="client-call", choices=list(FIXTURE_MAP.keys()) + ["all"])
    parser.add_argument("--provider", default="anthropic", choices=["anthropic", "openai"])
    args = parser.parse_args()

    r2 = R2Client(base_path=settings.r2_mock_base_path)

    types_to_run = list(FIXTURE_MAP.keys()) if args.type == "all" else [args.type]

    for meeting_type in types_to_run:
        print(f"\n[{meeting_type.upper()}] Provider: {args.provider}")
        r2_path, meta = seed_meeting(meeting_type, r2)
        trigger(r2_path, meta, args.provider)


if __name__ == "__main__":
    main()
