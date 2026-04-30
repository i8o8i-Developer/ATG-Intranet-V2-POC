from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from Backend.Apps.MainApp.models import CredentialShareGrant, CredentialVaultItem, LeaveRequest, NotificationSnoozeRecord, OnboardingOffer
from Backend.Apps.MainApp.services import CredentialVaultService, LeaveApprovalService, NotificationService, OfferLifecycleService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class MainAppModuleTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Main Tenant", slug="main-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="main-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Core", code="MAIN")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Main", code="MAIN")
        self.user = get_user_model().objects.create_user(username="main-user", email="main@example.com")
        self.grantee = get_user_model().objects.create_user(username="main-grantee", email="main-grantee@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="MAIN-1", display_name="Main User")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)

    def test_offer_leave_notification_and_credentials(self):
        offer = OnboardingOffer.objects.create(tenant=self.tenant, workspace=self.workspace, candidate_name="Alex", candidate_email="alex@example.com", expires_at=timezone.now() + timezone.timedelta(days=3))
        issued = OfferLifecycleService.issue_offer(self.context, offer.id)
        self.assertEqual(issued.data.status, "Issued")
        reminders = OfferLifecycleService.queue_offer_reminders(self.context)
        self.assertEqual(reminders.data["count"], 1)
        accepted = OfferLifecycleService.accept_offer(self.context, issued.data.token, {"ip": "127.0.0.1"})
        self.assertEqual(accepted.data.status, "Accepted")

        leave = LeaveRequest.objects.create(tenant=self.tenant, workspace=self.workspace, employee=self.employee, leave_type="Paid", starts_on=timezone.localdate(), ends_on=timezone.localdate())
        approved = LeaveApprovalService.approve(self.context, leave.id)
        self.assertEqual(approved.data.status, "Approved")

        notification = NotificationService.notify(self.context, self.user, "Hello")
        snoozed = NotificationService.snooze(self.context, notification.data.id, timezone.now() + timezone.timedelta(hours=1))
        self.assertEqual(snoozed.data.snooze_records.count(), 1)
        self.assertTrue(NotificationSnoozeRecord.objects.exists())

        credential = CredentialVaultItem.objects.create(tenant=self.tenant, workspace=self.workspace, owner=self.user, name="API", system_name="GitHub", secret_reference="old")
        rotated = CredentialVaultService.rotate(self.context, credential.id, "new")
        self.assertEqual(rotated.data.secret_reference, "new")
        grant = CredentialVaultService.share(self.context, credential.id, self.grantee)
        self.assertTrue(CredentialShareGrant.objects.filter(id=grant.data.id).exists())
        revoked = CredentialVaultService.revoke_share(self.context, grant.data.id)
        self.assertIsNotNone(revoked.data.revoked_at)