from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.IntegrationHub import views

router = DefaultRouter()
router.register("IntegrationProviders", views.IntegrationProviderViewSet, basename="integration-providers")
router.register("IntegrationConnections", views.IntegrationConnectionViewSet, basename="integration-connections")
router.register("WebhookInboxEvents", views.WebhookInboxEventViewSet, basename="integration-webhook-inbox-events")
router.register("IntegrationSyncJobs", views.IntegrationSyncJobViewSet, basename="integration-sync-jobs")
router.register("IntegrationAttempts", views.IntegrationAttemptViewSet, basename="integration-attempts")

urlpatterns = [
	path("api/connections/<int:connection_id>/queue-sync/", views.QueueSyncLegacyAPIView.as_view(), name="integration-queue-sync"),
	path("api/connections/<int:connection_id>/record-attempt/", views.RecordAttemptLegacyAPIView.as_view(), name="integration-record-attempt"),
	path("api/connections/<int:connection_id>/retry-failed/", views.RetryFailedLegacyAPIView.as_view(), name="integration-retry-failed"),
	path("api/webhooks/receive/", views.ReceiveWebhookLegacyAPIView.as_view(), name="integration-receive-webhook"),
	path("api/webhooks/<int:event_id>/mark-processed/", views.MarkProcessedLegacyAPIView.as_view(), name="integration-mark-processed"),
	path("api/jobs/<int:job_id>/start/", views.StartJobLegacyAPIView.as_view(), name="integration-start-job"),
	path("api/jobs/<int:job_id>/complete/", views.CompleteJobLegacyAPIView.as_view(), name="integration-complete-job"),
	path("api/jobs/<int:job_id>/fail/", views.FailJobLegacyAPIView.as_view(), name="integration-fail-job"),
] + router.urls
