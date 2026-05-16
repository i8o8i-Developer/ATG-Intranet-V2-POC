"""
Tests: Bounty Calculation.

Bounty is a unit count. Accountant totals units and multiplies by ₹100 to pay.
4 hours = 1 bounty unit at normal priority.
"""
from __future__ import annotations

import pytest

from cell.core.bounty import calculate_bounty, format_bounty_display


class TestBountyCalculation:

    def test_normal_4h(self):
        # 4h / 4h × 1.0 = 1 bounty
        assert calculate_bounty(4.0, "normal") == 1.0

    def test_urgent_4h(self):
        # 4h / 4h × 1.5 = 1.5 bounties
        assert calculate_bounty(4.0, "urgent") == 1.5

    def test_high_4h(self):
        # 4h / 4h × 1.25 = 1.25 bounties
        assert calculate_bounty(4.0, "high") == 1.25

    def test_low_4h(self):
        # 4h / 4h × 0.75 = 0.75 bounties
        assert calculate_bounty(4.0, "low") == 0.75

    def test_8h_normal(self):
        # 8h / 4h × 1.0 = 2 bounties
        assert calculate_bounty(8.0, "normal") == 2.0

    def test_8h_high(self):
        # 8h / 4h × 1.25 = 2.5 bounties
        assert calculate_bounty(8.0, "high") == 2.5

    def test_6h_high(self):
        # 6/4 × 1.25 = 1.875 → rounded to nearest 0.25 = 2.0
        assert calculate_bounty(6.0, "high") == 2.0

    def test_3h_normal(self):
        # 3/4 × 1.0 = 0.75 bounties
        assert calculate_bounty(3.0, "normal") == 0.75

    def test_2h_urgent(self):
        # 2/4 × 1.5 = 0.75 bounties
        assert calculate_bounty(2.0, "urgent") == 0.75

    def test_2h_normal(self):
        # 2/4 × 1.0 = 0.5 bounties
        assert calculate_bounty(2.0, "normal") == 0.5

    def test_1h_normal(self):
        # 1/4 × 1.0 = 0.25 bounties
        assert calculate_bounty(1.0, "normal") == 0.25

    def test_invalid_priority_defaults_to_normal(self):
        # Unknown priority → normal multiplier
        assert calculate_bounty(4.0, "superhigh") == 1.0

    def test_result_is_multiple_of_0_25(self):
        """All bounty values should be multiples of 0.25."""
        for hours in [1, 2, 3, 4, 5, 6, 7, 8, 10, 12]:
            for priority in ["urgent", "high", "normal", "low"]:
                val = calculate_bounty(float(hours), priority)
                assert (val * 4) == round(val * 4), \
                    f"{hours}h/{priority} gave {val} which is not a 0.25 multiple"

    def test_result_is_float(self):
        assert isinstance(calculate_bounty(4.0, "normal"), float)


class TestBountyDisplay:

    def test_whole_number_singular(self):
        assert format_bounty_display(1.0) == "1 bounty"

    def test_whole_number_plural(self):
        assert format_bounty_display(2.0) == "2 bounties"

    def test_zero_bounties(self):
        assert format_bounty_display(0.0) == "0 bounties"

    def test_fractional_1_5(self):
        assert format_bounty_display(1.5) == "1.5 bounties"

    def test_fractional_1_25(self):
        assert format_bounty_display(1.25) == "1.25 bounties"

    def test_fractional_0_75(self):
        assert format_bounty_display(0.75) == "0.75 bounties"

    def test_fractional_0_25(self):
        assert format_bounty_display(0.25) == "0.25 bounties"
