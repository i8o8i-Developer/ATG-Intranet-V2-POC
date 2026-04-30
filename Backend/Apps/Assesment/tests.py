from datetime import date, timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from Backend.Apps.Assesment.models import AssessmentActivity, AssessmentAssignment, AssessmentSubmission, AssessmentTemplate
from Backend.Apps.Users.models import Department, EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, OutboxEvent, Tenant, Workspace


class AssessmentModuleTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="assessment-admin", email="admin@example.com", password="test-password")
        self.employee_user = user_model.objects.create_user(username="intern", email="intern@example.com", password="test-password")
        self.tenant = Tenant.objects.create(name="Banao", slug="banao-assessment")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Banao Org", slug="banao-org-assessment")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="People", code="PEOPLE")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Default", code="ASSESS")
        self.department = Department.objects.create(tenant=self.tenant, workspace=self.workspace, name="Frontend", code="FE")
        self.employee = EmployeeProfile.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            user=self.employee_user,
            employee_code="INT-001",
            display_name="Intern One",
            department=self.department,
            joined_on=date.today() - timedelta(days=21),
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.headers = {
            "HTTP_X_TENANT_ID": str(self.tenant.id),
            "HTTP_X_WORKSPACE_ID": str(self.workspace.id),
        }

    def create_template(self, title="Django Basics", passing_score=70):
        return AssessmentTemplate.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            department=self.department,
            title=title,
            assessment_type="Skill",
            status=AssessmentTemplate.STATUS_ACTIVE,
            passing_score=passing_score,
            provider_template_id=f"provider-{title.lower().replace(' ', '-')}",
        )

    def test_template_sequence_is_department_scoped(self):
        first = self.create_template("HTML")
        second = self.create_template("CSS")

        self.assertEqual(first.sequence_number, 1)
        self.assertEqual(second.sequence_number, 2)
        self.assertEqual(first.code, "ASSESS-FE-1")

    def test_assign_start_submit_and_dashboard(self):
        template = self.create_template()

        assign_response = self.client.post(
            f"/Assesment/AssessmentTemplates/{template.id}/assign/",
            {"employee": self.employee.id, "due_at": (timezone.now() + timedelta(days=3)).isoformat()},
            format="json",
            **self.headers,
        )
        self.assertEqual(assign_response.status_code, 201)
        assignment_id = assign_response.data["id"]
        self.assertTrue(OutboxEvent.objects.filter(tenant=self.tenant, event_type="AssessmentAssigned").exists())

        start_response = self.client.post(f"/Assesment/AssessmentAssignments/{assignment_id}/start/", {}, format="json", **self.headers)
        self.assertEqual(start_response.status_code, 200)
        self.assertEqual(start_response.data["status"], AssessmentAssignment.STATUS_IN_PROGRESS)

        submit_response = self.client.post(
            f"/Assesment/AssessmentAssignments/{assignment_id}/submit/",
            {"score": "82.00", "answer_payload": {"answers": ["a"]}},
            format="json",
            **self.headers,
        )
        self.assertEqual(submit_response.status_code, 201)
        self.assertEqual(AssessmentSubmission.objects.filter(assignment_id=assignment_id, passed=True).count(), 1)

        assignment = AssessmentAssignment.objects.get(id=assignment_id)
        self.assertEqual(assignment.status, AssessmentAssignment.STATUS_PASSED)
        self.assertEqual(assignment.note, "Completed")

        dashboard_response = self.client.get("/Assesment/AssessmentAssignments/dashboard/", **self.headers)
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(dashboard_response.data[0]["employee_name"], "Intern One")
        self.assertEqual(dashboard_response.data[0]["assessments"][0]["status"], AssessmentAssignment.STATUS_PASSED)

    def test_provider_status_sync_and_auto_assign_next(self):
        first_template = self.create_template("Week One")
        second_template = self.create_template("Week Two")
        assignment = AssessmentAssignment.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            assessment=first_template,
            employee=self.employee,
        )

        sync_response = self.client.post(
            f"/Assesment/AssessmentAssignments/{assignment.id}/sync-provider-status/",
            {"provider_payload": {"attempts": [{"score_details": {"total_percentage": 88}}]}},
            format="json",
            **self.headers,
        )
        self.assertEqual(sync_response.status_code, 200)
        self.assertEqual(sync_response.data["status"], AssessmentAssignment.STATUS_PASSED)

        auto_assign_response = self.client.post(
            "/Assesment/AssessmentAssignments/auto-assign-next/",
            {"employee": self.employee.id},
            format="json",
            **self.headers,
        )
        self.assertEqual(auto_assign_response.status_code, 201)
        self.assertEqual(auto_assign_response.data["assessment"], second_template.id)

    def test_provider_link_can_be_recorded_without_calling_external_service(self):
        template = self.create_template()
        assignment = AssessmentAssignment.objects.create(tenant=self.tenant, workspace=self.workspace, assessment=template, employee=self.employee)

        response = self.client.post(
            f"/Assesment/AssessmentAssignments/{assignment.id}/record-provider-link/",
            {
                "external_user_id": "external-1",
                "assessment_url": "https://assessments.example.test/take/external-1",
                "provider_payload": {"source": "test"},
            },
            format="json",
            **self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["external_user_id"], "external-1")
        self.assertEqual(response.data["status"], AssessmentAssignment.STATUS_LINK_GENERATED)

    def test_overdue_listing_and_reminder_creation(self):
        template = self.create_template()
        assignment = AssessmentAssignment.objects.create(tenant=self.tenant, workspace=self.workspace, assessment=template, employee=self.employee)
        assignment.assigned_at = timezone.now() - timedelta(days=7)
        assignment.save(update_fields=["assigned_at"])

        overdue_response = self.client.get("/Assesment/AssessmentAssignments/overdue/", **self.headers)
        self.assertEqual(overdue_response.status_code, 200)
        self.assertEqual(len(overdue_response.data), 1)

        reminder_response = self.client.post(
            "/Assesment/AssessmentAssignments/create-overdue-reminders/",
            {"grace_days": 5},
            format="json",
            **self.headers,
        )
        self.assertEqual(reminder_response.status_code, 200)
        self.assertEqual(reminder_response.data["count"], 1)
        self.assertTrue(AssessmentActivity.objects.filter(activity_type="ReminderCreated", assignment=assignment).exists())
        self.assertTrue(OutboxEvent.objects.filter(event_type="AssessmentReminderCreated", aggregate_id=str(assignment.id)).exists())

    def test_assignment_list_is_tenant_isolated(self):
        template = self.create_template()
        AssessmentAssignment.objects.create(tenant=self.tenant, workspace=self.workspace, assessment=template, employee=self.employee)
        other_tenant = Tenant.objects.create(name="Other", slug="other-assessment")
        other_org = Organization.objects.create(tenant=other_tenant, name="Other Org", slug="other-org-assessment")
        other_bu = BusinessUnit.objects.create(tenant=other_tenant, organization=other_org, name="Other", code="OTHER")
        other_workspace = Workspace.objects.create(tenant=other_tenant, business_unit=other_bu, name="Other", code="OTHER")

        response = self.client.get(
            "/Assesment/AssessmentAssignments/",
            HTTP_X_TENANT_ID=str(other_tenant.id),
            HTTP_X_WORKSPACE_ID=str(other_workspace.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_run_assessment_check_command_auto_assigns_next(self):
        first_template = self.create_template("Week One")
        second_template = self.create_template("Week Two")
        AssessmentAssignment.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            assessment=first_template,
            employee=self.employee,
            status=AssessmentAssignment.STATUS_PASSED,
            is_pass=True,
        )

        output = StringIO()
        call_command(
            "run_assessment_check",
            "--tenant-id",
            str(self.tenant.id),
            "--workspace-id",
            str(self.workspace.id),
            stdout=output,
        )

        self.assertIn("Assessment check completed successfully", output.getvalue())
        self.assertTrue(AssessmentAssignment.objects.filter(tenant=self.tenant, employee=self.employee, assessment=second_template).exists())
