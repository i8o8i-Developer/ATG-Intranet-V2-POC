from zoneinfo import ZoneInfo

from celery.result import AsyncResult
from django.http import Http404, HttpResponse
from django.utils import timezone

from Backend.Apps.Users.logics import get_previous_payment_data, get_user_issues
from Backend.Apps.Users.models import EmployeeProfile
from Backend.Apps.Users.serializers import EmployeeProfileSerializer
from Backend.Apps.Users.services import EmployeeLifecycleService, PayrollExportService
from Backend.Apps.Users.tasks import generate_payroll_excel_task
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
            return Response({"employee": "Employee Not Found."}, status=404)
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
    def get(self, request):
        return super().get(request)


class CalculatePreviousPaymentData(TenantContextAPIView):
    def get(self, request):
        context = self.get_context(request)
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=request.query_params.get("employee") or request.query_params.get("user")).first()
        if not employee:
            return Response({"employee": "Employee Not Found."}, status=404)
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


class ExportPayrollAsyncAPIView(TenantContextAPIView):
    def _start_export(self, request):
        context = self.get_context(request)
        if not context.tenant:
            return Response({"tenant": "X-Tenant-Id Header Or Tenant Query Parameter Is Required."}, status=400)

        payload = request.data if request.method == "POST" else request.query_params
        report_month = payload.get("month")
        report_year = payload.get("year")
        pay_type = payload.get("pay_type") or payload.get("payType") or ""

        if report_month and report_year:
            current_date = timezone.localdate()
            if (int(report_year), int(report_month)) > (current_date.year, current_date.month):
                return Response({"error": "No Payroll Export Exists For Future Months.", "status": "error"}, status=400)

        task = generate_payroll_excel_task.delay(
            context.tenant.id,
            context.workspace.id if context.workspace else None,
            report_month,
            report_year,
            pay_type,
        )
        return Response(
            {
                "task_id": task.id,
                "status": "processing",
                "message": "Payroll Export Started. Use The Task Id To Poll Export Status.",
            },
            status=202,
        )

    def get(self, request):
        return self._start_export(request)

    def post(self, request):
        return self._start_export(request)


class PayrollExportStatusAPIView(TenantContextAPIView):
    def get(self, request, task_id):
        task = AsyncResult(task_id)
        if task.state == "PENDING":
            response = {"state": task.state, "status": "Task Is Waiting To Start."}
        elif task.state == "PROGRESS":
            meta = task.info if isinstance(task.info, dict) else {}
            response = {"state": task.state, "status": meta.get("status", "Processing.")}
        elif task.state == "SUCCESS":
            response = {"state": task.state, "status": "completed", "result": task.result}
        elif task.state == "FAILURE":
            response = {"state": task.state, "status": "failed", "error": str(task.info)}
        else:
            response = {"state": task.state, "status": str(task.info)}
        return Response(response)


class DownloadPayrollFileView(TenantContextAPIView):
    def get(self, request, filename):
        context = self.get_context(request)
        export_path = PayrollExportService.resolve_export_path(context, filename)
        if not export_path:
            raise Http404("File Not Found Or You Do Not Have Access To It.")

        file_bytes = export_path.read_bytes()
        export_path.unlink(missing_ok=True)
        response = HttpResponse(
            file_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{export_path.name}"'
        return response


class SaveTimezoneAPIView(TenantContextAPIView):
    def post(self, request):
        timezone_name = request.data.get("timezone") or request.headers.get("X-User-Timezone")
        if not timezone_name:
            return Response({"error": "timezone required"}, status=400)

        try:
            ZoneInfo(timezone_name)
        except Exception:
            return Response({"error": "invalid timezone"}, status=400)

        base_context = self.get_context(request)
        employee_qs = EmployeeProfile.objects.filter(user=request.user, is_active=True).select_related("tenant", "workspace")
        if base_context.tenant:
            employee_qs = employee_qs.filter(tenant=base_context.tenant)
        employee = employee_qs.first()
        if not employee:
            return Response({"employee": "Employee Not Found."}, status=404)

        context = TenantContext(
            tenant=base_context.tenant or employee.tenant,
            workspace=base_context.workspace or employee.workspace,
            actor=base_context.actor,
            source=base_context.source,
        )
        result = EmployeeLifecycleService.save_timezone(context, employee.id, timezone_name)
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        return Response(EmployeeProfileSerializer(result.data).data, status=result.status_code)
