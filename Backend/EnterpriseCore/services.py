from dataclasses import dataclass, field
from typing import Any

from django.utils import timezone

from Backend.EnterpriseCore.models import AccessAuditLog, OutboxEvent, RoleAssignment


@dataclass(frozen=True)
class TenantContext:
    tenant: Any
    workspace: Any = None
    actor: Any = None
    source: str = "Api"


@dataclass(frozen=True)
class ServiceResult:
    ok: bool
    data: Any = None
    errors: dict[str, Any] = field(default_factory=dict)
    status_code: int = 200

    @classmethod
    def success(cls, data=None, status_code=200):
        return cls(ok=True, data=data, status_code=status_code)

    @classmethod
    def failure(cls, errors, status_code=400):
        return cls(ok=False, errors=errors, status_code=status_code)


class AuditService:
    @staticmethod
    def log_access(context, action, resource_type, resource_id="", decision="Allowed", reason="", metadata=None):
        return AccessAuditLog.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            actor=context.actor,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id or ""),
            decision=decision,
            reason=reason,
            request_metadata=metadata or {},
        )


class OutboxService:
    @staticmethod
    def publish(context, aggregate_type, aggregate_id, event_type, payload=None, idempotency_key=""):
        return OutboxEvent.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            event_type=event_type,
            payload=payload or {},
            idempotency_key=idempotency_key,
            scheduled_at=timezone.now(),
        )


class CapabilityService:
    @staticmethod
    def list_user_capabilities(tenant, user, workspace=None):
        assignments = RoleAssignment.objects.filter(tenant=tenant, user=user, is_active=True).select_related("role")
        if workspace:
            assignments = assignments.filter(workspace__in=[workspace, None])
        return set(
            assignments.values_list("role__capability_links__capability__code", flat=True).exclude(
                role__capability_links__capability__code__isnull=True
            )
        )
