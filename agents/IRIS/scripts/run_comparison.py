#!/usr/bin/env python3
"""
A/B comparison runner.
Runs all 10 meeting types through both claude-haiku-4-5 and gpt-4o-mini.
Writes insights YAML to comparison/anthropic/ and comparison/openai/.
Prints a cost + accuracy comparison table.
"""

import sys
import os
import time
import importlib
import tempfile
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load .env before any iris imports
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from iris.storage.r2_client import R2Client
from iris.core.extractor import run_extraction

# ── Token cost constants (per 1M tokens, USD) ─────────────────────
COSTS = {
    "anthropic": {"input": 1.00, "output": 5.00},  # claude-haiku-4-5
    "openai":    {"input": 0.15, "output": 0.60},  # gpt-4o-mini
}

FIXTURES = [
    ("tests.fixtures.meetings.standup",          "standup"),
    ("tests.fixtures.meetings.client_call",      "client-call"),
    ("tests.fixtures.meetings.sprint_planning",  "sprint-planning"),
    ("tests.fixtures.meetings.milestone_review", "milestone-review"),
    ("tests.fixtures.meetings.cross_dept",       "cross-dept"),
    ("tests.fixtures.meetings.design_review",    "design-review"),
    ("tests.fixtures.meetings.sales_bd",         "sales-bd"),
    ("tests.fixtures.meetings.hr_meeting",       "hr"),
    ("tests.fixtures.meetings.allhands",         "company-allhands"),
    ("tests.fixtures.meetings.vendor_meeting",   "vendor"),
]

# Required fields per meeting type for accuracy scoring
REQUIRED_FIELDS = {
    "standup":          ["standup", "standup.blocked_today", "standup.silent_members"],
    "client-call":      ["client", "client.sentiment", "client.commitments", "client.deadline_pressure"],
    "sprint-planning":  ["internal", "internal.decisions", "internal.velocity_concern"],
    "milestone-review": ["milestone_review", "milestone_review.acceptance_status", "milestone_review.sign_offs"],
    "cross-dept":       ["cross_dept", "cross_dept.dependency_status", "cross_dept.departments_present"],
    "design-review":    ["design_review", "design_review.approval_status", "design_review.feedback_items"],
    "sales-bd":         ["sales_bd", "sales_bd.meeting_subtype", "sales_bd.qualification_signals"],
    "hr":               ["hr", "hr.subtype", "hr.decisions"],
    "company-allhands": ["allhands", "allhands.announcements", "allhands.concerns_raised"],
    "vendor":           ["vendor", "vendor.commitments", "vendor.cost_implication"],
}

BASE_REQUIRED = [
    "meeting_id", "project_id", "date", "meeting_type", "security_level",
    "extraction_confidence", "follow_up_type", "consumer_level", "tags",
]


def get_nested(d, dotpath):
    """Traverse a dotpath like 'client.commitments' in a dict."""
    parts = dotpath.split(".")
    cur = d
    for p in parts:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


