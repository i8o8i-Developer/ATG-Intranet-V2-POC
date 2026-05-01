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
	path("lms/", views.LmsIndexLegacyAPIView.as_view(), name="lms"),
	path("api/leads/", views.LeadListAPIView.as_view(), name="lms-lead-list"),
	path("api/add_lead/", views.LeadListAPIView.as_view(), name="lms-add-lead"),
	path("api/business-analysts/", views.BusinessAnalystTypesAPIView.as_view(), name="lms-business-analysts"),
	path("api/lead-dashboard/<int:lead_id>/", views.LeadDashboardAPIView.as_view(), name="lms-lead-dashboard"),
	path("api/Ba-Dashboard/<int:user_id>/", views.BaDashboardAPIView.as_view(), name="lms-ba-dashboard"),
	path("api/ba-checks/", views.BaChecksAPIView.as_view(), name="lms-ba-checks"),
	path("api/tags/", views.TagListCreateLegacyAPIView.as_view(), name="tag-list-create"),
	path("api/leads/<int:lead_id>/note-updated-today/", views.LeadNoteUpdatedTodayLegacyAPIView.as_view(), name="lead-note-updated-today"),
	path("lms/track-performance/", views.TrackPerformanceLegacyAPIView.as_view(), name="track_performance"),
	path("lms/lead/<int:lead_id>/", views.LeadDetailLegacyAPIView.as_view(), name="lead_detail"),
	path("lms/lead/<int:lead_id>/edit/", views.LeadEditLegacyAPIView.as_view(), name="lead_edit"),
	path("lms/jrba/<int:ba_id>/", views.JrbaDashboardLegacyAPIView.as_view(), name="jrba_dashboard"),
	path("lms/add_lead", views.AddLeadTemplateLegacyAPIView.as_view(), name="add_lead"),
	path("lms/weekly-workload/", views.WeeklyWorkloadAPIView.as_view(), name="lms-weekly-workload"),
	path("lms/dashboard/", views.DashboardLegacyAPIView.as_view(), name="dashboard"),
	path("lms/analytics_dashboard/", views.AnalyticsDashboardLegacyAPIView.as_view(), name="analytics_dashboard"),
	path("lms/api/closures/", views.AnalyticsClosuresAPIView.as_view(), name="lms-analytics-closures"),
	path("lms/eod-performance/", views.EODPerformanceLegacyAPIView.as_view(), name="eod_performance_dashboard"),
] + router.urls
