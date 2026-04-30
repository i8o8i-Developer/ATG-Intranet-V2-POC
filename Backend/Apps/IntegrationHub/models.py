from django.db import models

from Backend.EnterpriseCore.models import TenantScopedModel


class IntegrationProvider(TenantScopedModel):
    name = models.CharField(max_length=140)
    provider_type = models.CharField(max_length=100, db_index=True)
    base_url = models.URLField(blank=True)
    auth_type = models.CharField(max_length=80, blank=True)
    capability_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="integration_provider_name_per_tenant")]


class IntegrationConnection(TenantScopedModel):
    provider = models.ForeignKey("IntegrationHub.IntegrationProvider", on_delete=models.PROTECT, related_name="connections")
    owner_module = models.CharField(max_length=120, db_index=True)
    name = models.CharField(max_length=180)
    status = models.CharField(max_length=80, default="Active", db_index=True)
    credential_reference = models.CharField(max_length=240, blank=True)
    config_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "owner_module", "name"]


class WebhookInboxEvent(TenantScopedModel):
    provider = models.ForeignKey("IntegrationHub.IntegrationProvider", null=True, blank=True, on_delete=models.SET_NULL, related_name="webhook_events")
    event_type = models.CharField(max_length=160, db_index=True)
    external_event_id = models.CharField(max_length=180, blank=True, db_index=True)
    status = models.CharField(max_length=80, default="Received", db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    headers = models.JSONField(default=dict, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    processing_attempts = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class IntegrationSyncJob(TenantScopedModel):
    connection = models.ForeignKey("IntegrationHub.IntegrationConnection", on_delete=models.PROTECT, related_name="sync_jobs")
    job_type = models.CharField(max_length=120, db_index=True)
    status = models.CharField(max_length=80, default="Queued", db_index=True)
    cursor = models.CharField(max_length=220, blank=True)
    result_payload = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True)
    attempt_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)


class IntegrationAttempt(TenantScopedModel):
    connection = models.ForeignKey("IntegrationHub.IntegrationConnection", on_delete=models.PROTECT, related_name="attempts")
    operation = models.CharField(max_length=160, db_index=True)
    status = models.CharField(max_length=80, default="Pending", db_index=True)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["tenant_id", "-created_at"]
