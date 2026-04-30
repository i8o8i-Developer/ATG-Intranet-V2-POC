from django.contrib.auth import get_user_model
from django.test import TestCase

from Backend.Apps.HtmlTemplate.models import GenericHtmlTemplate, OfferMacro, TemplateVariable
from Backend.Apps.HtmlTemplate.services import TemplateRenderService
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class HtmlTemplateTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="HTML Tenant", slug="html-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="html-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="People", code="HTML")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="HTML", code="HTML")
        self.user = get_user_model().objects.create_user(username="html-user", email="html@example.com")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)

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