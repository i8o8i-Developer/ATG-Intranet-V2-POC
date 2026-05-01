from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from Backend.Apps.MainApp.models import CredentialShareGrant, CredentialVaultItem, ExternalIssueReference, LeaveRequest, ManagerScope, NotificationSnoozeRecord, OnboardingOffer
from Backend.Apps.MainApp.services import CredentialVaultService, LeaveApprovalService, NotificationService, OfferLifecycleService
from Backend.Apps.Users.models import Department, EmployeeProfile
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
        self.department = Department.objects.create(tenant=self.tenant, workspace=self.workspace, name="Engineering", code="ENG")
        self.employee.department = self.department
        self.employee.joined_on = timezone.localdate()
        self.employee.save(update_fields=["department", "joined_on"])
        self.reportee_user = get_user_model().objects.create_user(username="main-reportee", email="main-reportee@example.com")
        self.reportee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.reportee_user, employee_code="MAIN-2", display_name="Main Reportee", manager=self.employee, department=self.department)
        self.client = APIClient()
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

    def test_mainapp_legacy_route_surface(self):
        ManagerScope.objects.create(tenant=self.tenant, workspace=self.workspace, manager=self.employee, employee=self.reportee, scope_type="Employee", created_by=self.user, updated_by=self.user)
        self.client.force_authenticate(self.user)

        leave = self.client.post(
            "/MainApp/leave/apply/",
            {"leave_type": "Paid", "starts_on": timezone.localdate().isoformat(), "ends_on": timezone.localdate().isoformat()},
            format="json",
        )
        self.assertEqual(leave.status_code, 201)
        leave_id = leave.data["id"]

        leave_list = self.client.get("/MainApp/leave/")
        self.assertEqual(leave_list.status_code, 200)
        self.assertEqual(leave_list.data["count"], 1)

        hierarchy = self.client.get("/MainApp/Hierarchy/")
        self.assertEqual(hierarchy.status_code, 200)

        reportees = self.client.get("/MainApp/Onboard/Track_my_reportee")
        self.assertEqual(reportees.status_code, 200)
        self.assertEqual(len(reportees.data["results"]), 1)

        manager_track = self.client.get("/MainApp/Onboard/manager_track")
        self.assertEqual(manager_track.status_code, 200)

        offer = self.client.post(
            "/MainApp/Onboard/send-actual-offer",
            {"candidate_name": "Alex", "candidate_email": "alex@example.com"},
            format="json",
        )
        self.assertEqual(offer.status_code, 200)
        token = offer.data["token"]

        offer_view = self.client.get(f"/MainApp/offer/{token}")
        self.assertEqual(offer_view.status_code, 200)

        offer_accept = self.client.post(f"/MainApp/offer/{token}", {"ip": "127.0.0.1"}, format="json")
        self.assertEqual(offer_accept.status_code, 200)

        offer_download = self.client.get(f"/MainApp/download-offer/{token}")
        self.assertEqual(offer_download.status_code, 200)

        issue = self.client.post(
            "/MainApp/Onboard/Bug_Issue",
            {"title": "Broken flow"},
            format="json",
        )
        self.assertEqual(issue.status_code, 201)
        issue_id = issue.data["id"]

        updated_reportee = self.client.post(
            f"/MainApp/update_reportee/{issue_id}/",
            {"employee_id": self.reportee.id},
            format="json",
        )
        self.assertEqual(updated_reportee.status_code, 200)

        credential = self.client.post(
            "/MainApp/create-credentials/",
            {"owner": self.user.id, "name": "API", "system_name": "GitHub", "secret_reference": "secret"},
            format="json",
        )
        self.assertEqual(credential.status_code, 201)
        credential_id = credential.data["id"]

        grant = self.client.post(
            "/MainApp/share-credentials/",
            {"credential_id": credential_id, "grantee": self.grantee.id},
            format="json",
        )
        self.assertEqual(grant.status_code, 201)

        remove_share = self.client.post(
            "/MainApp/api/credentials/remove-share/",
            {"grant_id": grant.data["id"]},
            format="json",
        )
        self.assertEqual(remove_share.status_code, 200)

        password_reset = self.client.post(
            "/MainApp/api/test-password-reset/",
            {"email": self.user.email},
            format="json",
        )
        self.assertEqual(password_reset.status_code, 200)

        search_user = self.client.get("/MainApp/api/search-user/?q=main")
        self.assertEqual(search_user.status_code, 200)

        deactivate = self.client.post(
            "/MainApp/deactivate-employee/",
            {"employee_id": self.reportee.id},
            format="json",
        )
        self.assertEqual(deactivate.status_code, 200)

        payroll = self.client.get("/MainApp/Payroll/")
        self.assertEqual(payroll.status_code, 200)

        docs = self.client.get("/MainApp/docs-view-all/")
        self.assertEqual(docs.status_code, 200)

        search = self.client.get("/MainApp/search/?q=Alex")
        self.assertEqual(search.status_code, 200)

        api_testing = self.client.get("/MainApp/api-testing")
        self.assertEqual(api_testing.status_code, 200)