def score_accuracy(parsed: dict, meeting_type: str) -> tuple[float, list[str]]:
    """
    Score extraction accuracy 0.0–1.0 based on:
    1. All BASE fields present and non-null
    2. All type-specific required fields present and non-null
    3. Tags list non-empty
    4. consumer_level is a valid value
    Returns (score, list_of_missing_fields)
    """
    missing = []

    # BASE fields
    for f in BASE_REQUIRED:
        val = parsed.get(f)
        if val is None or val == "":
            missing.append(f"BASE:{f}")

    # Tags non-empty
    if not parsed.get("tags"):
        missing.append("BASE:tags(empty)")

    # consumer_level valid
    valid_levels = {"pm", "dept-head", "director", "hr-only"}
    if parsed.get("consumer_level") not in valid_levels:
        missing.append(f"BASE:consumer_level(invalid={parsed.get('consumer_level')})")

    # Type-specific fields
    for dotpath in REQUIRED_FIELDS.get(meeting_type, []):
        val = get_nested(parsed, dotpath)
        if val is None:
            missing.append(f"TYPE:{dotpath}")
        elif isinstance(val, list) and len(val) == 0:
            pass  # Empty list is acceptable (e.g. no blockers today)

    total_checks = len(BASE_REQUIRED) + 2 + len(REQUIRED_FIELDS.get(meeting_type, []))
    score = (total_checks - len(missing)) / total_checks
    return round(score, 3), missing


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def run_all():
    tmp = Path(tempfile.mkdtemp())
    r2 = R2Client(base_path=str(tmp))

    out_base = Path(__file__).parent.parent / "comparison"
    anthropic_dir = out_base / "anthropic"
    openai_dir = out_base / "openai"
    anthropic_dir.mkdir(parents=True, exist_ok=True)
    openai_dir.mkdir(parents=True, exist_ok=True)

    results = []

    print("\nRunning extractions for all 10 meeting types on both models...")
    print("This will take ~60-90 seconds.\n")

    for mod_path, meeting_type in FIXTURES:
        mod = importlib.import_module(mod_path)
        meta = mod.METADATA
        r2_path = f"/projects/{meta['project_id']}/{meta['date']}_{meta['meeting_id']}"
        r2.seed_meeting(r2_path, meta, mod.ATTENDEES, mod.TRANSCRIPT)

        row = {"type": meeting_type}

        for provider in ["anthropic", "openai"]:
            t0 = time.time()
            try:
                result = run_extraction(
                    r2_path, meta["meeting_id"],
                    r2_client=r2,
                    provider_override=provider,
                )
                elapsed = round(time.time() - t0, 1)
                parsed = yaml.safe_load(result.insights_yaml)

                # Accuracy scoring
                struct_score, missing = score_accuracy(parsed, meeting_type)
                llm_confidence = result.confidence_score

                # Cost estimation
                input_tokens = estimate_tokens(result.insights_yaml) + 3000  # prompt overhead
                output_tokens = estimate_tokens(result.insights_yaml)
                cost_usd = (
                    (input_tokens / 1_000_000) * COSTS[provider]["input"] +
                    (output_tokens / 1_000_000) * COSTS[provider]["output"]
                )

                # Save YAML output
                fname = meeting_type.replace("-", "_")
                out_path = (anthropic_dir if provider == "anthropic" else openai_dir) / f"insights_{fname}.yaml"
                out_path.write_text(result.insights_yaml)

                row[provider] = {
                    "llm_confidence": llm_confidence,
                    "struct_score": struct_score,
                    "missing": missing,
                    "cost_usd": cost_usd,
                    "latency_s": elapsed,
                    "flagged": result.flagged,
                }
                print(f"  [{provider:10s}] {meeting_type:<22} conf={llm_confidence:.2f} struct={struct_score:.2f} cost=${cost_usd:.5f} {elapsed}s")

            except Exception as e:
                elapsed = round(time.time() - t0, 1)
                row[provider] = {"error": str(e), "latency_s": elapsed}
                print(f"  [{provider:10s}] {meeting_type:<22} ERROR: {e}")

        results.append(row)

    print_comparison_table(results)
    return results


