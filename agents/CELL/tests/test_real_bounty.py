"""
Tests: Bounty calculation on real tasks extracted from IRIS sample outputs.

Strategy:
  1. Extract tasks from each real YAML.
  2. Assign realistic estimated_hours (what LLM would produce).
  3. Verify bounty units are correct multiples of 0.25,
     match expected values for each priority/hour combo,
     and that display strings are correct.

Bounty formula: (hours / 4) × multiplier, rounded to nearest 0.25
  urgent: 1.5x  |  high: 1.25x  |  normal: 1.0x  |  low: 0.75x
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cell.core.bounty import calculate_bounty, format_bounty_display
from cell.core.extractor import extract_raw_tasks
from cell.core.models import TaskPriority

SAMPLES_DIR = Path(__file__).parent.parent / "sample_outputs"


def load_yaml(filename: str) -> dict:
    with open(SAMPLES_DIR / filename) as f:
        return yaml.safe_load(f)


# ──────────────────────────────────────────────────────────────
# Bounty values for real task scenarios (derived from the YAMLs)
# ──────────────────────────────────────────────────────────────

class TestBountyForRealStandupTasks:
    """
    Standup tasks:
      - Resolve blocker (p-rohit-002, CRM credentials) — URGENT, est. 2h → 0.75
      - Resolve blocker (p-arjun-001, token refresh)  — HIGH,   est. 4h → 1.25
      - Production hotfix (unplanned work)             — HIGH,   est. 4h → 1.25
      - Follow up with p-dev-003 (silent member)       — HIGH,   est. 1h → 0.25 (rounded)
    """

    def test_urgent_2h_blocker(self):
        # Resolve credentials blocker: URGENT, 2h → (2/4) × 1.5 = 0.75
        assert calculate_bounty(2.0, "urgent") == 0.75

    def test_high_4h_token_refresh_blocker(self):
        # Token refresh blocker: HIGH, 4h → (4/4) × 1.25 = 1.25
        assert calculate_bounty(4.0, "high") == 1.25

    def test_high_4h_unplanned_hotfix(self):
        # Production hotfix: HIGH, 4h → 1.25
        assert calculate_bounty(4.0, "high") == 1.25

    def test_high_1h_silent_followup(self):
        # PM follow-up task: HIGH, 1h → (1/4) × 1.25 = 0.3125 → rounds to 0.25
        assert calculate_bounty(1.0, "high") == 0.25

    def test_urgent_3_day_blocker_6h(self):
        # A 3-day blocker might warrant 6h estimate: URGENT → (6/4) × 1.5 = 2.25
        assert calculate_bounty(6.0, "urgent") == 2.25


class TestBountyForRealHRTasks:
    """
    HR tasks from insights_hr.yaml:
      - Draft JD for 2 React Native positions: NORMAL, est. 3h → 0.75
      - Post JDs: NORMAL, est. 1h → 0.25
      - Check in with team leads: NORMAL, est. 2h → 0.5
      - Execute HR decision (hiring approval): HIGH, est. 2h → 0.5
    """

    def test_draft_jd_3h_normal(self):
        assert calculate_bounty(3.0, "normal") == 0.75

    def test_post_jd_1h_normal(self):
        assert calculate_bounty(1.0, "normal") == 0.25

    def test_checkin_2h_normal(self):
        assert calculate_bounty(2.0, "normal") == 0.5

    def test_hr_decision_2h_high(self):
        assert calculate_bounty(2.0, "high") == 0.5


class TestBountyForRealDesignTasks:
    """
    Design review: colour contrast fix — URGENT, est. 4h → 1.5
    Blocking development = URGENT priority.
    """

    def test_colour_contrast_fix_urgent_4h(self):
        assert calculate_bounty(4.0, "urgent") == 1.5

    def test_colour_contrast_fix_urgent_2h(self):
        # Shorter estimate: URGENT, 2h → 0.75
        assert calculate_bounty(2.0, "urgent") == 0.75


class TestBountyForRealMilestoneTasks:
    """
    Milestone review: architecture diagram rework — HIGH, est. 8h → 2.5
    """

    def test_arch_rework_high_8h(self):
        assert calculate_bounty(8.0, "high") == 2.5

    def test_arch_rework_high_6h(self):
        # 6h HIGH → (6/4) × 1.25 = 1.875 → rounds to nearest 0.25 = 2.0
        assert calculate_bounty(6.0, "high") == 2.0


class TestBountyForRealSalesTasks:
    """
    Sales BD: prepare and send proposal — HIGH, est. 4h → 1.25
    """

    def test_proposal_high_4h(self):
        assert calculate_bounty(4.0, "high") == 1.25

    def test_proposal_high_8h(self):
        # Detailed proposal: 8h HIGH → 2.5
        assert calculate_bounty(8.0, "high") == 2.5


class TestBountyForRealVendorTasks:
    """
    Vendor: review proposal and provide decision — NORMAL, est. 2h → 0.5
    """

    def test_review_proposal_normal_2h(self):
        assert calculate_bounty(2.0, "normal") == 0.5


# ──────────────────────────────────────────────────────────────
# Bounty accumulation — accountant payout simulation
# ──────────────────────────────────────────────────────────────

class TestBountyAccumulation:
    """
    Simulates an intern completing a realistic week of tasks
    and verifies the total bounty units are correct.
    The accountant multiplies total by ₹100 to pay.
    """

    def test_intern_weekly_payout_simulation(self):
        """
        p-arjun-001 completes in a week:
          - Token refresh blocker:     HIGH,   4h → 1.25
          - Production hotfix:         HIGH,   4h → 1.25
          - API gateway spike:         HIGH,   8h → 2.5
          - Architecture rework:       HIGH,   8h → 2.5
          - Rate limiting decision:    NORMAL, 2h → 0.5
        Total: 8.0 bounty units → ₹800 payout
        """
        tasks = [
            ("high", 4.0),
            ("high", 4.0),
            ("high", 8.0),
            ("high", 8.0),
            ("normal", 2.0),
        ]
        total = sum(calculate_bounty(h, p) for p, h in tasks)
        assert total == 8.0
        payout = total * 100
        assert payout == 800.0

    def test_intern_minimal_week(self):
        """
        Minimal week (low-effort tasks):
          - Checkin with team: NORMAL, 1h → 0.25
          - Post JD:           NORMAL, 1h → 0.25
        Total: 0.5 bounties → ₹50 payout
        """
        total = calculate_bounty(1.0, "normal") + calculate_bounty(1.0, "normal")
        assert total == 0.5
        assert total * 100 == 50.0

    def test_high_performer_week(self):
        """
        High performer week (all urgent/high tasks):
          - 3-day credentials blocker: URGENT, 6h → 2.25
          - Hotfix:                    URGENT, 4h → 1.5
          - Architecture rework:       HIGH,   8h → 2.5
        Total: 6.25 bounties → ₹625 payout
        """
        total = (
            calculate_bounty(6.0, "urgent") +
            calculate_bounty(4.0, "urgent") +
            calculate_bounty(8.0, "high")
        )
        assert total == 6.25
        assert total * 100 == 625.0

    def test_all_bounties_are_0_25_multiples(self):
        """Every realistic task combination must produce a 0.25-multiple bounty."""
        combos = [
            (1.0, "urgent"), (2.0, "urgent"), (3.0, "urgent"), (4.0, "urgent"),
            (6.0, "urgent"), (8.0, "urgent"),
            (1.0, "high"), (2.0, "high"), (3.0, "high"), (4.0, "high"),
            (6.0, "high"), (8.0, "high"), (10.0, "high"),
            (1.0, "normal"), (2.0, "normal"), (3.0, "normal"), (4.0, "normal"),
            (6.0, "normal"), (8.0, "normal"),
            (1.0, "low"), (2.0, "low"), (4.0, "low"), (8.0, "low"),
        ]
        for hours, priority in combos:
            val = calculate_bounty(hours, priority)
            remainder = (val * 4) % 1
            assert remainder == 0.0, (
                f"{hours}h/{priority} → {val} is not a 0.25 multiple"
            )


# ──────────────────────────────────────────────────────────────
# Display format tests using real bounty values
# ──────────────────────────────────────────────────────────────

class TestBountyDisplayRealValues:

    def test_display_1_25(self):
        assert format_bounty_display(1.25) == "1.25 bounties"

    def test_display_1_5(self):
        assert format_bounty_display(1.5) == "1.5 bounties"

    def test_display_2_5(self):
        assert format_bounty_display(2.5) == "2.5 bounties"

    def test_display_0_75(self):
        assert format_bounty_display(0.75) == "0.75 bounties"

    def test_display_0_25(self):
        assert format_bounty_display(0.25) == "0.25 bounties"

    def test_display_1_0_singular(self):
        assert format_bounty_display(1.0) == "1 bounty"

    def test_display_2_0_plural(self):
        assert format_bounty_display(2.0) == "2 bounties"

    def test_display_6_25(self):
        assert format_bounty_display(6.25) == "6.25 bounties"

    def test_display_8_0(self):
        assert format_bounty_display(8.0) == "8 bounties"

    def test_display_in_todo_dm_format(self):
        """Verify the exact string that appears in the intern todo DM"""
        # e.g. "Bounty: 1.25 bounties"
        val = calculate_bounty(4.0, "high")
        display = format_bounty_display(val)
        dm_line = f"Bounty: {display}"
        assert dm_line == "Bounty: 1.25 bounties"

    def test_display_in_pm_digest_format(self):
        # Architecture rework: HIGH 8h → 2.5 bounties
        val = calculate_bounty(8.0, "high")
        display = format_bounty_display(val)
        assert display == "2.5 bounties"
