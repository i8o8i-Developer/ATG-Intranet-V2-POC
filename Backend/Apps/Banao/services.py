from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from Backend.Apps.Banao.email_templates import get_audit_email_template, get_bbd_email_template, get_offer_letter_template
from Backend.Apps.Banao.models import AuditArtifact, LeadAccount, LeadActivity, LeadContact, LeadNote, LeadTest, ProposalArtifact, WorkflowStatusHistory, WorkflowTransition
from Backend.Apps.MainApp.models import OnboardingOffer
from Backend.Apps.MainApp.services import OfferLifecycleService
from Backend.Apps.Users.models import Department, EmployeeProfile
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class LeadWorkflowService:
    @staticmethod
    def _actor_employee(context):
        actor = getattr(context, "actor", None)
        if not actor:
            return None
        return EmployeeProfile.objects.filter(tenant=context.tenant, user=actor).order_by("id").first()

    @staticmethod
    def _normalize_domain(value):
        raw_value = str(value or "").strip()
        if not raw_value:
            return ""
        parsed = urlparse(raw_value)
        host = parsed.netloc or parsed.path
        host = host.split("/")[0].strip().lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    @staticmethod
    def _lead_matches_domain(lead, domain):
        if not domain:
            return False
        candidates = [
            lead.website_url,
            lead.source_page_url,
            lead.external_url,
            (lead.metadata or {}).get("url"),
        ]
        return any(LeadWorkflowService._normalize_domain(candidate) == domain for candidate in candidates if candidate)

    @staticmethod
    def capture_lead(
        context,
        company_name,
        source="",
        priority="Normal",
        owner_id=None,
        estimated_value=0,
        currency="INR",
        contact_name="",
        contact_email="",
        contact_phone="",
        metadata=None,
        website_url="",
        industry="",
        connection_id="",
        source_page_name="",
        source_page_url="",
        stage="",
        initial_note="",
        next_follow_up_at=None,
        action_item="",
        contact_role="",
    ):
        actor_profile = LeadWorkflowService._actor_employee(context)
        lead = LeadAccount.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            company_name=company_name,
            source=source,
            stage=stage or LeadAccount._meta.get_field("stage").default,
            priority=priority,
            owner_id=owner_id,
            estimated_value=estimated_value or 0,
            currency=currency,
            website_url=website_url or "",
            industry=industry or "",
            connection_id=connection_id or "",
            source_page_name=source_page_name or "",
            source_page_url=source_page_url or "",
            latest_comment=initial_note or "",
            next_follow_up_at=next_follow_up_at,
            action_item=action_item or "",
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
                role=contact_role,
                is_primary=True,
                created_by=context.actor,
                updated_by=context.actor,
            )
        if initial_note:
            LeadNote.objects.create(
                tenant=context.tenant,
                workspace=context.workspace,
                lead=lead,
                title="Lead request",
                body=initial_note,
                metadata={"source": source},
                created_by=context.actor,
                updated_by=context.actor,
            )
        LeadActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            lead=lead,
            actor=actor_profile,
            activity_type="LeadCaptured",
            title="Lead captured",
            note=initial_note,
            payload={
                "source": source,
                "industry": industry,
                "websiteUrl": website_url,
                "sourcePageName": source_page_name,
                "sourcePageUrl": source_page_url,
            },
            created_by=context.actor,
        )
        OutboxService.publish(context, "LeadAccount", lead.id, "LeadCaptured", {"company": company_name, "source": source})
        return ServiceResult.success(lead, status_code=201)

    @staticmethod
    def find_duplicate_public_lead(context, full_name, emails=None, phones=None, website_url=""):
        emails = {str(item or "").strip().lower() for item in (emails or []) if str(item or "").strip()}
        phones = {str(item or "").strip() for item in (phones or []) if str(item or "").strip()}
        normalized_name = str(full_name or "").strip().lower()
        leads = LeadAccount.objects.filter(tenant=context.tenant).prefetch_related("contacts")
        domain = LeadWorkflowService._normalize_domain(website_url)
        if domain:
            for lead in leads:
                if LeadWorkflowService._lead_matches_domain(lead, domain):
                    return lead
        for lead in leads:
            contacts = list(lead.contacts.all())
            if normalized_name and not any((contact.name or "").strip().lower() == normalized_name for contact in contacts):
                continue
            if emails and any((contact.email or "").strip().lower() in emails for contact in contacts if contact.email):
                return lead
            if phones and any((contact.phone or "").strip() in phones for contact in contacts if contact.phone):
                return lead
        return None

    @staticmethod
    def record_connection_sent(context, domain, intern_name="", client_name=""):
        normalized_domain = LeadWorkflowService._normalize_domain(domain)
        if not normalized_domain:
            return ServiceResult.failure({"domain": "Domain Is Required."}, status_code=400)
        lead = None
        for candidate in LeadAccount.objects.filter(tenant=context.tenant).order_by("id"):
            if LeadWorkflowService._lead_matches_domain(candidate, normalized_domain):
                lead = candidate
                break
        if not lead:
            return ServiceResult.failure({"lead": "Lead Not Found."}, status_code=404)
        note_body = f"Connection Sent To {client_name or lead.company_name} By {intern_name or 'Unknown'}"
        metadata = dict(lead.metadata or {})
        if intern_name:
            metadata["intern_name"] = intern_name
        if client_name:
            metadata["client_name"] = client_name
        stage_changed = False
        if lead.stage == "New":
            lead.stage = "ContactAttempted"
            stage_changed = True
        lead.metadata = metadata
        lead.latest_comment = "\n".join(part for part in [lead.latest_comment, note_body] if part).strip()
        lead.updated_by = context.actor
        update_fields = ["metadata", "latest_comment", "updated_by", "updated_at"]
        if stage_changed:
            update_fields.insert(0, "stage")
        lead.save(update_fields=update_fields)
        actor_profile = LeadWorkflowService._actor_employee(context)
        LeadNote.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            title="Connection Sent",
            body=note_body,
            metadata={"domain": normalized_domain},
            created_by=context.actor,
            updated_by=context.actor,
        )
        LeadActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            actor=actor_profile,
            activity_type="ConnectionSent",
            title="Connection Sent",
            note=note_body,
            payload={"domain": normalized_domain, "internName": intern_name, "clientName": client_name},
            created_by=context.actor,
        )
        OutboxService.publish(context, "LeadAccount", lead.id, "LeadConnectionSent", {"domain": normalized_domain})
        return ServiceResult.success(lead, status_code=201)

    @staticmethod
    def list_department_options(context):
        rows = [{"id": item.id, "name": item.name} for item in Department.objects.filter(tenant=context.tenant, is_archived=False).order_by("name")]
        return ServiceResult.success(rows)

    @staticmethod
    def list_user_options(context, department_ref=""):
        employees = EmployeeProfile.objects.filter(tenant=context.tenant, user__is_active=True, status=EmployeeProfile.STATUS_ACTIVE).select_related("user", "department")
        if department_ref:
            department_text = str(department_ref).strip()
            if department_text.isdigit():
                employees = employees.filter(department_id=int(department_text))
            else:
                employees = employees.filter(department__name__iexact=department_text)
        rows = [{"id": item.id, "name": item.user.username or item.display_name} for item in employees.order_by("display_name")]
        return ServiceResult.success(rows)

    @staticmethod
    def find_duplicate_offer(context, email, username=""):
        user_model = get_user_model()
        normalized_email = str(email or "").strip().lower()
        normalized_username = str(username or "").strip().lower()
        if normalized_email and user_model.objects.filter(email__iexact=normalized_email).exists():
            return "Username Or Email Already Exists"
        if normalized_username and user_model.objects.filter(username__iexact=normalized_username).exists():
            return "Username Or Email Already Exists"
        offers = OnboardingOffer.objects.filter(tenant=context.tenant, company_name__iexact="Banao")
        if normalized_email and offers.filter(candidate_email__iexact=normalized_email).exists():
            return "Username Or Email Already Exists"
        if normalized_username:
            for offer in offers.only("offer_payload"):
                existing_username = str((offer.offer_payload or {}).get("username") or "").strip().lower()
                if existing_username == normalized_username:
                    return "Username Or Email Already Exists"
        return ""

    @staticmethod
    def issue_banao_offer(context, offer_payload):
        expires_at = offer_payload.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = parse_datetime(expires_at)
        payload_to_store = {
            **offer_payload,
            "expires_at": expires_at.isoformat() if expires_at else "",
        }
        offer = OnboardingOffer.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            candidate_name=offer_payload.get("name") or offer_payload.get("candidate_name") or "",
            candidate_email=offer_payload.get("email") or offer_payload.get("candidate_email") or "",
            company_name="Banao",
            position_title=offer_payload.get("position_name") or offer_payload.get("position_title") or "",
            offer_type=offer_payload.get("offer_type") or "Intern",
            status="Draft",
            offer_payload=payload_to_store,
            expires_at=expires_at,
            created_by=context.actor,
            updated_by=context.actor,
        )
        result = OfferLifecycleService.issue_offer(context, offer.id, expires_at=expires_at)
        if not result.ok:
            return result
        return ServiceResult.success(result.data, status_code=201)

    @staticmethod
    def render_offer_preview_html(offer_payload, offer_url=""):
        pay_type = str(offer_payload.get("pay_type") or "Fixed")
        base_pay = str(offer_payload.get("base_pay") or "0")
        pay_per_task = str(offer_payload.get("pay_per_task") or "0")
        title = str(offer_payload.get("title") or "")
        position_name = str(offer_payload.get("position_name") or offer_payload.get("position_title") or "")
        department_name = str(offer_payload.get("department_name") or "")
        offer_date = str(offer_payload.get("offer_date") or timezone.localdate().isoformat())
        compensation_line = f"Fixed Pay : INR {base_pay}"
        if pay_type.lower() == "performance based" and pay_per_task not in {"", "0", "0.00"}:
            compensation_line = f"Expected Monthly Pay: INR {base_pay}; Performance Pay: INR {pay_per_task} per task"
        cta_html = f'<p style="margin-top:24px;"><a href="{offer_url}" style="display:inline-block;padding:12px 18px;background:#111827;color:#ffffff;text-decoration:none;border-radius:8px;">Open Offer</a></p>' if offer_url else ""
        return (
            "<html><body style=\"font-family:Segoe UI,Arial,sans-serif;background:#f6f7fb;padding:32px;\">"
            "<div style=\"max-width:720px;margin:0 auto;background:#ffffff;border:1px solid #d8dee8;border-radius:16px;padding:32px;\">"
            f"<p style=\"margin:0 0 12px;color:#4b5563;\">Offer Date: {offer_date}</p>"
            f"<h1 style=\"margin:0 0 12px;color:#111827;\">Offer For {offer_payload.get('name') or offer_payload.get('candidate_name') or 'Candidate'}</h1>"
            f"<p style=\"margin:0 0 16px;color:#374151;\">Banao Is Pleased To Extend an Offer For <strong>{position_name or 'the requested role'}</strong>.</p>"
            f"<p style=\"margin:0 0 8px;color:#374151;\"><strong>Department:</strong> {department_name or 'Banao'}</p>"
            f"<p style=\"margin:0 0 8px;color:#374151;\"><strong>Title:</strong> {title or position_name or 'Team Member'}</p>"
            f"<p style=\"margin:0 0 8px;color:#374151;\"><strong>Offer Type:</strong> {offer_payload.get('offer_type') or 'Intern'}</p>"
            f"<p style=\"margin:0 0 16px;color:#374151;\"><strong>Compensation:</strong> {compensation_line}</p>"
            f"<p style=\"margin:0;color:#374151;\">Slack: {offer_payload.get('slack') or 'Not provided'} | WhatsApp: {offer_payload.get('whatsapp') or 'Not provided'}</p>"
            f"{cta_html}"
            "</div></body></html>"
        )

    @staticmethod
    def move_stage(context, lead_id, to_stage, reason=""):
        lead = LeadAccount.objects.filter(tenant=context.tenant, id=lead_id).first()
        if not lead:
            return ServiceResult.failure({"lead": "Lead Not Found."}, status_code=404)
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
            return ServiceResult.failure({"lead": "Lead Not Found."}, status_code=404)
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
            return ServiceResult.failure({"lead": "Lead Not Found."}, status_code=404)
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
            return ServiceResult.failure({"lead": "Lead Not Found."}, status_code=404)
        template = get_bbd_email_template(lead)
        LeadActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            activity_type="SentToBBD",
            title="Sent To BBD",
            payload={"template": template, "notes": notes or {}},
            created_by=context.actor,
        )
        OutboxService.publish(context, "LeadAccount", lead.id, "LeadSentToBBD", {"subject": template["subject"]})
        return ServiceResult.success({"leadId": lead.id, "template": template})

    @staticmethod
    def send_audit(context, lead_id, notes=None):
        lead = LeadAccount.objects.filter(tenant=context.tenant, id=lead_id).first()
        if not lead:
            return ServiceResult.failure({"lead": "Lead Not Found."}, status_code=404)
        audit = AuditArtifact.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            title=f"Audit For {lead.company_name}",
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
            return ServiceResult.failure({"lead": "Lead Not Found."}, status_code=404)
        proposal = ProposalArtifact.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or lead.workspace,
            lead=lead,
            title=f"Offer For {lead.company_name}",
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
        owners = list(EmployeeProfile.objects.filter(tenant=context.tenant, id__in=owner_ids or [], is_active=True))
        if not owners:
            owners = list(EmployeeProfile.objects.filter(tenant=context.tenant, is_active=True).order_by("id")[:5])
        if not owners:
            return ServiceResult.failure({"owners": "No Active Employees Available For JRBA Allocation."}, status_code=400)
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
