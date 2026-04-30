from rest_framework import serializers

from Backend.Apps.McpAccessLayer.models import AgentPrincipal, DraftAgentAction, McpAccessGrant, McpInvocationAudit, McpResourceDefinition, McpToolDefinition


class AgentPrincipalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentPrincipal
        fields = "__all__"


class McpToolDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = McpToolDefinition
        fields = "__all__"


class McpResourceDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = McpResourceDefinition
        fields = "__all__"


class McpAccessGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = McpAccessGrant
        fields = "__all__"


class McpInvocationAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = McpInvocationAudit
        fields = "__all__"


class DraftAgentActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DraftAgentAction
        fields = "__all__"
