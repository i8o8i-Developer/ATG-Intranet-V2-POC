"""
Tests: Task extraction — synthetic fixtures using the REAL nested IRIS schema.

These test edge cases and rules that the real sample YAMLs don't cover
(e.g. rework_requested as string, priority inference, default assignee fallback).
All fixtures now use the correct nested meeting-type schema that IRIS actually produces.

For tests against the real IRIS sample files, see test_real_extraction.py.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict

import pytest

from cell.core.extractor import extract_raw_tasks
from cell.core.models import TaskPriority, TaskSource


# ──────────────────────────────────────────────────────────────
# Standup extraction (nested schema)
# ──────────────────────────────────────────────────────────────

class TestStandupExtraction:

    @pytest.fixture
    def insights(self) -> Dict[str, Any]:
        return {
            "meeting_type": "standup",
            "meeting_id": "meet-001",
            "project_id": "PROJ-001",
            "organiser_id": "p-pm-001",
            "follow_up_owner": "p-pm-001",
            "standup": {
                "blocked_today": [
                    {
                        "person_id": "p-arjun-001",
                        "desc": "Token refresh not working",
                        "days_carried": None,
                        "cross_team": False,
                        "blocking_dept": None,
                    },
                    {
                        "person_id": "p-rohit-002",
                        "desc": "Waiting for client credentials",
                        "days_carried": 3,
                        "cross_team": True,
                        "blocking_dept": "BA",
                    },
                ],
                "unplanned_work_mentioned": [
                    {
                        "desc": "Production hotfix for auth module",
                        "raised_by": "p-arjun-001",
                        "in_scope": True,
                    }
                ],
                "silent_members": [
                    {"person_id": "p-dev-003", "days_silent_in_row": 2}
                ],
            },
        }

    def test_blocked_intra_team_assigned_to_person(self, insights):
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm-001")
        arjun_blocker = next(
            (t for t in tasks if "p-arjun-001" in (t.notes or "") and t.source_yaml_field == "standup.blocked_today"),
            None,
        )
        assert arjun_blocker is not None
        assert arjun_blocker.assignee_id == "p-arjun-001"

    def test_blocked_cross_team_assigned_to_pm(self, insights):
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm-001")
        rohit_blocker = next(
            (t for t in tasks if "p-rohit-002" in (t.notes or "") and t.source_yaml_field == "standup.blocked_today"),
            None,
        )
        assert rohit_blocker is not None
        assert rohit_blocker.assignee_id == "p-pm-001"

    def test_blocker_3_days_is_urgent(self, insights):
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm-001")
        rohit_blocker = next(
            t for t in tasks if "p-rohit-002" in (t.notes or "")
        )
        assert rohit_blocker.priority == TaskPriority.URGENT

    def test_unplanned_work_extracted(self, insights):
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm-001")
        unplanned = [t for t in tasks if t.source_yaml_field == "standup.unplanned_work_mentioned"]
        assert len(unplanned) == 1
        assert unplanned[0].assignee_id == "p-arjun-001"
        # "hotfix" in description → URGENT; normal unplanned work → HIGH; never LOW/NORMAL
        assert unplanned[0].priority in (TaskPriority.HIGH, TaskPriority.URGENT)

    def test_silent_member_2_days_generates_task(self, insights):
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm-001")
        silent_tasks = [t for t in tasks if t.source_yaml_field == "standup.silent_members"]
        assert len(silent_tasks) == 1
        assert "p-dev-003" in silent_tasks[0].title
        assert silent_tasks[0].assignee_id == "p-pm-001"

    def test_silent_member_1_day_not_escalated(self):
        insights = {
            "meeting_type": "standup",
            "project_id": "PROJ-001",
            "follow_up_owner": "p-pm-001",
            "standup": {
                "silent_members": [{"person_id": "p-new-intern", "days_silent_in_row": 1}],
                "blocked_today": [],
                "unplanned_work_mentioned": [],
            },
        }
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm-001")
        silent_tasks = [t for t in tasks if t.source_yaml_field == "standup.silent_members"]
        assert len(silent_tasks) == 0

    def test_all_tasks_have_iris_source(self, insights):
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm-001")
        for t in tasks:
            assert t.source == TaskSource.IRIS

    def test_total_count(self, insights):
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm-001")
        # 2 blockers + 1 unplanned + 1 silent = 4
        assert len(tasks) == 4


# ──────────────────────────────────────────────────────────────
# Sales BD (nested schema)
# ──────────────────────────────────────────────────────────────

class TestSalesExtraction:

    @pytest.fixture
    def insights(self) -> Dict[str, Any]:
        return {
            "meeting_type": "sales-bd",
            "project_id": "PROJ-SALES",
            "meeting_id": "meet-sales-001",
            "follow_up_owner": "p-ba-001",
            "sales_bd": {
                "next_action": "Send proposal to client",
                "next_action_owner": "p-ba-001",
                "next_action_due": "2025-05-09",
                "lead_stage_after": "proposal",
            },
        }

    def test_next_action_extracted(self, insights):
        tasks = extract_raw_tasks(insights, "PROJ-SALES", "meet-sales-001", "p-ba-001")
        na_tasks = [t for t in tasks if t.source_yaml_field == "sales_bd.next_action"]
        assert len(na_tasks) == 1

    def test_next_action_assignee_and_due(self, insights):
        tasks = extract_raw_tasks(insights, "PROJ-SALES", "meet-sales-001", "p-ba-001")
        t = [t for t in tasks if t.source_yaml_field == "sales_bd.next_action"][0]
        assert t.assignee_id == "p-ba-001"
        assert t.due_date == date(2025, 5, 9)
        assert t.priority == TaskPriority.HIGH

    def test_next_action_not_extracted_for_standup(self):
        """sales_bd.next_action is not extracted for standup type"""
        insights = {
            "meeting_type": "standup",
            "project_id": "PROJ-001",
            "follow_up_owner": "p-pm-001",
            "standup": {"blocked_today": [], "unplanned_work_mentioned": [], "silent_members": []},
            "sales_bd": {"next_action": "Some action"},
        }
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm-001")
        na_tasks = [t for t in tasks if t.source_yaml_field == "sales_bd.next_action"]
        assert len(na_tasks) == 0


# ──────────────────────────────────────────────────────────────
# HR extraction (nested schema)
# ──────────────────────────────────────────────────────────────

class TestHRExtraction:

    @pytest.fixture
    def insights(self) -> Dict[str, Any]:
        return {
            "meeting_type": "hr",
            "project_id": "INTERNAL-HR",
            "meeting_id": "meet-hr-001",
            "hr": {
                "action_items": [
                    {"text": "Draft job descriptions", "owner": "hr-assoc-001", "due": "2025-05-09"},
                    {"text": "Post job descriptions", "owner": "hr-assoc-001", "due": "2025-05-15"},
                ],
                "decisions": [
                    {"text": "Approve 2 new hires", "owner": "hr-head", "due": "2025-05-15"},
                ],
            },
        }

    def test_hr_action_items_extracted(self, insights):
        tasks = extract_raw_tasks(insights, "INTERNAL-HR", "meet-hr-001", "hr-assoc-001")
        action_tasks = [t for t in tasks if t.source_yaml_field == "hr.action_items"]
        assert len(action_tasks) == 2

    def test_hr_tasks_marked_restricted(self, insights):
        tasks = extract_raw_tasks(insights, "INTERNAL-HR", "meet-hr-001", "hr-assoc-001")
        for t in tasks:
            assert t.notes and "HR RESTRICTED" in t.notes

    def test_hr_decision_extracted(self, insights):
        tasks = extract_raw_tasks(insights, "INTERNAL-HR", "meet-hr-001", "hr-assoc-001")
        decision_tasks = [t for t in tasks if t.source_yaml_field == "hr.decisions"]
        assert len(decision_tasks) == 1
        assert decision_tasks[0].assignee_id == "hr-head"
        assert decision_tasks[0].due_date == date(2025, 5, 15)

    def test_no_action_items_for_empty_list(self):
        insights = {
            "meeting_type": "hr",
            "project_id": "INTERNAL-HR",
            "hr": {"action_items": [], "decisions": []},
        }
        tasks = extract_raw_tasks(insights, "INTERNAL-HR", "meet-hr-001", "hr-head")
        assert tasks == []


# ──────────────────────────────────────────────────────────────
# Edge cases
# ──────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_empty_insights_returns_no_tasks(self):
        tasks = extract_raw_tasks({}, "PROJ-001", "meet-001", "p-default")
        assert tasks == []

    def test_unknown_meeting_type_returns_no_tasks(self):
        tasks = extract_raw_tasks(
            {"meeting_type": "town-hall", "project_id": "PROJ-001"},
            "PROJ-001", "meet-001", "p-default",
        )
        assert tasks == []

    def test_allhands_always_returns_no_tasks(self):
        insights = {
            "meeting_type": "company-allhands",
            "project_id": "INTERNAL-COMPANY",
            "allhands": {"announcements": [{"text": "Revenue hit target"}]},
        }
        tasks = extract_raw_tasks(insights, "INTERNAL-COMPANY", "meet-001", "ceo")
        assert tasks == []

    def test_project_id_from_yaml_overrides_argument(self):
        insights = {
            "meeting_type": "standup",
            "project_id": "PROJ-FROM-YAML",
            "follow_up_owner": "p-pm",
            "standup": {
                "blocked_today": [{"person_id": "p-dev", "desc": "blocked", "days_carried": None, "cross_team": False}],
                "unplanned_work_mentioned": [],
                "silent_members": [],
            },
        }
        tasks = extract_raw_tasks(insights, "PROJ-OVERRIDE", "meet-001", "p-pm")
        assert all(t.project_id == "PROJ-FROM-YAML" for t in tasks)

    def test_priority_inferred_urgent_from_title(self):
        insights = {
            "meeting_type": "standup",
            "project_id": "PROJ-001",
            "follow_up_owner": "p-pm",
            "standup": {
                "unplanned_work_mentioned": [
                    {"desc": "URGENT hotfix for production crash", "raised_by": "p-dev-001"}
                ],
                "blocked_today": [],
                "silent_members": [],
            },
        }
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm")
        unplanned = [t for t in tasks if t.source_yaml_field == "standup.unplanned_work_mentioned"]
        assert len(unplanned) == 1
        assert unplanned[0].priority == TaskPriority.URGENT

    def test_design_review_minor_feedback_not_extracted(self):
        """Only major/critical severity feedback generates tasks"""
        insights = {
            "meeting_type": "design-review",
            "project_id": "PROJ-001",
            "design_review": {
                "feedback_items": [
                    {"item": "Spacing looks slightly off", "severity": "minor", "owner": "p-uiux-001"},
                ],
                "blocking_development": False,
            },
        }
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-uiux-001")
        assert tasks == []

    def test_milestone_accepted_deliverable_no_task(self):
        insights = {
            "meeting_type": "milestone-review",
            "project_id": "PROJ-001",
            "milestone_review": {
                "milestone_id": "M1",
                "sign_offs": [
                    {"deliverable": "requirements", "status": "accepted", "rework_owner": None, "rework_due": None},
                ],
            },
        }
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm")
        assert tasks == []

    def test_vendor_internal_owner_extracted(self):
        insights = {
            "meeting_type": "vendor",
            "project_id": "PROJ-INFRA",
            "follow_up_owner": "p-rohan-pm",
            "organiser_id": "p-arjun-001",
            "vendor": {
                "commitments": [
                    {"id": "V-001", "text": "Vendor migration", "owner": "vendor-side", "status": "open"},
                    {"id": "V-002", "text": "Review proposal", "owner": "p-rohan-pm", "status": "open"},
                ],
            },
        }
        tasks = extract_raw_tasks(insights, "PROJ-INFRA", "meet-001", "p-rohan-pm")
        commitment_tasks = [t for t in tasks if t.source_yaml_field == "vendor.commitments"]
        assert len(commitment_tasks) == 1
        assert commitment_tasks[0].assignee_id == "p-rohan-pm"

    def test_client_call_only_our_side_open(self):
        insights = {
            "meeting_type": "client-call",
            "project_id": "PROJ-001",
            "follow_up_owner": "p-pm",
            "client": {
                "commitments": [
                    {"id": "C-1", "text": "Client sends credentials", "owner": "client-co", "made_by": "client-side", "status": "open"},
                    {"id": "C-2", "text": "We assess scope", "owner": "p-pm", "made_by": "our-side", "status": "open"},
                    {"id": "C-3", "text": "Already done item", "owner": "p-pm", "made_by": "our-side", "status": "fulfilled"},
                ],
            },
        }
        tasks = extract_raw_tasks(insights, "PROJ-001", "meet-001", "p-pm")
        assert len(tasks) == 1
        assert tasks[0].assignee_id == "p-pm"
