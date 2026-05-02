from urllib.parse import urlparse

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from Backend.Apps.Banao.models import AuditArtifact, LeadAccount, LeadActivity, LeadContact, LeadNote, LeadTag, LeadTest, ProposalArtifact, WorkflowStatusHistory, WorkflowTransition
from Backend.Apps.Banao.serializers import (
    AuditArtifactSerializer,
    BanaoOfferDispatchSerializer,
    LeadCaptureSerializer,
    LeadAccountSerializer,
    LeadActivitySerializer,
    LeadContactSerializer,
    LegacyLeadCaptureSerializer,
    LegacyLeadConnectionSerializer,
    LeadNoteCreateSerializer,
    LeadNoteSerializer,
    LeadTagSerializer,
    LeadTestCreateSerializer,
    LeadTestSerializer,
    ProposalArtifactSerializer,
    WorkflowActionSerializer,
    WorkflowStatusHistorySerializer,
    WorkflowTransitionSerializer,
)
from Backend.Apps.Banao.services import LeadWorkflowService
from Backend.Apps.MainApp.models import OnboardingOffer
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult, TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.response import Response


PERSONAL_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.co.in",
    "ymail.com",
    "rocketmail.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
    "pm.me",
    "zoho.com",
    "mail.com",
    "gmx.com",
    "rediffmail.com",
}

COUNTRY_DIAL_CODES = {
    "AE": "+971",
    "AU": "+61",
    "BD": "+880",
    "CA": "+1",
    "DE": "+49",
    "ES": "+34",
    "FR": "+33",
    "GB": "+44",
    "IN": "+91",
    "JP": "+81",
    "KE": "+254",
    "NG": "+234",
    "NL": "+31",
    "NZ": "+64",
    "PK": "+92",
    "QA": "+974",
    "SA": "+966",
    "SG": "+65",
    "US": "+1",
    "ZA": "+27",
}

LEGACY_ORIGIN_LABELS = {
    "w": "Banao Website",
    "l": "Linked In",
    "i": "Instagram",
    "t": "Twitter",
    "g": "GitHub",
    "cw": "Client Website",
    "ig": "InterviewGod",
    "vikaas": "Vikaas",
}

LEGACY_INDUSTRY_CHOICES = {
    "LMS",
    "Ed-Tech (Education)",
    "Agriculture",
    "Automobile / Automotive",
    "Business",
    "Architecture & Design",
    "Real Estate & Construction",
    "HRMS/CRM",
    "E-Commerce",
    "Finance/FinTech",
    "Health / Wellness",
    "Fitness",
    "Government/NGO",
    "Security / Defence",
    "Social Network",
    "Beauty and Wellness",
    "Animal Welfare",
    "Biotech/Nanotech",
    "Restaurants/ Foodtech",
    "ERP",
    "Entertainment",
    "SaaS",
    "Sports",
    "Others",
}

DEFAULT_BANAO_LEAD_RECIPIENTS = [
    "hello@banao.tech",
    "jahnavi.reddy@banao.tech",
    "poojasinha2012001@gmail.com",
    "aswanthtedlapu@gmail.com",
]

ROLE_BASE_PAY_OVERRIDES = {
    "Business Development Associate (Band 1)": "1500",
    "Business Development Associate (Band 2)": "1000",
    "Business Development Associate (Band 3)": "700",
    "Captain ( Business Development Management) Intern": "2500",
}


def _request_value(request, *keys):
    for key in keys:
        if hasattr(request, "data") and key in request.data:
            return request.data.get(key)
        if hasattr(request, "query_params") and key in request.query_params:
            return request.query_params.get(key)
        header_key = f"HTTP_{str(key).upper().replace('-', '_')}"
        if header_key in request.META:
            return request.META.get(header_key)
    return None


