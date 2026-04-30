from django.utils import timezone
from django.db.models import Count, Q

from Backend.Apps.Banao.models import LeadAccount, LeadNote, ProposalArtifact
from Backend.Apps.Banao.services import LeadWorkflowService
from Backend.Apps.Lms.models import LeadQueueSnapshot, LearningAssignment, RevenuePerformanceSnapshot
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class LearningAssignmentService:
    @staticmethod
    def mark_complete(context, assignment_id):
        assignment = LearningAssignment.objects.filter(tenant=context.tenant, id=assignment_id).first()
        if not assignment:
            return ServiceResult.failure({"assignment": "Learning assignment not found."}, status_code=404)
        assignment.status = "Completed"
        assignment.completed_at = timezone.now()
        assignment.updated_by = context.actor
        assignment.save(update_fields=["status", "completed_at", "updated_by", "updated_at"])
        OutboxService.publish(context, "LearningAssignment", assignment.id, "LearningAssignmentCompleted", {"employeeId": assignment.employee_id})
        return ServiceResult.success(assignment)


class LeadManagementService:
    @staticmethod
    def list_leads(context, filters=None):
        filters = filters or {}
        leads = LeadAccount.objects.filter(tenant=context.tenant).select_related("owner")
        if filters.get("owner"):
            leads = leads.filter(owner_id=filters["owner"])
        if filters.get("stage"):
            leads = leads.filter(stage=filters["stage"])
        if filters.get("search"):
            leads = leads.filter(company_name__icontains=filters["search"])
        rows = [
            {
                "id": lead.id,
                "company_name": lead.company_name,
                "stage": lead.stage,
                "priority": lead.priority,
                "owner_id": lead.owner_id,
                "estimated_value": str(lead.estimated_value),
                "source": lead.source,
            }
            for lead in leads.order_by("company_name")[: int(filters.get("limit", 100))]
        ]
        return ServiceResult.success({"count": leads.count(), "results": rows})

    @staticmethod
    def create_lead(context, data):
        return LeadWorkflowService.capture_lead(
            context,
            company_name=data.get("company_name") or data.get("company") or "Untitled Lead",
            source=data.get("source", "LMS"),
            priority=data.get("priority", "Normal"),
            owner_id=data.get("owner") or data.get("owner_id"),
            estimated_value=data.get("estimated_value", 0),
            currency=data.get("currency", "INR"),
            contact_name=data.get("contact_name", ""),
            contact_email=data.get("contact_email", ""),
            contact_phone=data.get("contact_phone", ""),
            metadata=data.get("metadata") or {},
        )

    @staticmethod
    def add_note(context, lead_id, body, author_id=None, title=""):
        return LeadWorkflowService.add_note(context, lead_id, body=body, author_id=author_id, title=title)

    @staticmethod
    def lead_dashboard(context, lead_id):
        lead = LeadAccount.objects.filter(tenant=context.tenant, id=lead_id).first()
        if not lead:
            return ServiceResult.failure({"lead": "Lead not found."}, status_code=404)
        return ServiceResult.success(
            {
                "id": lead.id,
                "company_name": lead.company_name,
                "stage": lead.stage,
                "owner_id": lead.owner_id,
                "notes_count": lead.notes.count(),
                "activity_count": lead.activities.count(),
                "proposal_count": lead.proposals.count(),
                "audit_count": lead.audits.count(),
            }
        )

    @staticmethod
    def business_analysts(context):
        from Backend.Apps.Users.models import EmployeeProfile

        employees = EmployeeProfile.objects.filter(tenant=context.tenant, is_active=True).select_related("user", "department")
        rows = [{"id": employee.id, "display_name": employee.display_name, "department": employee.department.name if employee.department_id else ""} for employee in employees.order_by("display_name")]
        return ServiceResult.success(rows)

    @staticmethod
    def ba_dashboard(context, employee_id):
        leads = LeadAccount.objects.filter(tenant=context.tenant, owner_id=employee_id)
        by_stage = list(leads.values("stage").annotate(count=Count("id")).order_by("stage"))
        notes_count = LeadNote.objects.filter(tenant=context.tenant, lead__owner_id=employee_id).count()
        proposal_count = ProposalArtifact.objects.filter(tenant=context.tenant, lead__owner_id=employee_id).count()
        return ServiceResult.success({"employee_id": employee_id, "lead_count": leads.count(), "by_stage": by_stage, "notes_count": notes_count, "proposal_count": proposal_count})

    @staticmethod
    def create_queue_snapshot(context, employee_id=None, snapshot_date=None):
        snapshot_date = snapshot_date or timezone.localdate()
        leads = LeadAccount.objects.filter(tenant=context.tenant)
        if employee_id:
            leads = leads.filter(owner_id=employee_id)
        stale_count = leads.exclude(stage__in=["ClosedWon", "ClosedLost"]).filter(Q(activities__isnull=True) | Q(notes__isnull=True)).distinct().count()
        proposal_count = ProposalArtifact.objects.filter(tenant=context.tenant, lead__in=leads).count()
        snapshot, _created = LeadQueueSnapshot.objects.update_or_create(
            tenant=context.tenant,
            employee_id=employee_id,
            snapshot_date=snapshot_date,
            defaults={
                "workspace": context.workspace,
                "open_count": leads.exclude(stage__in=["ClosedWon", "ClosedLost"]).count(),
                "stale_count": stale_count,
                "follow_up_due_count": leads.filter(activities__scheduled_at__date__lte=snapshot_date, activities__completed_at__isnull=True).distinct().count(),
                "proposal_count": proposal_count,
                "metrics": {"by_stage": list(leads.values("stage").annotate(count=Count("id")))},
                "updated_by": context.actor,
            },
        )
        return ServiceResult.success(snapshot)

    @staticmethod
    def check_leads_without_today_note(context):
        today = timezone.localdate()
        leads = LeadAccount.objects.filter(tenant=context.tenant).exclude(notes__created_at__date=today).distinct()
        return ServiceResult.success({"count": leads.count(), "lead_ids": list(leads.values_list("id", flat=True)[:200])})

    @staticmethod
    def weekly_workload(context):
        rows = list(LeadAccount.objects.filter(tenant=context.tenant).values("owner_id", "stage").annotate(count=Count("id")).order_by("owner_id", "stage"))
        return ServiceResult.success({"rows": rows})

    @staticmethod
    def analytics_closures(context, days=60):
        since = timezone.now() - timezone.timedelta(days=int(days))
        closed = LeadAccount.objects.filter(tenant=context.tenant, stage__in=["ClosedWon", "ClosedLost"], updated_at__gte=since)
        return ServiceResult.success({"days": int(days), "count": closed.count(), "estimated_value": str(sum(lead.estimated_value for lead in closed))})
