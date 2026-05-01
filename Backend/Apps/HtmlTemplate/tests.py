from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from Backend.Apps.HtmlTemplate.models import GenericHtmlTemplate, OfferMacro, TemplateVariable
from Backend.Apps.HtmlTemplate.services import TemplateRenderService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class HtmlTemplateTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="HTML Tenant", slug="html-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="html-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="People", code="HTML")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="HTML", code="HTML")
        self.user = get_user_model().objects.create_user(username="html-user", email="html@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="HTML-1", display_name="HTML User")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.client = APIClient()

    def test_template_render_macro_and_gtm_sync(self):
        created = TemplateRenderService.create_content_template(self.context, name="Offer", body_html="Hello {{candidate_name}}", template_type="Offer", status="Active")
        self.assertTrue(created.ok)
        self.assertTrue(TemplateVariable.objects.filter(tenant=self.tenant, key="candidate_name").exists())
        rendered = TemplateRenderService.render_text_template(created.data, {"candidate_name": "Alex"})
        self.assertEqual(rendered.data["rendered"], "Hello Alex")

        macro = TemplateRenderService.upsert_macro(self.context, "Candidate", "{{candidate_name}}")
        self.assertTrue(macro.ok)
        self.assertTrue(OfferMacro.objects.filter(tenant=self.tenant, macro="{{candidate_name}}").exists())

        synced = TemplateRenderService.sync_gtm_offer_template(self.context, html_content="<p>{{candidate_name}}</p>")
        self.assertTrue(synced.ok)
        self.assertEqual(GenericHtmlTemplate.objects.filter(tenant=self.tenant, position="Business Analyst").count(), 2)

    def test_html_template_legacy_routes(self):
        self.client.force_authenticate(self.user)
        created = self.client.post(
            "/HtmlTemplate/api/content-templates/create-template/",
            {"name": "Offer", "body_html": "Hello {{candidate_name}}", "template_type": "Offer", "status": "Active"},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        template_id = created.data["id"]

        rendered = self.client.post(
            f"/HtmlTemplate/api/content-templates/{template_id}/render/",
            {"variables": {"candidate_name": "Alex"}},
            format="json",
        )
        self.assertEqual(rendered.status_code, 200)
        self.assertEqual(rendered.data["rendered"], "Hello Alex")

        synced = self.client.post(
            "/HtmlTemplate/api/generic-html-templates/sync-gtm-template/",
            {"html_content": "<p>{{candidate_name}}</p>", "domains": ["ATG"]},
            format="json",
        )
        self.assertEqual(synced.status_code, 201)
        generic = GenericHtmlTemplate.objects.get(tenant=self.tenant, offer_domain="ATG")

        generic_render = self.client.post(
            f"/HtmlTemplate/api/generic-html-templates/{generic.id}/render/",
            {"variables": {"candidate_name": "Alex"}},
            format="json",
        )
        self.assertEqual(generic_render.status_code, 200)
        self.assertIn("Alex", generic_render.data["rendered"])