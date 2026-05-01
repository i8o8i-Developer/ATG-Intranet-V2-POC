from Backend.Apps.WorkflowIntelligence.models import BusinessWorkflowMap, RouteUsageAggregate, WorkflowReport
from Backend.Apps.WorkflowIntelligence.serializers import BusinessWorkflowMapSerializer, RouteUsageAggregateSerializer, WorkflowReportSerializer
from Backend.Apps.WorkflowIntelligence.services import WorkflowInsightService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult, TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


class RouteUsageAggregateViewSet(TenantScopedModelViewSet):
    queryset = RouteUsageAggregate.objects.select_related("tenant", "workspace").all()
    serializer_class = RouteUsageAggregateSerializer

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        result = WorkflowInsightService.summarize_route_usage(
            self.get_tenant_context(),
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
        )
        return self.service_response(result)


class WorkflowReportViewSet(TenantScopedModelViewSet):
    queryset = WorkflowReport.objects.select_related("tenant", "workspace").all()
    serializer_class = WorkflowReportSerializer


class BusinessWorkflowMapViewSet(TenantScopedModelViewSet):
    queryset = BusinessWorkflowMap.objects.select_related("tenant", "workspace").all()
    serializer_class = BusinessWorkflowMapSerializer


class WorkflowIntelligenceLegacyMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return ServiceResult.success(TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="WorkflowIntelligenceAPI"))
        tenant_hint = request.headers.get("X-Tenant-Id") or request.query_params.get("tenant") or request.data.get("tenant")
        workspace_hint = request.headers.get("X-Workspace-Id") or request.query_params.get("workspace") or request.data.get("workspace")
        tenant = Tenant.objects.filter(id=tenant_hint).first() if str(tenant_hint or "").isdigit() else Tenant.objects.filter(slug__iexact=str(tenant_hint or "")).first()
        workspace = Workspace.objects.filter(id=workspace_hint).first() if str(workspace_hint or "").isdigit() else Workspace.objects.filter(code__iexact=str(workspace_hint or "")).first()
        if not tenant:
            active_tenants = list(Tenant.objects.filter(status=Tenant.STATUS_ACTIVE).order_by("id")[:2])
            tenant = active_tenants[0] if len(active_tenants) == 1 else None
        if tenant and workspace and workspace.tenant_id != tenant.id:
            workspace = None
        if tenant and not workspace:
            workspace = Workspace.objects.filter(tenant=tenant).order_by("id").first()
        if not tenant:
            return ServiceResult.failure({"tenant": "Tenant context is required for WorkflowIntelligence request."}, status_code=400)
        return ServiceResult.success(TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="WorkflowIntelligenceAPI"))

    def with_context(self, request):
        result = self.get_context(request)
        if not result.ok:
            return None, Response(result.errors, status=result.status_code)
        return result.data, None


class RouteUsageSummaryLegacyAPIView(WorkflowIntelligenceLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = WorkflowInsightService.summarize_route_usage(context, start_date=request.query_params.get("start_date"), end_date=request.query_params.get("end_date"))
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class TopWorkflowsLegacyAPIView(WorkflowIntelligenceLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = WorkflowInsightService.top_workflows(context, start_date=request.query_params.get("start_date"), end_date=request.query_params.get("end_date"), limit=request.query_params.get("limit", 10))
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class GenerateWorkflowReportLegacyAPIView(WorkflowIntelligenceLegacyMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = WorkflowInsightService.generate_report(
            context,
            title=request.data.get("title", ""),
            start_date=request.data.get("start_date"),
            end_date=request.data.get("end_date"),
            report_type=request.data.get("report_type", "Manual"),
        )
        return Response(WorkflowReportSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class BusinessWorkflowMapListLegacyAPIView(WorkflowIntelligenceLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        queryset = BusinessWorkflowMap.objects.filter(tenant=context.tenant).order_by("owning_module", "workflow_name")
        return Response(BusinessWorkflowMapSerializer(queryset, many=True).data, status=200)
