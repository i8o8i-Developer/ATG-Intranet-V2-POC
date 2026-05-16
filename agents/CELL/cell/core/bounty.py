"""
CELL Bounty Calculator.

Bounty is a unit count, NOT a rupee amount.
  4 hours of work = 1 bounty unit (base, normal priority)
  Priority multipliers apply fractional adjustments.

The accountant collects total bounty units per intern and multiplies by ₹100 to pay.

Priority multipliers:
  urgent → 1.5x  → 4h = 1.5 bounties
  high   → 1.25x → 4h = 1.25 bounties
  normal → 1.0x  → 4h = 1.0 bounty
  low    → 0.75x → 4h = 0.75 bounties

Formula: bounty_value = (estimated_hours / 4) * multiplier
Result is rounded to nearest 0.25 to keep values clean (0.25 steps).
"""
from __future__ import annotations

from cell.config import settings
from cell.core.models import TaskPriority

MULTIPLIERS = {
    TaskPriority.URGENT: 1.5,
    TaskPriority.HIGH:   1.25,
    TaskPriority.NORMAL: 1.0,
    TaskPriority.LOW:    0.75,
}


def calculate_bounty(estimated_hours: float, priority: str) -> float:
    """
    Calculate bounty unit value.

    Args:
        estimated_hours: Estimated hours for the task.
        priority: One of 'urgent', 'high', 'normal', 'low'.

    Returns:
        Bounty units as a float (e.g. 1, 1.25, 1.5, 0.75).
        Rounded to nearest 0.25.
    """
    try:
        priority_enum = TaskPriority(priority)
    except ValueError:
        priority_enum = TaskPriority.NORMAL

    multiplier = MULTIPLIERS.get(priority_enum, 1.0)
    raw = (estimated_hours / settings.base_hours_per_bounty) * multiplier
    # Round to nearest 0.25
    return round(raw * 4) / 4


def format_bounty_display(value: float) -> str:
    """Return a display string for a bounty unit value (e.g. '1.5 bounties')."""
    # Show as integer if whole number, else show up to 2 decimal places stripped of trailing zeros
    if value == int(value):
        return f"{int(value)} {'bounty' if int(value) == 1 else 'bounties'}"
    # Format to 2 dp, strip trailing zeros
    formatted = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{formatted} bounties"
