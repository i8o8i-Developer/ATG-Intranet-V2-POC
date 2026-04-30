from django.contrib import admin

from Backend.Apps.FinanceAndPayroll.models import ApprovalDecision, BankAccount, CompensationPlan, PaymentOrder, PaymentWebhookEvent, PayPeriod, PayrollLineItem, PayrollRun, PayoutExecution, PayslipDocument


@admin.register(CompensationPlan)
class CompensationPlanAdmin(admin.ModelAdmin):
    list_display = ("employee", "plan_name", "base_amount", "frequency", "starts_on", "ends_on", "tenant")
    list_filter = ("frequency", "tenant")


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("employee", "account_holder_name", "ifsc_code", "verification_status", "tenant")
    list_filter = ("verification_status", "tenant")


@admin.register(PayPeriod)
class PayPeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "starts_on", "ends_on", "status", "tenant")
    list_filter = ("status", "tenant")


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ("pay_period", "status", "gross_amount", "net_amount", "tenant")
    list_filter = ("status", "tenant")


@admin.register(PayrollLineItem)
class PayrollLineItemAdmin(admin.ModelAdmin):
    list_display = ("payroll_run", "employee", "gross_amount", "net_amount", "status", "tenant")
    list_filter = ("status", "tenant")


@admin.register(ApprovalDecision)
class ApprovalDecisionAdmin(admin.ModelAdmin):
    list_display = ("resource_type", "resource_id", "decision", "decided_by", "tenant")
    list_filter = ("decision", "tenant")


@admin.register(PayoutExecution)
class PayoutExecutionAdmin(admin.ModelAdmin):
    list_display = ("payroll_run", "provider", "status", "amount", "external_id", "tenant")
    list_filter = ("provider", "status", "tenant")


@admin.register(PayslipDocument)
class PayslipDocumentAdmin(admin.ModelAdmin):
    list_display = ("payroll_line_item", "status", "storage_reference", "tenant")
    list_filter = ("status", "tenant")


@admin.register(PaymentOrder)
class PaymentOrderAdmin(admin.ModelAdmin):
    list_display = ("provider", "employee", "amount", "status", "provider_order_id", "tenant")
    list_filter = ("provider", "status", "tenant")


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_type", "verified", "processed_at", "tenant")
    list_filter = ("provider", "event_type", "verified", "tenant")
