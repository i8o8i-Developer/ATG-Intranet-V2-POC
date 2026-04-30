from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.Lms import views

router = DefaultRouter()
router.register("LearningPaths", views.LearningPathViewSet, basename="lms-learning-paths")
router.register("LearningModules", views.LearningModuleViewSet, basename="lms-learning-modules")
router.register("LearningAssignments", views.LearningAssignmentViewSet, basename="lms-learning-assignments")
router.register("RevenuePerformanceSnapshots", views.RevenuePerformanceSnapshotViewSet, basename="lms-revenue-performance-snapshots")
router.register("LeadQueueSnapshots", views.LeadQueueSnapshotViewSet, basename="lms-lead-queue-snapshots")

urlpatterns = [
	path("api/leads/", views.LeadListAPIView.as_view(), name="lms-lead-list"),
	path("api/add_lead/", views.LeadListAPIView.as_view(), name="lms-add-lead"),
	path("api/business-analysts/", views.BusinessAnalystTypesAPIView.as_view(), name="lms-business-analysts"),
	path("api/lead-dashboard/<int:lead_id>/", views.LeadDashboardAPIView.as_view(), name="lms-lead-dashboard"),
	path("api/Ba-Dashboard/<int:user_id>/", views.BaDashboardAPIView.as_view(), name="lms-ba-dashboard"),
	path("api/ba-checks/", views.BaChecksAPIView.as_view(), name="lms-ba-checks"),
	path("lms/weekly-workload/", views.WeeklyWorkloadAPIView.as_view(), name="lms-weekly-workload"),
	path("lms/api/closures/", views.AnalyticsClosuresAPIView.as_view(), name="lms-analytics-closures"),
] + router.urls
