from Backend.Apps.MainApp.models import CredentialShareGrant, CredentialVaultItem, ExternalIssueReference, LeaveRequest, ManagerScope, NotificationItem, NotificationSnoozeRecord, OnboardingOffer
from Backend.Apps.MainApp.serializers import (
    CredentialShareGrantSerializer,
    CredentialVaultItemSerializer,
    ExternalIssueReferenceSerializer,
    LeaveRequestSerializer,
    ManagerScopeSerializer,
    NotificationItemSerializer,
    NotificationSnoozeRecordSerializer,
    OnboardingOfferSerializer,
)
from Backend.Apps.MainApp.services import CredentialVaultService, LeaveApprovalService, MainAppLegacyService, NotificationService, OfferLifecycleService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult, TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


class OnboardingOfferViewSet(TenantScopedModelViewSet):
    queryset = OnboardingOffer.objects.select_related("tenant", "workspace").all()
    serializer_class = OnboardingOfferSerializer

    @action(detail=True, methods=["post"], url_path="issue")
    def issue(self, request, pk=None):
        result = OfferLifecycleService.issue_offer(self.get_tenant_context(), pk, expires_at=request.data.get("expires_at"))
        return self.service_response(result, OnboardingOfferSerializer)

    @action(detail=False, methods=["post"], url_path="accept")
    def accept(self, request):
        result = OfferLifecycleService.accept_offer(self.get_tenant_context(), request.data.get("token", ""), payload=request.data.get("payload") or {})
        return self.service_response(result, OnboardingOfferSerializer)

    @action(detail=False, methods=["post"], url_path="queue-reminders")
    def queue_reminders(self, request):
        result = OfferLifecycleService.queue_offer_reminders(self.get_tenant_context())
        return self.service_response(result)


class LeaveRequestViewSet(TenantScopedModelViewSet):
    queryset = LeaveRequest.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = LeaveRequestSerializer

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        result = LeaveApprovalService.approve(self.get_tenant_context(), pk)
        return self.service_response(result, LeaveRequestSerializer)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        result = LeaveApprovalService.reject(self.get_tenant_context(), pk, reason=request.data.get("reason", ""))
        return self.service_response(result, LeaveRequestSerializer)


class NotificationItemViewSet(TenantScopedModelViewSet):
    queryset = NotificationItem.objects.select_related("tenant", "workspace", "recipient").all()
    serializer_class = NotificationItemSerializer

    @action(detail=False, methods=["post"], url_path="send")
    def send(self, request):
        user_model = get_user_model()
        recipient = user_model.objects.filter(id=request.data.get("recipient")).first()
        if not recipient:
            return Response({"recipient": "Recipient user not found."}, status=404)
        result = NotificationService.notify(
            self.get_tenant_context(),
            recipient,
            request.data.get("title", "Notification"),
            message=request.data.get("message", ""),
            category=request.data.get("category", ""),
            resource_type=request.data.get("resource_type", ""),
            resource_id=request.data.get("resource_id", ""),
            metadata=request.data.get("metadata") or {},
        )
        return self.service_response(result, NotificationItemSerializer)

    @action(detail=True, methods=["post"], url_path="read")
    def read(self, request, pk=None):
        result = NotificationService.mark_read(self.get_tenant_context(), pk)
        return self.service_response(result, NotificationItemSerializer)

    @action(detail=True, methods=["post"], url_path="snooze")
    def snooze(self, request, pk=None):
        result = NotificationService.snooze(self.get_tenant_context(), pk, request.data.get("snoozed_until"), request.data.get("reason", ""))
        return self.service_response(result, NotificationItemSerializer)


class CredentialVaultItemViewSet(TenantScopedModelViewSet):
    queryset = CredentialVaultItem.objects.select_related("tenant", "workspace", "owner").all()
    serializer_class = CredentialVaultItemSerializer

    @action(detail=True, methods=["post"], url_path="rotate")
    def rotate(self, request, pk=None):
        result = CredentialVaultService.rotate(self.get_tenant_context(), pk, secret_reference=request.data.get("secret_reference", ""))
        return self.service_response(result, CredentialVaultItemSerializer)

    @action(detail=True, methods=["post"], url_path="share")
    def share(self, request, pk=None):
        user_model = get_user_model()
        grantee = user_model.objects.filter(id=request.data.get("grantee")).first()
        if not grantee:
            return Response({"grantee": "Grantee user not found."}, status=404)
        result = CredentialVaultService.share(self.get_tenant_context(), pk, grantee, permission=request.data.get("permission", "Read"), expires_at=request.data.get("expires_at"), reason=request.data.get("reason", ""))
        return self.service_response(result, CredentialShareGrantSerializer)


