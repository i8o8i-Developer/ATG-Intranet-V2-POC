from django.db import models

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class WorkItem(TenantScopedModel, ExternalReference):
    project = models.ForeignKey("Project.ProjectWorkspace", null=True, blank=True, on_delete=models.PROTECT, related_name="work_items")
    parent = models.ForeignKey("TasksDashboard.WorkItem", null=True, blank=True, on_delete=models.CASCADE, related_name="subtasks")
    owner = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.PROTECT, related_name="owned_work_items")
    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=80, default="Open", db_index=True)
    priority = models.CharField(max_length=40, default="Normal", db_index=True)
    order_index = models.PositiveIntegerField(default=0, db_index=True)
    bounty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_at = models.DateTimeField(null=True, blank=True)
    timer_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "status", "order_index", "due_at", "title"]
        indexes = [models.Index(fields=["tenant", "workspace", "status", "priority"])]


class WorkEntry(TenantScopedModel):
    work_item = models.ForeignKey("TasksDashboard.WorkItem", on_delete=models.CASCADE, related_name="entries")
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="work_entries")
    entry_date = models.DateField(db_index=True)
    minutes = models.PositiveIntegerField(default=0)
    entry_type = models.CharField(max_length=80, default="WorkLog", db_index=True)
    summary = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-entry_date"]
        indexes = [models.Index(fields=["tenant", "employee", "entry_date"])]


class TaskActivity(TenantScopedModel):
    work_item = models.ForeignKey("TasksDashboard.WorkItem", on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="task_activities")
    activity_type = models.CharField(max_length=100, db_index=True)
    message = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class DailyStatusEntry(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="daily_status_entries")
    status_date = models.DateField(db_index=True)
    summary = models.TextField(blank=True)
    blockers = models.TextField(blank=True)
    next_plan = models.TextField(blank=True)
    submitted_to_slack = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    slack_thread = models.ForeignKey("TasksDashboard.SlackDeliveryThread", null=True, blank=True, on_delete=models.SET_NULL, related_name="daily_status_entries")
    slack_message_ts = models.CharField(max_length=120, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-status_date"]
        constraints = [models.UniqueConstraint(fields=["tenant", "employee", "status_date"], name="tasks_daily_status_once")]


class SlackDeliveryThread(TenantScopedModel, ExternalReference):
    channel_name = models.CharField(max_length=120)
    channel_id = models.CharField(max_length=120, blank=True, db_index=True)
    thread_key = models.CharField(max_length=180, db_index=True)
    thread_date = models.DateField(db_index=True)
    status = models.CharField(max_length=80, default="Open", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-thread_date"]


class ExternalWorkMapping(TenantScopedModel, ExternalReference):
    work_item = models.ForeignKey("TasksDashboard.WorkItem", null=True, blank=True, on_delete=models.SET_NULL, related_name="external_mappings")
    provider = models.CharField(max_length=80, db_index=True)
    remote_status = models.CharField(max_length=100, blank=True, db_index=True)
    sync_status = models.CharField(max_length=80, default="Linked", db_index=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "provider", "external_id"]


class SlackDeliveryMessage(TenantScopedModel):
    thread = models.ForeignKey("TasksDashboard.SlackDeliveryThread", on_delete=models.CASCADE, related_name="messages")
    daily_status = models.ForeignKey("TasksDashboard.DailyStatusEntry", null=True, blank=True, on_delete=models.SET_NULL, related_name="slack_messages")
    employee = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="slack_eod_messages")
    slack_message_ts = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=80, default="Queued", db_index=True)
    failure_reason = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "thread_id", "employee_id"]


class ManagerAbbreviation(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="manager_abbreviations")
    abbreviation = models.CharField(max_length=20, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "employee"], name="tasks_manager_abbreviation_employee_once")]


class ClickUpProjectMapping(TenantScopedModel, ExternalReference):
    project = models.ForeignKey("Project.ProjectWorkspace", null=True, blank=True, on_delete=models.SET_NULL, related_name="clickup_mappings")
    project_name = models.CharField(max_length=220)
    space_id = models.CharField(max_length=120, blank=True)
    list_id = models.CharField(max_length=120, blank=True)
    sync_status = models.CharField(max_length=80, default="Linked", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "project_name"]
