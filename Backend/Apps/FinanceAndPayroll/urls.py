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

urlpatterns = router.urls