def _normalize_source_page_url(value):
    source_page_url = str(value or "").strip()
    if not source_page_url:
        return ""
    parsed = urlparse(source_page_url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return source_page_url[:1000]


def _derive_source_page_name(source_page_url):
    if not source_page_url:
        return ""
    parsed = urlparse(source_page_url)
    path = parsed.path.strip("/")
    if path:
        last_segment = path.split("/")[-1].replace("-", " ").replace("_", " ").strip()
        if last_segment:
            return last_segment.title()[:255]
    return (parsed.netloc or source_page_url)[:255]


def _extract_email_domain(email):
    value = str(email or "").strip().lower()
    if "@" not in value:
        return ""
    return value.rsplit("@", 1)[-1]


def _is_personal_email(email):
    return _extract_email_domain(email) in PERSONAL_EMAIL_DOMAINS


def _country_hint(request):
    for key in ("country_code", "country", "country_iso", "country_iso_code"):
        value = str(_request_value(request, key) or "").strip().upper()
        if value:
            return value[:2]
    return ""


def _explicit_dial_code(request):
    for key in ("phone_country_code", "country_dial_code", "dial_code", "countryCode"):
        value = str(_request_value(request, key) or "").strip()
        if value:
            digits = "".join(character for character in value if character.isdigit())
            if digits:
                return f"+{digits}"
    return ""


def _normalize_phone_number(phone, dial_code="", country_hint=""):
    raw_phone = str(phone or "").strip()
    if not raw_phone:
        return ""
    filtered = "".join(character for character in raw_phone if character.isdigit() or character == "+")
    if filtered.startswith("00"):
        filtered = f"+{filtered[2:]}"
    if filtered.startswith("+"):
        digits = "".join(character for character in filtered if character.isdigit())
        return f"+{digits}" if digits else ""
    digits = "".join(character for character in filtered if character.isdigit())
    if not digits:
        return ""
    effective_dial_code = dial_code or COUNTRY_DIAL_CODES.get((country_hint or "").upper(), "")
    if effective_dial_code:
        return f"{effective_dial_code}{digits}"
    return digits


def _get_authenticated_employee_profile(request, tenant=None):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None
    profiles = EmployeeProfile.objects.filter(user=user).select_related("tenant", "workspace")
    if tenant:
        profiles = profiles.filter(tenant=tenant)
    return profiles.order_by("id").first()


def _resolve_request_tenant_context(request):
    actor = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
    actor_profile = _get_authenticated_employee_profile(request)
    if actor_profile:
        return ServiceResult.success(TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="BanaoLegacy"))

    tenant_hint = _request_value(request, "tenant", "tenant_id", "x-tenant-id")
    workspace_hint = _request_value(request, "workspace", "workspace_id", "x-workspace-id")
    tenant = None
    if tenant_hint:
        tenant_text = str(tenant_hint).strip()
        if tenant_text.isdigit():
            tenant = Tenant.objects.filter(id=int(tenant_text), status=Tenant.STATUS_ACTIVE).first()
        if not tenant:
            tenant = Tenant.objects.filter(status=Tenant.STATUS_ACTIVE, slug__iexact=tenant_text).first() or Tenant.objects.filter(status=Tenant.STATUS_ACTIVE, name__iexact=tenant_text).first()
    else:
        active_tenants = list(Tenant.objects.filter(status=Tenant.STATUS_ACTIVE).order_by("id")[:2])
        if len(active_tenants) == 1:
            tenant = active_tenants[0]
    if not tenant:
        return ServiceResult.failure({"tenant": "Tenant Context Is Required For This Request."}, status_code=400)
    workspace = None
    if workspace_hint:
        workspace_text = str(workspace_hint).strip()
        if workspace_text.isdigit():
            workspace = Workspace.objects.filter(tenant=tenant, id=int(workspace_text)).first()
        if not workspace:
            workspace = Workspace.objects.filter(tenant=tenant, code__iexact=workspace_text).first() or Workspace.objects.filter(tenant=tenant, name__iexact=workspace_text).first()
    if not workspace:
        workspace = Workspace.objects.filter(tenant=tenant).order_by("id").first()
    return ServiceResult.success(TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="BanaoLegacy"))


