from celery import shared_task

from Backend.Apps.Assesment.models import AssessmentAssignment
from Backend.Apps.Assesment.services import AssessmentAssignmentService, AssessmentQueryService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


@shared_task
def create_overdue_assessment_reminders(tenant_id, workspace_id=None, grace_days=5):
    tenant = Tenant.objects.get(id=tenant_id)
    workspace = Workspace.objects.filter(id=workspace_id, tenant=tenant).first() if workspace_id else None
    context = TenantContext(tenant=tenant, workspace=workspace, source="Celery")
    result = AssessmentQueryService.create_overdue_reminders(context, grace_days=grace_days)
    return result.data


@shared_task
def sync_assessment_assignment_from_provider(tenant_id, assignment_id, provider_payload):
    tenant = Tenant.objects.get(id=tenant_id)
    assignment = AssessmentAssignment.objects.get(tenant=tenant, id=assignment_id)
    context = TenantContext(tenant=tenant, workspace=assignment.workspace, source="Celery")
    result = AssessmentAssignmentService.sync_provider_status(context, assignment_id, provider_payload)
    return {"ok": result.ok, "errors": result.errors, "assignment": assignment_id}
