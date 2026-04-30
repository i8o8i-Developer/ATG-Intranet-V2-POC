from django.conf import settings
from django.db import models

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class OnboardingOffer(TenantScopedModel, ExternalReference):
    candidate_name = models.CharField(max_length=180)
    candidate_email = models.EmailField()
    company_name = models.CharField(max_length=160, blank=True)
    position_title = models.CharField(max_length=180, blank=True)
    offer_type = models.CharField(max_length=80, blank=True, db_index=True)
    token = models.CharField(max_length=180, blank=True, db_index=True)
    status = models.CharField(max_length=60, default="Draft", db_index=True)
    offer_payload = models.JSONField(default=dict, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    reminder_count = models.PositiveIntegerField(default=0)
    last_reminder_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class LeaveRequest(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="leave_requests")
    leave_type = models.CharField(max_length=80)
    starts_on = models.DateField()
    ends_on = models.DateField()
    status = models.CharField(max_length=60, default="Submitted", db_index=True)
    requested_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    approval_stage = models.CharField(max_length=80, default="Manager", db_index=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_new_leave_requests")
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)
    approval_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-starts_on"]
        indexes = [models.Index(fields=["tenant", "employee", "status"])]


class NotificationItem(TenantScopedModel):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="new_notifications")
    title = models.CharField(max_length=180)
    message = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True, db_index=True)
    resource_type = models.CharField(max_length=120, blank=True)
    resource_id = models.CharField(max_length=120, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    snoozed_until = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class CredentialVaultItem(TenantScopedModel, ExternalReference):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_new_credentials")
    name = models.CharField(max_length=160)
    system_name = models.CharField(max_length=120, db_index=True)
    secret_reference = models.CharField(max_length=240)
    status = models.CharField(max_length=80, default="Active", db_index=True)
    last_rotated_at = models.DateTimeField(null=True, blank=True)
    rotation_due_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "system_name", "name"]


class CredentialShareGrant(TenantScopedModel):
    credential = models.ForeignKey("MainApp.CredentialVaultItem", on_delete=models.CASCADE, related_name="share_grants")
    grantee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="new_credential_share_grants")
    permission = models.CharField(max_length=80, default="Read")
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "credential", "grantee"], name="mainapp_credential_grant_once")]


class ExternalIssueReference(TenantScopedModel, ExternalReference):
    title = models.CharField(max_length=220)
    provider = models.CharField(max_length=80, db_index=True)
    issue_type = models.CharField(max_length=80, blank=True, db_index=True)
    priority = models.CharField(max_length=40, blank=True, db_index=True)
    status = models.CharField(max_length=80, blank=True, db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="new_external_issues")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "provider", "title"]


class NotificationSnoozeRecord(TenantScopedModel):
    notification = models.ForeignKey("MainApp.NotificationItem", on_delete=models.CASCADE, related_name="snooze_records")
    snoozed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="new_notification_snoozes")
    snoozed_until = models.DateTimeField()
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["tenant_id", "-snoozed_until"]


class ManagerScope(TenantScopedModel):
    manager = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="manager_scopes")
    employee = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.PROTECT, related_name="managed_by_scopes")
    department = models.ForeignKey("Users.Department", null=True, blank=True, on_delete=models.PROTECT, related_name="manager_scopes")
    scope_type = models.CharField(max_length=80, default="Department", db_index=True)
    status = models.CharField(max_length=60, default="Active", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "manager_id", "scope_type"]
