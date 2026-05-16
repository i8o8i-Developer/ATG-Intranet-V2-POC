"""
Tests: IST clock helpers and scheduler timing logic.
No live scheduler — just verifies time math is correct.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta, date
from unittest.mock import patch

import pytest
import pytz

from cell.scheduler.clock import (
    ist_now,
    ist_today,
    ist_yesterday,
    day_window_start_ts,
    utc_to_ist,
    format_ist_date,
)

IST = pytz.timezone("Asia/Kolkata")


def _ist(year, month, day, hour, minute=0) -> datetime:
    return IST.localize(datetime(year, month, day, hour, minute, 0))


class TestISTHelpers:

    def test_ist_now_is_ist_aware(self):
        now = ist_now()
        assert now.tzinfo is not None
        assert "Asia/Kolkata" in str(now.tzinfo) or "+05:30" in str(now.tzinfo)

    def test_utc_to_ist_offset(self):
        utc_dt = datetime(2025, 5, 6, 8, 30, 0, tzinfo=timezone.utc)
        ist_dt = utc_to_ist(utc_dt)
        # UTC+5:30 → 8:30 UTC = 14:00 IST
        assert ist_dt.hour == 14
        assert ist_dt.minute == 0

    def test_format_ist_date(self):
        d = date(2025, 5, 8)
        assert format_ist_date(d) == "8 May 2025"

    def test_format_ist_date_single_digit(self):
        d = date(2025, 1, 3)
        assert format_ist_date(d) == "3 January 2025"


class TestCellDayWindow:
    """
    Day window: 2AM IST → 1:59AM IST next calendar day.
    If current time is between 0:00 and 1:59 IST, ist_today() returns yesterday's date.
    """

    def test_after_2am_returns_calendar_date(self):
        # 3AM IST on May 6 → CELL day is May 6
        fake_now = _ist(2025, 5, 6, 3, 0)
        with patch("cell.scheduler.clock.ist_now", return_value=fake_now):
            assert ist_today() == date(2025, 5, 6)

    def test_before_2am_returns_previous_date(self):
        # 1AM IST on May 7 → CELL day is still May 6 (day started at 2AM May 6)
        fake_now = _ist(2025, 5, 7, 1, 0)
        with patch("cell.scheduler.clock.ist_now", return_value=fake_now):
            assert ist_today() == date(2025, 5, 6)

    def test_exactly_2am_returns_same_date(self):
        fake_now = _ist(2025, 5, 6, 2, 0)
        with patch("cell.scheduler.clock.ist_now", return_value=fake_now):
            assert ist_today() == date(2025, 5, 6)

    def test_yesterday_is_today_minus_one(self):
        fake_now = _ist(2025, 5, 6, 10, 0)
        with patch("cell.scheduler.clock.ist_now", return_value=fake_now):
            assert ist_yesterday() == date(2025, 5, 5)

    def test_day_window_start_ts_is_2am(self):
        # When current time is 10AM May 6, window start should be 2AM May 6
        fake_now = _ist(2025, 5, 6, 10, 0)
        with patch("cell.scheduler.clock.ist_now", return_value=fake_now):
            ts = day_window_start_ts()
            expected = _ist(2025, 5, 6, 2, 0).timestamp()
            assert ts == pytest.approx(expected, abs=1)

    def test_day_window_start_ts_before_2am(self):
        # 1AM May 7 → window start should be 2AM May 6 (yesterday)
        fake_now = _ist(2025, 5, 7, 1, 0)
        with patch("cell.scheduler.clock.ist_now", return_value=fake_now):
            ts = day_window_start_ts()
            expected = _ist(2025, 5, 6, 2, 0).timestamp()
            assert ts == pytest.approx(expected, abs=1)


class TestSchedulerJobTimes:
    """Verify job trigger cron expressions match architecture spec."""

    def test_morning_job_schedule(self):
        from cell.config import settings
        assert settings.schedule_morning_hour == 8
        assert settings.schedule_morning_minute == 0

    def test_eod_reminder_schedule(self):
        from cell.config import settings
        assert settings.schedule_eod_reminder_hour == 23
        assert settings.schedule_eod_reminder_minute == 30

    def test_night_process_schedule(self):
        from cell.config import settings
        assert settings.schedule_night_process_hour == 2
        assert settings.schedule_night_process_minute == 0
