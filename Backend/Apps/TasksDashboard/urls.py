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

urlpatterns = router.urls
