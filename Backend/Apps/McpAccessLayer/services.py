from Backend.Apps.McpAccessLayer.models import DraftAgentAction, McpAccessGrant, McpInvocationAudit
from Backend.EnterpriseCore.services import ServiceResult


class McpPolicyService:
    @staticmethod
    def can_invoke(context, agent, tool=None, resource=None, permission="Read"):
        grants = McpAccessGrant.objects.filter(tenant=context.tenant, agent=agent, permission=permission)
        if tool:
            grants = grants.filter(tool=tool)
        if resource:
            grants = grants.filter(resource=resource)
        return grants.exists()


class McpInvocationService:
    @staticmethod
    def record_invocation(context, agent, action, decision, tool=None, resource=None, input_payload=None, output_payload=None, reason=""):
        audit = McpInvocationAudit.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            agent=agent,
            tool=tool,
            resource=resource,
            action=action,
            decision=decision,
            input_payload=input_payload or {},
            output_payload=output_payload or {},
            reason=reason,
            created_by=context.actor,
        )
        return ServiceResult.success(audit, status_code=201)

    @staticmethod
    def create_draft_action(context, agent, action_type, target_resource_type, target_resource_id="", payload=None):
        draft = DraftAgentAction.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            agent=agent,
            action_type=action_type,
            target_resource_type=target_resource_type,
            target_resource_id=str(target_resource_id or ""),
            payload=payload or {},
            created_by=context.actor,
        )
        return ServiceResult.success(draft, status_code=201)
