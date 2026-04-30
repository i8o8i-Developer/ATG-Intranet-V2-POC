from django.db import models

from Backend.EnterpriseCore.models import TenantScopedModel


class RouteUsageAggregate(TenantScopedModel):
    route_name = models.CharField(max_length=220, db_index=True)
    route_pattern = models.CharField(max_length=260, db_index=True)
    workflow_name = models.CharField(max_length=180, db_index=True)
    username = models.CharField(max_length=160, blank=True, db_index=True)
    usage_date = models.DateField(db_index=True)
    hit_count = models.PositiveIntegerField(default=0)
    last_hit_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-usage_date", "workflow_name", "route_name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "route_pattern", "username", "usage_date"], name="workflow_route_usage_once")]


class WorkflowReport(TenantScopedModel):
    title = models.CharField(max_length=220)
    report_type = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=80, default="Generated", db_index=True)
    generated_for = models.CharField(max_length=160, blank=True)
    markdown_body = models.TextField(blank=True)
    data_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class BusinessWorkflowMap(TenantScopedModel):
    workflow_name = models.CharField(max_length=180)
    owning_module = models.CharField(max_length=120, db_index=True)
    description = models.TextField(blank=True)
    route_patterns = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "owning_module", "workflow_name"]
