from django.contrib.auth import get_user_model
from django.test import TestCase

from Backend.Apps.Banao.models import LeadNote, LeadTest, WorkflowStatusHistory
from Backend.Apps.Banao.services import LeadWorkflowService
from Backend.Apps.Users.models import EmployeeProfile
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
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)

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
