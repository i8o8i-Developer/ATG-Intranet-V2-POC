import os
import re

from django.conf import settings

from Backend.Apps.HtmlTemplate.models import ContentTemplate, GenericHtmlTemplate, OfferMacro, TemplateVariable
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class TemplateRenderService:
    @staticmethod
    def render_text_template(template, variables):
        body = getattr(template, "body_text", "") or getattr(template, "body_html", "") or getattr(template, "offer_html_template", "")
        for key, value in (variables or {}).items():
            body = body.replace("{{" + key + "}}", str(value))
            body = body.replace("{{ " + key + " }}", str(value))
        return ServiceResult.success({"rendered": body})

    @staticmethod
    def get_active_template(context, template_type, name):
        template = ContentTemplate.objects.filter(tenant=context.tenant, template_type=template_type, name=name, status="Active").first()
        if not template:
            return ServiceResult.failure({"template": "Active Template Not Found."}, status_code=404)
        return ServiceResult.success(template)

    @staticmethod
    def extract_variables(body):
        return sorted(set(re.findall(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}", body or "")))

    @staticmethod
    def create_content_template(context, **data):
        template = ContentTemplate.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            name=data["name"],
            template_type=data.get("template_type", "Offer"),
            subject=data.get("subject", ""),
            body_html=data.get("body_html", ""),
            body_text=data.get("body_text", ""),
            email_template=data.get("email_template", ""),
            email_subject=data.get("email_subject", ""),
            offer_type=data.get("offer_type", "Intern"),
            offer_domain=data.get("offer_domain", "ATG"),
            position=data.get("position", ""),
            status=data.get("status", "Draft"),
            metadata=data.get("metadata", {}),
            created_by=context.actor,
            updated_by=context.actor,
        )
        TemplateRenderService.ensure_variables(context, template)
        OutboxService.publish(context, "ContentTemplate", template.id, "ContentTemplateCreated", {"name": template.name})
        return ServiceResult.success(template, status_code=201)

    @staticmethod
    def ensure_variables(context, template):
        body = "\n".join([template.body_html or "", template.body_text or "", template.email_template or ""])
        variables = []
        for key in TemplateRenderService.extract_variables(body):
            variable, _created = TemplateVariable.objects.get_or_create(
                tenant=context.tenant,
                key=key,
                defaults={"workspace": context.workspace or template.workspace, "label": key.replace("_", " ").title(), "created_by": context.actor, "updated_by": context.actor},
            )
            template.variables.add(variable)
            variables.append(variable.id)
        return variables

    @staticmethod
    def sync_gtm_offer_template(context, template_path="", offer_type="Intern", position="Business Analyst", domains=None, html_content=""):
        domains = domains or ["ATG", "EI"]
        if not html_content:
            template_path = template_path or os.path.join(getattr(settings, "BASE_DIR", os.getcwd()), "mainapp", "templates", "mainapp", "offers", "gtm_enterprise_growth.html")
            try:
                with open(template_path, "r", encoding="utf-8") as template_file:
                    html_content = template_file.read()
            except FileNotFoundError:
                return ServiceResult.failure({"templatePath": f"Template File Not Found At: {template_path}"}, status_code=404)
        rows = []
        for domain in domains:
            content_template, _created = ContentTemplate.objects.update_or_create(
                tenant=context.tenant,
                name=f"{domain} {position} {offer_type} Offer",
                template_type="Offer",
                offer_domain=domain,
                offer_type=offer_type,
                position=position,
                defaults={
                    "workspace": context.workspace,
                    "body_html": html_content,
                    "status": "Active",
                    "metadata": {"source": "GTM", "position": position},
                    "updated_by": context.actor,
                },
            )
            GenericHtmlTemplate.objects.update_or_create(
                tenant=context.tenant,
                offer_domain=domain,
                offer_type=offer_type,
                position=position,
                defaults={"workspace": context.workspace, "template": content_template, "offer_html_template": html_content, "category": "Offer", "updated_by": context.actor},
            )
            TemplateRenderService.ensure_variables(context, content_template)
            rows.append({"domain": domain, "templateId": content_template.id})
        OutboxService.publish(context, "ContentTemplate", 0, "GtmOfferTemplateSynced", {"count": len(rows), "position": position})
        return ServiceResult.success({"count": len(rows), "rows": rows}, status_code=201)

    @staticmethod
    def upsert_macro(context, name, macro, description=""):
        item, _created = OfferMacro.objects.update_or_create(
            tenant=context.tenant,
            macro=macro,
            defaults={"workspace": context.workspace, "name": name, "description": description, "updated_by": context.actor},
        )
        return ServiceResult.success(item, status_code=201)
