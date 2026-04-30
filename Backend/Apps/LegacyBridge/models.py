from django.db import models

from Backend.EnterpriseCore.models import TenantScopedModel


class LegacyApplicationMap(TenantScopedModel):
    legacy_app_label = models.CharField(max_length=120, db_index=True)
    backend_app_label = models.CharField(max_length=120, db_index=True)
    target_domain = models.CharField(max_length=160, blank=True)
    route_prefix = models.CharField(max_length=160, blank=True)
    migration_status = models.CharField(max_length=80, default="Mapped", db_index=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["legacy_app_label"]
        constraints = [models.UniqueConstraint(fields=["tenant", "legacy_app_label", "backend_app_label"], name="legacy_app_map_once")]


class LegacyModelCrosswalk(TenantScopedModel):
    legacy_app_label = models.CharField(max_length=120, db_index=True)
    legacy_model_name = models.CharField(max_length=160, db_index=True)
    legacy_object_id = models.CharField(max_length=120, db_index=True)
    backend_app_label = models.CharField(max_length=120, db_index=True)
    backend_model_name = models.CharField(max_length=160, db_index=True)
    backend_object_id = models.CharField(max_length=120, db_index=True)
    direction = models.CharField(max_length=40, default="LegacyToBackend", db_index=True)
    sync_status = models.CharField(max_length=80, default="Synced", db_index=True)
    migration_batch_id = models.CharField(max_length=120, blank=True, db_index=True)
    checksum = models.CharField(max_length=128, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["legacy_app_label", "legacy_model_name", "legacy_object_id"]
        constraints = [models.UniqueConstraint(fields=["tenant", "legacy_app_label", "legacy_model_name", "legacy_object_id"], name="legacy_crosswalk_once")]


class MigrationRun(TenantScopedModel):
    batch_id = models.CharField(max_length=120, db_index=True)
    source_app_label = models.CharField(max_length=120, db_index=True)
    target_app_label = models.CharField(max_length=120, db_index=True)
    mode = models.CharField(max_length=80, default="Preview", db_index=True)
    dry_run = models.BooleanField(default=True, db_index=True)
    status = models.CharField(max_length=80, default="Pending", db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    total_rows = models.PositiveIntegerField(default=0)
    migrated_rows = models.PositiveIntegerField(default=0)
    skipped_rows = models.PositiveIntegerField(default=0)
    result_payload = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class LegacyMigrationIssue(TenantScopedModel):
    migration_run = models.ForeignKey("LegacyBridge.MigrationRun", null=True, blank=True, on_delete=models.CASCADE, related_name="issues")
    severity = models.CharField(max_length=40, default="Warning", db_index=True)
    source_app_label = models.CharField(max_length=120, db_index=True)
    legacy_model_name = models.CharField(max_length=160, blank=True, db_index=True)
    legacy_object_id = models.CharField(max_length=120, blank=True, db_index=True)
    message = models.TextField()
    resolution_status = models.CharField(max_length=80, default="Open", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "severity", "created_at"]
