from django.utils import timezone

from django.utils.crypto import get_random_string

from Backend.Apps.MainApp.models import CredentialShareGrant, CredentialVaultItem, LeaveRequest, NotificationItem, NotificationSnoozeRecord, OnboardingOffer
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
            return ServiceResult.failure({"notification": "Notification not found."}, status_code=404)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.updated_by = context.actor
        notification.save(update_fields=["is_read", "read_at", "updated_by", "updated_at"])
        return ServiceResult.success(notification)

    @staticmethod
    def snooze(context, notification_id, snoozed_until, reason=""):
        notification = NotificationItem.objects.filter(tenant=context.tenant, id=notification_id).first()
        if not notification:
            return ServiceResult.failure({"notification": "Notification not found."}, status_code=404)
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
    def approve(context, leave_request_id):
        leave_request = LeaveRequest.objects.filter(tenant=context.tenant, id=leave_request_id).first()
        if not leave_request:
            return ServiceResult.failure({"leaveRequest": "Leave request not found."}, status_code=404)
        leave_request.status = "Approved"
        leave_request.approved_by = context.actor
        leave_request.approved_at = timezone.now()
        leave_request.approval_payload = {**leave_request.approval_payload, "approvedAt": timezone.now().isoformat()}
        leave_request.updated_by = context.actor
        leave_request.save(update_fields=["status", "approved_by", "approved_at", "approval_payload", "updated_by", "updated_at"])
        OutboxService.publish(context, "LeaveRequest", leave_request.id, "LeaveRequestApproved", {"leaveRequestId": leave_request.id})
        return ServiceResult.success(leave_request)

    @staticmethod
    def reject(context, leave_request_id, reason=""):
        leave_request = LeaveRequest.objects.filter(tenant=context.tenant, id=leave_request_id).first()
        if not leave_request:
            return ServiceResult.failure({"leaveRequest": "Leave request not found."}, status_code=404)
        leave_request.status = "Rejected"
        leave_request.rejected_at = timezone.now()
        leave_request.approval_payload = {**leave_request.approval_payload, "rejectedAt": timezone.now().isoformat(), "reason": reason}
        leave_request.updated_by = context.actor
        leave_request.save(update_fields=["status", "rejected_at", "approval_payload", "updated_by", "updated_at"])
        OutboxService.publish(context, "LeaveRequest", leave_request.id, "LeaveRequestRejected", {"leaveRequestId": leave_request.id})
        return ServiceResult.success(leave_request)


class OfferLifecycleService:
    @staticmethod
    def issue_offer(context, offer_id, expires_at=None):
        offer = OnboardingOffer.objects.filter(tenant=context.tenant, id=offer_id).first()
        if not offer:
            return ServiceResult.failure({"offer": "Onboarding offer not found."}, status_code=404)
        offer.status = "Issued"
        offer.issued_at = timezone.now()
        offer.expires_at = expires_at or offer.expires_at
        offer.token = offer.token or get_random_string(48)
        offer.updated_by = context.actor
        offer.save(update_fields=["status", "issued_at", "expires_at", "token", "updated_by", "updated_at"])
        OutboxService.publish(context, "OnboardingOffer", offer.id, "OfferIssued", {"candidateEmail": offer.candidate_email})
        return ServiceResult.success(offer)

    @staticmethod
    def accept_offer(context, token, payload=None):
        offer = OnboardingOffer.objects.filter(tenant=context.tenant, token=token).first()
        if not offer:
            return ServiceResult.failure({"offer": "Offer token not found."}, status_code=404)
        offer.status = "Accepted"
        offer.accepted_at = timezone.now()
        offer.offer_payload = {**offer.offer_payload, "acceptance": payload or {}}
        offer.updated_by = context.actor
        offer.save(update_fields=["status", "accepted_at", "offer_payload", "updated_by", "updated_at"])
        OutboxService.publish(context, "OnboardingOffer", offer.id, "OfferAccepted", {"candidateEmail": offer.candidate_email})
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
            return ServiceResult.failure({"credential": "Credential not found."}, status_code=404)
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
            return ServiceResult.failure({"grant": "Credential share grant not found."}, status_code=404)
        grant.revoked_at = timezone.now()
        grant.updated_by = context.actor
        grant.save(update_fields=["revoked_at", "updated_by", "updated_at"])
        return ServiceResult.success(grant)

    @staticmethod
    def rotate(context, credential_id, secret_reference=""):
        credential = CredentialVaultItem.objects.filter(tenant=context.tenant, id=credential_id).first()
        if not credential:
            return ServiceResult.failure({"credential": "Credential not found."}, status_code=404)
        if secret_reference:
            credential.secret_reference = secret_reference
        credential.last_rotated_at = timezone.now()
        credential.updated_by = context.actor
        credential.save(update_fields=["secret_reference", "last_rotated_at", "updated_by", "updated_at"])
        OutboxService.publish(context, "CredentialVaultItem", credential.id, "CredentialRotated", {"system": credential.system_name})
        return ServiceResult.success(credential)
