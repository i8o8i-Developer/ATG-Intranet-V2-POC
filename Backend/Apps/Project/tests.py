from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from Backend.Apps.Project.models import ComplianceAssignment, DeliveryDocument, DeliveryMilestone, ProjectWorkspace, RepositoryLink, TeamAssignment
from Backend.Apps.Project.services import ProjectDeliveryService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class ProjectModuleTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Project Tenant", slug="project-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="project-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Delivery", code="PROJ")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Project", code="PROJ")
        self.user = get_user_model().objects.create_user(username="project-user", email="project@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="PROJ-1", display_name="Project User")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.project = ProjectWorkspace.objects.create(tenant=self.tenant, workspace=self.workspace, name="ERP", code="ERP", project_type="Build", terms_required=True, anti_phishing_enabled=True)

    def test_project_delivery_repo_document_and_compliance_flow(self):
        milestones = ProjectDeliveryService.create_default_checkpoints(self.context, self.project.id)
        self.assertGreater(milestones.data["count"], 0)
        milestone = DeliveryMilestone.objects.filter(project=self.project).first()
        milestone.due_on = timezone.localdate() - timezone.timedelta(days=1)
        milestone.save(update_fields=["due_on"])
        health = ProjectDeliveryService.calculate_health(self.context, self.project.id)
        self.assertEqual(health.data["health"], "Escalated")
        member = ProjectDeliveryService.add_team_member(self.context, self.project.id, self.employee.id, role="Developer")
        self.assertTrue(TeamAssignment.objects.filter(id=member.data.id).exists())
        terms = ProjectDeliveryService.accept_terms(self.context, member.data.id)
        self.assertIsNotNone(terms.data.terms_accepted_at)
        repo = ProjectDeliveryService.create_repository_link(self.context, self.project.id, "erp", owner="atgworld")
        self.assertTrue(RepositoryLink.objects.filter(id=repo.data.id).exists())
        document = ProjectDeliveryService.record_document(self.context, self.project.id, "Spec", file_id="doc-1")
        pinned = ProjectDeliveryService.pin_document(self.context, document.data.id)
        self.assertTrue(DeliveryDocument.objects.get(id=pinned.data.id).is_pinned)
        campaign = ProjectDeliveryService.launch_compliance_campaign(self.context, self.project.id)
        assignment = ComplianceAssignment.objects.get(id=campaign.data["assignmentIds"][0])
        completed = ProjectDeliveryService.complete_compliance_assignment(self.context, assignment.id, score=90)
        self.assertEqual(completed.data.status, "Completed")