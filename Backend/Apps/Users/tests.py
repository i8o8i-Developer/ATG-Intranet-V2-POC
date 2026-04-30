from datetime import date
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from Backend.Apps.Users.models import (
    BenchPeriod,
    Department,
    DepartmentMembership,
    EmployeePaymentSnapshot,
    EmployeeProfile,
    InterviewProgress,
    LeaveTransaction,
    PayProfile,
    Position,
    Skill,
    UserEffortReport,
    UserSkill,
)
from Backend.EnterpriseCore.models import BusinessUnit, Organization, OutboxEvent, Tenant, Workspace


class UsersModuleTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="users-admin", email="admin@example.com", password="test-password")
        self.employee_user = user_model.objects.create_user(username="employee", email="employee@example.com", password="test-password")
        self.tenant = Tenant.objects.create(name="Banao Users", slug="banao-users")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Banao Org", slug="banao-users-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="People", code="PEOPLE-USERS")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Default", code="USERS")
        self.department = Department.objects.create(tenant=self.tenant, workspace=self.workspace, name="Engineering", code="ENG")
        self.position = Position.objects.create(tenant=self.tenant, workspace=self.workspace, title="Intern", code="INTERN")
        self.employee = EmployeeProfile.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            user=self.employee_user,
            employee_code="EMP-001",
            display_name="Employee One",
            employment_type="Intern",
            position=self.position,
            joined_on=date.today(),
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.headers = {"HTTP_X_TENANT_ID": str(self.tenant.id), "HTTP_X_WORKSPACE_ID": str(self.workspace.id)}

    def test_department_transfer_assigns_default_skills(self):
        skill = Skill.objects.create(tenant=self.tenant, workspace=self.workspace, department=self.department, name="Django", category="Backend")

        response = self.client.post(
            f"/Users/EmployeeProfiles/{self.employee.id}/transfer-department/",
            {"department": self.department.id},
            format="json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(DepartmentMembership.objects.filter(tenant=self.tenant, employee=self.employee, department=self.department).exists())
        self.assertTrue(UserSkill.objects.filter(tenant=self.tenant, employee=self.employee, skill=skill, assigned_from_department=True).exists())

    def test_status_leave_resignation_and_dashboard_workflows(self):
        status_response = self.client.post(
            f"/Users/EmployeeProfiles/{self.employee.id}/change-status/",
            {"status": EmployeeProfile.STATUS_ON_BENCH, "reason": "Waiting for project"},
            format="json",
            **self.headers,
        )
        self.assertEqual(status_response.status_code, 200)
        self.assertTrue(BenchPeriod.objects.filter(tenant=self.tenant, employee=self.employee, ended_on__isnull=True).exists())

        reactivate_response = self.client.post(
            f"/Users/EmployeeProfiles/{self.employee.id}/change-status/",
            {"status": EmployeeProfile.STATUS_ACTIVE, "reason": "Assigned again"},
            format="json",
            **self.headers,
        )
        self.assertEqual(reactivate_response.status_code, 200)

        leave_response = self.client.post("/Users/LeaveBalances/accrue-all/", {"amount": "2.25"}, format="json", **self.headers)
        self.assertEqual(leave_response.status_code, 200)
        self.assertEqual(LeaveTransaction.objects.filter(tenant=self.tenant).count(), 1)

        resignation_response = self.client.post(
            "/Users/ResignationRequests/",
            {"employee": self.employee.id, "reason": "Moving on", "last_working_day": date.today().isoformat()},
            format="json",
            **self.headers,
        )
        self.assertEqual(resignation_response.status_code, 201)
        approve_response = self.client.post(
            f"/Users/ResignationRequests/{resignation_response.data['id']}/approve/",
            {"last_working_day": date.today().isoformat()},
            format="json",
            **self.headers,
        )
        self.assertEqual(approve_response.status_code, 200)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.status, EmployeeProfile.STATUS_EXITED)

        dashboard_response = self.client.get("/Users/EmployeeProfiles/dashboard/", **self.headers)
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(dashboard_response.data["headcount"], 1)

    def test_effort_interview_payment_and_command_entry_points(self):
        PayProfile.objects.create(tenant=self.tenant, workspace=self.workspace, employee=self.employee, pay_type="Fixed", base_pay=1000)
        effort_response = self.client.post(
            "/Users/UserEffortReports/submit/",
            {"employee": self.employee.id, "report_month": 4, "report_year": 2026, "effort_percent": "80.00", "project_reference": "ERP"},
            format="json",
            **self.headers,
        )
        self.assertEqual(effort_response.status_code, 201)
        self.assertEqual(UserEffortReport.objects.filter(tenant=self.tenant).count(), 1)

        interview_response = self.client.post(
            "/Users/InterviewProgress/sync-interns/",
            {"employee": self.employee.id, "dry_run": True},
            format="json",
            **self.headers,
        )
        self.assertEqual(interview_response.status_code, 200)
        self.assertEqual(interview_response.data["count"], 1)
        self.assertTrue(InterviewProgress.objects.filter(tenant=self.tenant, employee=self.employee).exists())

        EmployeePaymentSnapshot.objects.create(tenant=self.tenant, workspace=self.workspace, employee=self.employee, month=4, year=2026, payout_id="pout_1")
        payment_response = self.client.post("/Users/EmployeePaymentSnapshots/request-status-sync/", {}, format="json", **self.headers)
        self.assertEqual(payment_response.status_code, 200)
        self.assertEqual(payment_response.data["count"], 1)

        for command in [
            "assign",
            "update_leaves_wallet",
            "send_effort_report_notifications",
            "send_daily_activity_notifications",
            "sync_intern_interviews",
            "sync_payments",
        ]:
            output = StringIO()
            call_command(command, "--tenant-id", str(self.tenant.id), "--workspace-id", str(self.workspace.id), stdout=output)
            self.assertTrue(output.getvalue())

        self.assertTrue(OutboxEvent.objects.filter(tenant=self.tenant).exists())