class CredentialShareGrantViewSet(TenantScopedModelViewSet):
    queryset = CredentialShareGrant.objects.select_related("tenant", "workspace", "credential", "grantee").all()
    serializer_class = CredentialShareGrantSerializer

    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke(self, request, pk=None):
        result = CredentialVaultService.revoke_share(self.get_tenant_context(), pk)
        return self.service_response(result, CredentialShareGrantSerializer)


class ExternalIssueReferenceViewSet(TenantScopedModelViewSet):
    queryset = ExternalIssueReference.objects.select_related("tenant", "workspace", "assigned_to").all()
    serializer_class = ExternalIssueReferenceSerializer


class NotificationSnoozeRecordViewSet(TenantScopedModelViewSet):
    queryset = NotificationSnoozeRecord.objects.select_related("tenant", "workspace", "notification", "snoozed_by").all()
    serializer_class = NotificationSnoozeRecordSerializer


class ManagerScopeViewSet(TenantScopedModelViewSet):
    queryset = ManagerScope.objects.select_related("tenant", "workspace", "manager", "employee", "department").all()
    serializer_class = ManagerScopeSerializer


class MainAppLegacyMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return ServiceResult.success(TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="MainAppLegacyAPI"))
        tenant_hint = request.headers.get("X-Tenant-Id") or request.query_params.get("tenant") or request.data.get("tenant")
        workspace_hint = request.headers.get("X-Workspace-Id") or request.query_params.get("workspace") or request.data.get("workspace")
        tenant = Tenant.objects.filter(id=tenant_hint).first() if str(tenant_hint or "").isdigit() else Tenant.objects.filter(slug__iexact=str(tenant_hint or "")).first()
        workspace = Workspace.objects.filter(id=workspace_hint).first() if str(workspace_hint or "").isdigit() else Workspace.objects.filter(code__iexact=str(workspace_hint or "")).first()
        if not tenant:
            active_tenants = list(Tenant.objects.filter(status=Tenant.STATUS_ACTIVE).order_by("id")[:2])
            tenant = active_tenants[0] if len(active_tenants) == 1 else None
        if tenant and workspace and workspace.tenant_id != tenant.id:
            workspace = None
        if tenant and not workspace:
            workspace = Workspace.objects.filter(tenant=tenant).order_by("id").first()
        if not tenant:
            return ServiceResult.failure({"tenant": "Tenant context is required for MainApp request."}, status_code=400)
        return ServiceResult.success(TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="MainAppLegacyAPI"))

    def with_context(self, request):
        result = self.get_context(request)
        if not result.ok:
            return None, Response(result.errors, status=result.status_code)
        return result.data, None

    def to_response(self, result, serializer_class=None, many=False):
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        if serializer_class:
            return Response(serializer_class(result.data, many=many).data, status=result.status_code)
        return Response(result.data, status=result.status_code)

    @staticmethod
    def parse_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "y"}

    @staticmethod
    def parse_date_value(value):
        if not value:
            return None
        if hasattr(value, "year") and not hasattr(value, "hour"):
            return value
        return parse_date(str(value))

    @staticmethod
    def parse_datetime_value(value):
        if not value:
            return None
        if hasattr(value, "hour"):
            return value
        return parse_datetime(str(value))


