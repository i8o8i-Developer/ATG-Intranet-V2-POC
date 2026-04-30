from django.db import models

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class GitHubRepository(TenantScopedModel, ExternalReference):
    project = models.ForeignKey("Project.ProjectWorkspace", null=True, blank=True, on_delete=models.SET_NULL, related_name="github_repositories")
    owner = models.CharField(max_length=120)
    name = models.CharField(max_length=180)
    default_branch = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=80, default="Active", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "owner", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "owner", "name"], name="github_repo_once_per_tenant")]


class BranchReviewerAssignment(TenantScopedModel):
    repository = models.ForeignKey("GithubExtension.GitHubRepository", on_delete=models.CASCADE, related_name="reviewer_assignments")
    branch_name = models.CharField(max_length=180, db_index=True)
    reviewer = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="github_review_assignments")
    status = models.CharField(max_length=80, default="Assigned", db_index=True)
    is_pass = models.CharField(max_length=100, blank=True, db_index=True)
    is_claim = models.BooleanField(default=False)
    comment = models.CharField(max_length=500, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class BranchTestingAssignment(TenantScopedModel):
    repository = models.ForeignKey("GithubExtension.GitHubRepository", on_delete=models.CASCADE, related_name="testing_assignments")
    branch_name = models.CharField(max_length=180, db_index=True)
    tester = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="github_testing_assignments")
    status = models.CharField(max_length=80, default="Pending", db_index=True)
    test_report_url = models.CharField(max_length=300, blank=True)
    is_pass = models.CharField(max_length=100, blank=True, db_index=True)
    is_claim = models.BooleanField(default=False)
    comment = models.CharField(max_length=500, blank=True)
    tested_at = models.DateTimeField(null=True, blank=True)
    result_payload = models.JSONField(default=dict, blank=True)


class RepositoryBranchStatus(TenantScopedModel, ExternalReference):
    repository = models.ForeignKey("GithubExtension.GitHubRepository", on_delete=models.CASCADE, related_name="branch_statuses")
    branch_name = models.CharField(max_length=180, db_index=True)
    last_commit_sha = models.CharField(max_length=80, blank=True)
    review_status = models.CharField(max_length=80, default="Unknown", db_index=True)
    testing_status = models.CharField(max_length=80, default="Unknown", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "repository", "branch_name"], name="github_branch_status_once")]
