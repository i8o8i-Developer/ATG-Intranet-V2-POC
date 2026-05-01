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
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult, TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


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


class IntegrationHubLegacyMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return ServiceResult.success(TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="IntegrationHubLegacyAPI"))
        tenant_hint = request.headers.get("X-Tenant-Id") or request.query_params.get("tenant") or request.data.get("tenant")
        workspace_hint = request.headers.get("X-Workspace-Id") or request.query_params.get("workspace") or request.data.get("workspace")
        tenant = Tenant.objects.filter(id=tenant_hint).first() if str(tenant_hint or "").isdigit() else Tenant.objects.filter(slug__iexact=str(tenant_hint or "")).first()
        workspace = Workspace.objects.filter(id=workspace_hint).first() if str(workspace_hint or "").isdigit() else Workspace.objects.filter(code__iexact=str(workspace_hint or "")).first()
        if not tenant:
            active_tenants = list(Tenant.objects.filter(status=Tenant.STATUS_ACTIVE).order_by("id")[:2])
            tenant = active_tenants[0] if len(active_tenants) == 1 else None
        if tenant and workspace and workspace.tenant_id != tenant.id:
            workspace = None
        if tenant and not workspace:
            workspace = Workspace.objects.filter(tenant=tenant).order_by("id").first()
        if not tenant:
            return ServiceResult.failure({"tenant": "Tenant context is required for IntegrationHub request."}, status_code=400)
        return ServiceResult.success(TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="IntegrationHubLegacyAPI"))

    def with_context(self, request):
        result = self.get_context(request)
        if not result.ok:
            return None, Response(result.errors, status=result.status_code)
        return result.data, None


class QueueSyncLegacyAPIView(IntegrationHubLegacyMixin, APIView):
    def post(self, request, connection_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        connection = IntegrationConnection.objects.filter(tenant=context.tenant, id=connection_id).first()
        if not connection:
            return Response({"connection": "Integration connection not found."}, status=404)
        serializer = QueueSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = IntegrationJobService.queue_sync(context, connection, serializer.validated_data.get("job_type", "ManualSync"), cursor=serializer.validated_data.get("cursor", ""))
        return Response(IntegrationSyncJobSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class RecordAttemptLegacyAPIView(IntegrationHubLegacyMixin, APIView):
    def post(self, request, connection_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        connection = IntegrationConnection.objects.filter(tenant=context.tenant, id=connection_id).first()
        if not connection:
            return Response({"connection": "Integration connection not found."}, status=404)
        serializer = RecordAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = IntegrationJobService.record_attempt(context, connection, data.get("operation", "ManualOperation"), request_payload=data.get("request_payload") or {}, response_payload=data.get("response_payload") or {}, status=data.get("status", "Pending"))
        return Response(IntegrationAttemptSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class RetryFailedLegacyAPIView(IntegrationHubLegacyMixin, APIView):
    def post(self, request, connection_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        connection = IntegrationConnection.objects.filter(tenant=context.tenant, id=connection_id).first()
        if not connection:
            return Response({"connection": "Integration connection not found."}, status=404)
        result = IntegrationJobService.retry_failed_jobs(context, connection=connection)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class ReceiveWebhookLegacyAPIView(IntegrationHubLegacyMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        serializer = WebhookReceiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = WebhookInboxService.receive(context, provider_id=data.get("provider"), event_type=data.get("event_type", "unknown"), external_event_id=data.get("external_event_id", ""), payload=data.get("payload") or request.data, headers=data.get("headers") or dict(request.headers))
        return Response(WebhookInboxEventSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class MarkProcessedLegacyAPIView(IntegrationHubLegacyMixin, APIView):
    def post(self, request, event_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = WebhookInboxService.mark_processed(context, event_id, status=request.data.get("status", "Processed"), failure_reason=request.data.get("failure_reason", ""))
        return Response(WebhookInboxEventSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class StartJobLegacyAPIView(IntegrationHubLegacyMixin, APIView):
    def post(self, request, job_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = IntegrationJobService.start_job(context, job_id)
        return Response(IntegrationSyncJobSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class CompleteJobLegacyAPIView(IntegrationHubLegacyMixin, APIView):
    def post(self, request, job_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = IntegrationJobService.complete_job(context, job_id, result_payload=request.data.get("result_payload") or {})
        return Response(IntegrationSyncJobSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class FailJobLegacyAPIView(IntegrationHubLegacyMixin, APIView):
    def post(self, request, job_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = IntegrationJobService.fail_job(context, job_id, request.data.get("failure_reason", "Failed"))
        return Response(IntegrationSyncJobSerializer(result.data).data if result.ok else result.errors, status=result.status_code)
