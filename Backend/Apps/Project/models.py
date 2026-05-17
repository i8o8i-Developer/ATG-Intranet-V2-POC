from django.db import models
from django.utils import timezone

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class ProjectWorkspace(TenantScopedModel, ExternalReference):
    name = models.CharField(max_length=220)
    code = models.CharField(max_length=80)
    client_name = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    project_type = models.CharField(max_length=80, blank=True, db_index=True)
    priority = models.CharField(max_length=40, default="P2", db_index=True)
    status = models.CharField(max_length=80, default="Planning", db_index=True)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    health = models.CharField(max_length=40, default="Unknown", db_index=True)
    github_organization = models.CharField(max_length=120, blank=True)
    clickup_sync_enabled = models.BooleanField(default=False, db_index=True)
    terms_required = models.BooleanField(default=False, db_index=True)
    anti_phishing_enabled = models.BooleanField(default=False, db_index=True)
    associate_project_manager = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="apm_projects")
    project_manager = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="pm_projects")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "code"], name="project_workspace_code_per_tenant")]

    def __str__(self):
        return self.name


class ProjectContact(TenantScopedModel):
    project = models.ForeignKey("Project.ProjectWorkspace", on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=180)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=60, blank=True)
    role = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["tenant_id", "project_id", "name"]


class DefaultCheckpoint(TenantScopedModel):
    title = models.CharField(max_length=220)
    sequence = models.PositiveIntegerField(default=0)
    project_type = models.CharField(max_length=80, blank=True, db_index=True)
    bounty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    acceptance_criteria = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "project_type", "sequence", "title"]
        constraints = [models.UniqueConstraint(fields=["tenant", "project_type", "title"], name="project_default_checkpoint_once")]


class MilestoneComponent(TenantScopedModel):
    project = models.ForeignKey("Project.ProjectWorkspace", on_delete=models.CASCADE, related_name="milestone_components")
    name = models.CharField(max_length=180)
    sequence = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=80, default="Open", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "project_id", "sequence", "name"]


class DeliveryMilestone(TenantScopedModel, ExternalReference):
    project = models.ForeignKey("Project.ProjectWorkspace", on_delete=models.CASCADE, related_name="milestones")
    component = models.ForeignKey("Project.MilestoneComponent", null=True, blank=True, on_delete=models.SET_NULL, related_name="milestones")
    title = models.CharField(max_length=220)
    sequence = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=80, default="Open", db_index=True)
    due_on = models.DateField(null=True, blank=True)
    completed_on = models.DateField(null=True, blank=True)
    bounty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delayed_days = models.PositiveIntegerField(default=0)
    acceptance_criteria = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["tenant_id", "project_id", "sequence", "due_on"]


class TeamAssignment(TenantScopedModel):
    project = models.ForeignKey("Project.ProjectWorkspace", on_delete=models.CASCADE, related_name="team_assignments")
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="project_assignments")
    role = models.CharField(max_length=120)
    allocation_percent = models.PositiveSmallIntegerField(default=100)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    github_access_status = models.CharField(max_length=80, default="NotRequested", db_index=True)
    is_absent = models.BooleanField(default=False, db_index=True)
    absent_reason = models.TextField(blank=True)
    status = models.CharField(max_length=60, default="Active", db_index=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "project", "employee", "status"])]


class RepositoryLink(TenantScopedModel, ExternalReference):
    project = models.ForeignKey("Project.ProjectWorkspace", on_delete=models.CASCADE, related_name="repositories")
    name = models.CharField(max_length=180)
    owner = models.CharField(max_length=120, blank=True)
    full_name = models.CharField(max_length=260, blank=True, db_index=True)
    provider = models.CharField(max_length=80, default="GitHub", db_index=True)
    default_branch = models.CharField(max_length=120, blank=True)
    access_status = models.CharField(max_length=80, default="Linked", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "project_id", "name"]


