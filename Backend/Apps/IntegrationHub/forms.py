from django import forms

from Backend.Apps.IntegrationHub.models import IntegrationAttempt, IntegrationConnection, IntegrationProvider, IntegrationSyncJob, WebhookInboxEvent


class IntegrationProviderForm(forms.ModelForm):
    class Meta:
        model = IntegrationProvider
        fields = ["name", "provider_type", "base_url", "auth_type", "capability_payload"]


class IntegrationConnectionForm(forms.ModelForm):
    class Meta:
        model = IntegrationConnection
        fields = ["provider", "owner_module", "name", "status", "credential_reference", "config_payload"]


class WebhookInboxEventForm(forms.ModelForm):
    class Meta:
        model = WebhookInboxEvent
        fields = ["provider", "event_type", "external_event_id", "status", "payload", "headers", "failure_reason"]


class IntegrationSyncJobForm(forms.ModelForm):
    class Meta:
        model = IntegrationSyncJob
        fields = ["connection", "job_type", "status", "cursor", "result_payload", "failure_reason"]


class IntegrationAttemptForm(forms.ModelForm):
    class Meta:
        model = IntegrationAttempt
        fields = ["connection", "operation", "status", "request_payload", "response_payload", "failure_reason", "duration_ms"]