from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from Backend.Apps.Assesment.models import AssessmentAssignment, AssessmentTemplate
from Backend.Apps.AtgDocs.models import KnowledgeDocument
from Backend.Apps.Banao.models import LeadAccount
from Backend.Apps.FinanceAndPayroll.models import PayPeriod, PayrollLineItem, PayrollRun
from Backend.Apps.Git.models import GitRepositorySnapshot
from Backend.Apps.GithubExtension.models import GitHubRepository
from Backend.Apps.HtmlTemplate.models import ContentTemplate
from Backend.Apps.IntegrationHub.models import IntegrationConnection, IntegrationProvider
from Backend.Apps.L3.models import CandidateProfile, CollegePipelineRecord
from Backend.Apps.Lms.models import LearningAssignment, LearningPath
from Backend.Apps.MainApp.models import LeaveRequest, NotificationItem
from Backend.Apps.McpAccessLayer.models import AgentPrincipal, McpAccessGrant, McpToolDefinition
from Backend.Apps.Project.models import DeliveryAlert, DeliveryMilestone, ProjectWorkspace
from Backend.Apps.TasksDashboard.models import TaskActivity, WorkItem
from Backend.Apps.Users.models import EmployeeProfile, Skill, UserSkill
from Backend.Apps.WorkflowIntelligence.models import RouteUsageAggregate
from Backend.EnterpriseCore.models import BusinessUnit, Organization, OutboxEvent, Tenant, Workspace


class BackendEndToEndTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="operator", password="test-password")
        self.recipient = user_model.objects.create_user(username="recipient", password="test-password")
        self.tenant = Tenant.objects.create(name="Banao", slug="banao")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Banao Org", slug="banao-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Delivery", code="DEL")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Default", code="DEF")
        self.other_tenant = Tenant.objects.create(name="Other", slug="other")
        other_org = Organization.objects.create(tenant=self.other_tenant, name="Other Org", slug="other-org")
        other_bu = BusinessUnit.objects.create(tenant=self.other_tenant, organization=other_org, name="Other", code="OTH")
        self.other_workspace = Workspace.objects.create(tenant=self.other_tenant, business_unit=other_bu, name="Other", code="OTH")
        self.employee = EmployeeProfile.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            user=self.user,
            employee_code="EMP-001",
            display_name="Operator",
        )
        self.client = APIClient()
        self.headers = {
            "HTTP_X_TENANT_ID": str(self.tenant.id),
            "HTTP_X_WORKSPACE_ID": str(self.workspace.id),
        }

    def test_tenant_header_create_and_list_are_isolated(self):
        response = self.client.post(
            "/Users/Departments/",
            {"name": "Engineering", "code": "ENG"},
            format="json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["tenant"], self.tenant.id)
        self.assertEqual(response.data["workspace"], self.workspace.id)

        same_tenant_response = self.client.get("/Users/Departments/", **self.headers)
        self.assertEqual(same_tenant_response.status_code, 200)
        self.assertEqual(len(same_tenant_response.data), 1)

        other_tenant_response = self.client.get(
            "/Users/Departments/",
            HTTP_X_TENANT_ID=str(self.other_tenant.id),
            HTTP_X_WORKSPACE_ID=str(self.other_workspace.id),
        )
        self.assertEqual(other_tenant_response.status_code, 200)
        self.assertEqual(len(other_tenant_response.data), 0)

    def test_every_module_has_a_working_business_action(self):
        skill = Skill.objects.create(tenant=self.tenant, workspace=self.workspace, name="Django")
        activate_response = self.client.post(f"/Users/EmployeeProfiles/{self.employee.id}/activate/", {}, format="json", **self.headers)
        skill_response = self.client.post(
            f"/Users/EmployeeProfiles/{self.employee.id}/assign-skill/",
            {"skill": skill.id, "proficiency": 4},
            format="json",
            **self.headers,
        )
        self.assertEqual(activate_response.status_code, 200)
        self.assertEqual(skill_response.status_code, 200)
        self.assertTrue(UserSkill.objects.filter(tenant=self.tenant, employee=self.employee, skill=skill).exists())

        leave = LeaveRequest.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            leave_type="Casual",
            starts_on=date.today(),
            ends_on=date.today(),
        )
        leave_response = self.client.post(f"/MainApp/LeaveRequests/{leave.id}/approve/", {}, format="json", **self.headers)
        notify_response = self.client.post(
            "/MainApp/Notifications/send/",
            {"recipient": self.recipient.id, "title": "Hello"},
            format="json",
            **self.headers,
        )
        self.assertEqual(leave_response.data["status"], "Approved")
        self.assertEqual(notify_response.status_code, 201)
        self.assertTrue(NotificationItem.objects.filter(tenant=self.tenant, recipient=self.recipient).exists())

        project = ProjectWorkspace.objects.create(tenant=self.tenant, workspace=self.workspace, name="ERP", code="ERP")
        milestone = DeliveryMilestone.objects.create(tenant=self.tenant, workspace=self.workspace, project=project, title="M1")
        milestone_response = self.client.post(f"/Project/DeliveryMilestones/{milestone.id}/complete/", {}, format="json", **self.headers)
        alert_response = self.client.post(
            f"/Project/ProjectWorkspaces/{project.id}/raise-alert/",
            {"severity": "High", "title": "Scope risk"},
            format="json",
            **self.headers,
        )
        self.assertEqual(milestone_response.data["status"], "Completed")
        self.assertEqual(alert_response.status_code, 201)
        self.assertTrue(DeliveryAlert.objects.filter(tenant=self.tenant, project=project).exists())

        work_item = WorkItem.objects.create(tenant=self.tenant, workspace=self.workspace, project=project, owner=self.employee, title="Build API")
        work_response = self.client.post(
            f"/TasksDashboard/WorkItems/{work_item.id}/transition/",
            {"status": "InProgress", "message": "Started"},
            format="json",
            **self.headers,
        )
        self.assertEqual(work_response.data["status"], "InProgress")
        self.assertTrue(TaskActivity.objects.filter(tenant=self.tenant, work_item=work_item).exists())

        lead = LeadAccount.objects.create(tenant=self.tenant, workspace=self.workspace, company_name="Acme")
        lead_response = self.client.post(
            f"/Banao/LeadAccounts/{lead.id}/move-stage/",
            {"to_stage": "Proposal Sent", "reason": "Qualified"},
            format="json",
            **self.headers,
        )
        self.assertEqual(lead_response.data["stage"], "Proposal Sent")

        path = LearningPath.objects.create(tenant=self.tenant, workspace=self.workspace, title="AI Operator")
        learning_assignment = LearningAssignment.objects.create(tenant=self.tenant, workspace=self.workspace, path=path, employee=self.employee)
        learning_response = self.client.post(f"/Lms/LearningAssignments/{learning_assignment.id}/mark-complete/", {}, format="json", **self.headers)
        self.assertEqual(learning_response.data["status"], "Completed")

        document = KnowledgeDocument.objects.create(tenant=self.tenant, workspace=self.workspace, title="Runbook", slug="runbook")
        publish_response = self.client.post(f"/AtgDocs/KnowledgeDocuments/{document.id}/publish/", {}, format="json", **self.headers)
        self.assertEqual(publish_response.data["status"], "Published")

        assessment = AssessmentTemplate.objects.create(tenant=self.tenant, workspace=self.workspace, title="Django", assessment_type="Skill")
        assessment_assignment = AssessmentAssignment.objects.create(tenant=self.tenant, workspace=self.workspace, assessment=assessment, employee=self.employee)
        assessment_response = self.client.post(f"/Assesment/AssessmentAssignments/{assessment_assignment.id}/start/", {}, format="json", **self.headers)
        self.assertEqual(assessment_response.data["status"], "InProgress")

        college = CollegePipelineRecord.objects.create(tenant=self.tenant, workspace=self.workspace, college_name="Demo College")
        candidate = CandidateProfile.objects.create(tenant=self.tenant, workspace=self.workspace, college=college, full_name="Candidate")
        talent_response = self.client.post(
            f"/L3/CandidateProfiles/{candidate.id}/assign/",
            {"employee": self.employee.id, "assignment_type": "Review"},
            format="json",
            **self.headers,
        )
        self.assertEqual(talent_response.status_code, 201)

        github_repo = GitHubRepository.objects.create(tenant=self.tenant, workspace=self.workspace, owner="atgworld", name="intranet")
        branch_response = self.client.post(
            f"/GithubExtension/GitHubRepositories/{github_repo.id}/update-branch-status/",
            {"branch_name": "main", "review_status": "Ready", "testing_status": "Passed"},
            format="json",
            **self.headers,
        )
        self.assertEqual(branch_response.status_code, 200)

        git_repo = GitRepositorySnapshot.objects.create(tenant=self.tenant, workspace=self.workspace, repository_name="intranet")
        git_response = self.client.post(
            f"/Git/GitRepositorySnapshots/{git_repo.id}/queue-request/",
            {"request_type": "InspectRepository"},
            format="json",
            **self.headers,
        )
        self.assertEqual(git_response.status_code, 201)

        template = ContentTemplate.objects.create(tenant=self.tenant, workspace=self.workspace, name="Greeting", template_type="Email", body_text="Hello {{name}}")
        template_response = self.client.post(
            f"/HtmlTemplate/ContentTemplates/{template.id}/render/",
            {"variables": {"name": "Banao"}},
            format="json",
            **self.headers,
        )
        self.assertEqual(template_response.data["rendered"], "Hello Banao")

        RouteUsageAggregate.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            route_name="home",
            route_pattern="home/",
            workflow_name="PeopleOps",
            username="operator",
            usage_date=date.today(),
            hit_count=3,
            last_hit_at=timezone.now(),
        )
        workflow_response = self.client.get("/WorkflowIntelligence/RouteUsageAggregates/summary/", **self.headers)
        self.assertEqual(workflow_response.status_code, 200)
        self.assertEqual(workflow_response.data[0]["hit_count"], 3)

        pay_period = PayPeriod.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            name="Current",
            starts_on=date.today(),
            ends_on=date.today() + timedelta(days=30),
        )
        payroll_run = PayrollRun.objects.create(tenant=self.tenant, workspace=self.workspace, pay_period=pay_period)
        PayrollLineItem.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            payroll_run=payroll_run,
            employee=self.employee,
            gross_amount=100,
            deduction_amount=10,
            net_amount=90,
        )
        recalc_response = self.client.post(f"/FinanceAndPayroll/PayrollRuns/{payroll_run.id}/recalculate/", {}, format="json", **self.headers)
        submit_response = self.client.post(f"/FinanceAndPayroll/PayrollRuns/{payroll_run.id}/submit-for-approval/", {}, format="json", **self.headers)
        self.assertEqual(recalc_response.data["net_amount"], "90.00")
        self.assertEqual(submit_response.data["status"], "PendingApproval")

        provider = IntegrationProvider.objects.create(tenant=self.tenant, workspace=self.workspace, name="Slack", provider_type="Slack")
        connection = IntegrationConnection.objects.create(tenant=self.tenant, workspace=self.workspace, provider=provider, owner_module="TasksDashboard", name="Slack Workspace")
        sync_response = self.client.post(
            f"/IntegrationHub/IntegrationConnections/{connection.id}/queue-sync/",
            {"job_type": "ManualSync"},
            format="json",
            **self.headers,
        )
        attempt_response = self.client.post(
            f"/IntegrationHub/IntegrationConnections/{connection.id}/record-attempt/",
            {"operation": "SendMessage", "status": "Completed"},
            format="json",
            **self.headers,
        )
        self.assertEqual(sync_response.status_code, 201)
        self.assertEqual(attempt_response.status_code, 201)

        agent = AgentPrincipal.objects.create(tenant=self.tenant, workspace=self.workspace, name="Copilot", principal_key="copilot")
        tool = McpToolDefinition.objects.create(tenant=self.tenant, workspace=self.workspace, name="Project Summary", slug="project-summary", owning_module="Project")
        McpAccessGrant.objects.create(tenant=self.tenant, workspace=self.workspace, agent=agent, tool=tool, permission="Read")
        can_invoke_response = self.client.post(
            f"/McpAccessLayer/AgentPrincipals/{agent.id}/can-invoke/",
            {"tool": tool.id, "permission": "Read"},
            format="json",
            **self.headers,
        )
        audit_response = self.client.post(
            f"/McpAccessLayer/AgentPrincipals/{agent.id}/record-invocation/",
            {"tool": tool.id, "action": "project.summary", "decision": "Allowed"},
            format="json",
            **self.headers,
        )
        draft_response = self.client.post(
            f"/McpAccessLayer/AgentPrincipals/{agent.id}/draft-action/",
            {"action_type": "DraftProjectNote", "target_resource_type": "ProjectWorkspace", "target_resource_id": project.id},
            format="json",
            **self.headers,
        )
        self.assertEqual(can_invoke_response.data["allowed"], True)
        self.assertEqual(audit_response.status_code, 201)
        self.assertEqual(draft_response.status_code, 201)

        legacy_response = self.client.post("/LegacyBridge/LegacyApplicationMaps/seed-defaults/", {}, format="json", **self.headers)
        self.assertEqual(legacy_response.status_code, 200)
        self.assertGreaterEqual(legacy_response.data["count"], 1)
        self.assertTrue(OutboxEvent.objects.filter(tenant=self.tenant).exists())
