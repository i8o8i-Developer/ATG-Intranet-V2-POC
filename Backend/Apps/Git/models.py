from django.db import models

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class GitRepositorySnapshot(TenantScopedModel, ExternalReference):
    organization = models.CharField(max_length=160, blank=True, db_index=True)
    repository_name = models.CharField(max_length=220)
    repository_full_name = models.CharField(max_length=260, blank=True, db_index=True)
    provider = models.CharField(max_length=80, default="GitHub", db_index=True)
    default_branch = models.CharField(max_length=120, blank=True)
    latest_commit_sha = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=80, default="Active", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "organization", "repository_name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "provider", "organization", "repository_name"], name="git_repo_snapshot_once")]


class GitActivitySnapshot(TenantScopedModel):
    repository = models.ForeignKey("Git.GitRepositorySnapshot", on_delete=models.CASCADE, related_name="activity_snapshots")
    snapshot_date = models.DateField(db_index=True)
    commit_count = models.PositiveIntegerField(default=0)
    pull_request_count = models.PositiveIntegerField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    metrics = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-snapshot_date"]


class RepositoryUtilityRequest(TenantScopedModel):
    repository = models.ForeignKey("Git.GitRepositorySnapshot", null=True, blank=True, on_delete=models.SET_NULL, related_name="utility_requests")
    requested_by = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="git_utility_requests")
    request_type = models.CharField(max_length=120, db_index=True)
    status = models.CharField(max_length=80, default="Queued", db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    result_payload = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]
