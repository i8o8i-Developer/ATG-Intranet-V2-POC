from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.WorkflowIntelligence import views

router = DefaultRouter()
router.register("RouteUsageAggregates", views.RouteUsageAggregateViewSet, basename="workflow-route-usage-aggregates")
router.register("WorkflowReports", views.WorkflowReportViewSet, basename="workflow-reports")
router.register("BusinessWorkflowMaps", views.BusinessWorkflowMapViewSet, basename="workflow-business-workflow-maps")

urlpatterns = [
	path("api/route-usage/summary/", views.RouteUsageSummaryLegacyAPIView.as_view(), name="workflow-route-summary"),
	path("api/route-usage/top-workflows/", views.TopWorkflowsLegacyAPIView.as_view(), name="workflow-top-workflows"),
	path("api/workflow-reports/generate/", views.GenerateWorkflowReportLegacyAPIView.as_view(), name="workflow-generate-report"),
	path("api/business-workflows/", views.BusinessWorkflowMapListLegacyAPIView.as_view(), name="workflow-business-workflows"),
] + router.urls