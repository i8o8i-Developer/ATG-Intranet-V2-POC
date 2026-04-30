from django.contrib.auth import get_user_model
from django.test import TestCase

from Backend.Apps.Banao.models import LeadAccount
from Backend.Apps.Lms.models import LeadQueueSnapshot
from Backend.Apps.Lms.services import LeadManagementService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class LmsModuleTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="LMS Tenant", slug="lms-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="lms-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Revenue", code="LMS")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="LMS", code="LMS")
        self.user = get_user_model().objects.create_user(username="lms-user", email="lms@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="LMS-1", display_name="LMS User")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)

    def test_lms_lead_dashboard_and_snapshot(self):
        created = LeadManagementService.create_lead(self.context, {"company_name": "ATG Client", "owner": self.employee.id, "contact_email": "lead@example.com"})
        self.assertTrue(created.ok)
        lead = LeadAccount.objects.get(tenant=self.tenant)
        LeadManagementService.add_note(self.context, lead.id, "Called", author_id=self.employee.id)
        dashboard = LeadManagementService.lead_dashboard(self.context, lead.id)
        self.assertEqual(dashboard.data["notes_count"], 1)
        ba = LeadManagementService.ba_dashboard(self.context, self.employee.id)
        self.assertEqual(ba.data["lead_count"], 1)
        snapshot = LeadManagementService.create_queue_snapshot(self.context, self.employee.id)
        self.assertTrue(snapshot.ok)
        self.assertTrue(LeadQueueSnapshot.objects.filter(tenant=self.tenant, employee=self.employee).exists())