from Backend.Apps.WorkflowIntelligence.models import BusinessWorkflowMap, RouteUsageAggregate, WorkflowReport
from Backend.Apps.WorkflowIntelligence.serializers import BusinessWorkflowMapSerializer, RouteUsageAggregateSerializer, WorkflowReportSerializer
from Backend.Apps.WorkflowIntelligence.services import WorkflowInsightService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action


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
