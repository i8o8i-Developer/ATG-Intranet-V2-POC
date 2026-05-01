from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from Backend.Apps.Users.models import EmployeeProfile
from Backend.Apps.WorkflowIntelligence.models import BusinessWorkflowMap, RouteUsageAggregate, WorkflowReport
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class WorkflowIntelligenceTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Workflow Tenant", slug="workflow-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="workflow-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Ops", code="WF")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Workflow", code="WF")
        self.user = get_user_model().objects.create_user(username="workflow-user", email="workflow@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="WF-1", display_name="Workflow User")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.client = APIClient()

        RouteUsageAggregate.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            route_name="lead_list",
            route_pattern="api/leads/",
            workflow_name="Revenue Operations",
            username="tamanna",
            usage_date=timezone.localdate(),
            hit_count=25,
            last_hit_at=timezone.now(),
        )
        RouteUsageAggregate.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            route_name="project_dashboard",
            route_pattern="project/dashboard/<id>/",
            workflow_name="Projects And Delivery",
            username="faraz",
            usage_date=timezone.localdate(),
            hit_count=40,
            last_hit_at=timezone.now(),
        )
        BusinessWorkflowMap.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            workflow_name="Projects And Delivery",
            owning_module="Project",
            route_patterns=["project/dashboard/<id>/"],
        )

    def test_workflow_intelligence_legacy_routes(self):
        self.client.force_authenticate(self.user)

        summary = self.client.get("/WorkflowIntelligence/api/route-usage/summary/")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(len(summary.data), 2)

        top = self.client.get("/WorkflowIntelligence/api/route-usage/top-workflows/")
        self.assertEqual(top.status_code, 200)
        self.assertEqual(top.data[0]["workflow_name"], "Projects And Delivery")

        generated = self.client.post(
            "/WorkflowIntelligence/api/workflow-reports/generate/",
            {"title": "Weekly Workflow Report", "report_type": "Weekly"},
            format="json",
        )
        self.assertEqual(generated.status_code, 201)
        self.assertTrue(WorkflowReport.objects.filter(tenant=self.tenant, title="Weekly Workflow Report").exists())

        workflows = self.client.get("/WorkflowIntelligence/api/business-workflows/")
        self.assertEqual(workflows.status_code, 200)
        self.assertEqual(len(workflows.data), 1)