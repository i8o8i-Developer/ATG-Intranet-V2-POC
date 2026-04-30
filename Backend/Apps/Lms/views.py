from Backend.Apps.Lms.models import LeadQueueSnapshot, LearningAssignment, LearningModule, LearningPath, RevenuePerformanceSnapshot
from Backend.Apps.Lms.serializers import LeadQueueSnapshotSerializer, LearningAssignmentSerializer, LearningModuleSerializer, LearningPathSerializer, RevenuePerformanceSnapshotSerializer
from Backend.Apps.Lms.services import LeadManagementService, LearningAssignmentService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


class LearningPathViewSet(TenantScopedModelViewSet):
    queryset = LearningPath.objects.select_related("tenant", "workspace").all()
    serializer_class = LearningPathSerializer


class LearningModuleViewSet(TenantScopedModelViewSet):
    queryset = LearningModule.objects.select_related("tenant", "workspace", "path").all()
    serializer_class = LearningModuleSerializer


class LearningAssignmentViewSet(TenantScopedModelViewSet):
    queryset = LearningAssignment.objects.select_related("tenant", "workspace", "path", "employee").all()
    serializer_class = LearningAssignmentSerializer

    @action(detail=True, methods=["post"], url_path="mark-complete")
    def mark_complete(self, request, pk=None):
        result = LearningAssignmentService.mark_complete(self.get_tenant_context(), pk)
        return self.service_response(result, LearningAssignmentSerializer)


class RevenuePerformanceSnapshotViewSet(TenantScopedModelViewSet):
    queryset = RevenuePerformanceSnapshot.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = RevenuePerformanceSnapshotSerializer


class LeadQueueSnapshotViewSet(TenantScopedModelViewSet):
    queryset = LeadQueueSnapshot.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = LeadQueueSnapshotSerializer

    @action(detail=False, methods=["post"], url_path="snapshot")
    def snapshot(self, request):
        result = LeadManagementService.create_queue_snapshot(self.get_tenant_context(), employee_id=request.data.get("employee"), snapshot_date=request.data.get("snapshot_date"))
        return self.service_response(result, LeadQueueSnapshotSerializer)


class LmsLegacyMixin:
    def get_context(self, request):
        tenant = Tenant.objects.filter(id=request.headers.get("X-Tenant-Id") or request.query_params.get("tenant") or request.data.get("tenant")).first()
        workspace = Workspace.objects.filter(id=request.headers.get("X-Workspace-Id") or request.query_params.get("workspace") or request.data.get("workspace")).first()
        if tenant and workspace and workspace.tenant_id != tenant.id:
            workspace = None
        return TenantContext(tenant=tenant, workspace=workspace, actor=request.user if request.user.is_authenticated else None, source="LmsLegacyAPI")


class LeadListAPIView(LmsLegacyMixin, APIView):
    def get(self, request):
        result = LeadManagementService.list_leads(self.get_context(request), request.query_params)
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    def post(self, request):
        result = LeadManagementService.create_lead(self.get_context(request), request.data)
        return Response({"id": result.data.id, "company_name": result.data.company_name} if result.ok else result.errors, status=result.status_code)


class BusinessAnalystTypesAPIView(LmsLegacyMixin, APIView):
    def get(self, request):
        result = LeadManagementService.business_analysts(self.get_context(request))
        return Response(result.data, status=result.status_code)


class LeadDashboardAPIView(LmsLegacyMixin, APIView):
    def get(self, request, lead_id):
        result = LeadManagementService.lead_dashboard(self.get_context(request), lead_id)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class BaDashboardAPIView(LmsLegacyMixin, APIView):
    def get(self, request, user_id):
        result = LeadManagementService.ba_dashboard(self.get_context(request), user_id)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class BaChecksAPIView(LmsLegacyMixin, APIView):
    def get(self, request):
        result = LeadManagementService.check_leads_without_today_note(self.get_context(request))
        return Response(result.data, status=result.status_code)


class WeeklyWorkloadAPIView(LmsLegacyMixin, APIView):
    def get(self, request):
        result = LeadManagementService.weekly_workload(self.get_context(request))
        return Response(result.data, status=result.status_code)


class AnalyticsClosuresAPIView(LmsLegacyMixin, APIView):
    def get(self, request):
        result = LeadManagementService.analytics_closures(self.get_context(request), days=request.query_params.get("days", 60))
        return Response(result.data, status=result.status_code)
