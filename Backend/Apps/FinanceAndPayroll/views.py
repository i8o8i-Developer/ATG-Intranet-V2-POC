from django.http import JsonResponse
from django.utils import timezone

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
    LegacyBankDetailsSerializer,
    LegacyPaymentApprovalSerializer,
    LegacyProjectFinanceQuerySerializer,
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
from Backend.Apps.FinanceAndPayroll.services import FinanceLegacyService, PaymentOrderService, PaymentWebhookService, PayrollCalculationService, PayrollRunService, PayoutService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult, TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


class FinanceLegacyMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return ServiceResult.success(TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="FinanceLegacy"))
        tenant_hint = request.headers.get("X-Tenant-Id") or request.query_params.get("tenant") or request.data.get("tenant")
        workspace_hint = request.headers.get("X-Workspace-Id") or request.query_params.get("workspace") or request.data.get("workspace")
        tenant = Tenant.objects.filter(id=tenant_hint).first() if str(tenant_hint or "").isdigit() else Tenant.objects.filter(slug__iexact=str(tenant_hint or "")).first()
        workspace = Workspace.objects.filter(id=workspace_hint).first() if str(workspace_hint or "").isdigit() else Workspace.objects.filter(code__iexact=str(workspace_hint or "")).first()
        if not tenant:
            tenants = list(Tenant.objects.filter(status=Tenant.STATUS_ACTIVE).order_by("id")[:2])
            tenant = tenants[0] if len(tenants) == 1 else None
        if tenant and workspace and workspace.tenant_id != tenant.id:
            workspace = None
        if tenant and not workspace:
            workspace = Workspace.objects.filter(tenant=tenant).order_by("id").first()
        if not tenant:
            return ServiceResult.failure({"tenant": "Tenant context is required for finance request."}, status_code=400)
        return ServiceResult.success(TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="FinanceLegacy"))

    def with_context(self, request):
        result = self.get_context(request)
        if not result.ok:
            return None, Response(result.errors, status=result.status_code)
        return result.data, None


class LegacyFinanceDashboardAPIView(FinanceLegacyMixin, APIView):
    flag_name = ""
    manager_scope = False
    domain_name = ""

    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        selected_departments = request.query_params.getlist("departments")
        result = FinanceLegacyService.legacy_dashboard(
            context,
            month=request.query_params.get("month") or request.query_params.get("show_month"),
            year=request.query_params.get("year") or request.query_params.get("show_year"),
            month_name=request.query_params.get("month_name", ""),
            search=request.query_params.get("search", ""),
            selected_departments=selected_departments,
            show_approved=request.query_params.get("show_approved", "false").lower() == "true",
            manager_scope=self.manager_scope,
            domain_name=self.domain_name,
            flag_name=self.flag_name,
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class ManagePayrollLegacyAPIView(LegacyFinanceDashboardAPIView):
    flag_name = "Manage_Payrolls"
    manager_scope = True


class FinanceDepartmentLegacyAPIView(LegacyFinanceDashboardAPIView):
    flag_name = "Finance_Department"


class NewFinanceDepartmentLegacyAPIView(LegacyFinanceDashboardAPIView):
    flag_name = "New_Finance_Department"


class PaymentsLegacyAPIView(LegacyFinanceDashboardAPIView):
    flag_name = "New_Finance_Department"

    def get(self, request):
        response = super().get(request)
        if response.status_code == 200:
            current_year = timezone.localdate().year
            years = {current_year, current_year - 1}
            from Backend.Apps.Users.models import EmployeePaymentSnapshot

            years.update(EmployeePaymentSnapshot.objects.filter(tenant=self.get_context(request).data.tenant).values_list("year", flat=True))
            response.data["years"] = sorted(years, reverse=True)
        return response


class BanaoFinanceDepartmentLegacyAPIView(LegacyFinanceDashboardAPIView):
    flag_name = "Banao_Finance_Department"
    domain_name = "Banao"


class LegacyPaymentApprovalAPIView(FinanceLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = FinanceLegacyService.legacy_payment_records(
            context,
            month=request.query_params.get("show_month") or request.query_params.get("month"),
            year=request.query_params.get("show_year") or request.query_params.get("year"),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        serializer = LegacyPaymentApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = FinanceLegacyService.approve_payment(
            context,
            role=data.get("role", "Finance"),
            employee_id=data.get("employee"),
            user_id=data.get("userid"),
            month=data.get("show_month"),
            year=data.get("show_year"),
            bonus=data.get("bonus", 0),
            normal_pay=data.get("normalPay", 0),
            bounty=data.get("bounty", 0),
            task_count=data.get("taskCount", 0),
            bug_ids=data.get("bugIds", ""),
            pay_note=data.get("payNote", ""),
            pay_for=data.get("payFor", "ATG"),
            custom_pay=data.get("customPay", False),
            live=data.get("live", False),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class LegacyNewPaymentApprovalAPIView(FinanceLegacyMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        serializer = LegacyPaymentApprovalSerializer(data={**request.data, "role": "Finance"})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = FinanceLegacyService.approve_payment(
            context,
            role="Finance",
            employee_id=data.get("employee"),
            user_id=data.get("userid"),
            month=data.get("show_month"),
            year=data.get("show_year"),
            bonus=data.get("bonus", 0),
            normal_pay=data.get("normalPay", 0),
            bounty=data.get("bounty", 0),
            task_count=data.get("taskCount", 0),
            bug_ids=data.get("bugIds", ""),
            pay_note=data.get("payNote", "Payment"),
            pay_for=data.get("payFor", "ATG"),
            custom_pay=data.get("customPay", False),
            live=data.get("live", False),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class LegacyBankDetailsAPIView(FinanceLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = FinanceLegacyService.bank_details_summary(context)
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        serializer = LegacyBankDetailsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = FinanceLegacyService.upsert_bank_details(
            context,
            employee_id=data.get("employee"),
            user_id=data.get("userid"),
            account_number=data.get("Ac_No", ""),
            ifsc_code=data.get("Ac_IFSC", ""),
            upi_id=data.get("upi", ""),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class LegacyProjectFinancesAPIView(FinanceLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        serializer = LegacyProjectFinanceQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        result = FinanceLegacyService.project_finances(context, serializer.validated_data["project_id"])
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class LegacyCalculatePayrollAPIView(FinanceLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        serializer = PayrollCalculationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = PayrollCalculationService.calculate_for_employee(context, data.get("employee") or data.get("user"), month=data.get("month"), year=data.get("year"))
        return Response({"data": result.data} if result.ok else result.errors, status=result.status_code)


class LegacyCalculatePaymentsAPIView(LegacyCalculatePayrollAPIView):
    def get(self, request):
        return super().get(request)


class LegacyPreviousPaymentDataAPIView(FinanceLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        serializer = PayrollCalculationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = PayrollCalculationService.previous_payment_data(context, data.get("employee") or data.get("user"), month=data.get("month"), year=data.get("year"))
        return Response({"data": result.data} if result.ok else result.errors, status=result.status_code)


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
