from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from Backend.Apps.Project.models import ProjectWorkspace
from Backend.Apps.TasksDashboard.models import ClickUpProjectMapping, DailyStatusEntry, ExternalWorkMapping, ManagerAbbreviation, SlackDeliveryMessage, WorkItem
from Backend.Apps.TasksDashboard.services import ClickUpSyncService, EODService, ManagerAbbreviationService, WorkManagementService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class TasksDashboardTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tasks Tenant", slug="tasks-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="tasks-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Delivery", code="TASK")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Tasks", code="TASK")
        self.user = get_user_model().objects.create_user(username="tasks-user", email="tasks@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="TASK-1", display_name="Tasks User")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.project = ProjectWorkspace.objects.create(tenant=self.tenant, workspace=self.workspace, name="ERP", code="TASKERP")

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