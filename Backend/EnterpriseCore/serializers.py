from rest_framework import serializers

from Backend.EnterpriseCore.models import (
    AccessAuditLog,
    BusinessUnit,
    Capability,
    IdempotencyKey,
    Organization,
    OutboxEvent,
    ResourcePolicy,
    Role,
    RoleAssignment,
    RoleCapability,
    Tenant,
    Workspace,
)


class TenantScopedSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        tenant = attrs.get("tenant") or getattr(self.instance, "tenant", None)
        workspace = attrs.get("workspace") or getattr(self.instance, "workspace", None)
        if tenant and workspace and workspace.tenant_id != tenant.id:
            raise serializers.ValidationError({"workspace": "Workspace Must Belong To The Same Tenant."})
        return attrs


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = "__all__"


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"


class BusinessUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUnit
        fields = "__all__"


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = "__all__"


class CapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Capability
        fields = "__all__"


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class RoleCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleCapability
        fields = "__all__"


class RoleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleAssignment
        fields = "__all__"


class ResourcePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourcePolicy
        fields = "__all__"


class AccessAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessAuditLog
        fields = "__all__"
        read_only_fields = ["created_at"]


class OutboxEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutboxEvent
        fields = "__all__"


class IdempotencyKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = IdempotencyKey
        fields = "__all__"
