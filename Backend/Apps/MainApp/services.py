from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template
from django.template.loader import render_to_string

from django.utils.crypto import get_random_string

from io import BytesIO
import base64
from html import escape
import os
import re


_LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
_SCRIPT_TAG_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_FOCUS_VISIBLE_RULE_RE = re.compile(
    r"[^{}]*:(?:focus-visible|is\(|where\(|has\()[^{}]*\{[^{}]*\}",
    re.IGNORECASE,
)
_AT_IMPORT_RE = re.compile(r"@import\s+url\([^)]*\)\s*;?", re.IGNORECASE)
_ALL_IMG_RE = re.compile(r'<img\b[^>]*>', re.IGNORECASE)


def _sanitize_html_for_pisa(html: str) -> str:
    if not html:
        return html
    cleaned = _LINK_TAG_RE.sub("", html)
    cleaned = _SCRIPT_TAG_RE.sub("", cleaned)
    cleaned = _FOCUS_VISIBLE_RULE_RE.sub("", cleaned)
    cleaned = _AT_IMPORT_RE.sub("", cleaned)
    cleaned = _ALL_IMG_RE.sub("", cleaned)
    return cleaned


def _pisa_link_callback(uri, rel):
    if not uri:
        return uri
    lowered = uri.lower()
    if lowered.startswith(("http://", "https://", "//")):
        return None
    return uri

try:
    from xhtml2pdf import pisa
    from bs4 import BeautifulSoup
except ImportError:
    pisa = None
    BeautifulSoup = None

from Backend.Apps.MainApp.models import CredentialShareGrant, CredentialVaultItem, ExternalIssueReference, LeaveRequest, ManagerScope, NotificationItem, NotificationSnoozeRecord, OnboardingOffer
from Backend.Apps.MainApp.utils import PartyRemoteAutomationError, PartyRemoteAutomationProvider
from Backend.Apps.Users.models import Department, EmployeeProfile, SubDepartment
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class NotificationService:
    @staticmethod
    def notify(context, recipient, title, message="", category="", resource_type="", resource_id="", metadata=None):
        notification = NotificationItem.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            recipient=recipient,
            title=title,
            message=message,
            category=category,
            resource_type=resource_type,
            resource_id=str(resource_id or ""),
            metadata=metadata or {},
            created_by=context.actor,
        )
        return ServiceResult.success(notification, status_code=201)

    @staticmethod
    def mark_read(context, notification_id):
        notification = NotificationItem.objects.filter(tenant=context.tenant, id=notification_id).first()
        if not notification:
            return ServiceResult.failure({"notification": "Notification Not Found."}, status_code=404)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.updated_by = context.actor
        notification.save(update_fields=["is_read", "read_at", "updated_by", "updated_at"])
        return ServiceResult.success(notification)

    @staticmethod
    def mark_all_read(context, user):
        count = NotificationItem.objects.filter(tenant=context.tenant, recipient=user, is_read=False).update(
            is_read=True, read_at=timezone.now(), updated_at=timezone.now()
        )
        return ServiceResult.success({"updated": count})

    @staticmethod
    def snooze(context, notification_id, snoozed_until, reason=""):
        notification = NotificationItem.objects.filter(tenant=context.tenant, id=notification_id).first()
        if not notification:
            return ServiceResult.failure({"notification": "Notification Not Found."}, status_code=404)
        notification.snoozed_until = snoozed_until
        notification.updated_by = context.actor
        notification.save(update_fields=["snoozed_until", "updated_by", "updated_at"])
        NotificationSnoozeRecord.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or notification.workspace,
            notification=notification,
            snoozed_by=context.actor,
            snoozed_until=snoozed_until,
            reason=reason,
            created_by=context.actor,
            updated_by=context.actor,
        )
        return ServiceResult.success(notification)


class LeaveApprovalService:
    @staticmethod
    def actor_employee(context):
        if not context.actor:
            return None
        return EmployeeProfile.objects.filter(tenant=context.tenant, user=context.actor).select_related("department", "position", "manager").first()

    @staticmethod
    def is_leave_admin(context):
        actor = getattr(context, "actor", None)
        return bool(actor and (getattr(actor, "is_superuser", False) or getattr(actor, "is_staff", False)))

    @staticmethod
    def visible_queryset(context):
        queryset = LeaveRequest.objects.filter(tenant=context.tenant).select_related("employee", "employee__user", "employee__manager")
        if context.workspace:
            queryset = queryset.filter(workspace=context.workspace)
        if LeaveApprovalService.is_leave_admin(context):
            return queryset
        employee = LeaveApprovalService.actor_employee(context)
        if not employee:
            return queryset.none()
        return queryset.filter(Q(employee=employee) | Q(employee__manager=employee))

    @staticmethod
    def can_review(context, leave_request):
        if LeaveApprovalService.is_leave_admin(context):
            return True
        employee = LeaveApprovalService.actor_employee(context)
        if not employee:
            return False
        return leave_request.employee.manager_id == employee.id and leave_request.employee_id != employee.id

    @staticmethod
    def _notify_leave_actor(context, leave_request, title, message):
        if leave_request.employee and leave_request.employee.user:
            NotificationService.notify(context, leave_request.employee.user, title, message=message, category="leave", resource_type="LeaveRequest", resource_id=str(leave_request.id))

    @staticmethod
    def approve(context, leave_request_id):
        leave_request = LeaveApprovalService.visible_queryset(context).filter(id=leave_request_id).first()
        if not leave_request:
            return ServiceResult.failure({"leaveRequest": "Leave Request Not Found."}, status_code=404)
        if not LeaveApprovalService.can_review(context, leave_request):
            return ServiceResult.failure({"permission": "You Cannot Approve This Leave Request."}, status_code=403)
        leave_request.status = "Approved"
        leave_request.approved_by = context.actor
        leave_request.approved_at = timezone.now()
        leave_request.approval_payload = {**leave_request.approval_payload, "approvedAt": timezone.now().isoformat()}
        leave_request.updated_by = context.actor
        leave_request.save(update_fields=["status", "approved_by", "approved_at", "approval_payload", "updated_by", "updated_at"])
        LeaveApprovalService._notify_leave_actor(context, leave_request, "Leave Approved", f"Your Leave ({leave_request.starts_on} - {leave_request.ends_on}) Has Been Approved.")
        OutboxService.publish(context, "LeaveRequest", leave_request.id, "LeaveRequestApproved", {"leaveRequestId": leave_request.id})
        return ServiceResult.success(leave_request)

    @staticmethod
    def reject(context, leave_request_id, reason=""):
        leave_request = LeaveApprovalService.visible_queryset(context).filter(id=leave_request_id).first()
        if not leave_request:
            return ServiceResult.failure({"leaveRequest": "Leave Request Not Found."}, status_code=404)
        if not LeaveApprovalService.can_review(context, leave_request):
            return ServiceResult.failure({"permission": "You Cannot Reject This Leave Request."}, status_code=403)
        leave_request.status = "Rejected"
        leave_request.rejected_at = timezone.now()
        leave_request.approval_payload = {**leave_request.approval_payload, "rejectedAt": timezone.now().isoformat(), "reason": reason}
        leave_request.updated_by = context.actor
        leave_request.save(update_fields=["status", "rejected_at", "approval_payload", "updated_by", "updated_at"])
        LeaveApprovalService._notify_leave_actor(context, leave_request, "Leave Rejected", f"Your Leave ({leave_request.starts_on} - {leave_request.ends_on}) Has Been Rejected. Reason: {reason}")
        OutboxService.publish(context, "LeaveRequest", leave_request.id, "LeaveRequestRejected", {"leaveRequestId": leave_request.id})
        return ServiceResult.success(leave_request)


