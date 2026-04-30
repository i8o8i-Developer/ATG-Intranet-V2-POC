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
from Backend.Apps.MainApp.services import CredentialVaultService, LeaveApprovalService, NotificationService, OfferLifecycleService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response


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
