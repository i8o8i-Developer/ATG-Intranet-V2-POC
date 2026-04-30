from Backend.Apps.HtmlTemplate.services import TemplateRenderService


def sync_gtm_template(context, template_path="", offer_type="Intern", position="Business Analyst", domains=None):
    return TemplateRenderService.sync_gtm_offer_template(context, template_path=template_path, offer_type=offer_type, position=position, domains=domains or ["ATG", "EI"])


def create_content_template(context, **data):
    return TemplateRenderService.create_content_template(context, **data)


def render_template(template, variables=None):
    return TemplateRenderService.render_text_template(template, variables or {})