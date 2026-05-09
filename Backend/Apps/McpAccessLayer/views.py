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
from Backend.Apps.McpAccessLayer.mcp_server import mcp_server
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


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
    
    @action(detail=False, methods=["get"], url_path="available")
    def available_tools(self, request):
        """List all available MCP tools from the server"""
        tools = mcp_server.list_tools()
        return Response({"tools": tools})
    
    @action(detail=True, methods=["post"], url_path="invoke")
    def invoke_tool(self, request, pk=None):
        
        tool_definition = self.get_object()
        params = request.data.get("params", {})
        agent_id = request.data.get("agent_id")
        
        if agent_id:
            agent = AgentPrincipal.objects.filter(
                tenant=self.get_tenant_context().tenant,
                id=agent_id
            ).first()
            
            if not agent:
                return Response(
                    {"error": "Agent Principal Not Found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            allowed = McpPolicyService.can_invoke(
                self.get_tenant_context(),
                agent,
                tool=tool_definition
            )
            
            if not allowed:
                McpInvocationService.record_invocation(
                    self.get_tenant_context(),
                    agent,
                    "Invoke",
                    "Denied",
                    tool=tool_definition,
                    input_payload=params,
                    reason="Permission Denied"
                )
                
                return Response(
                    {"error": "Permission Denied"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        result = mcp_server.invoke_tool(
            self.get_tenant_context(),
            tool_definition.slug,
            params
        )
        
        if agent_id:
            McpInvocationService.record_invocation(
                self.get_tenant_context(),
                agent,
                "Invoke",
                "Allowed" if result.ok else "Failed",
                tool=tool_definition,
                input_payload=params,
                output_payload=result.data if result.ok else result.errors,
                reason=result.errors.get("error", "") if not result.ok else ""
            )
        
        if result.ok:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response(result.errors, status=result.status_code or status.HTTP_400_BAD_REQUEST)


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
