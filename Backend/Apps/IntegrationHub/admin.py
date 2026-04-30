from django.contrib import admin

from Backend.Apps.IntegrationHub.models import IntegrationAttempt, IntegrationConnection, IntegrationProvider, IntegrationSyncJob, WebhookInboxEvent


@admin.register(IntegrationProvider)
class IntegrationProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "provider_type", "auth_type", "base_url", "tenant")
    list_filter = ("provider_type", "auth_type", "tenant")
    search_fields = ("name", "provider_type", "base_url")


@admin.register(IntegrationConnection)
class IntegrationConnectionAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "owner_module", "status", "tenant")
    list_filter = ("owner_module", "status", "tenant")


@admin.register(WebhookInboxEvent)
class WebhookInboxEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "provider", "status", "processing_attempts", "tenant", "created_at")
    list_filter = ("event_type", "status", "tenant")


@admin.register(IntegrationSyncJob)
class IntegrationSyncJobAdmin(admin.ModelAdmin):
    list_display = ("job_type", "connection", "status", "attempt_count", "tenant", "created_at")
    list_filter = ("job_type", "status", "tenant")


@admin.register(IntegrationAttempt)
class IntegrationAttemptAdmin(admin.ModelAdmin):
    list_display = ("operation", "connection", "status", "duration_ms", "tenant", "created_at")
    list_filter = ("operation", "status", "tenant")