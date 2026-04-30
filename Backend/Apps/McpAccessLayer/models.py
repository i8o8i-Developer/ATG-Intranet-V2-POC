from django.db import models

from Backend.EnterpriseCore.models import TenantScopedModel


class AgentPrincipal(TenantScopedModel):
    name = models.CharField(max_length=180)
    principal_key = models.CharField(max_length=160)
    status = models.CharField(max_length=80, default="Active", db_index=True)
    owner = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_agent_principals")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "principal_key"], name="mcp_agent_principal_key_per_tenant")]


class McpToolDefinition(TenantScopedModel):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=120)
    owning_module = models.CharField(max_length=120, db_index=True)
    description = models.TextField(blank=True)
    input_schema = models.JSONField(default=dict, blank=True)
    output_schema = models.JSONField(default=dict, blank=True)
    is_mutating = models.BooleanField(default=False, db_index=True)
    status = models.CharField(max_length=80, default="Draft", db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "slug"], name="mcp_tool_slug_per_tenant")]


class McpResourceDefinition(TenantScopedModel):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=120)
    owning_module = models.CharField(max_length=120, db_index=True)
    description = models.TextField(blank=True)
    resource_schema = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=80, default="Draft", db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "slug"], name="mcp_resource_slug_per_tenant")]


class McpAccessGrant(TenantScopedModel):
    agent = models.ForeignKey("McpAccessLayer.AgentPrincipal", on_delete=models.CASCADE, related_name="access_grants")
    tool = models.ForeignKey("McpAccessLayer.McpToolDefinition", null=True, blank=True, on_delete=models.CASCADE, related_name="access_grants")
    resource = models.ForeignKey("McpAccessLayer.McpResourceDefinition", null=True, blank=True, on_delete=models.CASCADE, related_name="access_grants")
    permission = models.CharField(max_length=80, default="Read")
    constraints = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "agent", "permission"])]


class McpInvocationAudit(TenantScopedModel):
    agent = models.ForeignKey("McpAccessLayer.AgentPrincipal", null=True, blank=True, on_delete=models.SET_NULL, related_name="invocation_audits")
    tool = models.ForeignKey("McpAccessLayer.McpToolDefinition", null=True, blank=True, on_delete=models.SET_NULL, related_name="invocation_audits")
    resource = models.ForeignKey("McpAccessLayer.McpResourceDefinition", null=True, blank=True, on_delete=models.SET_NULL, related_name="invocation_audits")
    action = models.CharField(max_length=160, db_index=True)
    decision = models.CharField(max_length=80, db_index=True)
    input_payload = models.JSONField(default=dict, blank=True)
    output_payload = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class DraftAgentAction(TenantScopedModel):
    agent = models.ForeignKey("McpAccessLayer.AgentPrincipal", on_delete=models.PROTECT, related_name="draft_actions")
    action_type = models.CharField(max_length=160, db_index=True)
    target_resource_type = models.CharField(max_length=120, db_index=True)
    target_resource_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=80, default="Draft", db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    approval_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]
