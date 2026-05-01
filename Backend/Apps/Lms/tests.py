from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from Backend.Apps.Banao.models import LeadAccount, LeadTag
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
        self.client = APIClient()

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

    def test_lms_legacy_route_surface(self):
        self.client.force_authenticate(self.user)

        tag_response = self.client.post("/Lms/api/tags/", {"name": "Hot", "color": "red"}, format="json")
        self.assertEqual(tag_response.status_code, 201)
        self.assertTrue(LeadTag.objects.filter(tenant=self.tenant, name="Hot").exists())

        created = self.client.post(
            "/Lms/api/add_lead/",
            {"company_name": "ATG Client", "owner": self.employee.id, "source": "LMS", "estimated_value": "1000.00"},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        lead = LeadAccount.objects.get(tenant=self.tenant)
        tag = LeadTag.objects.get(tenant=self.tenant, name="Hot")
        lead.tags.add(tag)
        LeadManagementService.add_note(self.context, lead.id, "Called", author_id=self.employee.id)

        index = self.client.get("/Lms/lms/")
        self.assertEqual(index.status_code, 200)
        self.assertIn("bas", index.data)

        leads = self.client.get("/Lms/api/leads/?search=ATG&tags=%d" % tag.id)
        self.assertEqual(leads.status_code, 200)
        self.assertEqual(leads.data["count"], 1)

        note_today = self.client.get(f"/Lms/api/leads/{lead.id}/note-updated-today/")
        self.assertEqual(note_today.status_code, 200)
        self.assertTrue(note_today.data["updated_today"])

        detail = self.client.get(f"/Lms/lms/lead/{lead.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["lead_id"], lead.id)

        edit = self.client.get(f"/Lms/lms/lead/{lead.id}/edit/")
        self.assertEqual(edit.status_code, 200)

        jrba = self.client.get(f"/Lms/lms/jrba/{self.employee.id}/")
        self.assertEqual(jrba.status_code, 200)

        dashboard = self.client.get("/Lms/lms/dashboard/")
        self.assertEqual(dashboard.status_code, 200)

        add_lead = self.client.get("/Lms/lms/add_lead")
        self.assertEqual(add_lead.status_code, 200)
        self.assertGreaterEqual(len(add_lead.data["tags"]), 1)

        analytics = self.client.get("/Lms/lms/analytics_dashboard/")
        self.assertEqual(analytics.status_code, 200)
        self.assertIn("closures", analytics.data)

        eod = self.client.get("/Lms/lms/eod-performance/")
        self.assertEqual(eod.status_code, 200)
        self.assertIn("rows", eod.data)