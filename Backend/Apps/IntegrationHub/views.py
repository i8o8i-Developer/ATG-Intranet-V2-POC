from Backend.Apps.IntegrationHub.models import IntegrationAttempt, IntegrationConnection, IntegrationProvider, IntegrationSyncJob, WebhookInboxEvent
from Backend.Apps.IntegrationHub.serializers import (
    IntegrationAttemptSerializer,
    IntegrationConnectionSerializer,
    IntegrationProviderSerializer,
    IntegrationSyncJobSerializer,
    QueueSyncSerializer,
    RecordAttemptSerializer,
    WebhookReceiveSerializer,
    WebhookInboxEventSerializer,
)
from Backend.Apps.IntegrationHub.services import IntegrationJobService, WebhookInboxService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


class IntegrationProviderViewSet(TenantScopedModelViewSet):
    queryset = IntegrationProvider.objects.select_related("tenant", "workspace").all()
    serializer_class = IntegrationProviderSerializer


class IntegrationConnectionViewSet(TenantScopedModelViewSet):
    queryset = IntegrationConnection.objects.select_related("tenant", "workspace", "provider").all()
    serializer_class = IntegrationConnectionSerializer

    @action(detail=True, methods=["post"], url_path="queue-sync")
    def queue_sync(self, request, pk=None):
        serializer = QueueSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = IntegrationJobService.queue_sync(
            self.get_tenant_context(),
            self.get_object(),
            serializer.validated_data.get("job_type", "ManualSync"),
            cursor=serializer.validated_data.get("cursor", ""),
        )
        return self.service_response(result, IntegrationSyncJobSerializer)

    @action(detail=True, methods=["post"], url_path="record-attempt")
    def record_attempt(self, request, pk=None):
        serializer = RecordAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = IntegrationJobService.record_attempt(
            self.get_tenant_context(),
            self.get_object(),
            data.get("operation", "ManualOperation"),
            request_payload=data.get("request_payload") or {},
            response_payload=data.get("response_payload") or {},
            status=data.get("status", "Pending"),
        )
        return self.service_response(result, IntegrationAttemptSerializer)

    @action(detail=True, methods=["post"], url_path="retry-failed")
    def retry_failed(self, request, pk=None):
        result = IntegrationJobService.retry_failed_jobs(self.get_tenant_context(), connection=self.get_object())
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class WebhookInboxEventViewSet(TenantScopedModelViewSet):
    queryset = WebhookInboxEvent.objects.select_related("tenant", "workspace", "provider").all()
    serializer_class = WebhookInboxEventSerializer

    @action(detail=False, methods=["post"], url_path="receive")
    def receive(self, request):
        serializer = WebhookReceiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = WebhookInboxService.receive(
            self.get_tenant_context(),
            provider_id=data.get("provider"),
            event_type=data.get("event_type", "unknown"),
            external_event_id=data.get("external_event_id", ""),
            payload=data.get("payload") or request.data,
            headers=data.get("headers") or dict(request.headers),
        )
        return self.service_response(result, WebhookInboxEventSerializer)

    @action(detail=True, methods=["post"], url_path="mark-processed")
    def mark_processed(self, request, pk=None):
        result = WebhookInboxService.mark_processed(self.get_tenant_context(), pk, status=request.data.get("status", "Processed"), failure_reason=request.data.get("failure_reason", ""))
        return self.service_response(result, WebhookInboxEventSerializer)


class IntegrationSyncJobViewSet(TenantScopedModelViewSet):
    queryset = IntegrationSyncJob.objects.select_related("tenant", "workspace", "connection").all()
    serializer_class = IntegrationSyncJobSerializer

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        result = IntegrationJobService.start_job(self.get_tenant_context(), pk)
        return self.service_response(result, IntegrationSyncJobSerializer)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        result = IntegrationJobService.complete_job(self.get_tenant_context(), pk, result_payload=request.data.get("result_payload") or {})
        return self.service_response(result, IntegrationSyncJobSerializer)

    @action(detail=True, methods=["post"], url_path="fail")
    def fail(self, request, pk=None):
        result = IntegrationJobService.fail_job(self.get_tenant_context(), pk, request.data.get("failure_reason", "Failed"))
        return self.service_response(result, IntegrationSyncJobSerializer)


class IntegrationAttemptViewSet(TenantScopedModelViewSet):
    queryset = IntegrationAttempt.objects.select_related("tenant", "workspace", "connection").all()
    serializer_class = IntegrationAttemptSerializer
