from Backend.Apps.Users.logics import get_previous_payment_data, get_user_issues
from Backend.Apps.Users.models import EmployeeProfile
from Backend.Apps.Users.services import EmployeeLifecycleService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext
from rest_framework.response import Response
from rest_framework.views import APIView


class TenantContextAPIView(APIView):
    def get_context(self, request):
        tenant = Tenant.objects.filter(id=request.headers.get("X-Tenant-Id") or request.data.get("tenant") or request.query_params.get("tenant")).first()
        workspace = Workspace.objects.filter(id=request.headers.get("X-Workspace-Id") or request.data.get("workspace") or request.query_params.get("workspace")).first()
        if tenant and workspace and workspace.tenant_id != tenant.id:
            workspace = None
        return TenantContext(tenant=tenant, workspace=workspace, actor=request.user if request.user.is_authenticated else None)


class FetchIssuesAPIView(TenantContextAPIView):
    def get(self, request):
        context = self.get_context(request)
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=request.query_params.get("employee")).first()
        if not employee:
            return Response({"employee": "Employee not found."}, status=404)
        return Response({"issues": get_user_issues(employee, status=request.query_params.get("status", ""))})


class CalculatePayments(TenantContextAPIView):
    def get(self, request):
        from Backend.Apps.FinanceAndPayroll.services import PayrollCalculationService

        context = self.get_context(request)
        result = PayrollCalculationService.calculate_for_employee(
            context,
            request.query_params.get("employee") or request.query_params.get("user"),
            month=request.query_params.get("month"),
            year=request.query_params.get("year"),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class CalculatePayroll(CalculatePayments):
    pass


class CalculatePreviousPaymentData(TenantContextAPIView):
    def get(self, request):
        context = self.get_context(request)
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=request.query_params.get("employee") or request.query_params.get("user")).first()
        if not employee:
            return Response({"employee": "Employee not found."}, status=404)
        rows = get_previous_payment_data(employee, int(request.query_params.get("month", 0)), int(request.query_params.get("year", 0)))
        return Response({"data": rows})


class ChangeDepartmentView(TenantContextAPIView):
    def post(self, request):
        context = self.get_context(request)
        result = EmployeeLifecycleService.transfer_department(
            context,
            request.data.get("employee") or request.data.get("user"),
            request.data.get("department"),
            sub_department_id=request.data.get("sub_department"),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)
