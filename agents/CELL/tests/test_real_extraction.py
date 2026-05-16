"""
Tests: Task extraction against REAL IRIS sample outputs.

Each test loads the actual .yaml file from sample_outputs/ and asserts
exactly which tasks are extracted, who they're assigned to, and what
yaml_field they come from.

No mocks, no synthetic data — these test the real extractor against
the real IRIS output schema.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pytest
import yaml

from cell.core.extractor import extract_raw_tasks
from cell.core.models import TaskPriority, TaskSource

SAMPLES_DIR = Path(__file__).parent.parent / "sample_outputs"


def load_yaml(filename: str) -> dict:
    with open(SAMPLES_DIR / filename) as f:
        return yaml.safe_load(f)


# ──────────────────────────────────────────────────────────────
# STANDUP
# ──────────────────────────────────────────────────────────────

class TestStandupExtraction:
    """insights_standup.yaml — meet-standup-001, PROJ-CRM-0014"""

    @pytest.fixture
    def tasks(self):
        insights = load_yaml("insights_standup.yaml")
        return extract_raw_tasks(insights, "PROJ-CRM-0014", "meet-standup-001", "p-rohan-pm")

    def test_project_and_meeting_ids_from_yaml(self, tasks):
        for t in tasks:
            assert t.project_id == "PROJ-CRM-0014"
            assert t.source_meeting_id == "meet-standup-001"

    def test_source_is_iris(self, tasks):
        for t in tasks:
            assert t.source == TaskSource.IRIS

    def test_blocked_rohit_is_extracted(self, tasks):
        """p-rohit-002 blocked by CRM credentials — cross-team, carried 3 days → URGENT"""
        blocker_tasks = [t for t in tasks if t.source_yaml_field == "standup.blocked_today"]
        persons = {t.notes for t in blocker_tasks}
        rohit_task = next(
            (t for t in blocker_tasks if "p-rohit-002" in (t.notes or "")),
            None,
        )
        assert rohit_task is not None, "Should extract p-rohit-002 blocker"
        assert rohit_task.priority == TaskPriority.URGENT
        # Cross-team blocker → assigned to follow_up_owner (PM)
        assert rohit_task.assignee_id == "p-rohan-pm"
        assert "3 days" in rohit_task.notes or "carried 3" in rohit_task.notes

    def test_blocked_arjun_is_extracted(self, tasks):
        """p-arjun-001 blocked by token refresh — not cross-team, no days_carried"""
        blocker_tasks = [t for t in tasks if t.source_yaml_field == "standup.blocked_today"]
        arjun_task = next(
            (t for t in blocker_tasks if "p-arjun-001" in (t.notes or "")),
            None,
        )
        assert arjun_task is not None
        # Not cross-team → assigned to the blocked person themselves
        assert arjun_task.assignee_id == "p-arjun-001"

    def test_unplanned_work_hotfix_extracted(self, tasks):
        """Production hotfix for token refresh → unplanned_work_mentioned"""
        unplanned = [t for t in tasks if t.source_yaml_field == "standup.unplanned_work_mentioned"]
        assert len(unplanned) == 1
        assert "token refresh" in unplanned[0].title.lower() or "hotfix" in unplanned[0].title.lower()
        assert unplanned[0].assignee_id == "p-arjun-001"
        # "Production hotfix" triggers URGENT keyword → inferred URGENT (floor is HIGH anyway)
        assert unplanned[0].priority in (TaskPriority.HIGH, TaskPriority.URGENT)

    def test_silent_member_dev003_escalated(self, tasks):
        """p-dev-003 silent 2 consecutive standups → PM follow-up task"""
        silent_tasks = [t for t in tasks if t.source_yaml_field == "standup.silent_members"]
        assert len(silent_tasks) == 1
        assert "p-dev-003" in silent_tasks[0].title
        assert silent_tasks[0].assignee_id == "p-rohan-pm"
        assert silent_tasks[0].priority == TaskPriority.HIGH

    def test_total_task_count(self, tasks):
        # 2 blocked + 1 unplanned + 1 silent = 4 tasks
        assert len(tasks) == 4

    def test_no_tasks_assigned_to_unassigned(self, tasks):
        for t in tasks:
            assert t.assignee_id != "UNASSIGNED"


# ──────────────────────────────────────────────────────────────
# HR
# ──────────────────────────────────────────────────────────────

class TestHRExtraction:
    """insights_hr.yaml — meet-hr-001, INTERNAL-HR"""

    @pytest.fixture
    def tasks(self):
        insights = load_yaml("insights_hr.yaml")
        return extract_raw_tasks(insights, "INTERNAL-HR", "meet-hr-001", "hr-assoc-001")

    def test_project_id_from_yaml(self, tasks):
        for t in tasks:
            assert t.project_id == "INTERNAL-HR"

    def test_three_action_items_extracted(self, tasks):
        action_tasks = [t for t in tasks if t.source_yaml_field == "hr.action_items"]
        assert len(action_tasks) == 3

    def test_draft_jd_task(self, tasks):
        action_tasks = [t for t in tasks if t.source_yaml_field == "hr.action_items"]
        draft_task = next(
            (t for t in action_tasks if "job description" in t.title.lower() or "draft" in t.title.lower()),
            None,
        )
        assert draft_task is not None
        assert draft_task.assignee_id == "hr-assoc-001"
        assert draft_task.due_date == date(2025, 5, 9)

    def test_post_jd_task(self, tasks):
        action_tasks = [t for t in tasks if t.source_yaml_field == "hr.action_items"]
        post_task = next(
            (t for t in action_tasks if "post" in t.title.lower()),
            None,
        )
        assert post_task is not None
        assert post_task.due_date == date(2025, 5, 15)

    def test_check_in_task_no_due_date(self, tasks):
        """Check in with team leads has no due date in YAML"""
        action_tasks = [t for t in tasks if t.source_yaml_field == "hr.action_items"]
        checkin_task = next(
            (t for t in action_tasks if "check" in t.title.lower() or "morale" in t.title.lower()),
            None,
        )
        assert checkin_task is not None
        assert checkin_task.due_date is None

    def test_hr_decision_extracted(self, tasks):
        decision_tasks = [t for t in tasks if t.source_yaml_field == "hr.decisions"]
        assert len(decision_tasks) == 1
        assert decision_tasks[0].assignee_id == "hr-head"
        assert decision_tasks[0].due_date == date(2025, 5, 15)
        assert "react native" in decision_tasks[0].title.lower() or "hiring" in decision_tasks[0].title.lower()

    def test_all_tasks_marked_hr_restricted(self, tasks):
        for t in tasks:
            assert t.notes and "HR RESTRICTED" in t.notes

    def test_total_task_count(self, tasks):
        # 3 action items + 1 decision = 4
        assert len(tasks) == 4


# ──────────────────────────────────────────────────────────────
# CLIENT CALL
# ──────────────────────────────────────────────────────────────

class TestClientCallExtraction:
    """insights_client_call.yaml — meet-client-001, PROJ-CRM-0014"""

    @pytest.fixture
    def tasks(self):
        insights = load_yaml("insights_client_call.yaml")
        return extract_raw_tasks(insights, "PROJ-CRM-0014", "meet-client-001", "p-rohan-pm")

    def test_only_our_side_commitments_extracted(self, tasks):
        """C-001 is client-side → must NOT be extracted. C-002 is our-side → must be extracted."""
        commitment_tasks = [t for t in tasks if t.source_yaml_field == "client.commitments"]
        assert len(commitment_tasks) == 1

    def test_correct_commitment_extracted(self, tasks):
        """C-002: Assess effort for reporting dashboard scope change"""
        commitment_tasks = [t for t in tasks if t.source_yaml_field == "client.commitments"]
        t = commitment_tasks[0]
        assert "reporting dashboard" in t.title.lower() or "scope change" in t.title.lower() or "assess" in t.title.lower()
        assert t.assignee_id == "p-rohan-pm"

    def test_client_side_commitment_not_extracted(self, tasks):
        """C-001 (share API credentials) is client-side — must not appear"""
        titles_lower = [t.title.lower() for t in tasks]
        assert not any("api credentials" in title or "share api" in title for title in titles_lower)

    def test_total_task_count(self, tasks):
        assert len(tasks) == 1


# ──────────────────────────────────────────────────────────────
# VENDOR
# ──────────────────────────────────────────────────────────────

class TestVendorExtraction:
    """insights_vendor.yaml — meet-vendor-001, INTERNAL-INFRA"""

    @pytest.fixture
    def tasks(self):
        insights = load_yaml("insights_vendor.yaml")
        return extract_raw_tasks(insights, "INTERNAL-INFRA", "meet-vendor-001", "p-rohan-pm")

    def test_only_internal_commitments_extracted(self, tasks):
        """V-001, V-002, V-003 are vendor-side → skip. V-004 is p-rohan-pm → extract."""
        commitment_tasks = [t for t in tasks if t.source_yaml_field == "vendor.commitments"]
        assert len(commitment_tasks) == 1

    def test_v004_review_proposal_extracted(self, tasks):
        commitment_tasks = [t for t in tasks if t.source_yaml_field == "vendor.commitments"]
        t = commitment_tasks[0]
        assert "proposal" in t.title.lower() or "review" in t.title.lower() or "decision" in t.title.lower()
        assert t.assignee_id == "p-rohan-pm"
        assert t.due_date == date(2025, 5, 15)

    def test_vendor_side_commitments_not_extracted(self, tasks):
        """Migration support, migration completion, formal proposal are all vendor-side"""
        titles_lower = [t.title.lower() for t in tasks]
        assert not any("migration support" in title for title in titles_lower)
        assert not any("formal proposal" in title for title in titles_lower)

    def test_total_task_count(self, tasks):
        assert len(tasks) == 1


# ──────────────────────────────────────────────────────────────
# SALES BD
# ──────────────────────────────────────────────────────────────

class TestSalesBDExtraction:
    """insights_sales_bd.yaml — meet-sales-001, PROJ-SALES-NEW"""

    @pytest.fixture
    def tasks(self):
        insights = load_yaml("insights_sales_bd.yaml")
        return extract_raw_tasks(insights, "PROJ-SALES-NEW", "meet-sales-001", "p-ba-001")

    def test_next_action_extracted(self, tasks):
        na_tasks = [t for t in tasks if t.source_yaml_field == "sales_bd.next_action"]
        assert len(na_tasks) == 1

    def test_next_action_content(self, tasks):
        na_tasks = [t for t in tasks if t.source_yaml_field == "sales_bd.next_action"]
        t = na_tasks[0]
        assert "proposal" in t.title.lower()
        assert t.assignee_id == "p-ba-001"
        assert t.due_date == date(2025, 5, 9)
        assert t.priority == TaskPriority.HIGH

    def test_total_task_count(self, tasks):
        assert len(tasks) == 1


# ──────────────────────────────────────────────────────────────
# SPRINT PLANNING
# ──────────────────────────────────────────────────────────────

class TestSprintPlanningExtraction:
    """insights_sprint_planning.yaml — meet-sprint-001, PROJ-CRM-0014"""

    @pytest.fixture
    def tasks(self):
        insights = load_yaml("insights_sprint_planning.yaml")
        return extract_raw_tasks(insights, "PROJ-CRM-0014", "meet-sprint-001", "p-rohan-pm")

    def test_no_decisions_without_due_extracted(self, tasks):
        """D-001, D-002, D-003 all have no 'due' date → none produce decision-execution tasks"""
        decision_tasks = [t for t in tasks if t.source_yaml_field == "internal.decisions"]
        assert len(decision_tasks) == 0

    def test_deferred_item_db_migration_extracted(self, tasks):
        """Database migration strategy deferred 2x → HIGH priority"""
        deferred_tasks = [t for t in tasks if t.source_yaml_field == "internal.deferred_items"]
        assert len(deferred_tasks) == 1
        t = deferred_tasks[0]
        assert "database" in t.title.lower() or "migration" in t.title.lower()
        assert t.assignee_id == "p-arjun-001"
        assert t.priority == TaskPriority.HIGH   # deferred 2x

    def test_cross_dept_dependency_extracted(self, tasks):
        """UIUX blocking REACT — dashboard mockups due 2025-05-08"""
        cross_tasks = [t for t in tasks if t.source_yaml_field == "internal.cross_dept_dependencies"]
        assert len(cross_tasks) == 1
        t = cross_tasks[0]
        assert "mockup" in t.title.lower() or "dashboard" in t.title.lower() or "dependency" in t.title.lower()
        assert t.due_date == date(2025, 5, 8)
        assert t.priority == TaskPriority.HIGH

    def test_total_task_count(self, tasks):
        # 0 decisions + 1 deferred + 1 cross-dept = 2
        assert len(tasks) == 2


# ──────────────────────────────────────────────────────────────
# DESIGN REVIEW
# ──────────────────────────────────────────────────────────────

class TestDesignReviewExtraction:
    """insights_design_review.yaml — meet-design-001, PROJ-CRM-0014"""

    @pytest.fixture
    def tasks(self):
        insights = load_yaml("insights_design_review.yaml")
        return extract_raw_tasks(insights, "PROJ-CRM-0014", "meet-design-001", "p-uiux-001")

    def test_major_feedback_extracted(self, tasks):
        feedback_tasks = [t for t in tasks if t.source_yaml_field == "design_review.feedback_items"]
        assert len(feedback_tasks) == 1

    def test_colour_contrast_task(self, tasks):
        feedback_tasks = [t for t in tasks if t.source_yaml_field == "design_review.feedback_items"]
        t = feedback_tasks[0]
        assert "colour" in t.title.lower() or "color" in t.title.lower() or "contrast" in t.title.lower() or "accessibility" in t.title.lower()
        assert t.assignee_id == "p-uiux-001"
        assert t.due_date == date(2025, 5, 8)

    def test_blocking_dev_means_urgent_priority(self, tasks):
        """blocking_development: true → URGENT"""
        feedback_tasks = [t for t in tasks if t.source_yaml_field == "design_review.feedback_items"]
        assert feedback_tasks[0].priority == TaskPriority.URGENT

    def test_total_task_count(self, tasks):
        assert len(tasks) == 1


# ──────────────────────────────────────────────────────────────
# MILESTONE REVIEW
# ──────────────────────────────────────────────────────────────

class TestMilestoneReviewExtraction:
    """insights_milestone_review.yaml — meet-milestone-001, PROJ-CRM-0014"""

    @pytest.fixture
    def tasks(self):
        insights = load_yaml("insights_milestone_review.yaml")
        return extract_raw_tasks(insights, "PROJ-CRM-0014", "meet-milestone-001", "p-arjun-001")

    def test_rejected_deliverable_produces_rework_task(self, tasks):
        rework_tasks = [t for t in tasks if t.source_yaml_field == "milestone_review.sign_offs"]
        assert len(rework_tasks) == 1

    def test_accepted_deliverable_not_extracted(self, tasks):
        """requirements document was accepted — must not generate a task"""
        titles_lower = [t.title.lower() for t in tasks]
        assert not any("requirements document" in title for title in titles_lower)

    def test_architecture_rework_task(self, tasks):
        rework_tasks = [t for t in tasks if t.source_yaml_field == "milestone_review.sign_offs"]
        t = rework_tasks[0]
        assert "architecture" in t.title.lower() or "data flow" in t.title.lower() or "rework" in t.title.lower()
        assert t.assignee_id == "p-arjun-001"
        assert t.due_date == date(2025, 5, 12)
        assert t.priority == TaskPriority.HIGH

    def test_notes_contain_milestone_id(self, tasks):
        rework_tasks = [t for t in tasks if t.source_yaml_field == "milestone_review.sign_offs"]
        assert "M1" in (rework_tasks[0].notes or "")

    def test_total_task_count(self, tasks):
        assert len(tasks) == 1


# ──────────────────────────────────────────────────────────────
# CROSS-DEPT
# ──────────────────────────────────────────────────────────────

class TestCrossDeptExtraction:
    """insights_cross_dept.yaml — meet-crossdept-001, PROJ-CRM-0014"""

    @pytest.fixture
    def tasks(self):
        insights = load_yaml("insights_cross_dept.yaml")
        return extract_raw_tasks(insights, "PROJ-CRM-0014", "meet-crossdept-001", "p-arjun-001")

    def test_unresolved_rate_limiting_extracted(self, tasks):
        unresolved_tasks = [t for t in tasks if t.source_yaml_field == "cross_dept.unresolved_items"]
        assert len(unresolved_tasks) == 1
        t = unresolved_tasks[0]
        assert "rate limit" in t.title.lower() or "rate limiting" in t.title.lower()
        assert t.assignee_id == "p-arjun-001"
        assert t.due_date == date(2025, 5, 8)

    def test_total_task_count(self, tasks):
        assert len(tasks) == 1


# ──────────────────────────────────────────────────────────────
# COMPANY ALL-HANDS
# ──────────────────────────────────────────────────────────────

class TestAllHandsExtraction:
    """insights_company_allhands.yaml — no tasks (strategic only)"""

    def test_no_tasks_from_allhands(self):
        insights = load_yaml("insights_company_allhands.yaml")
        tasks = extract_raw_tasks(insights, "INTERNAL-COMPANY", "meet-allhands-001", "ceo")
        assert tasks == [], "company-allhands must produce zero tasks"


# ──────────────────────────────────────────────────────────────
# Cross-cutting: source fields and metadata
# ──────────────────────────────────────────────────────────────

class TestCrossCuttingMetadata:

    def test_all_tasks_have_source_iris(self):
        for filename in [
            "insights_standup.yaml",
            "insights_hr.yaml",
            "insights_client_call.yaml",
            "insights_vendor.yaml",
            "insights_sales_bd.yaml",
            "insights_sprint_planning.yaml",
            "insights_design_review.yaml",
            "insights_milestone_review.yaml",
            "insights_cross_dept.yaml",
        ]:
            insights = load_yaml(filename)
            tasks = extract_raw_tasks(
                insights,
                insights.get("project_id", "PROJ-TEST"),
                insights.get("meeting_id", "meet-test"),
                insights.get("organiser_id", "UNASSIGNED"),
            )
            for t in tasks:
                assert t.source == TaskSource.IRIS, f"{filename}: task '{t.title}' has wrong source"

    def test_all_tasks_have_nonempty_title(self):
        for filename in [
            "insights_standup.yaml",
            "insights_hr.yaml",
            "insights_client_call.yaml",
            "insights_vendor.yaml",
            "insights_sales_bd.yaml",
            "insights_sprint_planning.yaml",
            "insights_design_review.yaml",
            "insights_milestone_review.yaml",
            "insights_cross_dept.yaml",
        ]:
            insights = load_yaml(filename)
            tasks = extract_raw_tasks(
                insights,
                insights.get("project_id", "PROJ-TEST"),
                insights.get("meeting_id", "meet-test"),
                insights.get("organiser_id", "UNASSIGNED"),
            )
            for t in tasks:
                assert t.title.strip() != "", f"{filename}: extracted a task with empty title"

    def test_all_tasks_have_valid_priority(self):
        valid = {p.value for p in TaskPriority}
        for filename in [
            "insights_standup.yaml",
            "insights_hr.yaml",
            "insights_sales_bd.yaml",
            "insights_sprint_planning.yaml",
            "insights_design_review.yaml",
            "insights_milestone_review.yaml",
        ]:
            insights = load_yaml(filename)
            tasks = extract_raw_tasks(
                insights,
                insights.get("project_id", "PROJ-TEST"),
                insights.get("meeting_id", "meet-test"),
                insights.get("organiser_id", "UNASSIGNED"),
            )
            for t in tasks:
                assert t.priority.value in valid, f"{filename}: invalid priority {t.priority}"

    def test_project_id_always_matches_yaml(self):
        """project_id in extracted tasks must match the YAML file's project_id"""
        for filename in [
            "insights_standup.yaml",
            "insights_hr.yaml",
            "insights_client_call.yaml",
            "insights_vendor.yaml",
            "insights_sales_bd.yaml",
            "insights_sprint_planning.yaml",
            "insights_design_review.yaml",
            "insights_milestone_review.yaml",
            "insights_cross_dept.yaml",
        ]:
            insights = load_yaml(filename)
            expected_project = insights["project_id"]
            tasks = extract_raw_tasks(insights, "OVERRIDE", "meet-test", "UNASSIGNED")
            for t in tasks:
                assert t.project_id == expected_project, (
                    f"{filename}: task project_id='{t.project_id}' "
                    f"but YAML says '{expected_project}'"
                )
