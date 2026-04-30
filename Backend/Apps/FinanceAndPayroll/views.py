from Backend.Apps.FinanceAndPayroll.models import (
    ApprovalDecision,
    BankAccount,
    CompensationPlan,
    PaymentOrder,
    PaymentWebhookEvent,
    PayPeriod,
    PayrollLineItem,
    PayrollRun,
    PayoutExecution,
    PayslipDocument,
)
from Backend.Apps.FinanceAndPayroll.serializers import (
    ApprovalDecisionSerializer,
    BankAccountSerializer,
    CompensationPlanSerializer,
    EmployeePayoutRequestSerializer,
    PaymentOrderCreateSerializer,
    PaymentOrderSerializer,
    PaymentWebhookEventSerializer,
    PayPeriodSerializer,
    PayrollCalculationQuerySerializer,
    PayrollLineItemSerializer,
    PayrollRunSerializer,
    PayoutExecutionSerializer,
    PayslipDocumentSerializer,
)
from Backend.Apps.FinanceAndPayroll.services import PaymentOrderService, PaymentWebhookService, PayrollCalculationService, PayrollRunService, PayoutService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


class CompensationPlanViewSet(TenantScopedModelViewSet):
    queryset = CompensationPlan.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = CompensationPlanSerializer


class BankAccountViewSet(TenantScopedModelViewSet):
    queryset = BankAccount.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = BankAccountSerializer


class PayPeriodViewSet(TenantScopedModelViewSet):
    queryset = PayPeriod.objects.select_related("tenant", "workspace").all()
    serializer_class = PayPeriodSerializer


class PayrollRunViewSet(TenantScopedModelViewSet):
    queryset = PayrollRun.objects.select_related("tenant", "workspace", "pay_period").all()
    serializer_class = PayrollRunSerializer

    @action(detail=True, methods=["post"], url_path="recalculate")
    def recalculate(self, request, pk=None):
        result = PayrollRunService.recalculate_totals(self.get_tenant_context(), pk)
        return self.service_response(result, PayrollRunSerializer)

    @action(detail=True, methods=["post"], url_path="submit-for-approval")
    def submit_for_approval(self, request, pk=None):
        result = PayrollRunService.submit_for_approval(self.get_tenant_context(), pk)
        return self.service_response(result, PayrollRunSerializer)

    @action(detail=False, methods=["get"], url_path="calculate-employee")
    def calculate_employee(self, request):
        serializer = PayrollCalculationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = PayrollCalculationService.calculate_for_employee(self.get_tenant_context(), data.get("employee") or data.get("user"), month=data.get("month"), year=data.get("year"))
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=False, methods=["get"], url_path="previous-payment-data")
    def previous_payment_data(self, request):
        serializer = PayrollCalculationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = PayrollCalculationService.previous_payment_data(self.get_tenant_context(), data.get("employee") or data.get("user"), month=data.get("month"), year=data.get("year"))
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class PayrollLineItemViewSet(TenantScopedModelViewSet):
    queryset = PayrollLineItem.objects.select_related("tenant", "workspace", "payroll_run", "employee").all()
    serializer_class = PayrollLineItemSerializer


class ApprovalDecisionViewSet(TenantScopedModelViewSet):
    queryset = ApprovalDecision.objects.select_related("tenant", "workspace", "decided_by").all()
    serializer_class = ApprovalDecisionSerializer


class PayoutExecutionViewSet(TenantScopedModelViewSet):
    queryset = PayoutExecution.objects.select_related("tenant", "workspace", "payroll_run").all()
    serializer_class = PayoutExecutionSerializer

    @action(detail=False, methods=["post"], url_path="request-employee-payout")
    def request_employee_payout(self, request):
        serializer = EmployeePayoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = PayoutService.request_employee_payout(self.get_tenant_context(), serializer.validated_data["payment_snapshot"], live=serializer.validated_data.get("live", False))
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=True, methods=["post"], url_path="sync-provider-status")
    def sync_provider_status(self, request, pk=None):
        result = PayoutService.sync_payout_status(self.get_tenant_context(), pk, provider_payload=request.data.get("provider_payload") or {})
        return self.service_response(result, PayoutExecutionSerializer)


class PayslipDocumentViewSet(TenantScopedModelViewSet):
    queryset = PayslipDocument.objects.select_related("tenant", "workspace", "payroll_line_item").all()
    serializer_class = PayslipDocumentSerializer


class PaymentOrderViewSet(TenantScopedModelViewSet):
    queryset = PaymentOrder.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = PaymentOrderSerializer

    @action(detail=False, methods=["post"], url_path="create-razorpay-order")
    def create_razorpay_order(self, request):
        serializer = PaymentOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = PaymentOrderService.create_order(
            self.get_tenant_context(),
            data["amount"],
            currency=data.get("currency", "INR"),
            receipt=data.get("receipt", ""),
            notes=data.get("notes", {}),
            employee_id=data.get("employee"),
            live=data.get("live", False),
        )
        return self.service_response(result, PaymentOrderSerializer)


class PaymentWebhookEventViewSet(TenantScopedModelViewSet):
    queryset = PaymentWebhookEvent.objects.select_related("tenant", "workspace").all()
    serializer_class = PaymentWebhookEventSerializer

    @action(detail=False, methods=["post"], url_path="razorpay")
    def razorpay(self, request):
        signature = request.headers.get("X-Razorpay-Signature", "")
        result = PaymentWebhookService.record_event(self.get_tenant_context(), request.data, signature=signature, raw_body=request.body)
        return self.service_response(result, PaymentWebhookEventSerializer)
