"""
CELL IST Clock Helpers.
All time logic in CELL uses IST (UTC+5:30) — hardcoded, no flexibility.
Day window: 2:00 AM IST → 1:59 AM IST next calendar day.
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone

import pytz

IST = pytz.timezone("Asia/Kolkata")
_IST_OFFSET = timedelta(hours=5, minutes=30)


def ist_now() -> datetime:
    """Return current datetime in IST."""
    return datetime.now(IST)


def ist_today() -> date:
    """
    Return the current 'CELL day' date.
    If it's between 0:00 AM and 1:59 AM IST, the day is still yesterday
    (because the day window starts at 2AM).
    """
    now = ist_now()
    if now.hour < 2:
        return (now - timedelta(days=1)).date()
    return now.date()


def ist_yesterday() -> date:
    return ist_today() - timedelta(days=1)


def day_window_start_ts() -> float:
    """
    Return Unix timestamp (float) of today's 2:00 AM IST.
    This is the start of the current CELL day window.
    If current time is before 2AM, return yesterday's 2AM.
    """
    today = ist_today()
    # 2AM IST on today (CELL day)
    dt_ist = IST.localize(datetime(today.year, today.month, today.day, 2, 0, 0))
    return dt_ist.timestamp()


def utc_to_ist(dt_utc: datetime) -> datetime:
    """Convert a UTC datetime to IST."""
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(IST)


def ist_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """Construct an IST-aware datetime."""
    return IST.localize(datetime(year, month, day, hour, minute, 0))


def format_ist_date(d: date) -> str:
    """Return a human-readable date string: '8 May 2025'."""
    return d.strftime("%-d %B %Y")
