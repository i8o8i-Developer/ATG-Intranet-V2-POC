from rest_framework.routers import DefaultRouter

from Backend.Apps.IntegrationHub import views

router = DefaultRouter()
router.register("IntegrationProviders", views.IntegrationProviderViewSet, basename="integration-providers")
router.register("IntegrationConnections", views.IntegrationConnectionViewSet, basename="integration-connections")
router.register("WebhookInboxEvents", views.WebhookInboxEventViewSet, basename="integration-webhook-inbox-events")
router.register("IntegrationSyncJobs", views.IntegrationSyncJobViewSet, basename="integration-sync-jobs")
router.register("IntegrationAttempts", views.IntegrationAttemptViewSet, basename="integration-attempts")

urlpatterns = router.urls
