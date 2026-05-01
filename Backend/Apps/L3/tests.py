from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

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
        self.manager = get_user_model().objects.create_user(username="l3-manager", email="manager@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="L3-1", display_name="L3 User")
        self.manager_employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.manager, employee_code="L3-2", display_name="L3 Manager")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.client = APIClient()

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

    def test_l3_legacy_route_surface(self):
        self.client.force_authenticate(self.manager)
        imported = self.client.post(
            "/L3/dataentry/",
            {
                "rows": [
                    {"college_name": "ATG College", "email": "tpo@example.com", "phone": "1234567890"},
                    {"college_name": "Beta College", "email": "beta@example.com", "phone": "9876543210"},
                ]
            },
            format="json",
        )
        self.assertEqual(imported.status_code, 200)
        self.assertEqual(CollegePipelineRecord.objects.count(), 2)

        assigned = self.client.post("/L3/perform/l3-user", {"limit": 1}, format="json")
        self.assertEqual(assigned.status_code, 201)
        assignment = CollegeAssignment.objects.get(assigned_to=self.employee)

        self.client.force_authenticate(self.user)
        new_colleges = self.client.get("/L3/caller/new_colleges")
        self.assertEqual(new_colleges.status_code, 200)
        self.assertEqual(new_colleges.data["colleges_count"], 1)

        emailed = self.client.post(f"/L3/send_mail/{assignment.college_id}/legacy/{assignment.id}", {"subject": "Invite"}, format="json")
        self.assertEqual(emailed.status_code, 201)
        pending = self.client.get("/L3/caller/pending_colleges")
        self.assertEqual(pending.status_code, 200)
        self.assertEqual(pending.data["colleges_count"], 1)

        email_update = self.client.post(f"/L3/update_email/{assignment.college_id}/l3-user", {"email": "new@example.com"}, format="json")
        self.assertEqual(email_update.status_code, 200)
        contact_update = self.client.post(f"/L3/update_contact/{assignment.college_id}/{assignment.id}", {"phone": "1112223333"}, format="json")
        self.assertEqual(contact_update.status_code, 200)

        self.client.force_authenticate(self.manager)
        detail = self.client.get("/L3/manager/performance_detail/l3-user")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["intern"], "l3-user")

        hold = self.client.post("/L3/hold/l3-user/hold", {}, format="json")
        self.assertEqual(hold.status_code, 200)
        self.employee.refresh_from_db()
        self.assertTrue(self.employee.profile_payload["l3_is_paused"])

        performance_list = self.client.get("/L3/manager/performance_list/")
        self.assertEqual(performance_list.status_code, 200)
        self.assertIn("l3-user", performance_list.data["data"])

        analytics = self.client.get("/L3/manager/performance_analytics/")
        self.assertEqual(analytics.status_code, 200)
        self.assertIn("total_college", analytics.data)

        archived = self.client.post(f"/L3/archive_task/{assignment.id}/l3-user", {}, format="json")
        self.assertEqual(archived.status_code, 200)
        assignment.refresh_from_db()
        self.assertTrue(assignment.is_archived)