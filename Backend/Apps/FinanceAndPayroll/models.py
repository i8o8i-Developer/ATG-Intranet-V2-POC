from django.db import models

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class CompensationPlan(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="compensation_plans")
    plan_name = models.CharField(max_length=160)
    base_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default="INR")
    frequency = models.CharField(max_length=80, default="Monthly")
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)
    component_payload = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["tenant_id", "employee_id", "-starts_on"]


class BankAccount(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="bank_accounts")
    account_holder_name = models.CharField(max_length=180)
    bank_name = models.CharField(max_length=180, blank=True)
    masked_account_number = models.CharField(max_length=80)
    ifsc_code = models.CharField(max_length=40, blank=True)
    verification_status = models.CharField(max_length=80, default="Unverified", db_index=True)
    secret_reference = models.CharField(max_length=240, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class PayPeriod(TenantScopedModel):
    name = models.CharField(max_length=120)
    starts_on = models.DateField()
    ends_on = models.DateField()
    status = models.CharField(max_length=80, default="Open", db_index=True)

    class Meta:
        ordering = ["tenant_id", "-starts_on"]
        constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="finance_pay_period_name_per_tenant")]


class PayrollRun(TenantScopedModel):
    pay_period = models.ForeignKey("FinanceAndPayroll.PayPeriod", on_delete=models.PROTECT, related_name="payroll_runs")
    status = models.CharField(max_length=80, default="Draft", db_index=True)
    gross_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    deduction_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default="INR")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class PayrollLineItem(TenantScopedModel):
    payroll_run = models.ForeignKey("FinanceAndPayroll.PayrollRun", on_delete=models.CASCADE, related_name="line_items")
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="payroll_line_items")
    gross_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    deduction_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=80, default="Draft", db_index=True)
    component_payload = models.JSONField(default=list, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "payroll_run", "employee", "status"])]


class ApprovalDecision(TenantScopedModel):
    resource_type = models.CharField(max_length=120, db_index=True)
    resource_id = models.CharField(max_length=120, db_index=True)
    decision = models.CharField(max_length=80, db_index=True)
    decided_by = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="finance_approval_decisions")
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class PayoutExecution(TenantScopedModel, ExternalReference):
    payroll_run = models.ForeignKey("FinanceAndPayroll.PayrollRun", null=True, blank=True, on_delete=models.PROTECT, related_name="payout_executions")
    provider = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=80, default="Queued", db_index=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default="INR")
    response_payload = models.JSONField(default=dict, blank=True)


class PayslipDocument(TenantScopedModel, ExternalReference):
    payroll_line_item = models.ForeignKey("FinanceAndPayroll.PayrollLineItem", on_delete=models.PROTECT, related_name="payslip_documents")
    storage_reference = models.CharField(max_length=260, blank=True)
    status = models.CharField(max_length=80, default="Generated", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)


class PaymentOrder(TenantScopedModel, ExternalReference):
    provider = models.CharField(max_length=100, default="Razorpay", db_index=True)
    employee = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.PROTECT, related_name="finance_payment_orders")
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default="INR")
    status = models.CharField(max_length=80, default="Created", db_index=True)
    provider_order_id = models.CharField(max_length=180, blank=True, db_index=True)
    provider_payment_id = models.CharField(max_length=180, blank=True, db_index=True)
    provider_signature = models.CharField(max_length=260, blank=True)
    receipt = models.CharField(max_length=180, blank=True)
    notes = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class PaymentWebhookEvent(TenantScopedModel):
    provider = models.CharField(max_length=100, default="Razorpay", db_index=True)
    event_type = models.CharField(max_length=180, db_index=True)
    external_event_id = models.CharField(max_length=180, blank=True, db_index=True)
    signature = models.CharField(max_length=260, blank=True)
    verified = models.BooleanField(default=False, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]