class DeliveryDocument(TenantScopedModel, ExternalReference):
    project = models.ForeignKey("Project.ProjectWorkspace", on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=220)
    document_type = models.CharField(max_length=100, db_index=True)
    storage_reference = models.CharField(max_length=260, blank=True)
    file_id = models.CharField(max_length=180, blank=True, db_index=True)
    is_pinned = models.BooleanField(default=False, db_index=True)
    status = models.CharField(max_length=80, default="Active", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "project_id", "title"]


class DeliveryAlert(TenantScopedModel):
    project = models.ForeignKey("Project.ProjectWorkspace", on_delete=models.CASCADE, related_name="alerts")
    milestone = models.ForeignKey("Project.DeliveryMilestone", null=True, blank=True, on_delete=models.CASCADE, related_name="flags")
    severity = models.CharField(max_length=40, default="Info", db_index=True)
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=60, default="Open", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class ComplianceCampaign(TenantScopedModel):
    project = models.ForeignKey("Project.ProjectWorkspace", null=True, blank=True, on_delete=models.PROTECT, related_name="compliance_campaigns")
    name = models.CharField(max_length=220)
    campaign_type = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=80, default="Draft", db_index=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    content_payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class ComplianceAssignment(TenantScopedModel):
    campaign = models.ForeignKey("Project.ComplianceCampaign", on_delete=models.CASCADE, related_name="assignments")
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="compliance_assignments")
    token = models.CharField(max_length=160, blank=True, db_index=True)
    status = models.CharField(max_length=80, default="Assigned", db_index=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    evidence = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "campaign", "employee"], name="project_compliance_assignment_once")]


class ProjectDelay(TenantScopedModel):
    """Track delays in projects, tasks, or employee work"""
    delay_type = models.CharField(max_length=40, db_index=True)  # Project, Task, Employee
    item_id = models.PositiveIntegerField()  # ID Of The Delayed Item
    project = models.ForeignKey(
        "Project.ProjectWorkspace",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delays",
    )
    task = models.ForeignKey(
        "TasksDashboard.WorkItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delays",
    )
    reported_by = models.ForeignKey(
        "Users.EmployeeProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_delays",
    )
    days = models.PositiveIntegerField(default=0)
    reason = models.TextField()
    status = models.CharField(max_length=40, default="Active", db_index=True)  # Active, Resolved
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_delays",
    )

    class Meta:
        ordering = ["tenant_id", "-created_at"]
        indexes = [
            models.Index(fields=["tenant", "delay_type", "status"]),
            models.Index(fields=["tenant", "item_id"]),
        ]

    def __str__(self):
        return f"{self.delay_type} Delay - {self.days} days"


class ProjectBudget(TenantScopedModel):
    project = models.ForeignKey("Project.ProjectWorkspace", on_delete=models.CASCADE, related_name="budgets")
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    role_and_budget = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]

    def __str__(self):
        return f"Budget for {self.project.name}"


class TeamAssignmentHistory(TenantScopedModel):
    ACTION_CHOICES = [
        ("added", "Added"),
        ("removed", "Removed"),
        ("replaced", "Replaced"),
        ("added_back", "Added Back"),
        ("status_changed", "Status Changed"),
    ]
    team_assignment = models.ForeignKey("Project.TeamAssignment", on_delete=models.CASCADE, related_name="history")
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True)
    changed_by = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="team_history_changes")

    class Meta:
        ordering = ["tenant_id", "-created_at"]

    def __str__(self):
        return f"{self.team_assignment.employee.display_name} - {self.action}"


class UserRepositoryStatus(TenantScopedModel):
    repository = models.ForeignKey("Project.RepositoryLink", on_delete=models.CASCADE, related_name="user_statuses")
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="repository_statuses")
    status = models.CharField(max_length=80, blank=True)
    last_checked = models.DateTimeField(default=timezone.now)
    days_since = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["tenant_id", "-last_checked"]
        constraints = [models.UniqueConstraint(fields=["tenant", "repository", "employee"], name="project_user_repo_status_once")]

    def __str__(self):
        return f"{self.employee.display_name} - {self.repository.name}"
