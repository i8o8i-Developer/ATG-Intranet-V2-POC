from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from Backend.Apps.FinanceAndPayroll.models import PaymentOrder, PayoutExecution
from Backend.Apps.FinanceAndPayroll.services import PaymentOrderService, PayrollCalculationService, PayoutService
from Backend.Apps.Users.models import EmployeePaymentSnapshot, EmployeeProfile, PayProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class FinanceAndPayrollServiceTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant", slug="tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Finance", code="FIN")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Main", code="FIN")
        self.user = get_user_model().objects.create_user(username="finance-user", email="finance@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="FIN-1", display_name="Finance User")
        PayProfile.objects.create(tenant=self.tenant, workspace=self.workspace, employee=self.employee, base_pay=Decimal("1000.00"), pay_per_task=Decimal("10.00"))
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)

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
