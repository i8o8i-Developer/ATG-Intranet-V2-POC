from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from Backend.Apps.FinanceAndPayroll.models import BankAccount, PaymentOrder, PayoutExecution
from Backend.Apps.FinanceAndPayroll.services import PaymentOrderService, PayrollCalculationService, PayoutService
from Backend.Apps.Project.models import DeliveryMilestone, ProjectWorkspace, TeamAssignment
from Backend.Apps.Users.models import Department, Domain, EmployeeBankAccount, EmployeePaymentSnapshot, EmployeeProfile, PayProfile, UserEffortReport
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class FinanceAndPayrollServiceTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant", slug="tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Finance", code="FIN")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Main", code="FIN")
        self.user = get_user_model().objects.create_user(username="finance-user", email="finance@example.com")
        self.domain = Domain.objects.create(tenant=self.tenant, workspace=self.workspace, name="Finance", code="FIN")
        self.banao_domain = Domain.objects.create(tenant=self.tenant, workspace=self.workspace, name="Banao", code="BANAO")
        self.department = Department.objects.create(tenant=self.tenant, workspace=self.workspace, name="Finance", code="FINANCE", domain=self.domain)
        self.banao_department = Department.objects.create(tenant=self.tenant, workspace=self.workspace, name="Banao Finance", code="BANAO-FIN", domain=self.banao_domain)
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="FIN-1", display_name="Finance User", department=self.department, employment_type="Full-Time")
        self.subordinate_user = get_user_model().objects.create_user(username="staff-user", email="staff@example.com")
        self.subordinate = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.subordinate_user, employee_code="FIN-2", display_name="Staff User", department=self.department, manager=self.employee, employment_type="Full-Time")
        self.banao_user = get_user_model().objects.create_user(username="banao-finance", email="banao@example.com")
        self.banao_employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.banao_user, employee_code="FIN-3", display_name="Banao Finance", department=self.banao_department, employment_type="Part-Time")
        PayProfile.objects.create(tenant=self.tenant, workspace=self.workspace, employee=self.employee, base_pay=Decimal("1000.00"), pay_per_task=Decimal("10.00"), pay_type="Fixed")
        PayProfile.objects.create(tenant=self.tenant, workspace=self.workspace, employee=self.subordinate, base_pay=Decimal("1200.00"), pay_per_task=Decimal("10.00"), pay_type="Fixed")
        PayProfile.objects.create(tenant=self.tenant, workspace=self.workspace, employee=self.banao_employee, base_pay=Decimal("700.00"), pay_per_task=Decimal("5.00"), pay_type="Performance Based")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.client = APIClient()

    def test_calculate_order_and_payout(self):
        calculation = PayrollCalculationService.calculate_for_employee(self.context, self.employee.id, month=1, year=2025)
        self.assertTrue(calculation.ok)
        self.assertEqual(calculation.data["netPay"], Decimal("1000.00"))

        order = PaymentOrderService.create_order(self.context, Decimal("99.00"), receipt="r-1")
        self.assertTrue(order.ok)
        self.assertTrue(PaymentOrder.objects.filter(receipt="r-1").exists())

        snapshot = EmployeePaymentSnapshot.objects.create(tenant=self.tenant, workspace=self.workspace, employee=self.employee, month=1, year=2025, normal_pay=Decimal("1000.00"))
        payout = PayoutService.request_employee_payout(self.context, snapshot.id, live=False)
        self.assertTrue(payout.ok)
        self.assertTrue(PayoutExecution.objects.filter(response_payload__paymentSnapshotId=snapshot.id).exists())

    def test_legacy_bankdetails_and_payment_approval_routes(self):
        self.client.force_authenticate(self.subordinate_user)
        bank_response = self.client.post(
            "/FinanceAndPayroll/Bankdetails/",
            {"Ac_No": "123456789012", "Ac_IFSC": "SBIN0000123", "upi": "staff@upi"},
            format="json",
        )
        self.assertEqual(bank_response.status_code, 201)
        self.assertTrue(EmployeeBankAccount.objects.filter(employee=self.subordinate).exists())
        self.assertTrue(BankAccount.objects.filter(employee=self.subordinate).exists())

        self.client.force_authenticate(self.user)
        manager_response = self.client.post(
            "/FinanceAndPayroll/payment-approval/",
            {
                "role": "Manager",
                "userid": self.subordinate_user.id,
                "show_month": 1,
                "show_year": 2025,
                "bonus": "100.00",
                "normalPay": "1200.00",
                "bugIds": "BUG-1,BUG-2",
                "bounty": "50.00",
                "taskCount": 4,
            },
            format="json",
        )
        self.assertEqual(manager_response.status_code, 200)
        snapshot = EmployeePaymentSnapshot.objects.get(employee=self.subordinate, month=1, year=2025)
        self.assertEqual(snapshot.manager_status, "Approved")

        finance_response = self.client.post(
            "/FinanceAndPayroll/new-payment-approval/",
            {
                "userid": self.subordinate_user.id,
                "show_month": 1,
                "show_year": 2025,
                "bonus": "100.00",
                "normalPay": "1200.00",
                "bounty": "50.00",
                "taskCount": 4,
                "payNote": "Monthly payroll",
            },
            format="json",
        )
        self.assertEqual(finance_response.status_code, 200)
        snapshot.refresh_from_db()
        self.assertEqual(snapshot.finance_status, "Approved")
        self.assertEqual(snapshot.payment_status, "Queued")
        self.assertTrue(snapshot.payout_id)

        listing = self.client.get("/FinanceAndPayroll/payment-approval/", {"show_month": 1, "show_year": 2025})
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data["filled_data"]), 1)
        self.assertGreaterEqual(len(listing.data["bank_data"]), 1)

    def test_legacy_dashboards_and_project_finances(self):
        EmployeePaymentSnapshot.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.subordinate,
            month=1,
            year=2025,
            normal_pay=Decimal("1200.00"),
            finance_status="Approved",
        )
        project = ProjectWorkspace.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            name="Client Portal",
            code="CP1",
            metadata={"budget": "5000.00"},
        )
        TeamAssignment.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            project=project,
            employee=self.subordinate,
            role="Developer",
            allocation_percent=100,
        )
        DeliveryMilestone.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            project=project,
            title="Build API",
            sequence=1,
            status="Completed",
            bounty=Decimal("10.00"),
        )
        DeliveryMilestone.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            project=project,
            title="Frontend polish",
            sequence=2,
            status="Open",
            bounty=Decimal("20.00"),
        )
        UserEffortReport.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.subordinate,
            project_reference=str(project.id),
            report_month=1,
            report_year=2025,
            effort_percent=Decimal("50.00"),
        )

        self.client.force_authenticate(self.user)
        manage = self.client.get("/FinanceAndPayroll/manage-payroll/", {"month_name": "January", "show_approved": "true"})
        self.assertEqual(manage.status_code, 200)
        self.assertTrue(manage.data["Manage_Payrolls"])
        self.assertEqual(manage.data["user_list"][0]["username"], "staff-user")

        finance = self.client.get("/FinanceAndPayroll/finance-department/", {"month_name": "January", "show_approved": "true"})
        self.assertEqual(finance.status_code, 200)
        self.assertTrue(finance.data["Finance_Department"])

        payments = self.client.get("/FinanceAndPayroll/payments/", {"month_name": "January", "show_approved": "true"})
        self.assertEqual(payments.status_code, 200)
        self.assertIn(2025, payments.data["years"])

        banao = self.client.get("/FinanceAndPayroll/banao-finance-department/")
        self.assertEqual(banao.status_code, 200)
        self.assertEqual(banao.data["departments"][0]["name"], "Banao Finance")

        project_finances = self.client.get("/FinanceAndPayroll/api/project-finances/", {"project_id": project.id})
        self.assertEqual(project_finances.status_code, 200)
        self.assertEqual(project_finances.data["project_name"], "Client Portal")
        self.assertEqual(project_finances.data["details"][0]["personnel"], "staff-user")

    def test_legacy_calculation_aliases(self):
        EmployeePaymentSnapshot.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            month=1,
            year=2025,
            normal_pay=Decimal("1000.00"),
            bonus=Decimal("25.00"),
            bounty=Decimal("10.00"),
        )
        self.client.force_authenticate(self.user)
        calculate = self.client.get("/FinanceAndPayroll/api/calculate-payroll/", {"employee": self.employee.id, "month": 1, "year": 2025})
        self.assertEqual(calculate.status_code, 200)
        self.assertEqual(calculate.data["data"]["employee"], self.employee.id)

        previous = self.client.get("/FinanceAndPayroll/api/previous-payment-data/", {"employee": self.employee.id})
        self.assertEqual(previous.status_code, 200)
        self.assertEqual(previous.data["data"][0]["year"], 2025)
