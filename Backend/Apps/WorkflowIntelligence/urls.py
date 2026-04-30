from rest_framework.routers import DefaultRouter

from Backend.Apps.WorkflowIntelligence import views

router = DefaultRouter()
router.register("RouteUsageAggregates", views.RouteUsageAggregateViewSet, basename="workflow-route-usage-aggregates")
router.register("WorkflowReports", views.WorkflowReportViewSet, basename="workflow-reports")
router.register("BusinessWorkflowMaps", views.BusinessWorkflowMapViewSet, basename="workflow-business-workflow-maps")

urlpatterns = router.urls