def _build_authenticated_user_context(request, tenant):
    profile = _get_authenticated_employee_profile(request, tenant=tenant)
    user = getattr(request, "user", None)
    is_registered = bool(user and user.is_authenticated)
    return {
        "is_registered": is_registered,
        "user_id": str(user.id) if is_registered else "",
        "username": getattr(user, "username", "") if is_registered else "",
        "full_name": (profile.display_name if profile else user.get_full_name().strip()) if is_registered else "",
        "email": getattr(user, "email", "") if is_registered else "",
        "phone": profile.contact_number if profile else "",
    }


def _build_lead_contact_context(request, validated_data, tenant):
    user_context = _build_authenticated_user_context(request, tenant)
    dial_code = _explicit_dial_code(request)
    country_hint = _country_hint(request)
    full_name = str(validated_data.get("full_name") or user_context["full_name"] or "").strip()
    email = str(validated_data.get("email") or user_context["email"] or "").strip()
    phone = _normalize_phone_number(validated_data.get("phone") or user_context["phone"] or "", dial_code=dial_code, country_hint=country_hint)
    linkedin_url = str(validated_data.get("linkedin_url") or "").strip()
    original_message = str(validated_data.get("message") or "").strip()
    return {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "linkedin_url": linkedin_url,
        "original_message": original_message,
        "user_type": "REGISTERED USER" if user_context["is_registered"] else "GUEST",
        "registered_status": "Registered" if user_context["is_registered"] else "Guest",
        "user_id": user_context["user_id"],
        "username": user_context["username"],
        "is_registered": user_context["is_registered"],
    }


def _build_structured_lead_message(lead_context):
    lines = [
        f"Name: {lead_context['full_name']}",
        f"Email: {lead_context['email']}",
        f"Phone: {lead_context['phone']}",
        f"User Type: {lead_context['user_type']}",
        f"Registered Status: {lead_context['registered_status']}",
    ]
    if lead_context.get("user_id"):
        lines.append(f"USER_ID: {lead_context['user_id']}")
    if lead_context.get("username"):
        lines.append(f"Username: {lead_context['username']}")
    if lead_context.get("linkedin_url"):
        lines.append(f"LinkedIn: {lead_context['linkedin_url']}")
    lines.append("")
    lines.append(f"Message: {lead_context['original_message']}")
    return "\n".join(lines)


def _origin_label(origin):
    return LEGACY_ORIGIN_LABELS.get(origin, "Lead Form")


def _get_source_page_details(request, validated_data):
    source_page_url = _normalize_source_page_url(
        validated_data.get("source_page_url")
        or validated_data.get("page_url")
        or validated_data.get("form_page_url")
        or request.META.get("HTTP_REFERER")
    )
    source_page_name = str(
        validated_data.get("source_page_name")
        or validated_data.get("page_name")
        or validated_data.get("form_page_name")
        or ""
    ).strip()[:255]
    if source_page_url and not source_page_name:
        source_page_name = _derive_source_page_name(source_page_url)
    return source_page_name, source_page_url


def _notification_bodies(source_label, formatted_message, source_page_name="", source_page_url=""):
    plain_lines = [f"Request Received From {source_label}."]
    if source_page_url:
        page_label = source_page_name or source_page_url
        plain_lines.append(f"Source Page: {page_label} - {source_page_url}")
    plain_lines.append("")
    plain_lines.append(formatted_message)
    html_lines = [f"<p>Request Received From {source_label}.</p>"]
    if source_page_url:
        link_label = source_page_name or source_page_url
        html_lines.append(f'<p>Source Page: <a href="{source_page_url}" target="_blank" rel="noopener noreferrer">{link_label}</a></p>')
    html_lines.append(f"<p>{formatted_message.replace(chr(10), '<br>')}</p>")
    return "\n".join(plain_lines), "\n".join(html_lines)