class OfferLifecycleService:
    @staticmethod
    def issue_offer(context, offer_id, expires_at=None):
        offer = OnboardingOffer.objects.filter(tenant=context.tenant, id=offer_id).first()
        if not offer:
            return ServiceResult.failure({"offer": "Onboarding Offer Not Found."}, status_code=404)
        offer.status = "Issued"
        offer.issued_at = timezone.now()
        offer.expires_at = expires_at or offer.expires_at
        offer.token = offer.token or get_random_string(48)
        offer.updated_by = context.actor
        offer.save(update_fields=["status", "issued_at", "expires_at", "token", "updated_by", "updated_at"])
        try:
            OutboxService.publish(context, "OnboardingOffer", offer.id, "OfferIssued", {"candidateEmail": offer.candidate_email})
        except Exception:
            pass
        return ServiceResult.success(offer)

    @staticmethod
    def accept_offer(context, token, payload=None):
        from django.conf import settings

        offer = OnboardingOffer.objects.filter(tenant=context.tenant, token=token).first()
        if not offer:
            return ServiceResult.failure({"offer": "Offer Token Not Found."}, status_code=404)
        if offer.status == "Accepted":
            return ServiceResult.failure({"offer": "Offer Already Accepted."}, status_code=409)
        if offer.status != "Issued":
            return ServiceResult.failure({"offer": "Offer Is Not Available For Acceptance."}, status_code=409)
        if offer.expires_at and offer.expires_at < timezone.now():
            return ServiceResult.failure({"offer": "Offer Token Has Expired."}, status_code=410)

        offer.status = "Accepted"
        offer.accepted_at = timezone.now()
        offer.offer_payload = {**offer.offer_payload, "acceptance": payload or {}}
        offer.updated_by = context.actor
        offer.save(update_fields=["status", "accepted_at", "offer_payload", "updated_by", "updated_at"])
        OutboxService.publish(context, "OnboardingOffer", offer.id, "OfferAccepted", {"candidateEmail": offer.candidate_email})

        # ── AUTO ONBOARDING ──────────────────────────────────────────────────
        op = offer.offer_payload or {}
        profile_data = op.get("acceptance", {}).get("profile_data") or {}
        username = (op.get("username") or "").strip() or (offer.candidate_email or "").split("@")[0]
        password = get_random_string(10)

        user_model = get_user_model()
        auto_user = None
        auto_employee = None
        provision_error = None
        try:
            if not user_model.objects.filter(username__iexact=username).exists():
                auto_user = user_model.objects.create_user(
                    username=username,
                    email=offer.candidate_email or "",
                    password=password,
                    first_name=(offer.candidate_name or "").split(" ")[0][:30],
                    last_name=(" ".join((offer.candidate_name or "").split(" ")[1:]))[:150],
                )
                # Generate sequential employee code
                emp_count = EmployeeProfile.objects.filter(tenant=context.tenant).count() + 1
                employee_code = f"EMP-{emp_count:04d}"
                while EmployeeProfile.objects.filter(tenant=context.tenant, employee_code=employee_code).exists():
                    emp_count += 1
                    employee_code = f"EMP-{emp_count:04d}"

                auto_employee = EmployeeProfile.objects.create(
                    tenant=context.tenant,
                    workspace=context.workspace,
                    user=auto_user,
                    employee_code=employee_code,
                    display_name=offer.candidate_name or username,
                    contact_number=profile_data.get("phone", ""),
                    slack_username=profile_data.get("slack_username", ""),
                    employment_type=op.get("employment_type", "Intern"),
                    status=EmployeeProfile.STATUS_ACTIVE,
                    joined_on=timezone.localdate(),
                    onboarding_completed=False,
                    profile_payload={
                        "registered_via": "offer_acceptance",
                        "offer_id": offer.id,
                        "offer_token": token,
                        "position_title": offer.position_title,
                        "department_name": op.get("department_name", ""),
                        "city": profile_data.get("city", ""),
                        "emergency_contact": profile_data.get("emergency_contact", ""),
                    },
                    created_by=context.actor,
                    updated_by=context.actor,
                )
            else:
                auto_user = user_model.objects.filter(username__iexact=username).first()
                auto_user.set_password(password)
                auto_user.save(update_fields=["password"])
                auto_employee = EmployeeProfile.objects.filter(tenant=context.tenant, user=auto_user, is_active=True).first()
        except Exception as exc:
            provision_error = str(exc)

        # ── ASSIGN ROLE & COMPLETE ONBOARDING ───────────────────────────────────
        if auto_employee and not provision_error:
            try:
                auto_employee.onboarding_completed = True
                auto_employee.save(update_fields=["onboarding_completed", "updated_at"])
                from Backend.EnterpriseCore.models import Role, RoleAssignment
                dept_name = (op.get("department_name") or "").lower()
                role_map = {"python django": "MANAGER", "mern stack": "MANAGER", "business analysis": "BUSINESS_ANALYST",
                            "human resources": "HR", "finance": "FINANCE_MANAGER", "design": "DOCS_EDIT",
                            "manual testing": "BUSINESS_ANALYST", "l3 team": "L3_CALLER"}
                role_code = "MANAGER"
                for key, code in role_map.items():
                    if key in dept_name:
                        role_code = code
                        break
                role = Role.objects.filter(tenant=context.tenant, code=role_code).first()
                if role:
                    RoleAssignment.objects.get_or_create(tenant=context.tenant, workspace=context.workspace, user=auto_user, role=role, defaults={"is_active": True})
            except Exception:
                pass

        try:
            base_url = str(getattr(settings, "PUBLIC_BASE_URL", "http://localhost:5173") or "http://localhost:5173").rstrip("/")
            intranet_url = base_url
            from_email = (
                getattr(settings, "DEFAULT_FROM_EMAIL", "")
                or getattr(settings, "EMAIL_HOST_USER", "")
                or "admin@atg.world"
            )
            candidate_name = offer.candidate_name or username
            creds_context = {
                "candidate_name": candidate_name,
                "username": username,
                "password": password,
                "position_title": offer.position_title or "Intern",
                "intranet_url": intranet_url,
                "from_email": from_email,
            }
            creds_html = render_to_string("Credentials-Email.html", creds_context)
            msg = EmailMultiAlternatives(
                subject=f"Welcome to ATG! Your Intranet Credentials — {candidate_name}",
                body=f"Welcome {candidate_name}!\nYour ATG Intranet Username: {username}\nTemporary Password: {password}\nLogin at: {intranet_url}",
                from_email=from_email,
                to=[offer.candidate_email],
            )
            msg.attach_alternative(creds_html, "text/html")
            msg.send(fail_silently=True)
        except Exception:
            pass

        offer.offer_payload = {
            **offer.offer_payload,
            "onboarding": {
                "username": username,
                "employee_id": auto_employee.id if auto_employee else None,
                "user_id": auto_user.id if auto_user else None,
                "provisioned": auto_user is not None,
                "provision_error": provision_error,
            },
        }
        offer.token = None
        offer.expires_at = None
        offer.save(update_fields=["offer_payload", "token", "expires_at", "updated_at"])

        return ServiceResult.success(offer)


    @staticmethod
    def queue_offer_reminders(context, now=None):
        now = now or timezone.now()
        offers = OnboardingOffer.objects.filter(tenant=context.tenant, status="Issued").filter(expires_at__gte=now)
        rows = []
        for offer in offers:
            offer.reminder_count += 1
            offer.last_reminder_at = now
            offer.updated_by = context.actor
            offer.save(update_fields=["reminder_count", "last_reminder_at", "updated_by", "updated_at"])
            OutboxService.publish(context, "OnboardingOffer", offer.id, "OfferReminderQueued", {"candidateEmail": offer.candidate_email})
            rows.append(offer.id)
        return ServiceResult.success({"count": len(rows), "offerIds": rows})


