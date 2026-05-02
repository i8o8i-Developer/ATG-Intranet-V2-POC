from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditStampedModel(TimeStampedModel):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True


class Tenant(AuditStampedModel):
    STATUS_ACTIVE = "Active"
    STATUS_SUSPENDED = "Suspended"
    STATUS_ARCHIVED = "Archived"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_SUSPENDED, "Suspended"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=120, unique=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    legal_name = models.CharField(max_length=220, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Organization(AuditStampedModel):
    tenant = models.ForeignKey("EnterpriseCore.Tenant", on_delete=models.PROTECT, related_name="organizations")
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=120)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "slug"], name="enterprise_organization_slug_per_tenant")]

    def __str__(self):
        return self.name


class BusinessUnit(AuditStampedModel):
    tenant = models.ForeignKey("EnterpriseCore.Tenant", on_delete=models.PROTECT, related_name="business_units")
    organization = models.ForeignKey("EnterpriseCore.Organization", on_delete=models.PROTECT, related_name="business_units")
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=40)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "code"], name="enterprise_business_unit_code_per_tenant")]

    def clean(self):
        if self.organization_id and self.tenant_id and self.organization.tenant_id != self.tenant_id:
            raise ValidationError("Business Unit Organization Must Belong To The Same Tenant.")

    def __str__(self):
        return self.name


class Workspace(AuditStampedModel):
    tenant = models.ForeignKey("EnterpriseCore.Tenant", on_delete=models.PROTECT, related_name="workspaces")
    business_unit = models.ForeignKey("EnterpriseCore.BusinessUnit", on_delete=models.PROTECT, related_name="workspaces")
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=60)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "code"], name="enterprise_workspace_code_per_tenant")]

    def clean(self):
        if self.business_unit_id and self.tenant_id and self.business_unit.tenant_id != self.tenant_id:
            raise ValidationError("Workspace Business Unit Must Belong To The Same Tenant.")

    def __str__(self):
        return self.name


class Capability(AuditStampedModel):
    code = models.CharField(max_length=140, unique=True)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=100, db_index=True)

    class Meta:
        ordering = ["module", "code"]

    def __str__(self):
        return self.code


class Role(AuditStampedModel):
    tenant = models.ForeignKey("EnterpriseCore.Tenant", on_delete=models.PROTECT, related_name="roles")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)

    class Meta:
        ordering = ["tenant_id", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "code"], name="enterprise_role_code_per_tenant")]

    def __str__(self):
        return self.name


class RoleCapability(AuditStampedModel):
    tenant = models.ForeignKey("EnterpriseCore.Tenant", on_delete=models.PROTECT, related_name="role_capabilities")
    role = models.ForeignKey("EnterpriseCore.Role", on_delete=models.CASCADE, related_name="capability_links")
    capability = models.ForeignKey("EnterpriseCore.Capability", on_delete=models.PROTECT, related_name="role_links")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "role", "capability"], name="enterprise_role_capability_once")]

    def clean(self):
        if self.role_id and self.tenant_id and self.role.tenant_id != self.tenant_id:
            raise ValidationError("Role Capability Must Stay Within One Tenant.")


class RoleAssignment(AuditStampedModel):
    tenant = models.ForeignKey("EnterpriseCore.Tenant", on_delete=models.PROTECT, related_name="role_assignments")
    workspace = models.ForeignKey(
        "EnterpriseCore.Workspace",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="role_assignments",
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enterprise_role_assignments")
    role = models.ForeignKey("EnterpriseCore.Role", on_delete=models.PROTECT, related_name="assignments")
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "workspace", "user", "is_active"])]

    def clean(self):
        if self.role_id and self.tenant_id and self.role.tenant_id != self.tenant_id:
            raise ValidationError("Role Assignment Role Must Belong To The Same Tenant.")
        if self.workspace_id and self.tenant_id and self.workspace.tenant_id != self.tenant_id:
            raise ValidationError("Role Assignment Workspace Must Belong To The Same Tenant.")


class ResourcePolicy(AuditStampedModel):
    tenant = models.ForeignKey("EnterpriseCore.Tenant", on_delete=models.PROTECT, related_name="resource_policies")
    workspace = models.ForeignKey(
        "EnterpriseCore.Workspace",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="resource_policies",
    )
    resource_type = models.CharField(max_length=120)
    resource_id = models.CharField(max_length=120, blank=True)
    policy_code = models.CharField(max_length=120)
    constraints = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "workspace", "resource_type", "policy_code"])]


class AccessAuditLog(TimeStampedModel):
    tenant = models.ForeignKey("EnterpriseCore.Tenant", null=True, blank=True, on_delete=models.SET_NULL, related_name="access_audit_logs")
    workspace = models.ForeignKey(
        "EnterpriseCore.Workspace",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="access_audit_logs",
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="access_audit_logs")
    action = models.CharField(max_length=160, db_index=True)
    resource_type = models.CharField(max_length=120, db_index=True)
    resource_id = models.CharField(max_length=120, blank=True)
    decision = models.CharField(max_length=40, db_index=True)
    reason = models.TextField(blank=True)
    request_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant", "actor", "action", "created_at"])]


class TenantScopedModel(AuditStampedModel):
    tenant = models.ForeignKey("EnterpriseCore.Tenant", on_delete=models.PROTECT)
    workspace = models.ForeignKey("EnterpriseCore.Workspace", null=True, blank=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True

    def clean(self):
        if self.workspace_id and self.tenant_id and self.workspace.tenant_id != self.tenant_id:
            raise ValidationError("Workspace Must Belong To The Same Tenant As The Record.")


class ExternalReference(models.Model):
    source_system = models.CharField(max_length=80, blank=True, db_index=True)
    external_id = models.CharField(max_length=180, blank=True, db_index=True)
    external_url = models.URLField(blank=True)
    external_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True


class OutboxEvent(TimeStampedModel):
    STATUS_PENDING = "Pending"
    STATUS_PROCESSING = "Processing"
    STATUS_COMPLETED = "Completed"
    STATUS_FAILED = "Failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    tenant = models.ForeignKey("EnterpriseCore.Tenant", null=True, blank=True, on_delete=models.PROTECT, related_name="outbox_events")
    workspace = models.ForeignKey(
        "EnterpriseCore.Workspace",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="outbox_events",
    )
    aggregate_type = models.CharField(max_length=120, db_index=True)
    aggregate_id = models.CharField(max_length=120, db_index=True)
    event_type = models.CharField(max_length=160, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    idempotency_key = models.CharField(max_length=160, blank=True, db_index=True)
    scheduled_at = models.DateTimeField(default=timezone.now, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["scheduled_at"]
        indexes = [models.Index(fields=["status", "scheduled_at"])]


class IdempotencyKey(TimeStampedModel):
    tenant = models.ForeignKey("EnterpriseCore.Tenant", null=True, blank=True, on_delete=models.PROTECT, related_name="idempotency_keys")
    key = models.CharField(max_length=180)
    request_hash = models.CharField(max_length=128)
    response_payload = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "key"], name="enterprise_idempotency_key_per_tenant")]