def _send_lead_notification_email(full_name, formatted_message, source_label, source_page_name="", source_page_url=""):
    recipients = getattr(settings, "BANAO_LEAD_RECIPIENTS", DEFAULT_BANAO_LEAD_RECIPIENTS)
    if not recipients:
        return {"sent": False, "reason": "No Banao Lead Recipients Configured."}
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "") or getattr(settings, "EMAIL_HOST_USER", "") or "noreply@atg.world"
    plain_body, html_body = _notification_bodies(source_label, formatted_message, source_page_name=source_page_name, source_page_url=source_page_url)
    try:
        message = EmailMultiAlternatives(
            subject=f"New Lead Submitted - {full_name}",
            body=plain_body,
            from_email=from_email,
            to=list(recipients),
            cc=list(getattr(settings, "BANAO_LEAD_CC", ["saurabh@atg.world"])),
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)
        return {"sent": True}
    except Exception as exc:
        return {"sent": False, "error": str(exc)}


def _company_name_for_lead(validated_data, lead_context, website_url=""):
    provided_company_name = str(validated_data.get("company_name") or "").strip()
    if provided_company_name:
        return provided_company_name
    domain = LeadWorkflowService._normalize_domain(website_url)
    if domain:
        return domain
    return lead_context["full_name"] or "Prospect"


def _capture_public_lead(request, dedupe_by_url=False):
    serializer = LegacyLeadCaptureSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    context_result = _resolve_request_tenant_context(request)
    if not context_result.ok:
        return Response(context_result.errors, status=context_result.status_code)
    context = context_result.data
    validated_data = serializer.validated_data
    lead_context = _build_lead_contact_context(request, validated_data, context.tenant)
    if not (lead_context["full_name"] and lead_context["email"] and lead_context["phone"] and lead_context["original_message"]):
        return Response({"error": "Full Name, Email, Phone, and Message Are Required"}, status=status.HTTP_400_BAD_REQUEST)
    if _is_personal_email(lead_context["email"]) and not lead_context["linkedin_url"]:
        return Response({"error": "LinkedIn Profile Is Required When Using a Personal Email Address.", "linkedin_required": True}, status=status.HTTP_400_BAD_REQUEST)
    origin = str(validated_data.get("origin") or "w").strip() or "w"
    source_label = _origin_label(origin)
    source_page_name, source_page_url = _get_source_page_details(request, validated_data)
    website_url = str(validated_data.get("url") or "").strip()
    industry = str(validated_data.get("industry") or "Others").strip() or "Others"
    if dedupe_by_url and industry not in LEGACY_INDUSTRY_CHOICES:
        industry = "Others"
    emails = [item.strip() for item in lead_context["email"].split(",") if item.strip()]
    phones = [_normalize_phone_number(item, country_hint=_country_hint(request)) for item in lead_context["phone"].split(",") if item.strip()]
    duplicate_lead = LeadWorkflowService.find_duplicate_public_lead(
        context,
        lead_context["full_name"],
        emails=emails,
        phones=phones,
        website_url=website_url if dedupe_by_url else "",
    )
    if duplicate_lead:
        duplicate_message = "Lead Already Exists With The Same URL" if dedupe_by_url and website_url else "Lead Already Exists With The Same Full Name, Email, And Phone"
        return Response({"message": duplicate_message, "lead_id": duplicate_lead.id}, status=status.HTTP_200_OK)
    structured_message = f"Request Received From {source_label}.\n\n{_build_structured_lead_message(lead_context)}"
    metadata = {
        "url": website_url,
        "linkedin_url": lead_context["linkedin_url"],
        "registered_user": lead_context["is_registered"],
        "registered_status": lead_context["registered_status"],
        "username": lead_context["username"],
        "user_id": lead_context["user_id"],
        "original_message": lead_context["original_message"],
        "source_label": source_label,
    }
    result = LeadWorkflowService.capture_lead(
        context,
        _company_name_for_lead(validated_data, lead_context, website_url=website_url),
        source=origin,
        contact_name=lead_context["full_name"],
        contact_email=lead_context["email"],
        contact_phone=lead_context["phone"],
        website_url=website_url,
        industry=industry,
        connection_id=str(validated_data.get("connection_id") or ""),
        source_page_name=source_page_name,
        source_page_url=source_page_url,
        stage="ContactAttempted" if origin == "cw" else "New",
        initial_note=structured_message,
        metadata=metadata,
    )
    if not result.ok:
        return Response(result.errors, status=result.status_code)
    notification_result = {"sent": False, "reason": "Skipped For Client Website Leads."}
    if origin != "cw":
        notification_result = _send_lead_notification_email(
            lead_context["full_name"],
            structured_message,
            source_label,
            source_page_name=source_page_name,
            source_page_url=source_page_url,
        )
    return Response(
        {"message": "Lead Successfully Saved", "lead_id": result.data.id, "notification_sent": notification_result.get("sent", False), "notification_error": notification_result.get("error", "")},
        status=status.HTTP_201_CREATED,
    )


