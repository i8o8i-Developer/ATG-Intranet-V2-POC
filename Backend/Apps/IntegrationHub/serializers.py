from rest_framework import serializers

from Backend.Apps.IntegrationHub.models import IntegrationAttempt, IntegrationConnection, IntegrationProvider, IntegrationSyncJob, WebhookInboxEvent


class IntegrationProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationProvider
        fields = "__all__"


class IntegrationConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationConnection
        fields = "__all__"


class WebhookInboxEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookInboxEvent
        fields = "__all__"


class IntegrationSyncJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationSyncJob
        fields = "__all__"


class IntegrationAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationAttempt
        fields = "__all__"


class QueueSyncSerializer(serializers.Serializer):
    job_type = serializers.CharField(default="ManualSync")
    cursor = serializers.CharField(required=False, allow_blank=True)


class RecordAttemptSerializer(serializers.Serializer):
    operation = serializers.CharField(default="ManualOperation")
    request_payload = serializers.JSONField(required=False)
    response_payload = serializers.JSONField(required=False)
    status = serializers.CharField(default="Pending")


class WebhookReceiveSerializer(serializers.Serializer):
    provider = serializers.IntegerField(required=False, allow_null=True)
    event_type = serializers.CharField(default="unknown")
    external_event_id = serializers.CharField(required=False, allow_blank=True)
    payload = serializers.JSONField(required=False)
    headers = serializers.JSONField(required=False)