class CredentialVaultService:
    @staticmethod
    def share(context, credential_id, grantee, permission="Read", expires_at=None, reason=""):
        credential = CredentialVaultItem.objects.filter(tenant=context.tenant, id=credential_id).first()
        if not credential:
            return ServiceResult.failure({"credential": "Credential Not Found."}, status_code=404)
        grant, _created = CredentialShareGrant.objects.update_or_create(
            tenant=context.tenant,
            credential=credential,
            grantee=grantee,
            defaults={"workspace": context.workspace or credential.workspace, "permission": permission, "expires_at": expires_at, "reason": reason, "revoked_at": None, "updated_by": context.actor},
        )
        return ServiceResult.success(grant, status_code=201)

    @staticmethod
    def revoke_share(context, grant_id):
        grant = CredentialShareGrant.objects.filter(tenant=context.tenant, id=grant_id).first()
        if not grant:
            return ServiceResult.failure({"grant": "Credential Share Grant Not Found."}, status_code=404)
        grant.revoked_at = timezone.now()
        grant.updated_by = context.actor
        grant.save(update_fields=["revoked_at", "updated_by", "updated_at"])
        return ServiceResult.success(grant)

    @staticmethod
    def rotate(context, credential_id, secret_reference=""):
        credential = CredentialVaultItem.objects.filter(tenant=context.tenant, id=credential_id).first()
        if not credential:
            return ServiceResult.failure({"credential": "Credential Not Found."}, status_code=404)
        if secret_reference:
            credential.secret_reference = secret_reference
        credential.last_rotated_at = timezone.now()
        credential.updated_by = context.actor
        credential.save(update_fields=["secret_reference", "last_rotated_at", "updated_by", "updated_at"])
        OutboxService.publish(context, "CredentialVaultItem", credential.id, "CredentialRotated", {"system": credential.system_name})
        return ServiceResult.success(credential)