def _offer_payload(validated_data, preview_mode=False):
    position_name = str(validated_data.get("position_name") or "").strip()
    base_pay_override = ROLE_BASE_PAY_OVERRIDES.get(position_name)
    base_pay = base_pay_override or str(validated_data.get("base_pay") or "0")
    offer_date = validated_data.get("offer_date") or timezone.localdate()
    return {
        "email": str(validated_data.get("email") or "").strip(),
        "username": str(validated_data.get("username") or "").strip(),
        "name": str(validated_data.get("name") or "").strip(),
        "position_name": position_name,
        "department_name": str(validated_data.get("department_name") or "").strip(),
        "pay_type": str(validated_data.get("pay_type") or "Fixed").strip() or "Fixed",
        "base_pay": str(base_pay),
        "pay_per_task": str(validated_data.get("pay_per_task") or "0"),
        "offer_type": str(validated_data.get("offer_type") or "Intern").strip() or "Intern",
        "title": str(validated_data.get("title") or "").strip(),
        "whatsapp": str(validated_data.get("whatsapp") or "").strip(),
        "slack": str(validated_data.get("slack") or "").strip(),
        "whatsapp_link": str(validated_data.get("whatsapp_link") or "").strip(),
        "offer_date": offer_date.isoformat(),
        "preview": preview_mode,
        "expires_at": timezone.now() + timezone.timedelta(days=2),
    }


