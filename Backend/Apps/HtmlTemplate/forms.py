from django import forms

from Backend.Apps.HtmlTemplate.models import ContentTemplate, GenericHtmlTemplate, OfferMacro, OfferTemplate, TemplateVariable


class TemplateVariableForm(forms.ModelForm):
    class Meta:
        model = TemplateVariable
        fields = ["key", "label", "description", "default_value"]


class OfferMacroForm(forms.ModelForm):
    class Meta:
        model = OfferMacro
        fields = ["name", "macro", "description"]


class ContentTemplateForm(forms.ModelForm):
    class Meta:
        model = ContentTemplate
        fields = ["name", "template_type", "subject", "body_html", "body_text", "email_template", "email_subject", "offer_type", "offer_domain", "position", "status", "variables", "macros", "departments", "metadata"]


class OfferTemplateForm(forms.ModelForm):
    class Meta:
        model = OfferTemplate
        fields = ["template", "position_title", "compensation_payload", "policy_payload"]


class GenericHtmlTemplateForm(forms.ModelForm):
    class Meta:
        model = GenericHtmlTemplate
        fields = ["template", "category", "offer_type", "offer_html_template", "offer_domain", "position", "render_settings"]