class MainAppLegacyService:
    @staticmethod
    def actor_employee(context):
        return LeaveApprovalService.actor_employee(context)

    @staticmethod
    def list_leaves(context, employee_id=None):
        queryset = LeaveApprovalService.visible_queryset(context)
        is_admin = LeaveApprovalService.is_leave_admin(context)
        actor_employee = MainAppLegacyService.actor_employee(context)
        if employee_id:
            if not is_admin:
                allowed = actor_employee and (
                    str(employee_id) == str(actor_employee.id)
                    or EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id, manager=actor_employee).exists()
                )
                if not allowed:
                    return ServiceResult.failure({"permission": "You Cannot View This Employee's Leave Requests."}, status_code=403)
            queryset = queryset.filter(employee_id=employee_id)

        return ServiceResult.success(
            {
                "count": queryset.count(),
                "results": [
                    {
                        "id": leave.id,
                        "employee_id": leave.employee_id,
                        "employee_name": leave.employee.display_name,
                        "leave_type": leave.leave_type,
                        "starts_on": leave.starts_on.isoformat(),
                        "ends_on": leave.ends_on.isoformat(),
                        "status": leave.status,
                        "requested_days": str(leave.requested_days),
                    }
                    for leave in queryset.order_by("-starts_on")
                ],
            }
        )

    @staticmethod
    def create_leave(context, employee_id, leave_type, starts_on, ends_on, reason="", status="Submitted"):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee Not Found."}, status_code=404)
        actor_employee = MainAppLegacyService.actor_employee(context)
        is_admin = LeaveApprovalService.is_leave_admin(context)
        if not (is_admin or (actor_employee and actor_employee.id == employee.id)):
            return ServiceResult.failure({"permission": "You Cannot Create Leave For Another Employee."}, status_code=403)
        if not starts_on or not ends_on:
            return ServiceResult.failure({"dates": "Start Date And End Date Are Required."}, status_code=400)
        requested_days = (ends_on - starts_on).days + 1
        leave = LeaveRequest.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or employee.workspace,
            employee=employee,
            leave_type=leave_type,
            starts_on=starts_on,
            ends_on=ends_on,
            requested_days=requested_days,
            reason=reason,
            status=status,
            created_by=context.actor,
            updated_by=context.actor,
        )
        return ServiceResult.success(leave, status_code=201)

    @staticmethod
    def leave_calendar(context, employee_id=None, department_id=None):
        leaves = LeaveApprovalService.visible_queryset(context)
        is_admin = LeaveApprovalService.is_leave_admin(context)
        actor_employee = MainAppLegacyService.actor_employee(context)
        if employee_id:
            if not is_admin:
                allowed = actor_employee and (
                    str(employee_id) == str(actor_employee.id)
                    or EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id, manager=actor_employee).exists()
                )
                if not allowed:
                    return ServiceResult.failure({"permission": "You Cannot View This Employee's Leave Calendar."}, status_code=403)
            leaves = leaves.filter(employee_id=employee_id)
        if department_id:
            if not is_admin:
                return ServiceResult.failure({"permission": "You Cannot View Department Leave Calendar."}, status_code=403)
            leaves = leaves.filter(employee__department_id=department_id)
        return ServiceResult.success(
            {
                "results": [
                    {
                        "id": leave.id,
                        "title": f"{leave.employee.display_name} - {leave.leave_type}",
                        "start": leave.starts_on.isoformat(),
                        "end": leave.ends_on.isoformat(),
                        "status": leave.status,
                    }
                    for leave in leaves.order_by("starts_on")
                ]
            }
        )

    @staticmethod
    def employees_by_department(context, department_id=None):
        employees = EmployeeProfile.objects.filter(tenant=context.tenant).select_related("department", "position", "manager", "user")
        if department_id:
            employees = employees.filter(department_id=department_id)
        return ServiceResult.success(
            {
                "count": employees.count(),
                "results": [
                    {
                        "id": employee.id,
                        "name": employee.display_name,
                        "employee_code": employee.employee_code,
                        "department": employee.department.name if employee.department else "",
                        "position": employee.position.title if employee.position else "",
                        "manager": employee.manager.display_name if employee.manager else "",
                        "status": employee.status,
                    }
                    for employee in employees.order_by("display_name")
                ],
            }
        )

    @staticmethod
    def hierarchy(context):
        managers = EmployeeProfile.objects.filter(tenant=context.tenant, direct_reports__isnull=False).distinct().select_related("department")
        return ServiceResult.success(
            {
                "results": [
                    {
                        "manager_id": manager.id,
                        "manager_name": manager.display_name,
                        "department": manager.department.name if manager.department else "",
                        "reportee_count": manager.direct_reports.filter(status=EmployeeProfile.STATUS_ACTIVE).count(),
                    }
                    for manager in managers.order_by("display_name")
                ]
            }
        )

    @staticmethod
    def payroll_summary(context):
        employees = EmployeeProfile.objects.filter(tenant=context.tenant).select_related("department", "position")
        return ServiceResult.success(
            {
                "count": employees.count(),
                "results": [
                    {
                        "employee_id": employee.id,
                        "employee_name": employee.display_name,
                        "department": employee.department.name if employee.department else "",
                        "position": employee.position.title if employee.position else "",
                        "employment_type": employee.employment_type,
                        "leaves_wallet": str(employee.leaves_wallet),
                        "leaves_per_month": str(employee.leaves_per_month),
                    }
                    for employee in employees.order_by("display_name")
                ],
            }
        )

    @staticmethod
    def documentation_summary(context):
        return ServiceResult.success(
            {
                "offers": OnboardingOffer.objects.filter(tenant=context.tenant).count(),
                "credentials": CredentialVaultItem.objects.filter(tenant=context.tenant).count(),
                "notifications": NotificationItem.objects.filter(tenant=context.tenant).count(),
            }
        )

    @staticmethod
    def create_issue(context, title, provider="Mantis", issue_type="Bug", priority="", status="Open", assigned_to_id=None, metadata=None):
        user_model = get_user_model()
        assigned_to = user_model.objects.filter(id=assigned_to_id).first() if assigned_to_id else None
        issue = ExternalIssueReference.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            title=title,
            provider=provider,
            issue_type=issue_type,
            priority=priority,
            status=status,
            assigned_to=assigned_to,
            metadata=metadata or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        return ServiceResult.success(issue, status_code=201)

    @staticmethod
    def track(context):
        offers = OnboardingOffer.objects.filter(tenant=context.tenant).values("status").annotate(count=Count("id")).order_by("status")
        issues = ExternalIssueReference.objects.filter(tenant=context.tenant).values("status").annotate(count=Count("id")).order_by("status")
        return ServiceResult.success({"offers": list(offers), "issues": list(issues)})

    @staticmethod
    def get_offer_by_token(token):
        offer = OnboardingOffer.objects.filter(token=token).first()
        if not offer:
            return ServiceResult.failure({"offer": "Offer Token Not Found."}, status_code=404)
        return ServiceResult.success(offer)

    @staticmethod
    def reportee_track(context):
        actor_employee = MainAppLegacyService.actor_employee(context)
        if not actor_employee:
            return ServiceResult.success({"results": []})
        reportees = actor_employee.direct_reports.select_related("department", "position").order_by("display_name")
        return ServiceResult.success(
            {
                "results": [
                    {
                        "id": employee.id,
                        "name": employee.display_name,
                        "department": employee.department.name if employee.department else "",
                        "status": employee.status,
                        "joined_on": employee.joined_on.isoformat() if employee.joined_on else None,
                    }
                    for employee in reportees
                ]
            }
        )

    @staticmethod
    def manager_track(context):
        actor_employee = MainAppLegacyService.actor_employee(context)
        if not actor_employee:
            return ServiceResult.success({"results": []})
        scopes = ManagerScope.objects.filter(tenant=context.tenant, manager=actor_employee).select_related("employee", "department")
        return ServiceResult.success(
            {
                "results": [
                    {
                        "id": scope.id,
                        "scope_type": scope.scope_type,
                        "employee": scope.employee.display_name if scope.employee else "",
                        "department": scope.department.name if scope.department else "",
                        "status": scope.status,
                    }
                    for scope in scopes.order_by("scope_type", "id")
                ]
            }
        )

    @staticmethod
    def create_offer(context, data, issue=False):
        offer = OnboardingOffer.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            candidate_name=data.get("candidate_name") or data.get("name") or "Candidate",
            candidate_email=data.get("candidate_email") or data.get("email") or "candidate@example.com",
            company_name=data.get("company_name", ""),
            position_title=data.get("position_title", ""),
            offer_type=data.get("offer_type", ""),
            offer_payload=data.get("offer_payload") or {},
            expires_at=data.get("expires_at"),
            created_by=context.actor,
            updated_by=context.actor,
        )
        if issue:
            return OfferLifecycleService.issue_offer(context, offer.id, expires_at=data.get("expires_at"))
        return ServiceResult.success(offer, status_code=201)

    @staticmethod
    def offer_template_context(offer, overrides=None):
        payload = offer.offer_payload or {}
        issued_on = offer.issued_at or timezone.now()
        joining_value = payload.get("joining_date") or payload.get("joined_on")
        if hasattr(joining_value, "strftime"):
            joining_date = joining_value.strftime("%d/%m/%Y")
        elif joining_value:
            joining_date = str(joining_value)
        else:
            joining_date = issued_on.strftime("%d/%m/%Y")
        actual_offer = offer.status == "Issued"
        candidate_name = offer.candidate_name or "Candidate"
        position_title = offer.position_title or payload.get("title") or payload.get("position_title") or "Intern"
        company_name = offer.company_name or "ATG"
        username = payload.get("username") or "-"
        pay_type = payload.get("pay_type") or "Performance Based"
        
        payment_data_1 = payload.get("payment_data_1") or [
            "Salary Components",
            "INR",
        ]
        payment_data_2 = payload.get("payment_data_2") or [
            pay_type,
            payload.get("amount") or payload.get("fixed") or "As per discussion",
        ]
        intern_duration = payload.get("intern_duration") or payload.get("duration") or "6"
        task = payload.get("task") or payload.get("min_tasks") or "5"
        fixed = payload.get("fixed") or payload.get("amount") or "1000"
        performance_based_pay_type = payload.get("performance_based_pay_type") or "task"
        context_data = {
            "candidate_name": candidate_name,
            "company_name": company_name,
            "position_title": position_title,
            "offer_type": offer.offer_type or payload.get("offer_type") or "Internship",
            "department_name": payload.get("department_name") or payload.get("department") or "General",
            "sub_department_name": payload.get("sub_department_name") or payload.get("sub_department") or "-",
            "username": username,
            "employment_type": payload.get("employment_type") or "Internship",
            "pay_type": pay_type,
            "issued_date": issued_on.strftime("%d/%m/%Y"),
            "joining_date": joining_date,
            "actual_offer": actual_offer,
            "offer_heading": "OFFER LETTER" if actual_offer else "PROVISIONAL OFFER LETTER",
            "offer_disclaimer": "" if actual_offer else "<p style='text-align:center;margin:8px 0 22px;font-size:13px;font-weight:700;'>This is a provisional offer letter. This is NOT an actual offer letter which will be sent after successful first month completion.</p>",
            "candidate_email": offer.candidate_email or "",
            # 
            "user": candidate_name,
            "name": candidate_name,
            "title": position_title,
            "position_name": position_title,
            "position": position_title,
            "present_date": joining_date,
            "intern_duration": intern_duration,
            "task": task,
            "fixed": fixed,
            "Fixed": fixed,
            "performance_based_pay_type": performance_based_pay_type,
            "payment_data_1": payment_data_1,
            "payment_data_2": payment_data_2,
            "payment_data_1_html": "".join(f"<th>{item}</th>" for item in payment_data_1),
            "payment_data_2_html": "".join(f"<th>{item}</th>" for item in payment_data_2),
        }
        if overrides:
            for key, value in overrides.items():
                if value not in (None, ""):
                    context_data[key] = value
        return context_data

    @staticmethod
    def _render_offer_template(template_name, context_data, extra_context=None):
        ctx = {**context_data}
        if extra_context:
            ctx.update(extra_context)
        return render_to_string(template_name, ctx)

    @staticmethod
    def build_legacy_offer_html(offer, overrides=None):
        details = MainAppLegacyService.offer_template_context(offer, overrides)
        return MainAppLegacyService._render_offer_template("Offer-Letter.html", details, {"offer_url": ""})

    @staticmethod
    def build_offer_email_html(offer, offer_url, overrides=None):
        details = MainAppLegacyService.offer_template_context(offer, overrides)
        return MainAppLegacyService._render_offer_template("Offer-Email.html", details, {"offer_url": offer_url})

    @staticmethod
    def check_name(context, email="", username=""):
        user_model = get_user_model()
        exists = False
        if email:
            exists = OnboardingOffer.objects.filter(tenant=context.tenant, candidate_email__iexact=email).exists() or user_model.objects.filter(email__iexact=email).exists()
        if username:
            exists = exists or user_model.objects.filter(username__iexact=username).exists()
        return ServiceResult.success({"exists": exists})

    @staticmethod
    def department_validation(context, department_id=None):
        department = Department.objects.filter(tenant=context.tenant, id=department_id).first() if department_id else None
        return ServiceResult.success(
            {
                "department": {"id": department.id, "name": department.name} if department else None,
                "sub_departments": [{"id": sub.id, "name": sub.name} for sub in SubDepartment.objects.filter(tenant=context.tenant, department_id=department_id).order_by("name")],
            }
        )

    @staticmethod
    def remind_work(context, issue_id=None, summary=""):
        if not issue_id:
            return OfferLifecycleService.queue_offer_reminders(context)
        issue = ExternalIssueReference.objects.filter(tenant=context.tenant).filter(Q(id=issue_id) | Q(external_id=str(issue_id))).select_related("assigned_to").first()
        if not issue:
            return ServiceResult.failure({"issue": "External Issue Not Found."}, status_code=404)
        recipient = issue.assigned_to or context.actor
        if not recipient:
            return ServiceResult.failure({"recipient": "No Issue Assignee or Actor Available for Reminder."}, status_code=400)
        notification = NotificationService.notify(context, recipient, f"Reminder: {issue.title}", message=summary or "Issue Needs Attention.", category="IssueReminder", resource_type="ExternalIssueReference", resource_id=issue.id, metadata={"provider": issue.provider, "external_id": issue.external_id})
        return ServiceResult.success({"issue_id": issue.id, "notification_id": notification.data.id}, status_code=notification.status_code)

    @staticmethod
    def execute_issue_sync(context, issues=None, provider="Mantis", page=0, page_size=0):
        from Backend.Apps.IntegrationHub.models import IntegrationConnection, IntegrationProvider
        from Backend.Apps.IntegrationHub.services import IntegrationJobService

        issues = issues or []
        imported = []
        for issue in issues:
            external_id = str(issue.get("id") or issue.get("external_id") or "")
            if not external_id:
                continue
            title = issue.get("summary") or issue.get("title") or f"{provider} Issue {external_id}"
            item, _created = ExternalIssueReference.objects.update_or_create(
                tenant=context.tenant,
                provider=provider,
                external_id=external_id,
                defaults={"workspace": context.workspace, "title": title, "status": issue.get("status", {}).get("name", issue.get("status", "")), "metadata": issue, "updated_by": context.actor},
            )
            imported.append(item.id)
        integration_provider, _created = IntegrationProvider.objects.get_or_create(
            tenant=context.tenant,
            name=provider,
            defaults={"workspace": context.workspace, "provider_type": "IssueTracker", "auth_type": "Token", "created_by": context.actor, "updated_by": context.actor},
        )
        connection, _created = IntegrationConnection.objects.get_or_create(
            tenant=context.tenant,
            provider=integration_provider,
            name=f"{provider} Legacy Sync",
            defaults={"workspace": context.workspace, "owner_module": "MainApp", "status": "Active", "created_by": context.actor, "updated_by": context.actor},
        )
        job = IntegrationJobService.queue_sync(context, connection, "LegacyIssueSync", cursor=str(page or ""))
        if job.ok:
            IntegrationJobService.complete_job(context, job.data.id, {"importedIssueIds": imported, "page": page, "pageSize": page_size})
        return ServiceResult.success({"status": "synced" if imported else "queued", "imported": len(imported), "issue_ids": imported, "job_id": job.data.id if job.ok else None}, status_code=201)

    @staticmethod
    def send_pdf_offer(context, offer_id, email=None, html_template=None, email_subject=None, email_template=None, macro_values=None):

        from django.conf import settings
        from django.template import Template, Context

        offer = OnboardingOffer.objects.filter(tenant=context.tenant, id=offer_id).first()
        if not offer:
            return ServiceResult.failure({"offer": "Onboarding Offer Not Found."}, status_code=404)

        if offer.status == "Draft":
            issued = OfferLifecycleService.issue_offer(context, offer.id)
            if not issued.ok:
                return issued
            offer = issued.data

        if not pisa:
            return ServiceResult.failure({"error": "PDF Generation Dependencies Not Installed (xhtml2pdf)"}, status_code=500)

        try:
            template_context = MainAppLegacyService.offer_template_context(offer, macro_values or {})
            base_url = str(getattr(settings, "PUBLIC_BASE_URL", "http://localhost:8000") or "http://localhost:8000").rstrip("/")
            offer_url = f"{base_url}/offer/accept/{offer.token or ''}"
            template_context.update({
                "offer_id": offer.id,
                "candidate_name": offer.candidate_name,
                "candidate_email": offer.candidate_email,
                "position": offer.position_title,
                "offer_url": offer_url,
            })
            email = email or offer.candidate_email
            if not email:
                return ServiceResult.failure({"email": "Candidate email not available"}, status_code=400)

            
            pdf_html = MainAppLegacyService._render_offer_template("Offer-Letter.html", template_context)

            pdf_buf = BytesIO()
            pdf_status = pisa.pisaDocument(
                BytesIO(pdf_html.encode("utf-8")),
                pdf_buf,
                encoding="utf-8",
                link_callback=_pisa_link_callback,
            )
            if pdf_status.err:
                return ServiceResult.failure({"error": "PDF generation failed"}, status_code=500)

           
            if email_template:
                try:
                    email_content = Template(email_template).render(Context(template_context))
                except Exception:
                    email_content = MainAppLegacyService.build_offer_email_html(offer, offer_url, template_context)
            else:
                email_content = MainAppLegacyService.build_offer_email_html(offer, offer_url, template_context)

            raw_subject = email_subject or f"Congratulations! Offer As {{{{ position_title }}}} From Across The Globe (ATG)"
            try:
                email_subject = Template(raw_subject).render(Context(template_context))
            except Exception:
                email_subject = f"Congratulations! Offer As {offer.position_title or 'Intern'} From Across The Globe (ATG)"
            if not email_subject or "{{" in email_subject:
                email_subject = f"Congratulations! Offer As {offer.position_title or 'Intern'} From Across The Globe (ATG)"
            from_email = (
                getattr(settings, "DEFAULT_FROM_EMAIL", "")
                or getattr(settings, "EMAIL_HOST_USER", "")
                or "admin@atg.world"
            )

            msg = EmailMultiAlternatives(
                subject=email_subject,
                body="",
                from_email=from_email,
                to=[email],
            )
            msg.attach("Offer Letter.pdf", pdf_buf.getvalue(), "application/pdf")
            msg.attach_alternative(email_content, "text/html")
            msg.send(fail_silently=False)

            return ServiceResult.success({
                "offer_id": offer.id,
                "token": offer.token,
                "filename": f"offer-{offer.id}.pdf",
                "candidate_email": email,
                "email_sent": True,
            })
        except Exception as e:
            return ServiceResult.failure({"error": f"Failed To Send Offer: {str(e)}"}, status_code=500)

    @staticmethod
    def send_certificate(context, recipient_id, joining_date, completion_date, position, responsibility="", title="Certificate issued"):

        from django.conf import settings
        from django.utils.safestring import mark_safe
        
        user_model = get_user_model()
        recipient = user_model.objects.filter(id=recipient_id).first()
        if not recipient:
            return ServiceResult.failure({"recipient": "Recipient User Not Found."}, status_code=404)
        recipient_employee = EmployeeProfile.objects.filter(tenant=context.tenant, user=recipient).select_related("position").first()
        joining_date = joining_date or (recipient_employee.joined_on.isoformat() if recipient_employee and recipient_employee.joined_on else "")
        completion_date = completion_date or timezone.now().date().isoformat()
        position = position or (recipient_employee.position.title if recipient_employee and recipient_employee.position else "Team Member")

        if not pisa:
            return ServiceResult.failure({"error": "PDF Generation Dependencies Not Installed (xhtml2pdf)"}, status_code=500)
        
        try:
            def load_image_data_uri(path_parts, mime_type):
                from django.conf import settings
                base_dir = settings.BASE_DIR
                image_path = os.path.join(base_dir, *path_parts)
                if not os.path.exists(image_path):
                    return ""
                
                with open(image_path, 'rb') as image_file:
                    encoded_img = base64.b64encode(image_file.read()).decode('utf-8')
                return mark_safe(f"data:{mime_type};base64,{encoded_img}")
            
            gender = getattr(getattr(recipient, 'profile', None), 'gender', None)
            if gender == 1:  # Male
                title_prefix = 'Mr.'
                pronoun = 'his'
                pronoun2 = 'him'
                pronoun3 = 'he'
            elif gender == 2:  # Female
                title_prefix = 'Ms./Mrs.'
                pronoun = 'her'
                pronoun2 = 'her'
                pronoun3 = 'she'
            else:
                title_prefix = 'Mr./Ms.'
                pronoun = 'his/her'
                pronoun2 = 'his/her'
                pronoun3 = 'he/she'
            
            cert_context = {
                'joining_date': joining_date,
                'completion_date': completion_date,
                'position': position,
                'name': recipient.get_full_name(),
                'title': title_prefix,
                'pronoun': pronoun,
                'pronoun2': pronoun2,
                'pronoun3': pronoun3,
            }
            
            try:
                cert_context['certificate_logo'] = load_image_data_uri(
                    ('Apps', 'Banao', 'static', 'banao', 'images', 'logo.png'),
                    'image/png',
                )
                cert_context['signature_image'] = load_image_data_uri(
                    ('Apps', 'MainApp', 'static', 'images', 'signature-1.jpg'),
                    'image/jpeg',
                )
            except:
                pass 
            
            if responsibility:
                cert_context['responsibility'] = responsibility
            
            html_content = render_to_string('mainapp/certificates/certificate.html', cert_context)
            pdf_html = _sanitize_html_for_pisa(html_content)
            result = BytesIO()
            pdf_status = pisa.pisaDocument(
                BytesIO(pdf_html.encode("utf-8")),
                result,
                encoding="utf-8",
                link_callback=_pisa_link_callback,
            )
            
            if pdf_status.err:
                return ServiceResult.failure({"error": "Certificate PDF generation failed"}, status_code=500)
            
            email_content = render_to_string('mainapp/certificates/certificate_email.html', {'name': recipient.get_full_name()})
            
            if recipient.email and recipient.email != '':
                from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "") or getattr(settings, "EMAIL_HOST_USER", "") or "admin@atg.world"
                
                certificate_email = EmailMultiAlternatives(
                    'Across The Globe (ATG) : Internship Completion Certificate',
                    "",
                    from_email,
                    [recipient.email]
                )
                certificate_email.attach('Certificate.pdf', result.getvalue(), 'application/pdf')
                certificate_email.attach_alternative(email_content, 'text/html')
                certificate_email.send(fail_silently=False)
                
                try:
                    from Backend.Apps.Users.models import EmployeeCertificate
                    EmployeeCertificate.objects.create(
                        tenant=context.tenant,
                        manager=context.actor,
                        employee=recipient_employee,
                        position_title=position,
                        issued_on=timezone.now().date(),
                        created_by=context.actor,
                        updated_by=context.actor,
                    )
                except:
                    pass  
                
                NotificationService.notify(context, recipient, title, message="Certificate Has Been Generated And Sent vVa Email.", category="Certificate")
                
                return ServiceResult.success({
                    "recipient_id": recipient.id,
                    "recipient_email": recipient.email,
                    "certificate_sent": True
                })
            else:
                return ServiceResult.failure({"email": "Recipient Email Not Available"}, status_code=400)
        
        except Exception as e:
            return ServiceResult.failure({"error": f"Failed To Send Certificate: {str(e)}"}, status_code=500)

    @staticmethod
    def search_username(context, query):
        user_model = get_user_model()
        users = user_model.objects.filter(Q(username__icontains=query) | Q(email__icontains=query)).order_by("username")[:20]
        return ServiceResult.success({"results": [{"id": user.id, "username": user.username, "email": user.email} for user in users]})

    @staticmethod
    def get_joining_date(context, employee_id=None):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first() if employee_id else MainAppLegacyService.actor_employee(context)
        if not employee:
            return ServiceResult.failure({"employee": "Employee Not Found."}, status_code=404)
        return ServiceResult.success({"employee_id": employee.id, "joined_on": employee.joined_on.isoformat() if employee.joined_on else None})

    @staticmethod
    def deactivate_employee(context, employee_id, reason=""):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee Not Found."}, status_code=404)
        from Backend.Apps.Users.models import UserStatusSnapshot
        employee.status = EmployeeProfile.STATUS_EXITED
        employee.exited_on = timezone.localdate()
        employee.updated_by = context.actor
        employee.save(update_fields=["status", "exited_on", "updated_by", "updated_at"])
        user = employee.user
        if user and user.is_active:
            user.is_active = False
            user.save(update_fields=["is_active", "updated_at"])
        UserStatusSnapshot.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or employee.workspace,
            employee=employee,
            status=EmployeeProfile.STATUS_EXITED,
            reason=reason,
            effective_from=timezone.localdate(),
            created_by=context.actor,
            updated_by=context.actor,
        )
        NotificationService.notify(
            context=context,
            recipient=user,
            title="Account Deactivated",
            message=f"Your account has been deactivated. Reason: {reason}" if reason else "Your account has been deactivated.",
            category="Account",
            resource_type="EmployeeProfile",
            resource_id=employee.id,
        )
        OutboxService.publish(context, "EmployeeProfile", employee.id, "EmployeeDeactivated", {"employeeId": employee.id, "reason": reason})
        if user and user.email:
            try:
                from django.conf import settings
                from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", "") or "admin@atg.world"
                msg = EmailMultiAlternatives(
                    subject="Your ATG Intranet Account Has Been Deactivated",
                    body=f"Dear {employee.display_name or user.username},\n\nYour ATG Intranet account has been deactivated."
                         + (f"\nReason: {reason}" if reason else "")
                         + "\n\nIf you believe this is a mistake, please contact HR.\n\n— ATG Intranet",
                    from_email=from_email,
                    to=[user.email],
                )
                msg.send(fail_silently=True)
            except Exception:
                pass
        return ServiceResult.success(employee)

    @staticmethod
    def deactivate_multiple_employees(context, employee_ids, reason=""):
        rows = []
        for employee_id in employee_ids:
            result = MainAppLegacyService.deactivate_employee(context, employee_id, reason=reason)
            if result.ok:
                rows.append(result.data.id)
        return ServiceResult.success({"count": len(rows), "employee_ids": rows})

    @staticmethod
    def api_testing(context, branch_name="master", live=False):
        try:
            result = PartyRemoteAutomationProvider(live=live).run_branch_api_tests(branch_name)
        except (PartyRemoteAutomationError, KeyError, TypeError) as exc:
            return ServiceResult.failure({"automation": str(exc)}, status_code=502)
        if not isinstance(result, dict):
            return ServiceResult.failure({"automation": "Invalid Response From Automation Provider."}, status_code=502)
        OutboxService.publish(context, "RemoteAutomation", branch_name or "master", "LegacyApiAutomationRequested", {"live": live, "failedCount": result.get("api_testing", {}).get("failed_count", 0)})
        return ServiceResult.success({"status": "ok", "tenant": context.tenant.slug, "workspace": context.workspace.code if context.workspace else None, "automation": result})

    @staticmethod
    def all_users_doc_view(context):
        offers = OnboardingOffer.objects.filter(tenant=context.tenant).order_by("-created_at")[:25]
        return ServiceResult.success({"results": [{"id": offer.id, "candidate_name": offer.candidate_name, "status": offer.status, "candidate_email": offer.candidate_email} for offer in offers]})

    @staticmethod
    def search(context, query):
        employees = EmployeeProfile.objects.filter(tenant=context.tenant).filter(Q(display_name__icontains=query) | Q(employee_code__icontains=query))[:10]
        offers = OnboardingOffer.objects.filter(tenant=context.tenant).filter(Q(candidate_name__icontains=query) | Q(candidate_email__icontains=query))[:10]
        credentials = CredentialVaultItem.objects.filter(tenant=context.tenant).filter(Q(name__icontains=query) | Q(system_name__icontains=query))[:10]
        return ServiceResult.success(
            {
                "employees": [{"id": employee.id, "name": employee.display_name} for employee in employees],
                "offers": [{"id": offer.id, "candidate_name": offer.candidate_name} for offer in offers],
                "credentials": [{"id": credential.id, "name": credential.name} for credential in credentials],
            }
        )

    @staticmethod
    def update_reportee(context, issue_id, employee_id):
        issue = ExternalIssueReference.objects.filter(tenant=context.tenant, id=issue_id).first()
        if not issue:
            return ServiceResult.failure({"issue": "External Issue Not Found."}, status_code=404)
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).select_related("user").first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee Not Found."}, status_code=404)
        issue.assigned_to = employee.user
        issue.updated_by = context.actor
        issue.save(update_fields=["assigned_to", "updated_by", "updated_at"])
        return ServiceResult.success(issue)

    @staticmethod
    def pass_management(context):
        credentials = CredentialVaultItem.objects.filter(tenant=context.tenant).select_related("owner")
        return ServiceResult.success(
            {
                "results": [
                    {
                        "id": credential.id,
                        "name": credential.name,
                        "system_name": credential.system_name,
                        "owner": credential.owner.username,
                        "status": credential.status,
                    }
                    for credential in credentials.order_by("system_name", "name")
                ]
            }
        )

    @staticmethod
    def create_credential(context, owner_id, name, system_name, secret_reference, metadata=None):
        user_model = get_user_model()
        owner = user_model.objects.filter(id=owner_id).first()
        if not owner:
            return ServiceResult.failure({"owner": "Owner User Not Found."}, status_code=404)
        credential = CredentialVaultItem.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            owner=owner,
            name=name,
            system_name=system_name,
            secret_reference=secret_reference,
            metadata=metadata or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        return ServiceResult.success(credential, status_code=201)

    @staticmethod
    def get_credentials(context, owner_id=None):
        credentials = CredentialVaultItem.objects.filter(tenant=context.tenant).select_related("owner")
        if owner_id:
            credentials = credentials.filter(owner_id=owner_id)
        return ServiceResult.success(
            {
                "results": [
                    {
                        "id": credential.id,
                        "name": credential.name,
                        "system_name": credential.system_name,
                        "owner": credential.owner.username,
                        "status": credential.status,
                    }
                    for credential in credentials.order_by("name")
                ]
            }
        )

    @staticmethod
    def share_credential(context, credential_id, grantee_id, permission="Read", expires_at=None, reason=""):
        user_model = get_user_model()
        grantee = user_model.objects.filter(id=grantee_id).first()
        if not grantee:
            return ServiceResult.failure({"grantee": "Grantee User Not Found."}, status_code=404)
        return CredentialVaultService.share(context, credential_id, grantee, permission=permission, expires_at=expires_at, reason=reason)

    @staticmethod
    def search_user(context, query):
        employees = EmployeeProfile.objects.filter(tenant=context.tenant).filter(Q(display_name__icontains=query) | Q(user__username__icontains=query)).select_related("user")[:20]
        return ServiceResult.success({"results": [{"id": employee.user_id, "employee_id": employee.id, "username": employee.user.username, "name": employee.display_name} for employee in employees]})

    @staticmethod
    def remove_share(context, grant_id):
        return CredentialVaultService.revoke_share(context, grant_id)

    @staticmethod
    def test_password_reset(context, user_id=None, email=""):
        user_model = get_user_model()
        user = user_model.objects.filter(id=user_id).first() if user_id else user_model.objects.filter(email__iexact=email).first()
        if not user:
            return ServiceResult.failure({"user": "User Not Found."}, status_code=404)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return ServiceResult.success({"uid": uid, "token": token, "email": user.email})

    @staticmethod
    def register_employee(context, data):
        user_model = get_user_model()
        username = (data.get("username") or "").strip()
        email = (data.get("email") or data.get("candidate_email") or "").strip()
        display_name = (data.get("display_name") or data.get("candidate_name") or username or email or "Employee").strip()
        employee_code = (data.get("employee_code") or "").strip()
        if not employee_code:
            return ServiceResult.failure({"employee_code": "Employee Code Is Required."}, status_code=400)
        if not username and not email:
            return ServiceResult.failure({"username": "Username Or Email Is Required."}, status_code=400)
        if not username:
            username = email.split("@")[0]
        existing = user_model.objects.filter(Q(username__iexact=username) | (Q(email__iexact=email) if email else Q(pk__in=[]))).first()
        if existing:
            conflict = {}
            if username and str(existing.username).lower() == username.lower():
                conflict["username"] = "Username Already Exists. Use A Different Login ID For The New Employee."
            if email and str(existing.email or "").lower() == email.lower():
                conflict["email"] = "Email Already Exists. Use A Different Employee Email For The New Account."
            linked_employee = EmployeeProfile.objects.filter(user=existing, is_active=True).select_related("tenant", "workspace").order_by("id").first()
            if linked_employee:
                workspace_name = linked_employee.workspace.name if linked_employee.workspace_id else (linked_employee.tenant.name if linked_employee.tenant_id else "Current Workspace")
                conflict["employee"] = f"This login is already mapped to {linked_employee.display_name} ({linked_employee.employee_code}) in {workspace_name}."
            return ServiceResult.failure(conflict or {"user": "User Already Exists."}, status_code=409)
        password = data.get("password") or get_random_string(12)
        user = user_model.objects.create_user(username=username, email=email or "", password=password)
        first, _, last = display_name.partition(" ")
        if first:
            user.first_name = first[:30]
        if last:
            user.last_name = last[:150]
        user.save(update_fields=["first_name", "last_name"])
        if EmployeeProfile.objects.filter(tenant=context.tenant, user=user).exists():
            employee = EmployeeProfile.objects.filter(tenant=context.tenant, user=user).first()
            return ServiceResult.failure({"employee": f"User Already Has An Employee Profile In {context.tenant.name}: {employee.display_name} ({employee.employee_code})."}, status_code=409)
        if EmployeeProfile.objects.filter(tenant=context.tenant, employee_code=employee_code).exists():
            return ServiceResult.failure({"employee_code": "Employee Code Already In Use."}, status_code=400)
        department_id = data.get("department") or None
        position_id = data.get("position") or None
        manager_id = data.get("manager") or None
        joined_on = data.get("joined_on") or None
        employee = EmployeeProfile.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            user=user,
            employee_code=employee_code,
            display_name=display_name,
            contact_number=data.get("contact_number", ""),
            github_username=data.get("github_username", ""),
            slack_username=data.get("slack_username", ""),
            department_id=department_id or None,
            position_id=position_id or None,
            manager_id=manager_id or None,
            employment_type=data.get("employment_type", ""),
            status=data.get("status") or EmployeeProfile.STATUS_ACTIVE,
            joined_on=joined_on or timezone.localdate(),
            leaves_wallet=data.get("leaves_wallet") or 0,
            leaves_per_month=data.get("leaves_per_month") or 0,
            onboarding_completed=False,
            profile_payload=data.get("profile_payload") or {"registered_via": "employee_registrar"},
            created_by=context.actor,
            updated_by=context.actor,
        )
        return ServiceResult.success(employee, status_code=201)