def _send_offer_email(offer, offer_url):
    payload = offer.offer_payload or {}
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "") or getattr(settings, "EMAIL_HOST_USER", "") or "noreply@atg.world"
    subject = f"Congratulations! Offer As {payload.get('position_name') or offer.position_title} ({payload.get('title') or offer.position_title}) From Across The Globe (ATG)"
    plain_body = "\n".join(
        [
            f"Hi {offer.candidate_name},",
            "",
            "Your Banao offer is ready.",
            f"Role: {payload.get('position_name') or offer.position_title}",
            f"Department: {payload.get('department_name') or 'Banao'}",
            f"Offer URL: {offer_url}",
        ]
    )
    html_body = LeadWorkflowService.render_offer_preview_html(payload, offer_url=offer_url)
    message = EmailMultiAlternatives(subject=subject, body=plain_body, from_email=from_email, to=[offer.candidate_email])
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def lead_create(request):
    return _capture_public_lead(request, dedupe_by_url=False)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def new_lead_create(request):
    return _capture_public_lead(request, dedupe_by_url=True)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def update_lead_on_connection_sent(request):
    serializer = LegacyLeadConnectionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    context_result = _resolve_request_tenant_context(request)
    if not context_result.ok:
        return Response(context_result.errors, status=context_result.status_code)
    result = LeadWorkflowService.record_connection_sent(context_result.data, serializer.validated_data["domain"], intern_name=serializer.validated_data.get("intern_name", ""), client_name=serializer.validated_data.get("client_name", ""))
    return Response({"message": "Lead Successfully Saved", "lead_id": result.data.id} if result.ok else result.errors, status=result.status_code)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def department_options(request):
    context_result = _resolve_request_tenant_context(request)
    if not context_result.ok:
        return Response(context_result.errors, status=context_result.status_code)
    result = LeadWorkflowService.list_department_options(context_result.data)
    return Response(result.data if result.ok else result.errors, status=result.status_code)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_options(request):
    context_result = _resolve_request_tenant_context(request)
    if not context_result.ok:
        return Response(context_result.errors, status=context_result.status_code)
    department_ref = request.query_params.get("data") or request.query_params.get("department") or ""
    result = LeadWorkflowService.list_user_options(context_result.data, department_ref=department_ref)
    return Response(result.data if result.ok else result.errors, status=result.status_code)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def sendoffer(request):
    serializer = BanaoOfferDispatchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    context_result = _resolve_request_tenant_context(request)
    if not context_result.ok:
        return Response(context_result.errors, status=context_result.status_code)
    context = context_result.data
    preview_mode = str(request.data.get("preview") or "").strip().lower() in {"preview", "true", "1", "yes"}
    validated_data = serializer.validated_data
    duplicate_message = LeadWorkflowService.find_duplicate_offer(context, validated_data.get("email"), username=validated_data.get("username"))
    if duplicate_message:
        return HttpResponse(duplicate_message, status=400) if preview_mode else Response({"error": duplicate_message}, status=status.HTTP_400_BAD_REQUEST)
    actor_profile = _get_authenticated_employee_profile(request, tenant=context.tenant)
    department = None
    department_name = validated_data.get("department_name")
    if department_name:
        department = actor_profile.department.__class__.objects.filter(tenant=context.tenant, name=department_name).first() if actor_profile and actor_profile.department else None
        if not department:
            from Backend.Apps.Users.models import Department

            department = Department.objects.filter(tenant=context.tenant, name=department_name).first()
        if not department:
            return Response({"error": "Department Not Found."}, status=status.HTTP_400_BAD_REQUEST)
        if department.category and department.category != validated_data.get("position_name"):
            return Response({"error": "Department And Position Does Not Have Dependency!!"}, status=status.HTTP_400_BAD_REQUEST)
    offer_payload = _offer_payload(validated_data, preview_mode=preview_mode)
    if preview_mode:
        return HttpResponse(LeadWorkflowService.render_offer_preview_html(offer_payload), content_type="text/html")
    result = LeadWorkflowService.issue_banao_offer(context, offer_payload)
    if not result.ok:
        return Response(result.errors, status=result.status_code)
    offer = result.data
    offer_url = request.build_absolute_uri(reverse("banaodummy", args=[offer.token]))
    _send_offer_email(offer, offer_url)
    return Response({"message": "Offer Sent Successfully", "offer_id": offer.id, "token": offer.token, "offer_url": offer_url}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def banao_dummy(request, token):
    offer = OnboardingOffer.objects.filter(company_name__iexact="Banao", token=token).first()
    if not offer:
        return HttpResponse("Offer Letter Has Expired!", status=404)
    if offer.status == "Accepted":
        return HttpResponse("Offer Already Accepted!!!")
    if offer.expires_at and timezone.now() > offer.expires_at:
        return HttpResponse("Offer Expired, Valid For 2 Days From Offer Sent Date!", status=410)
    offer_url = request.build_absolute_uri(reverse("banaodummy", args=[offer.token]))
    return HttpResponse(LeadWorkflowService.render_offer_preview_html(offer.offer_payload or {}, offer_url=offer_url), content_type="text/html")


class LeadTagViewSet(TenantScopedModelViewSet):
    queryset = LeadTag.objects.select_related("tenant", "workspace").all()
    serializer_class = LeadTagSerializer


class LeadAccountViewSet(TenantScopedModelViewSet):
    queryset = LeadAccount.objects.select_related("tenant", "workspace", "owner").prefetch_related("tags").all()
    serializer_class = LeadAccountSerializer

    @action(detail=True, methods=["post"], url_path="move-stage")
    def move_stage(self, request, pk=None):
        result = LeadWorkflowService.move_stage(
            self.get_tenant_context(),
            pk,
            request.data.get("to_stage", "New"),
            reason=request.data.get("reason", ""),
        )
        return self.service_response(result, LeadAccountSerializer)

    @action(detail=False, methods=["post"], url_path="capture")
    def capture(self, request):
        serializer = LeadCaptureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = LeadWorkflowService.capture_lead(
            self.get_tenant_context(),
            data["company_name"],
            source=data.get("source", ""),
            priority=data.get("priority", "Normal"),
            owner_id=data.get("owner"),
            estimated_value=data.get("estimated_value", 0),
            currency=data.get("currency", "INR"),
            contact_name=data.get("contact_name", ""),
            contact_email=data.get("contact_email", ""),
            contact_phone=data.get("contact_phone", ""),
            metadata=data.get("metadata", {}),
        )
        return self.service_response(result, LeadAccountSerializer)

    @action(detail=True, methods=["post"], url_path="add-note")
    def add_note(self, request, pk=None):
        serializer = LeadNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = LeadWorkflowService.add_note(self.get_tenant_context(), pk, data["body"], title=data.get("title", ""), author_id=data.get("author"), metadata=data.get("metadata", {}))
        return self.service_response(result, LeadNoteSerializer)

    @action(detail=True, methods=["post"], url_path="add-test")
    def add_test(self, request, pk=None):
        serializer = LeadTestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = LeadWorkflowService.add_test(self.get_tenant_context(), pk, data["title"], status=data.get("status", "Pending"), score=data.get("score", 0), due_at=data.get("due_at"), metadata=data.get("metadata", {}))
        return self.service_response(result, LeadTestSerializer)

    @action(detail=True, methods=["post"], url_path="send-to-bbd")
    def send_to_bbd(self, request, pk=None):
        serializer = WorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = LeadWorkflowService.send_to_bbd(self.get_tenant_context(), pk, notes=serializer.validated_data.get("notes", {}))
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=True, methods=["post"], url_path="send-audit")
    def send_audit(self, request, pk=None):
        serializer = WorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = LeadWorkflowService.send_audit(self.get_tenant_context(), pk, notes=serializer.validated_data.get("notes", {}))
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=True, methods=["post"], url_path="offer-template")
    def offer_template(self, request, pk=None):
        result = LeadWorkflowService.create_offer_template(self.get_tenant_context(), pk, amount=request.data.get("amount"), notes=request.data.get("notes") or {})
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=False, methods=["post"], url_path="check-workflow-status")
    def check_workflow_status(self, request):
        result = LeadWorkflowService.check_workflow_status(self.get_tenant_context())
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=False, methods=["post"], url_path="allocate-jrba")
    def allocate_jrba(self, request):
        result = LeadWorkflowService.allocate_jrba_leads(self.get_tenant_context(), owner_ids=request.data.get("owners") or [], source=request.data.get("source", "JRBA"))
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class LeadContactViewSet(TenantScopedModelViewSet):
    queryset = LeadContact.objects.select_related("tenant", "workspace", "lead").all()
    serializer_class = LeadContactSerializer


