from django.contrib.auth import get_user_model
from django.test import TestCase

from Backend.Apps.L3.models import CollegeAssignment, CollegeEmailTemplate, CollegePipelineRecord, TalentEmail
from Backend.Apps.L3.services import TalentPipelineService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class L3ModuleTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="L3 Tenant", slug="l3-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="l3-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Talent", code="L3")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="L3", code="L3")
        self.user = get_user_model().objects.create_user(username="l3-user", email="l3@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="L3-1", display_name="L3 User")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)

    def test_college_assignment_email_and_summary(self):
        imported = TalentPipelineService.import_colleges(self.context, [{"college_name": "ATG College", "email": "tpo@example.com"}])
        self.assertTrue(imported.ok)
        college = CollegePipelineRecord.objects.get(tenant=self.tenant)
        assigned = TalentPipelineService.assign_colleges(self.context, self.employee.id, college_ids=[college.id])
        self.assertEqual(assigned.data["count"], 1)
        assignment = CollegeAssignment.objects.get(tenant=self.tenant)
        template = CollegeEmailTemplate.objects.create(tenant=self.tenant, workspace=self.workspace, name="Invite", subject="Hi", body_text="Hello")
        emailed = TalentPipelineService.send_college_email(self.context, college.id, template_id=template.id, assignment_id=assignment.id)
        self.assertTrue(emailed.ok)
        self.assertEqual(TalentEmail.objects.get().status, "Queued")
        updated = TalentPipelineService.update_workflow_status(self.context, assignment_id=assignment.id, workflow_status="Data received")
        self.assertEqual(updated.data.workflow_status, "Data received")
        summary = TalentPipelineService.performance_summary(self.context, self.employee.id)
        self.assertEqual(summary.data["emailCount"], 1)