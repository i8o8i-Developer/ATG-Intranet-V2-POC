from rest_framework.routers import DefaultRouter

from Backend.Apps.McpAccessLayer import views

router = DefaultRouter()
router.register("AgentPrincipals", views.AgentPrincipalViewSet, basename="mcp-agent-principals")
router.register("McpToolDefinitions", views.McpToolDefinitionViewSet, basename="mcp-tool-definitions")
router.register("McpResourceDefinitions", views.McpResourceDefinitionViewSet, basename="mcp-resource-definitions")
router.register("McpAccessGrants", views.McpAccessGrantViewSet, basename="mcp-access-grants")
router.register("McpInvocationAudits", views.McpInvocationAuditViewSet, basename="mcp-invocation-audits")
router.register("DraftAgentActions", views.DraftAgentActionViewSet, basename="mcp-draft-agent-actions")

urlpatterns = router.urls
