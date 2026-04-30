from django.db import models

from Backend.EnterpriseCore.models import TenantScopedModel


class LearningPath(TenantScopedModel):
    title = models.CharField(max_length=220)
    audience = models.CharField(max_length=120, blank=True, db_index=True)
    status = models.CharField(max_length=80, default="Active", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "title"]


class LearningModule(TenantScopedModel):
    path = models.ForeignKey("Lms.LearningPath", on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=220)
    sequence = models.PositiveIntegerField(default=0)
    content_reference = models.CharField(max_length=260, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "path_id", "sequence"]


class LearningAssignment(TenantScopedModel):
    path = models.ForeignKey("Lms.LearningPath", on_delete=models.PROTECT, related_name="assignments")
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="learning_assignments")
    status = models.CharField(max_length=80, default="Assigned", db_index=True)
    due_on = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "status"])]


class RevenuePerformanceSnapshot(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="revenue_performance_snapshots")
    snapshot_date = models.DateField(db_index=True)
    lead_count = models.PositiveIntegerField(default=0)
    converted_count = models.PositiveIntegerField(default=0)
    proposal_count = models.PositiveIntegerField(default=0)
    score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    metrics = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-snapshot_date"]


class LeadQueueSnapshot(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="lead_queue_snapshots")
    snapshot_date = models.DateField(db_index=True)
    open_count = models.PositiveIntegerField(default=0)
    stale_count = models.PositiveIntegerField(default=0)
    follow_up_due_count = models.PositiveIntegerField(default=0)
    proposal_count = models.PositiveIntegerField(default=0)
    metrics = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-snapshot_date"]
        constraints = [models.UniqueConstraint(fields=["tenant", "employee", "snapshot_date"], name="lms_lead_queue_snapshot_once")]
