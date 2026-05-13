from django.utils import timezone
from django.db.models import Count, Q

from Backend.Apps.Banao.models import LeadAccount, LeadNote, LeadTag, ProposalArtifact
from Backend.Apps.Banao.services import LeadWorkflowService
from Backend.Apps.Lms.models import LeadQueueSnapshot, LearningAssignment, RevenuePerformanceSnapshot
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class LearningAssignmentService:
    @staticmethod
    def mark_complete(context, assignment_id):
        assignment = LearningAssignment.objects.filter(tenant=context.tenant, id=assignment_id).first()
        if not assignment:
            return ServiceResult.failure({"assignment": "Learning Assignment Not Found."}, status_code=404)
        assignment.status = "Completed"
        assignment.completed_at = timezone.now()
        assignment.updated_by = context.actor
        assignment.save(update_fields=["status", "completed_at", "updated_by", "updated_at"])
        OutboxService.publish(context, "LearningAssignment", assignment.id, "LearningAssignmentCompleted", {"employeeId": assignment.employee_id})
        return ServiceResult.success(assignment)


class LeadManagementService:
    @staticmethod
    def _bool_filter(value):
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        text = str(value).strip().lower()
        if text in {"1", "true", "yes"}:
            return True
        if text in {"0", "false", "no"}:
            return False
        return None

    @staticmethod
    def list_leads(context, filters=None):
        filters = filters or {}
        leads = LeadAccount.objects.filter(tenant=context.tenant).select_related("owner", "owner__user", "owner__department").prefetch_related("tags", "notes", "proposals", "activities")
        owner_id = filters.get("owner") or filters.get("assigned_to") or filters.get("owner_id")
        if owner_id:
            leads = leads.filter(owner_id=owner_id)
        stage = filters.get("stage") or filters.get("workflow_status")
        if stage:
            if isinstance(stage, str) and "," in stage:
                leads = leads.filter(stage__in=[item.strip() for item in stage.split(",") if item.strip()])
            else:
                leads = leads.filter(stage=stage)
        source = filters.get("origin") or filters.get("source")
        if source:
            if isinstance(source, str) and "," in source:
                leads = leads.filter(source__in=[item.strip() for item in source.split(",") if item.strip()])
            else:
                leads = leads.filter(source=source)
        search = filters.get("search") or filters.get("search_query")
        if search:
            leads = leads.filter(Q(company_name__icontains=search) | Q(source__icontains=search) | Q(industry__icontains=search) | Q(website_url__icontains=search))
        tags = filters.get("tags")
        if tags:
            tag_ids = [int(item.strip()) for item in str(tags).split(",") if item.strip().isdigit()]
            if tag_ids:
                leads = leads.filter(tags__id__in=tag_ids).distinct()
        follow_up_state = LeadManagementService._bool_filter(filters.get("fu_set"))
        if follow_up_state is True:
            leads = leads.filter(next_follow_up_at__isnull=False)
        elif follow_up_state is False:
            leads = leads.filter(next_follow_up_at__isnull=True)
        if LeadManagementService._bool_filter(filters.get("overdue")):
            leads = leads.filter(next_follow_up_at__lt=timezone.now()).exclude(stage__in=["ClosedWon", "ClosedLost"])
        if LeadManagementService._bool_filter(filters.get("action_pending")):
            leads = leads.exclude(action_item__in=["", "[]"])
        sort_by = filters.get("sort_by") or filters.get("ordering")
        allowed_sorts = {"created_at", "updated_at", "next_follow_up_at", "company_name", "estimated_value"}
        if sort_by:
            sort_field = str(sort_by).lstrip("-")
            leads = leads.order_by(sort_by if sort_field in allowed_sorts else "-created_at")
        else:
            leads = leads.order_by("-created_at")
        try:
            result_limit = int(str(filters.get("limit", "100")))
        except (ValueError, TypeError):
            result_limit = 100
        rows = [
            {
                "id": lead.id,
                "company_name": lead.company_name,
                "stage": lead.stage,
                "priority": lead.priority,
                "owner_id": lead.owner_id,
                "owner_name": lead.owner.display_name if lead.owner_id else "",
                "estimated_value": str(lead.estimated_value),
                "source": lead.source,
                "next_follow_up_at": lead.next_follow_up_at.isoformat() if lead.next_follow_up_at else None,
                "tags": [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in lead.tags.all()],
                "notes_count": lead.notes.count(),
            }
            for lead in leads[: max(1, min(result_limit, 500))]
        ]
        origin_counts = {item["source"] or "": item["count"] for item in leads.values("source").annotate(count=Count("id"))}
        return ServiceResult.success({"count": leads.count(), "results": rows, "origin_counts": origin_counts})

    @staticmethod
    def create_lead(context, data):
        return LeadWorkflowService.capture_lead(
            context,
            company_name=data.get("company_name") or data.get("company") or "Untitled Lead",
            source=data.get("source", "LMS"),
            priority=data.get("priority", "Normal"),
            owner_id=data.get("owner") or data.get("owner_id") or data.get("assigned_to"),
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
            return ServiceResult.failure({"lead": "Lead Not Found."}, status_code=404)
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
    def dashboard_context(context):
        workload = LeadManagementService.weekly_workload(context)
        return ServiceResult.success({"is_user_jr_ba": False, "is_lms_manager": False, "bas": workload.data.get("rows", [])})

    @staticmethod
    def ba_dashboard(context, employee_id):
        leads = LeadAccount.objects.filter(tenant=context.tenant, owner_id=employee_id)
        by_stage = list(leads.values("stage").annotate(count=Count("id")).order_by("stage"))
        notes_count = LeadNote.objects.filter(tenant=context.tenant, lead__owner_id=employee_id).count()
        proposal_count = ProposalArtifact.objects.filter(tenant=context.tenant, lead__owner_id=employee_id).count()
        return ServiceResult.success({"employee_id": employee_id, "lead_count": leads.count(), "by_stage": by_stage, "notes_count": notes_count, "proposal_count": proposal_count})

    @staticmethod
    def jrba_dashboard(context, employee_id):
        dashboard = LeadManagementService.ba_dashboard(context, employee_id)
        if not dashboard.ok:
            return dashboard
        leads = LeadManagementService.list_leads(context, {"owner": employee_id, "limit": 25})
        return ServiceResult.success({**dashboard.data, "leads": leads.data["results"]})

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
    def note_updated_today(context, lead_id):
        today = timezone.localdate()
        updated_today = LeadNote.objects.filter(tenant=context.tenant, lead_id=lead_id, created_at__date=today).exists()
        return ServiceResult.success({"lead_id": lead_id, "updated_today": updated_today})

    @staticmethod
    def weekly_workload(context):
        rows = list(LeadAccount.objects.filter(tenant=context.tenant).values("owner_id", "owner__display_name", "stage").annotate(count=Count("id")).order_by("owner_id", "stage"))
        return ServiceResult.success({"rows": rows})

    @staticmethod
    def analytics_closures(context, days=60):
        since = timezone.now() - timezone.timedelta(days=int(days))
        closed = LeadAccount.objects.filter(tenant=context.tenant, stage__in=["ClosedWon", "ClosedLost"], updated_at__gte=since)
        by_owner = list(closed.values("owner_id", "owner__display_name", "stage").annotate(count=Count("id")).order_by("owner_id", "stage"))
        total_value = sum(lead.estimated_value or 0 for lead in closed)
        return ServiceResult.success({"days": int(days), "count": closed.count(), "estimated_value": str(total_value), "rows": by_owner})

    @staticmethod
    def lead_detail(context, lead_id):
        lead = LeadAccount.objects.filter(tenant=context.tenant, id=lead_id).prefetch_related("tags", "notes", "proposals", "activities").select_related("owner").first()
        if not lead:
            return ServiceResult.failure({"lead": "Lead Not Found."}, status_code=404)
        bas = LeadManagementService.business_analysts(context)
        return ServiceResult.success(
            {
                "lead_id": lead.id,
                "company_name": lead.company_name,
                "stage": lead.stage,
                "priority": lead.priority,
                "owner_id": lead.owner_id,
                "estimated_value": str(lead.estimated_value),
                "tags": [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in lead.tags.all()],
                "notes": [{"id": note.id, "title": note.title, "body": note.body} for note in lead.notes.all()[:20]],
                "proposal_count": lead.proposals.count(),
                "activity_count": lead.activities.count(),
                "bas": bas.data,
            }
        )

    @staticmethod
    def lead_edit_context(context, lead_id):
        detail = LeadManagementService.lead_detail(context, lead_id)
        if not detail.ok:
            return detail
        return ServiceResult.success(detail.data)

    @staticmethod
    def list_tags(context):
        tags = LeadTag.objects.filter(tenant=context.tenant).order_by("name")
        return ServiceResult.success([{"id": tag.id, "name": tag.name, "color": tag.color} for tag in tags])

    @staticmethod
    def create_tag(context, data):
        name = (data.get("name") or "").strip()
        if not name:
            return ServiceResult.failure({"name": "This Field Is Required."}, status_code=400)
        tag, _created = LeadTag.objects.get_or_create(
            tenant=context.tenant,
            name=name,
            defaults={"workspace": context.workspace, "color": data.get("color", "")},
        )
        if data.get("color") and tag.color != data.get("color"):
            tag.color = data.get("color", "")
            tag.updated_by = context.actor
            tag.save(update_fields=["color", "updated_by", "updated_at"])
        return ServiceResult.success({"id": tag.id, "name": tag.name, "color": tag.color}, status_code=201)

    @staticmethod
    def analytics_dashboard(context, days=60):
        closures = LeadManagementService.analytics_closures(context, days=days)
        workload = LeadManagementService.weekly_workload(context)
        return ServiceResult.success({"closures": closures.data, "workload": workload.data})

    @staticmethod
    def eod_performance(context):
        rows = list(
            LeadAccount.objects.filter(tenant=context.tenant)
            .values("owner_id", "owner__display_name")
            .annotate(
                lead_count=Count("id"),
                proposal_count=Count("proposals", distinct=True),
                overdue_count=Count("id", filter=Q(next_follow_up_at__lt=timezone.now())),
            )
            .order_by("owner__display_name")
        )
        return ServiceResult.success({"rows": rows})