def print_comparison_table(results):
    sep = "=" * 100

    print(f"\n{sep}")
    print("  IRIS A/B COMPARISON — claude-haiku-4-5  vs  gpt-4o-mini")
    print(sep)

    # Per-meeting breakdown
    print(f"\n{'Meeting Type':<22} {'Metric':<20} {'claude-haiku-4-5':>18} {'gpt-4o-mini':>14}  {'Winner'}")
    print("-" * 82)

    totals = {"anthropic": {"conf": 0, "struct": 0, "cost": 0, "lat": 0, "wins_conf": 0, "wins_struct": 0},
              "openai":    {"conf": 0, "struct": 0, "cost": 0, "lat": 0}}

    for row in results:
        mt = row["type"]
        a = row.get("anthropic", {})
        o = row.get("openai", {})

        if "error" in a or "error" in o:
            err = a.get("error", o.get("error", "unknown"))
            print(f"{mt:<22} {'ERROR':<20} {err}")
            continue

        # Confidence
        winner_conf = "haiku" if a["llm_confidence"] >= o["llm_confidence"] else "gpt-4o-mini"
        print(f"{mt:<22} {'LLM confidence':<20} {a['llm_confidence']:>18.2f} {o['llm_confidence']:>14.2f}  {winner_conf}")

        # Struct score
        winner_struct = "haiku" if a["struct_score"] >= o["struct_score"] else "gpt-4o-mini"
        print(f"{'':22} {'Field completeness':<20} {a['struct_score']:>18.2f} {o['struct_score']:>14.2f}  {winner_struct}")

        # Cost
        winner_cost = "gpt-4o-mini" if o["cost_usd"] <= a["cost_usd"] else "haiku"
        print(f"{'':22} {'Cost (USD)':<20} ${a['cost_usd']:>17.5f} ${o['cost_usd']:>13.5f}  {winner_cost}")

        # Latency
        winner_lat = "haiku" if a["latency_s"] <= o["latency_s"] else "gpt-4o-mini"
        print(f"{'':22} {'Latency (s)':<20} {a['latency_s']:>18.1f} {o['latency_s']:>14.1f}s  {winner_lat}")

        # Missing fields
        if a["missing"] or o["missing"]:
            print(f"{'':22} {'Missing (haiku)':<20} {', '.join(a['missing'][:3]) or 'none':>18}")
            print(f"{'':22} {'Missing (gpt)':<20} {', '.join(o['missing'][:3]) or 'none':>18}")

        print()

        totals["anthropic"]["conf"]  += a["llm_confidence"]
        totals["anthropic"]["struct"] += a["struct_score"]
        totals["anthropic"]["cost"]  += a["cost_usd"]
        totals["anthropic"]["lat"]   += a["latency_s"]
        totals["openai"]["conf"]     += o["llm_confidence"]
        totals["openai"]["struct"]   += o["struct_score"]
        totals["openai"]["cost"]     += o["cost_usd"]
        totals["openai"]["lat"]      += o["latency_s"]

        if a["llm_confidence"] >= o["llm_confidence"]:
            totals["anthropic"]["wins_conf"] += 1
        if a["struct_score"] >= o["struct_score"]:
            totals["anthropic"]["wins_struct"] += 1

    n = len(results)

    print(sep)
    print("  SUMMARY")
    print(sep)
    print(f"\n{'Metric':<30} {'claude-haiku-4-5':>18} {'gpt-4o-mini':>14}  Winner")
    print("-" * 70)

    avg_conf_a = totals["anthropic"]["conf"] / n
    avg_conf_o = totals["openai"]["conf"] / n
    print(f"{'Avg LLM confidence':<30} {avg_conf_a:>18.3f} {avg_conf_o:>14.3f}  {'haiku' if avg_conf_a >= avg_conf_o else 'gpt-4o-mini'}")

    avg_struct_a = totals["anthropic"]["struct"] / n
    avg_struct_o = totals["openai"]["struct"] / n
    print(f"{'Avg field completeness':<30} {avg_struct_a:>18.3f} {avg_struct_o:>14.3f}  {'haiku' if avg_struct_a >= avg_struct_o else 'gpt-4o-mini'}")

    total_cost_a = totals["anthropic"]["cost"]
    total_cost_o = totals["openai"]["cost"]
    savings = ((total_cost_a - total_cost_o) / total_cost_a * 100) if total_cost_a > 0 else 0
    print(f"{'Total cost (10 meetings)':<30} ${total_cost_a:>17.5f} ${total_cost_o:>13.5f}  {'gpt-4o-mini' if total_cost_o < total_cost_a else 'haiku'}")
    print(f"{'Cost per meeting (avg)':<30} ${total_cost_a/n:>17.5f} ${total_cost_o/n:>13.5f}")

    avg_lat_a = totals["anthropic"]["lat"] / n
    avg_lat_o = totals["openai"]["lat"] / n
    print(f"{'Avg latency (s)':<30} {avg_lat_a:>18.1f} {avg_lat_o:>14.1f}  {'haiku' if avg_lat_a <= avg_lat_o else 'gpt-4o-mini'}")

    wins_a = totals["anthropic"]["wins_conf"]
    wins_o = n - wins_a
    print(f"{'Confidence wins':<30} {wins_a:>18}/10 {wins_o:>13}/10  {'haiku' if wins_a >= wins_o else 'gpt-4o-mini'}")

    wins_struct_a = totals["anthropic"]["wins_struct"]
    wins_struct_o = n - wins_struct_a
    print(f"{'Field completeness wins':<30} {wins_struct_a:>18}/10 {wins_struct_o:>13}/10  {'haiku' if wins_struct_a >= wins_struct_o else 'gpt-4o-mini'}")

    if total_cost_a > total_cost_o:
        print(f"\n  Cost saving with gpt-4o-mini: {savings:.1f}% cheaper per run")
    else:
        print(f"\n  Cost saving with haiku: {abs(savings):.1f}% cheaper per run")

    monthly_meetings = 450  # ~15 meetings/day * 30 days
    print(f"\n  Projected monthly cost @ 450 meetings/month:")
    print(f"    claude-haiku-4-5 : ${total_cost_a/n * monthly_meetings:.2f}/month")
    print(f"    gpt-4o-mini      : ${total_cost_o/n * monthly_meetings:.2f}/month")

    print(f"\n  Output files written to:")
    print(f"    comparison/anthropic/  — 10 YAML files from claude-haiku-4-5")
    print(f"    comparison/openai/     — 10 YAML files from gpt-4o-mini")
    print(f"\n{sep}\n")


if __name__ == "__main__":
    run_all()
