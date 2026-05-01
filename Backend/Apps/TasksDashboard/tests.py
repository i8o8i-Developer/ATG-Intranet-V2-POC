from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from Backend.Apps.Project.models import ProjectWorkspace, TeamAssignment
from Backend.Apps.TasksDashboard.models import ClickUpProjectMapping, DailyStatusEntry, ExternalWorkMapping, ManagerAbbreviation, SlackDeliveryMessage, SlackDeliveryThread, WorkItem
from Backend.Apps.TasksDashboard.services import ClickUpSyncService, EODService, ManagerAbbreviationService, WorkManagementService
from Backend.Apps.TasksDashboard.services.slack_eod import SlackEODService
from Backend.Apps.Users.models import Department, EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class TasksDashboardTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tasks Tenant", slug="tasks-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="tasks-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Delivery", code="TASK")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Tasks", code="TASK")
        self.user = get_user_model().objects.create_user(username="tasks-user", email="tasks@example.com")
        self.manager_user = get_user_model().objects.create_user(username="tasks-manager", email="tasks-manager@example.com")
        self.department = Department.objects.create(tenant=self.tenant, workspace=self.workspace, name="Engineering", code="ENG")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="TASK-1", display_name="Tasks User", department=self.department)
        self.manager_employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.manager_user, employee_code="TASK-2", display_name="Tasks Manager", department=self.department)
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.project = ProjectWorkspace.objects.create(tenant=self.tenant, workspace=self.workspace, name="ERP", code="TASKERP", project_type="Delivery")
        TeamAssignment.objects.create(tenant=self.tenant, workspace=self.workspace, project=self.project, employee=self.manager_employee, role="Project Manager")
        self.client = APIClient()

    def test_task_eod_clickup_and_abbreviation_flow(self):
        created = WorkManagementService.create_work_item(self.context, "Build dashboard", project_id=self.project.id, owner_id=self.employee.id, bounty=10)
        self.assertTrue(created.ok)
        child = WorkManagementService.create_work_item(self.context, "Subtask", project_id=self.project.id, owner_id=self.employee.id, parent_id=created.data.id)
        self.assertEqual(WorkItem.objects.get(id=child.data.id).parent_id, created.data.id)
        timer = WorkManagementService.initialize_timer(self.context, created.data.id)
        self.assertIsNotNone(timer.data.timer_started_at)
        transitioned = WorkManagementService.transition_work_item(self.context, created.data.id, "Completed")
        self.assertIsNotNone(transitioned.data.completed_at)
        WorkManagementService.log_work_entry(self.context, created.data.id, self.employee.id, minutes=30)
        status = EODService.submit_status(self.context, self.employee.id, summary="Done", status_date=timezone.localdate())
        self.assertTrue(DailyStatusEntry.objects.filter(id=status.data.id).exists())
        delivered = EODService.deliver_daily_summary(self.context, channel_name="eng-eod")
        self.assertEqual(delivered.data["count"], 1)
        self.assertTrue(SlackDeliveryMessage.objects.exists())
        mapping = ClickUpProjectMapping.objects.create(tenant=self.tenant, workspace=self.workspace, project=self.project, project_name="ERP", external_id="space-1")
        synced = ClickUpSyncService.sync_tasks(self.context, [{"id": "cu-1", "name": "ClickUp task", "status": "open"}], project_mapping_id=mapping.id)
        self.assertEqual(synced.data["count"], 1)
        self.assertTrue(ExternalWorkMapping.objects.filter(external_id="cu-1").exists())
        abbreviation = ManagerAbbreviationService.generate(self.context, self.employee)
        self.assertTrue(ManagerAbbreviation.objects.filter(id=abbreviation.data.id).exists())

    def test_slack_eod_service_syncs_user_report_and_summary_in_dry_run(self):
        self.employee.department.metadata = {"slack_channel_id": "C-DEMO", "slack_channel_name": "eng-eod"}
        self.employee.department.save(update_fields=["metadata", "updated_at"])
        work_item = WorkItem.objects.create(tenant=self.tenant, workspace=self.workspace, project=self.project, owner=self.employee, title="Ship EOD")
        WorkManagementService.log_work_entry(self.context, work_item.id, self.employee.id, minutes=45, summary="Implemented EOD sync")
        DailyStatusEntry.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            status_date=timezone.localdate(),
            summary="Completed Slack EOD parity",
            blockers="None",
            next_plan="Run tests",
        )

        service = SlackEODService(self.context, live=False)
        message = service.sync_user_report(self.employee, timezone.localdate())
        self.assertEqual(message.status, "DryRun")
        self.assertTrue(message.slack_message_ts.startswith("dry-"))
        self.assertTrue(SlackDeliveryThread.objects.filter(tenant=self.tenant, channel_id="C-DEMO").exists())

        summary = service.send_department_daily_summary(status_date=timezone.localdate(), channel_name="eng-eod")
        self.assertTrue(summary.ok)
        self.assertGreaterEqual(summary.data["count"], 1)

    def test_tasks_dashboard_legacy_routes(self):
        self.client.force_authenticate(self.user)
        overdue = WorkItem.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            project=self.project,
            owner=self.employee,
            title="Overdue task",
            due_at=timezone.now() - timezone.timedelta(days=1),
        )
        today_item = WorkItem.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            project=self.project,
            owner=self.employee,
            title="Today task",
            due_at=timezone.now(),
        )
        WorkItem.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            project=self.project,
            owner=self.employee,
            title="No due task",
        )
        DailyStatusEntry.objects.create(tenant=self.tenant, workspace=self.workspace, employee=self.employee, status_date=timezone.localdate(), summary="Done")

        dashboard = self.client.get("/TasksDashboard/dashboard/Delivery/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(len(dashboard.data["tasks"]), 3)

        filtered = self.client.post(
            "/TasksDashboard/dashboard/Delivery/",
            {"projects": ["ERP"], "overdue_managers": [self.manager_employee.id]},
            format="json",
        )
        self.assertEqual(filtered.status_code, 200)
        self.assertGreaterEqual(len(filtered.data["tasks_overdue"]), 1)

        update_clickup = self.client.post(
            "/TasksDashboard/update_clickup/",
            {"tasks": [{"id": "cu-legacy", "name": "ClickUp sync task", "status": "Open"}]},
            format="json",
        )
        self.assertEqual(update_clickup.status_code, 200)
        task_id = update_clickup.data["task_id"]

        check_status = self.client.get(f"/TasksDashboard/check_task_status/{task_id}/")
        self.assertEqual(check_status.status_code, 200)
        self.assertEqual(check_status.data["status"], "completed")

        log_update = self.client.get("/TasksDashboard/check-log-update/")
        self.assertEqual(log_update.status_code, 200)
        self.assertEqual(log_update.data["status"], "UPDATED")

        init_timer = self.client.get("/TasksDashboard/initialize-timer/")
        self.assertEqual(init_timer.status_code, 200)
        self.assertEqual(init_timer.data["minutes"], "0")

        overdue.order_index = 10
        overdue.save(update_fields=["order_index", "updated_at"])
        today_item.order_index = 5
        today_item.save(update_fields=["order_index", "updated_at"])
        reorder = self.client.post("/TasksDashboard/reorder-tasks/", {}, format="json")
        self.assertEqual(reorder.status_code, 200)

        activity = self.client.post("/TasksDashboard/activity/", {}, format="json")
        self.assertEqual(activity.status_code, 200)
        self.assertEqual(activity.data["status"], "success")

        eod_report = self.client.get(f"/TasksDashboard/api/eod-report/?user={self.employee.id}&filter=last_7_days")
        self.assertEqual(eod_report.status_code, 200)
        self.assertEqual(eod_report.data["count"], 1)