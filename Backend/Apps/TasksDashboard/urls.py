from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.TasksDashboard import views

router = DefaultRouter()
router.register("WorkItems", views.WorkItemViewSet, basename="tasks-work-items")
router.register("WorkEntries", views.WorkEntryViewSet, basename="tasks-work-entries")
router.register("TaskActivities", views.TaskActivityViewSet, basename="tasks-task-activities")
router.register("DailyStatusEntries", views.DailyStatusEntryViewSet, basename="tasks-daily-status-entries")
router.register("SlackDeliveryThreads", views.SlackDeliveryThreadViewSet, basename="tasks-slack-delivery-threads")
router.register("SlackDeliveryMessages", views.SlackDeliveryMessageViewSet, basename="tasks-slack-delivery-messages")
router.register("ExternalWorkMappings", views.ExternalWorkMappingViewSet, basename="tasks-external-work-mappings")
router.register("ClickUpProjectMappings", views.ClickUpProjectMappingViewSet, basename="tasks-clickup-project-mappings")
router.register("ManagerAbbreviations", views.ManagerAbbreviationViewSet, basename="tasks-manager-abbreviations")

urlpatterns = [
	path("dashboard/<str:type>/", views.DashboardLegacyAPIView.as_view(), name="tasks"),
	path("check-log-update/", views.CheckLogUpdateLegacyAPIView.as_view(), name="check-log-update"),
	path("initialize-timer/", views.InitializeSyncTimerLegacyAPIView.as_view(), name="initialize_timer"),
	path("update_clickup/", views.UpdateClickupLegacyAPIView.as_view(), name="clickup-update"),
	path("check_task_status/<str:task_id>/", views.CheckTaskStatusLegacyAPIView.as_view(), name="check_task_status"),
	path("reorder-tasks/", views.ReorderTaskLegacyAPIView.as_view(), name="reorder-tasks"),
	path("activity/", views.CreateActivityLegacyAPIView.as_view(), name="create_activity"),
	path("api/eod-report/", views.EODReportLegacyAPIView.as_view(), name="eod-report"),
] + router.urls
