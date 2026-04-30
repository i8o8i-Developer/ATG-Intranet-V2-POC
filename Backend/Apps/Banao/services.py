from django.db.models import Count
from django.utils import timezone

from Backend.Apps.Banao.email_templates import get_audit_email_template, get_bbd_email_template, get_offer_letter_template
from Backend.Apps.Banao.models import AuditArtifact, LeadAccount, LeadActivity, LeadContact, LeadNote, LeadTest, ProposalArtifact, WorkflowStatusHistory, WorkflowTransition
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class LeadWorkflowService:
    @staticmethod
    def capture_lead(context, company_name, source="", priority="Normal", owner_id=None, estimated_value=0, currency="INR", contact_name="", contact_email="", contact_phone="", metadata=None):
        lead = LeadAccount.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            company_name=company_name,
            source=source,
            priority=priority,
            owner_id=owner_id,
            estimated_value=estimated_value or 0,
            currency=currency,
            metadata=metadata or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        if contact_name or contact_email or contact_phone:
            LeadContact.objects.create(
                tenant=context.tenant,
                workspace=context.workspace,
                lead=lead,
                name=contact_name or company_name,
                email=contact_email,
                phone=contact_phone,
                is_primary=True,
                created_by=context.actor,
                updated_by=context.actor,
            )
        LeadActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            lead=lead,
            activity_type="LeadCaptured",
            title="Lead captured",
            payload={"source": source},
            created_by=context.actor,
        )
        OutboxService.publish(context, "LeadAccount", lead.id, "LeadCaptured", {"company": company_name})
        return ServiceResult.success(lead, status_code=201)

    @staticmethod
    def move_stage(context, lead_id, to_stage, reason=""):
        lead = LeadAccount.objects.filter(tenant=context.tenant, id=lead_id).first()
        if not lead:
            return ServiceResult.failure({"lead": "Lead not found."}, status_code=404)
        from_stage = lead.stage
        lead.stage = to_stage
        lead.updated_by = context.actor
        lead.save(update_fields=["stage", "updated_by", "updated_at"])
        WorkflowTransition.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            lead=lead,
            from_stage=from_stage,
            to_stage=to_stage,
            reason=reason,
            created_by=context.actor,
        )
        OutboxService.publish(context, "LeadAccount", lead.id, "LeadStageChanged", {"from": from_stage, "to": to_stage})
        return ServiceResult.success(lead)

    @staticmethod
    def add_note(context, lead_id, body, title="", author_id=None, metadata=None):
        lead = LeadAccount.objects.filter(tenant=context.tenant, id=lead_id).first()
        if not lead:
            return ServiceResult.failure({"lead": "Lead not found."}, status_code=404)
        note = LeadNote.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            title=title,
            body=body,
            author_id=author_id,
            metadata=metadata or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        LeadActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            activity_type="NoteAdded",
            title=title or "Note added",
            note=body,
            created_by=context.actor,
        )
        return ServiceResult.success(note, status_code=201)

    @staticmethod
    def add_test(context, lead_id, title, status="Pending", score=0, due_at=None, metadata=None):
        lead = LeadAccount.objects.filter(tenant=context.tenant, id=lead_id).first()
        if not lead:
            return ServiceResult.failure({"lead": "Lead not found."}, status_code=404)
        test = LeadTest.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            title=title,
            status=status,
            score=score or 0,
            due_at=due_at,
            metadata=metadata or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        OutboxService.publish(context, "LeadTest", test.id, "LeadTestCreated", {"leadId": lead.id, "status": status})
        return ServiceResult.success(test, status_code=201)

    @staticmethod
    def send_to_bbd(context, lead_id, notes=None):
        lead = LeadAccount.objects.filter(tenant=context.tenant, id=lead_id).first()
        if not lead:
            return ServiceResult.failure({"lead": "Lead not found."}, status_code=404)
        template = get_bbd_email_template(lead)
        LeadActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            activity_type="SentToBBD",
            title="Sent to BBD",
            payload={"template": template, "notes": notes or {}},
            created_by=context.actor,
        )
        OutboxService.publish(context, "LeadAccount", lead.id, "LeadSentToBBD", {"subject": template["subject"]})
        return ServiceResult.success({"leadId": lead.id, "template": template})

    @staticmethod
    def send_audit(context, lead_id, notes=None):
        lead = LeadAccount.objects.filter(tenant=context.tenant, id=lead_id).first()
        if not lead:
            return ServiceResult.failure({"lead": "Lead not found."}, status_code=404)
        audit = AuditArtifact.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            title=f"Audit for {lead.company_name}",
            status="Queued",
            metadata=notes or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        template = get_audit_email_template(lead, audit)
        OutboxService.publish(context, "AuditArtifact", audit.id, "AuditEmailQueued", {"subject": template["subject"]})
        return ServiceResult.success({"auditId": audit.id, "template": template}, status_code=201)

    @staticmethod
    def create_offer_template(context, lead_id, amount=None, notes=None):
        lead = LeadAccount.objects.filter(tenant=context.tenant, id=lead_id).first()
        if not lead:
            return ServiceResult.failure({"lead": "Lead not found."}, status_code=404)
        proposal = ProposalArtifact.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            title=f"Offer for {lead.company_name}",
            status="Draft",
            amount=amount or lead.estimated_value,
            metadata=notes or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        template = get_offer_letter_template(lead, proposal)
        OutboxService.publish(context, "ProposalArtifact", proposal.id, "OfferTemplateCreated", {"subject": template["subject"]})
        return ServiceResult.success({"proposalId": proposal.id, "template": template}, status_code=201)

    @staticmethod
    def check_workflow_status(context):
        rows = []
        leads = LeadAccount.objects.filter(tenant=context.tenant).annotate(activity_count=Count("activities"))
        for lead in leads:
            result = "NeedsFollowUp" if lead.stage not in {"ClosedWon", "ClosedLost"} and lead.activity_count == 0 else "Healthy"
            history = WorkflowStatusHistory.objects.create(
                tenant=context.tenant,
                workspace=context.workspace or lead.workspace,
                lead=lead,
                status=lead.stage,
                checked_at=timezone.now(),
                result=result,
                payload={"activity_count": lead.activity_count},
                created_by=context.actor,
                updated_by=context.actor,
            )
            rows.append({"leadId": lead.id, "result": history.result})
        return ServiceResult.success({"count": len(rows), "rows": rows})

    @staticmethod
    def allocate_jrba_leads(context, owner_ids=None, source="JRBA"):
        from Backend.Apps.Users.models import EmployeeProfile

        owners = list(EmployeeProfile.objects.filter(tenant=context.tenant, id__in=owner_ids or [], is_active=True))
        if not owners:
            owners = list(EmployeeProfile.objects.filter(tenant=context.tenant, is_active=True).order_by("id")[:5])
        if not owners:
            return ServiceResult.failure({"owners": "No active employees available for JRBA allocation."}, status_code=400)
        rows = []
        leads = LeadAccount.objects.filter(tenant=context.tenant, source__iexact=source, owner__isnull=True).order_by("id")
        for index, lead in enumerate(leads):
            owner = owners[index % len(owners)]
            lead.owner = owner
            lead.updated_by = context.actor
            lead.save(update_fields=["owner", "updated_by", "updated_at"])
            rows.append({"leadId": lead.id, "ownerId": owner.id})
        OutboxService.publish(context, "LeadAccount", 0, "JRBALeadsAllocated", {"count": len(rows)})
        return ServiceResult.success({"count": len(rows), "rows": rows})
