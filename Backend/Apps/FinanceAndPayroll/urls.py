from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.FinanceAndPayroll import views

router = DefaultRouter()
router.register("CompensationPlans", views.CompensationPlanViewSet, basename="finance-compensation-plans")
router.register("BankAccounts", views.BankAccountViewSet, basename="finance-bank-accounts")
router.register("PayPeriods", views.PayPeriodViewSet, basename="finance-pay-periods")
router.register("PayrollRuns", views.PayrollRunViewSet, basename="finance-payroll-runs")
router.register("PayrollLineItems", views.PayrollLineItemViewSet, basename="finance-payroll-line-items")
router.register("ApprovalDecisions", views.ApprovalDecisionViewSet, basename="finance-approval-decisions")
router.register("PayoutExecutions", views.PayoutExecutionViewSet, basename="finance-payout-executions")
router.register("PayslipDocuments", views.PayslipDocumentViewSet, basename="finance-payslip-documents")
router.register("PaymentOrders", views.PaymentOrderViewSet, basename="finance-payment-orders")
router.register("PaymentWebhookEvents", views.PaymentWebhookEventViewSet, basename="finance-payment-webhook-events")

urlpatterns = [
	path("manage-payroll/", views.ManagePayrollLegacyAPIView.as_view(), name="finance-manage-payroll-legacy"),
	path("finance-department/", views.FinanceDepartmentLegacyAPIView.as_view(), name="finance-department-legacy"),
	path("new-finance-department/", views.NewFinanceDepartmentLegacyAPIView.as_view(), name="finance-new-department-legacy"),
	path("payments/", views.PaymentsLegacyAPIView.as_view(), name="finance-payments-legacy"),
	path("banao-finance-department/", views.BanaoFinanceDepartmentLegacyAPIView.as_view(), name="finance-banao-department-legacy"),
	path("payment-approval/", views.LegacyPaymentApprovalAPIView.as_view(), name="finance-payment-approval-legacy"),
	path("new-payment-approval/", views.LegacyNewPaymentApprovalAPIView.as_view(), name="finance-new-payment-approval-legacy"),
	path("Bankdetails/", views.LegacyBankDetailsAPIView.as_view(), name="finance-bankdetails-legacy"),
	path("api/calculate-payroll/", views.LegacyCalculatePayrollAPIView.as_view(), name="finance-calculate-payroll-legacy"),
	path("api/calculate-payments/", views.LegacyCalculatePaymentsAPIView.as_view(), name="finance-calculate-payments-legacy"),
	path("api/previous-payment-data/", views.LegacyPreviousPaymentDataAPIView.as_view(), name="finance-previous-payment-data-legacy"),
	path("api/project-finances/", views.LegacyProjectFinancesAPIView.as_view(), name="finance-project-finances-legacy"),
] + router.urls
