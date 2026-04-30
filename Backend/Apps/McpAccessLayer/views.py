from Backend.Apps.McpAccessLayer.models import AgentPrincipal, DraftAgentAction, McpAccessGrant, McpInvocationAudit, McpResourceDefinition, McpToolDefinition
from Backend.Apps.McpAccessLayer.serializers import (
    AgentPrincipalSerializer,
    DraftAgentActionSerializer,
    McpAccessGrantSerializer,
    McpInvocationAuditSerializer,
    McpResourceDefinitionSerializer,
    McpToolDefinitionSerializer,
)
from Backend.Apps.McpAccessLayer.services import McpInvocationService, McpPolicyService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


class AgentPrincipalViewSet(TenantScopedModelViewSet):
    queryset = AgentPrincipal.objects.select_related("tenant", "workspace", "owner").all()
    serializer_class = AgentPrincipalSerializer

    @action(detail=True, methods=["post"], url_path="can-invoke")
    def can_invoke(self, request, pk=None):
        tool = McpToolDefinition.objects.filter(tenant=self.get_tenant_context().tenant, id=request.data.get("tool")).first() if request.data.get("tool") else None
        resource = McpResourceDefinition.objects.filter(tenant=self.get_tenant_context().tenant, id=request.data.get("resource")).first() if request.data.get("resource") else None
        allowed = McpPolicyService.can_invoke(
            self.get_tenant_context(),
            self.get_object(),
            tool=tool,
            resource=resource,
            permission=request.data.get("permission", "Read"),
        )
        return Response({"allowed": allowed})

    @action(detail=True, methods=["post"], url_path="record-invocation")
    def record_invocation(self, request, pk=None):
        tool = McpToolDefinition.objects.filter(tenant=self.get_tenant_context().tenant, id=request.data.get("tool")).first() if request.data.get("tool") else None
        resource = McpResourceDefinition.objects.filter(tenant=self.get_tenant_context().tenant, id=request.data.get("resource")).first() if request.data.get("resource") else None
        result = McpInvocationService.record_invocation(
            self.get_tenant_context(),
            self.get_object(),
            request.data.get("action", "Invoke"),
            request.data.get("decision", "Allowed"),
            tool=tool,
            resource=resource,
            input_payload=request.data.get("input_payload") or {},
            output_payload=request.data.get("output_payload") or {},
            reason=request.data.get("reason", ""),
        )
        return self.service_response(result, McpInvocationAuditSerializer)

    @action(detail=True, methods=["post"], url_path="draft-action")
    def draft_action(self, request, pk=None):
        result = McpInvocationService.create_draft_action(
            self.get_tenant_context(),
            self.get_object(),
            request.data.get("action_type", "Draft"),
            request.data.get("target_resource_type", "Unknown"),
            target_resource_id=request.data.get("target_resource_id", ""),
            payload=request.data.get("payload") or {},
        )
        return self.service_response(result, DraftAgentActionSerializer)


class McpToolDefinitionViewSet(TenantScopedModelViewSet):
    queryset = McpToolDefinition.objects.select_related("tenant", "workspace").all()
    serializer_class = McpToolDefinitionSerializer


class McpResourceDefinitionViewSet(TenantScopedModelViewSet):
    queryset = McpResourceDefinition.objects.select_related("tenant", "workspace").all()
    serializer_class = McpResourceDefinitionSerializer


class McpAccessGrantViewSet(TenantScopedModelViewSet):
    queryset = McpAccessGrant.objects.select_related("tenant", "workspace", "agent", "tool", "resource").all()
    serializer_class = McpAccessGrantSerializer


class McpInvocationAuditViewSet(TenantScopedModelViewSet):
    queryset = McpInvocationAudit.objects.select_related("tenant", "workspace", "agent", "tool", "resource").all()
    serializer_class = McpInvocationAuditSerializer


class DraftAgentActionViewSet(TenantScopedModelViewSet):
    queryset = DraftAgentAction.objects.select_related("tenant", "workspace", "agent").all()
    serializer_class = DraftAgentActionSerializer
