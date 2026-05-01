from django.core import mail
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from Backend.Apps.Banao.models import LeadAccount, LeadNote, LeadTest, WorkflowStatusHistory
from Backend.Apps.Banao.services import LeadWorkflowService
from Backend.Apps.MainApp.models import OnboardingOffer
from Backend.Apps.Users.models import Department, Domain, EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class BanaoWorkflowTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant", slug="tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Banao", code="BANAO")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Main", code="BANAO")
        self.user = get_user_model().objects.create_user(username="banao-user", email="banao@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="EMP-1", display_name="Banao User")
        self.domain = Domain.objects.create(tenant=self.tenant, workspace=self.workspace, name="Banao", code="BANAO")
        self.department = Department.objects.create(tenant=self.tenant, workspace=self.workspace, name="Sales", code="SALES", category="Business Development Associate (Band 1)", domain=self.domain)
        self.employee.department = self.department
        self.employee.save(update_fields=["department"])
        self.recruiter_user = get_user_model().objects.create_user(username="team-lead", email="teamlead@example.com")
        self.recruiter = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.recruiter_user, employee_code="EMP-2", display_name="Team Lead", department=self.department)
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.client = APIClient()

    def test_capture_note_test_and_workflow_actions(self):
        created = LeadWorkflowService.capture_lead(self.context, "Acme", source="JRBA", contact_email="buyer@example.com")
        self.assertTrue(created.ok)
        lead = created.data

        note = LeadWorkflowService.add_note(self.context, lead.id, "Call completed", author_id=self.employee.id)
        self.assertTrue(note.ok)
        self.assertTrue(LeadNote.objects.filter(lead=lead).exists())

        test = LeadWorkflowService.add_test(self.context, lead.id, "Pilot")
        self.assertTrue(test.ok)
        self.assertTrue(LeadTest.objects.filter(lead=lead).exists())

        bbd = LeadWorkflowService.send_to_bbd(self.context, lead.id)
        self.assertTrue(bbd.ok)
        audit = LeadWorkflowService.send_audit(self.context, lead.id)
        self.assertTrue(audit.ok)
        offer = LeadWorkflowService.create_offer_template(self.context, lead.id)
        self.assertTrue(offer.ok)

        status = LeadWorkflowService.check_workflow_status(self.context)
        self.assertTrue(status.ok)
        self.assertTrue(WorkflowStatusHistory.objects.filter(lead=lead).exists())

        allocation = LeadWorkflowService.allocate_jrba_leads(self.context, owner_ids=[self.employee.id])
        self.assertTrue(allocation.ok)

    def test_lead_create_requires_linkedin_for_personal_email(self):
        response = self.client.post(
            "/Banao/lead-create/",
            {"full_name": "Prospect User", "email": "prospect@gmail.com", "phone": "9876543210", "message": "Need a proposal"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.data["linkedin_required"])

    def test_new_lead_create_dedupes_by_url_and_skips_client_website_notifications(self):
        response = self.client.post(
            "/Banao/new-lead-create/",
            {
                "full_name": "Acme Contact",
                "email": "sales@acme.com",
                "phone": "+1 202 555 0101",
                "message": "We need a CRM build.",
                "origin": "cw",
                "industry": "SaaS",
                "url": "https://acme.com/contact",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        lead = LeadAccount.objects.get()
        self.assertEqual(lead.stage, "ContactAttempted")
        self.assertEqual(lead.website_url, "https://acme.com/contact")
        self.assertFalse(response.data["notification_sent"])
        self.assertEqual(len(mail.outbox), 0)

        duplicate_response = self.client.post(
            "/Banao/new-lead-create/",
            {
                "full_name": "Another Contact",
                "email": "another@acme.com",
                "phone": "+1 202 555 0199",
                "message": "Following up.",
                "origin": "cw",
                "url": "https://acme.com/pricing",
            },
            format="json",
        )
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(LeadAccount.objects.count(), 1)

    def test_update_lead_on_connection_sent_updates_comment_and_stage(self):
        created = LeadWorkflowService.capture_lead(
            self.context,
            "Acme",
            source="w",
            contact_name="Acme Contact",
            contact_email="buyer@acme.com",
            website_url="https://acme.com/about",
        )
        self.assertTrue(created.ok)
        response = self.client.post(
            "/Banao/update-lead-on-connection-sent/",
            {"domain": "acme.com", "intern_name": "Sam", "client_name": "Acme"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        lead = LeadAccount.objects.get(id=created.data.id)
        self.assertEqual(lead.stage, "ContactAttempted")
        self.assertIn("Connection sent to Acme by Sam", lead.latest_comment)
        self.assertTrue(LeadNote.objects.filter(lead=lead, title="Connection sent").exists())

    def test_department_and_user_list_legacy_endpoints(self):
        self.client.force_authenticate(self.user)
        departments = self.client.get("/Banao/department-list/")
        self.assertEqual(departments.status_code, 200)
        self.assertEqual(departments.data[0]["name"], "Sales")

        users = self.client.get("/Banao/user-list/", {"data": self.department.id})
        self.assertEqual(users.status_code, 200)
        self.assertEqual({item["name"] for item in users.data}, {"banao-user", "team-lead"})

    def test_sendoffer_preview_issue_and_offer_page(self):
        self.client.force_authenticate(self.user)
        payload = {
            "email": "candidate@example.com",
            "username": "candidate-user",
            "name": "Candidate User",
            "position_name": "Business Development Associate (Band 1)",
            "department_name": "Sales",
            "pay_type": "Fixed",
            "base_pay": "0",
            "pay_per_task": "0",
            "offer_type": "Intern",
            "title": "Business Development Intern",
            "whatsapp": "+91-9999999999",
            "slack": "candidate.slack",
        }

        preview = self.client.post("/Banao/sendoffer/", {**payload, "preview": "Preview"}, format="json")
        self.assertEqual(preview.status_code, 200)
        self.assertIn("Offer for Candidate User", preview.content.decode())
        self.assertEqual(OnboardingOffer.objects.count(), 0)

        issued = self.client.post("/Banao/sendoffer/", payload, format="json")
        self.assertEqual(issued.status_code, 201)
        offer = OnboardingOffer.objects.get(candidate_email="candidate@example.com")
        self.assertEqual(offer.status, "Issued")
        self.assertTrue(offer.token)
        self.assertEqual(len(mail.outbox), 1)

        preview_page = self.client.get(f"/Banao/offer/{offer.token}")
        self.assertEqual(preview_page.status_code, 200)
        self.assertIn("Candidate User", preview_page.content.decode())
        self.assertIn("1500", preview_page.content.decode())
