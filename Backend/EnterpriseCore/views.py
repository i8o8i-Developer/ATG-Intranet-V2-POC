from rest_framework import viewsets

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
from Backend.EnterpriseCore.serializers import (
    AccessAuditLogSerializer,
    BusinessUnitSerializer,
    CapabilitySerializer,
    IdempotencyKeySerializer,
    OrganizationSerializer,
    OutboxEventSerializer,
    ResourcePolicySerializer,
    RoleAssignmentSerializer,
    RoleCapabilitySerializer,
    RoleSerializer,
    TenantSerializer,
    WorkspaceSerializer,
)
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer


class OrganizationViewSet(TenantScopedModelViewSet):
    queryset = Organization.objects.select_related("tenant").all()
    serializer_class = OrganizationSerializer


class BusinessUnitViewSet(TenantScopedModelViewSet):
    queryset = BusinessUnit.objects.select_related("tenant", "organization").all()
    serializer_class = BusinessUnitSerializer


class WorkspaceViewSet(TenantScopedModelViewSet):
    queryset = Workspace.objects.select_related("tenant", "business_unit").all()
    serializer_class = WorkspaceSerializer


class CapabilityViewSet(viewsets.ModelViewSet):
    queryset = Capability.objects.all()
    serializer_class = CapabilitySerializer


class RoleViewSet(TenantScopedModelViewSet):
    queryset = Role.objects.select_related("tenant").all()
    serializer_class = RoleSerializer


class RoleCapabilityViewSet(TenantScopedModelViewSet):
    queryset = RoleCapability.objects.select_related("tenant", "role", "capability").all()
    serializer_class = RoleCapabilitySerializer


class RoleAssignmentViewSet(TenantScopedModelViewSet):
    queryset = RoleAssignment.objects.select_related("tenant", "workspace", "role", "user").all()
    serializer_class = RoleAssignmentSerializer


class ResourcePolicyViewSet(TenantScopedModelViewSet):
    queryset = ResourcePolicy.objects.select_related("tenant", "workspace").all()
    serializer_class = ResourcePolicySerializer


class AccessAuditLogViewSet(TenantScopedModelViewSet):
    queryset = AccessAuditLog.objects.select_related("tenant", "workspace", "actor").all()
    serializer_class = AccessAuditLogSerializer


class OutboxEventViewSet(TenantScopedModelViewSet):
    queryset = OutboxEvent.objects.select_related("tenant", "workspace").all()
    serializer_class = OutboxEventSerializer


class IdempotencyKeyViewSet(TenantScopedModelViewSet):
    queryset = IdempotencyKey.objects.select_related("tenant").all()
    serializer_class = IdempotencyKeySerializer
