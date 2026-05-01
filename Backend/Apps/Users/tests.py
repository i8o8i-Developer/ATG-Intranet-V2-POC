from datetime import date
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.conf import settings
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
from Backend.Apps.Users.services import PayrollExportService
from Backend.EnterpriseCore.services import TenantContext
from Backend.EnterpriseCore.models import BusinessUnit, Capability, Organization, OutboxEvent, Role, RoleAssignment, RoleCapability, Tenant, Workspace


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

    def test_session_auth_returns_current_operator_context(self):
        capability = Capability.objects.create(code="Users.View", name="View users", module="Users")
        role = Role.objects.create(tenant=self.tenant, name="HR Operator", code="HR_OPERATOR")
        RoleCapability.objects.create(tenant=self.tenant, role=role, capability=capability)
        RoleAssignment.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.employee_user, role=role)

        session_client = APIClient()
        login_response = session_client.post(
            "/Users/Auth/Login/",
            {"username": "employee", "password": "test-password"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.data["activeTenant"]["id"], self.tenant.id)
        self.assertEqual(login_response.data["activeWorkspace"]["id"], self.workspace.id)
        self.assertIn("Users.View", login_response.data["capabilities"])
        self.assertEqual(login_response.data["employees"][0]["employeeCode"], "EMP-001")

        me_response = session_client.get("/Users/Auth/Me/", **self.headers)
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.data["user"]["username"], "employee")

        logout_response = session_client.post("/Users/Auth/Logout/", {}, format="json")
        self.assertEqual(logout_response.status_code, 200)
        protected_response = session_client.get("/Users/Departments/", **self.headers)
        self.assertIn(protected_response.status_code, [401, 403])

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

        setup_output = StringIO()
        call_command(
            "setup_interviewgod_test_data",
            "--tenant-id",
            str(self.tenant.id),
            "--workspace-id",
            str(self.workspace.id),
            "--count",
            "1",
            stdout=setup_output,
        )
        self.assertIn("Prepared", setup_output.getvalue())

        self.assertTrue(OutboxEvent.objects.filter(tenant=self.tenant).exists())

    @patch("Backend.Apps.Users.apis.generate_payroll_excel_task.delay")
    def test_payroll_export_and_timezone_legacy_endpoints(self, mock_delay):
        PayProfile.objects.create(tenant=self.tenant, workspace=self.workspace, employee=self.employee, pay_type="Fixed", base_pay=Decimal("1000.00"))
        EmployeePaymentSnapshot.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            month=4,
            year=2026,
            normal_pay=Decimal("1000.00"),
            bonus=Decimal("50.00"),
            deduction=Decimal("25.00"),
            bounty=Decimal("10.00"),
            payment_status="processed",
            utr_number="UTR-1",
        )
        UserEffortReport.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            report_month=4,
            report_year=2026,
            effort_percent=Decimal("80.00"),
        )

        context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user, source="Test")
        export_result = PayrollExportService.generate_excel(context, report_month=4, report_year=2026, pay_type="Fixed")
        self.assertTrue(export_result.ok)
        export_path = PayrollExportService.resolve_export_path(context, export_result.data["filename"])
        self.assertIsNotNone(export_path)
        self.assertTrue(export_path.exists())

        download_response = self.client.get(f"/Users/api/download-payroll/{export_result.data['filename']}/", **self.headers)
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(
            download_response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertFalse(export_path.exists())

        mock_delay.return_value = Mock(id="task-123")
        start_response = self.client.get("/Users/api/export-payroll-async/?month=4&year=2026&pay_type=Fixed", **self.headers)
        self.assertEqual(start_response.status_code, 202)
        self.assertEqual(start_response.data["task_id"], "task-123")

        timezone_client = APIClient()
        timezone_client.force_authenticate(self.employee_user)
        timezone_response = timezone_client.post(
            "/Users/api/save-timezone/",
            {"timezone": "Asia/Kolkata"},
            format="json",
            **self.headers,
        )
        self.assertEqual(timezone_response.status_code, 200)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.timezone_name, "Asia/Kolkata")