class MainAppLegacyActionAPIView(MainAppLegacyMixin, APIView):
    action_name = ""
    response_serializer = None

    def get(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def handle(self, request, *args, **kwargs):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response

        action = self.action_name
        if action == "leave_list":
            result = MainAppLegacyService.list_leaves(context, employee_id=request.query_params.get("employee_id"))
        elif action == "apply_leave":
            actor_employee = MainAppLegacyService.actor_employee(context)
            result = MainAppLegacyService.create_leave(
                context,
                request.data.get("employee_id") or (actor_employee.id if actor_employee else None),
                request.data.get("leave_type", "Paid"),
                self.parse_date_value(request.data.get("starts_on")),
                self.parse_date_value(request.data.get("ends_on")),
                reason=request.data.get("reason", ""),
            )
        elif action == "issue_leave":
            result = MainAppLegacyService.create_leave(
                context,
                request.data.get("employee_id"),
                request.data.get("leave_type", "Paid"),
                self.parse_date_value(request.data.get("starts_on")),
                self.parse_date_value(request.data.get("ends_on")),
                reason=request.data.get("reason", ""),
                status=request.data.get("status", "Approved"),
            )
        elif action == "leave_detail":
            leave = LeaveRequest.objects.filter(tenant=context.tenant, id=kwargs["pk"]).first()
            result = ServiceResult.success(leave) if leave else ServiceResult.failure({"leave": "Leave request not found."}, status_code=404)
        elif action == "leave_calendar":
            result = MainAppLegacyService.leave_calendar(context, employee_id=request.query_params.get("employee_id"), department_id=request.query_params.get("department_id"))
        elif action == "employees_by_department":
            result = MainAppLegacyService.employees_by_department(context, department_id=request.query_params.get("department") or request.data.get("department"))
        elif action == "employee_leaves":
            result = MainAppLegacyService.list_leaves(context, employee_id=request.query_params.get("employee_id") or request.data.get("employee_id"))
        elif action == "add_employee_leave":
            result = MainAppLegacyService.create_leave(
                context,
                request.data.get("employee_id"),
                request.data.get("leave_type", "Paid"),
                self.parse_date_value(request.data.get("starts_on")),
                self.parse_date_value(request.data.get("ends_on")),
                reason=request.data.get("reason", ""),
                status=request.data.get("status", "Approved"),
            )
        elif action == "hierarchy":
            result = MainAppLegacyService.hierarchy(context)
        elif action == "payroll":
            result = MainAppLegacyService.payroll_summary(context)
        elif action == "documentation":
            result = MainAppLegacyService.documentation_summary(context)
        elif action == "createmantis":
            result = MainAppLegacyService.create_issue(context, request.data.get("title", "Mantis issue"), provider="Mantis", issue_type=request.data.get("issue_type", "Bug"), priority=request.data.get("priority", ""), assigned_to_id=request.data.get("assigned_to"), metadata=request.data.get("metadata") or {})
        elif action == "track":
            result = MainAppLegacyService.track(context)
        elif action == "track_reportee":
            result = MainAppLegacyService.reportee_track(context)
        elif action == "manager_track":
            result = MainAppLegacyService.manager_track(context)
        elif action == "delete_onboard":
            offer = OnboardingOffer.objects.filter(tenant=context.tenant, id=request.data.get("offer_id")).first()
            if not offer:
                result = ServiceResult.failure({"offer": "Onboarding Offer Not Found."}, status_code=404)
            else:
                offer.delete()
                result = ServiceResult.success({"offer_id": request.data.get("offer_id"), "deleted": True})
        elif action == "bug_issue":
            result = MainAppLegacyService.create_issue(context, request.data.get("title", "Bug issue"), provider=request.data.get("provider", "Internal"), issue_type=request.data.get("issue_type", "Bug"), priority=request.data.get("priority", ""), assigned_to_id=request.data.get("assigned_to"), metadata=request.data.get("metadata") or {})
        elif action == "send_offer":
            result = MainAppLegacyService.create_offer(context, request.data, issue=False)
        elif action == "send_actual_offer":
            result = MainAppLegacyService.create_offer(context, request.data, issue=True)
        elif action == "checkname":
            result = MainAppLegacyService.check_name(context, email=request.data.get("email") or request.query_params.get("email", ""), username=request.data.get("username") or request.query_params.get("username", ""))
        elif action == "dep_valid":
            result = MainAppLegacyService.department_validation(context, department_id=request.data.get("department_id") or request.query_params.get("department_id"))
        elif action == "remind_work":
            result = MainAppLegacyService.remind_work(context, issue_id=request.data.get("name") or request.data.get("issue_id") or request.query_params.get("name") or request.query_params.get("issue_id"), summary=request.data.get("summary") or request.query_params.get("summary", ""))
        elif action == "execute":
            result = MainAppLegacyService.execute_issue_sync(context, issues=request.data.get("issues") or [], provider=request.data.get("provider", "Mantis"), page=request.data.get("page", 0), page_size=request.data.get("page_size", 0))
        elif action == "send_pdf_offer":
            result = MainAppLegacyService.send_pdf_offer(context, request.data.get("offer_id"))
        elif action == "send_certificate":
            result = MainAppLegacyService.send_certificate(context, request.data.get("recipient") or request.data.get("user_id"), title=request.data.get("title", "Certificate issued"))
            if result.ok:
                result = ServiceResult.success({"notification_id": result.data.id, "title": result.data.title, "recipient": result.data.recipient_id}, status_code=result.status_code)
        elif action == "search_username":
            result = MainAppLegacyService.search_username(context, request.data.get("q") or request.query_params.get("q", ""))
        elif action == "get_joining_date":
            result = MainAppLegacyService.get_joining_date(context, employee_id=request.data.get("employee_id") or request.query_params.get("employee_id"))
        elif action == "deactivate_multiple":
            result = MainAppLegacyService.deactivate_multiple_employees(context, request.data.get("employee_ids") or [])
        elif action == "deactivate":
            result = MainAppLegacyService.deactivate_employee(context, request.data.get("employee_id"))
            if result.ok:
                result = ServiceResult.success({"employee_id": result.data.id, "status": result.data.status, "exited_on": result.data.exited_on.isoformat() if result.data.exited_on else None}, status_code=result.status_code)
        elif action == "dep_pos_val":
            result = MainAppLegacyService.department_validation(context, department_id=request.data.get("department_id") or request.query_params.get("department_id"))
        elif action == "api_testing":
            result = MainAppLegacyService.api_testing(context, branch_name=request.data.get("branchName") or request.data.get("branch_name") or request.query_params.get("branchName") or request.query_params.get("branch_name", "master"), live=self.parse_bool(request.data.get("live") or request.query_params.get("live"), False))
        elif action == "docs_view_all":
            result = MainAppLegacyService.all_users_doc_view(context)
        elif action == "search":
            result = MainAppLegacyService.search(context, request.data.get("q") or request.query_params.get("q", ""))
        elif action == "update_reportee":
            result = MainAppLegacyService.update_reportee(context, kwargs["bug_id"], request.data.get("employee_id"))
        elif action == "load_sub_departments":
            result = MainAppLegacyService.department_validation(context, department_id=request.query_params.get("department_id") or request.data.get("department_id"))
        elif action == "department_choices":
            result = ServiceResult.success({"results": [{"id": department.id, "name": department.name} for department in EmployeeProfile._meta.get_field("department").related_model.objects.filter(tenant=context.tenant, is_archived=False).order_by("name")]})
        elif action == "pass_management":
            result = MainAppLegacyService.pass_management(context)
        elif action == "create_credentials":
            result = MainAppLegacyService.create_credential(context, request.data.get("owner") or request.user.id, request.data.get("name", "Credential"), request.data.get("system_name", "System"), request.data.get("secret_reference", "secret"), metadata=request.data.get("metadata") or {})
        elif action == "get_credentials":
            result = MainAppLegacyService.get_credentials(context, owner_id=request.query_params.get("owner_id") or request.data.get("owner_id"))
        elif action == "share_credentials":
            result = MainAppLegacyService.share_credential(context, request.data.get("credential_id"), request.data.get("grantee"), permission=request.data.get("permission", "Read"), expires_at=self.parse_datetime_value(request.data.get("expires_at")), reason=request.data.get("reason", ""))
        elif action == "search_user":
            result = MainAppLegacyService.search_user(context, request.data.get("q") or request.query_params.get("q", ""))
        elif action == "remove_share":
            result = MainAppLegacyService.remove_share(context, request.data.get("grant_id"))
        elif action == "test_password_reset":
            result = MainAppLegacyService.test_password_reset(context, user_id=request.data.get("user_id"), email=request.data.get("email", ""))
        elif action == "nda":
            result = ServiceResult.success({"document": "NDA", "status": "available"})
        else:
            result = ServiceResult.failure({"action": "UnSupported MainApp Compatibility Action."}, status_code=400)

        return self.to_response(result, self.response_serializer)


class MainAppOfferTokenLegacyAPIView(APIView):
    permission_classes = []

    def get(self, request, token):
        result = MainAppLegacyService.get_offer_by_token(token)
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        return Response(OnboardingOfferSerializer(result.data).data, status=result.status_code)

    def post(self, request, token):
        result = MainAppLegacyService.get_offer_by_token(token)
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        offer = result.data
        context = TenantContext(tenant=offer.tenant, workspace=offer.workspace, actor=request.user if request.user.is_authenticated else None, source="MainAppOfferToken")
        accepted = OfferLifecycleService.accept_offer(context, token, payload=request.data or {})
        if not accepted.ok:
            return Response(accepted.errors, status=accepted.status_code)
        return Response(OnboardingOfferSerializer(accepted.data).data, status=accepted.status_code)


class MainAppOfferDownloadLegacyAPIView(APIView):
    permission_classes = []

    def get(self, request, token):
        result = MainAppLegacyService.get_offer_by_token(token)
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        offer = result.data
        return Response({"offer_id": offer.id, "filename": f"offer-{offer.id}.pdf", "candidate_name": offer.candidate_name, "candidate_email": offer.candidate_email, "payload": offer.offer_payload}, status=200)