class LeadActivityViewSet(TenantScopedModelViewSet):
    queryset = LeadActivity.objects.select_related("tenant", "workspace", "lead", "actor").all()
    serializer_class = LeadActivitySerializer


class LeadNoteViewSet(TenantScopedModelViewSet):
    queryset = LeadNote.objects.select_related("tenant", "workspace", "lead", "author").all()
    serializer_class = LeadNoteSerializer


class LeadTestViewSet(TenantScopedModelViewSet):
    queryset = LeadTest.objects.select_related("tenant", "workspace", "lead").all()
    serializer_class = LeadTestSerializer


class ProposalArtifactViewSet(TenantScopedModelViewSet):
    queryset = ProposalArtifact.objects.select_related("tenant", "workspace", "lead").all()
    serializer_class = ProposalArtifactSerializer


class AuditArtifactViewSet(TenantScopedModelViewSet):
    queryset = AuditArtifact.objects.select_related("tenant", "workspace", "lead").all()
    serializer_class = AuditArtifactSerializer


class WorkflowTransitionViewSet(TenantScopedModelViewSet):
    queryset = WorkflowTransition.objects.select_related("tenant", "workspace", "lead", "changed_by").all()
    serializer_class = WorkflowTransitionSerializer


class WorkflowStatusHistoryViewSet(TenantScopedModelViewSet):
    queryset = WorkflowStatusHistory.objects.select_related("tenant", "workspace", "lead").all()
    serializer_class = WorkflowStatusHistorySerializer
