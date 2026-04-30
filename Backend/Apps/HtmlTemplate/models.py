from django.db import models

from Backend.EnterpriseCore.models import TenantScopedModel


class TemplateVariable(TenantScopedModel):
    key = models.CharField(max_length=120)
    label = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    default_value = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "key"], name="html_template_variable_key_per_tenant")]


class OfferMacro(TenantScopedModel):
    name = models.CharField(max_length=300)
    macro = models.CharField(max_length=300, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["tenant_id", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "macro"], name="html_offer_macro_per_tenant")]


class ContentTemplate(TenantScopedModel):
    name = models.CharField(max_length=180)
    template_type = models.CharField(max_length=100, db_index=True)
    subject = models.CharField(max_length=220, blank=True)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)
    email_template = models.TextField(blank=True)
    email_subject = models.TextField(blank=True)
    offer_type = models.CharField(max_length=40, default="Intern", db_index=True)
    offer_domain = models.CharField(max_length=40, default="ATG", db_index=True)
    position = models.CharField(max_length=200, blank=True, db_index=True)
    status = models.CharField(max_length=80, default="Draft", db_index=True)
    variables = models.ManyToManyField("HtmlTemplate.TemplateVariable", blank=True, related_name="templates")
    macros = models.ManyToManyField("HtmlTemplate.OfferMacro", blank=True, related_name="templates")
    departments = models.ManyToManyField("Users.Department", blank=True, related_name="html_templates")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "name"]


class OfferTemplate(TenantScopedModel):
    template = models.ForeignKey("HtmlTemplate.ContentTemplate", on_delete=models.PROTECT, related_name="offer_templates")
    position_title = models.CharField(max_length=180, blank=True)
    compensation_payload = models.JSONField(default=dict, blank=True)
    policy_payload = models.JSONField(default=dict, blank=True)


class GenericHtmlTemplate(TenantScopedModel):
    template = models.ForeignKey("HtmlTemplate.ContentTemplate", null=True, blank=True, on_delete=models.SET_NULL, related_name="generic_templates")
    category = models.CharField(max_length=120, blank=True, db_index=True)
    offer_type = models.CharField(max_length=40, default="Intern", db_index=True)
    offer_html_template = models.TextField(blank=True)
    offer_domain = models.CharField(max_length=40, default="ATG", db_index=True)
    position = models.CharField(max_length=200, blank=True, db_index=True)
    render_settings = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "offer_domain", "offer_type", "position"]
        constraints = [models.UniqueConstraint(fields=["tenant", "offer_domain", "offer_type", "position"], name="html_generic_offer_once")]
