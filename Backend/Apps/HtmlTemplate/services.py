import os
import re
from pathlib import Path

from django.conf import settings

from Backend.Apps.HtmlTemplate.models import ContentTemplate, GenericHtmlTemplate, OfferMacro, OfferTemplate, TemplateVariable
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


LEGACY_TEMPLATE_LABELS = {
    "common_template": "Common",
    "developer": "Developer",
    "generic": "Generic",
    "graphics": "Graphics Designer",
    "gtm_enterprise_growth": "GTM Enterprise Growth",
    "hr": "HR",
    "l3_team_1": "L3 Team 1",
    "l3_team_2": "L3 Team 2",
    "marketing": "Marketing",
    "marketing_graphics": "Marketing Graphics",
    "product_manager": "Product Manager",
    "selenium_automation": "Selenium Automation",
    "tech_lead": "Tech Lead",
    "testing": "Testing",
}

LEGACY_TEMPLATE_SUMMARIES = {
    "common_template": "A standard internship offer with ATG onboarding and policy references.",
    "developer": "Role tuned for engineering interns who will work across Django, React, APIs, and delivery fixes.",
    "generic": "Reusable internship offer for operational and project roles that need a standard ATG offer structure.",
    "graphics": "Creative internship offer focused on design execution, revisions, and delivery standards.",
    "gtm_enterprise_growth": "Structured go-to-market offer with enterprise growth exposure, hybrid execution, and revenue-aligned outcomes.",
    "hr": "People operations offer covering hiring support, onboarding execution, and policy coordination.",
    "l3_team_1": "Learning and talent track offer for L3 operations and candidate enablement work.",
    "l3_team_2": "Alternate L3 team offer for talent operations, outreach, and execution ownership.",
    "marketing": "Performance-oriented marketing offer for lead generation, campaigns, and reporting ownership.",
    "marketing_graphics": "Marketing design offer combining campaign asset creation with iteration-based delivery.",
    "product_manager": "Product-focused offer centered on requirements, prioritization, and execution coordination.",
    "selenium_automation": "QA automation offer for Selenium-driven testing, regression coverage, and release confidence.",
    "tech_lead": "Leadership offer for engineers owning delivery quality, mentoring, and technical direction.",
    "testing": "Manual and functional testing offer with task-based delivery expectations.",
}

LEGACY_TEMPLATE_HIGHLIGHTS = {
    "developer": ["Build and fix product features end to end", "Collaborate on API and frontend parity work", "Maintain delivery quality and commit discipline"],
    "graphics": ["Design production-ready visual assets", "Iterate quickly on stakeholder feedback", "Support campaign and product design deliverables"],
    "gtm_enterprise_growth": ["Handle enterprise lead research and outreach", "Participate in client meetings and GTM execution", "Track business impact and closure support"],
    "marketing": ["Run campaign execution with measurable outcomes", "Manage lead funnel quality and reporting", "Coordinate with design and CRM stakeholders"],
    "marketing_graphics": ["Ship marketing assets on schedule", "Adapt creative work across multiple channels", "Own revisions until final approval"],
    "product_manager": ["Translate goals into executable requirements", "Coordinate priorities across delivery stakeholders", "Track quality, scope, and release outcomes"],
    "selenium_automation": ["Automate core regression paths", "Document reproducible quality issues", "Increase release confidence with test coverage"],
    "testing": ["Execute manual test plans and regressions", "Track issues with clear reproduction detail", "Verify fixes before release sign-off"],
}

LEGACY_TEMPLATE_OFFER_TYPES = {
    "gtm_enterprise_growth": "Internship Track",
    "tech_lead": "Full Time",
}

LEGACY_TEMPLATE_DOMAIN_HINTS = {
    "gtm_enterprise_growth": "Banao",
}


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

    @staticmethod
    def legacy_workspace_root():
        base_dir = Path(getattr(settings, "BASE_DIR", os.getcwd())).resolve()
        candidates = [base_dir, *base_dir.parents]
        # Prefer the rebuild MainApp templates (vendored copy of the old intranet templates)
        for candidate in candidates:
            for sub in (candidate, candidate / "Backend"):
                offers_path = sub / "Apps" / "MainApp" / "templates" / "mainapp" / "offers"
                if offers_path.exists():
                    return sub / "Apps" / "MainApp"
        for candidate in candidates:
            offers_path = candidate / "mainapp" / "templates" / "mainapp" / "offers"
            if offers_path.exists():
                return candidate
        return base_dir

    @staticmethod
    def _legacy_templates_root():
        root = TemplateRenderService.legacy_workspace_root()
        # When pointing at the MainApp app, templates live under templates/mainapp
        if (root / "templates" / "mainapp").exists():
            return root / "templates" / "mainapp"
        return root / "mainapp" / "templates" / "mainapp"

    @staticmethod
    def _read_legacy_file(*parts):
        path = TemplateRenderService._legacy_templates_root().joinpath(*parts)
        if not path.exists() or not path.is_file():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1")

    @staticmethod
    def _clean_legacy_body_for_storage(html):
        """Strip Django-only template tags so the stored body works in
        both Django backend rendering and the frontend's mustache-style
        preview without surfacing raw {% ... %} markers."""
        if not html:
            return html
        cleaned = re.sub(r"{%\s*load\s+[^%]+%}", "", html)
        cleaned = re.sub(r"{%\s*csrf_token\s*%}", "", cleaned)
        cleaned = re.sub(r"{%\s*extends\s+[^%]+%}", "", cleaned)
        cleaned = re.sub(r"{%\s*block\s+[^%]+%}", "", cleaned)
        cleaned = re.sub(r"{%\s*endblock\s*[^%]*%}", "", cleaned)
        # Replace `{% for i in payment_data_X %}<th>{{i}}</th>{% endfor %}` with a placeholder var
        cleaned = re.sub(
            r"{%\s*for\s+\w+\s+in\s+(payment_data_1|payment_data_2)\s*%}.*?{%\s*endfor\s*%}",
            lambda m: "{{ " + m.group(1) + "_html }}",
            cleaned,
            flags=re.DOTALL,
        )
        # Convert `{% if foo %}A{% endif %}` to plain text fallback retaining body
        cleaned = re.sub(r"{%\s*if\s+[^%]+%}", "", cleaned)
        cleaned = re.sub(r"{%\s*else\s*%}", "", cleaned)
        cleaned = re.sub(r"{%\s*endif\s*%}", "", cleaned)
        cleaned = re.sub(r"{%\s*include\s+[^%]+%}", "", cleaned)
        cleaned = re.sub(r"{%\s*now\s+[^%]+%}", "", cleaned)
        return cleaned

    @staticmethod
    def legacy_offer_catalog(offers_dir=""):
        directory = Path(offers_dir).resolve() if offers_dir else TemplateRenderService._legacy_templates_root() / "offers"
        if not directory.exists():
            return []
        catalog = []
        for file_path in sorted(directory.glob("*.html")):
            template_key = file_path.stem
            label = LEGACY_TEMPLATE_LABELS.get(template_key, template_key.replace("_", " ").title())
            try:
                raw_html = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                raw_html = file_path.read_text(encoding="latin-1")
            catalog.append(
                {
                    "template_key": template_key,
                    "label": label,
                    "position": label,
                    "summary": LEGACY_TEMPLATE_SUMMARIES.get(template_key, f"Legacy ATG offer template for {label.lower()} roles."),
                    "highlights": LEGACY_TEMPLATE_HIGHLIGHTS.get(template_key, ["Confirm reporting expectations", "Track onboarding milestones", "Align execution with ATG delivery standards"]),
                    "offer_type": LEGACY_TEMPLATE_OFFER_TYPES.get(template_key, "Intern"),
                    "domain_hint": LEGACY_TEMPLATE_DOMAIN_HINTS.get(template_key, "ATG"),
                    "source_file": str(file_path),
                    "raw_html": raw_html,
                }
            )
        return catalog

    @staticmethod
    def build_legacy_offer_template_html(definition):
        highlights = "".join(f"<li>{item}</li>" for item in definition["highlights"])
        return """<!doctype html>
<html>
    <head>
        <meta charset=\"utf-8\" />
        <style>
            body { margin: 0; padding: 28px; background: #ffffff; color: #111827; font-family: Georgia, 'Times New Roman', serif; }
            .offer-shell { max-width: 860px; margin: 0 auto; border: 2px solid #111827; padding: 36px 42px 48px; }
            .offer-logo { text-align: center; margin-bottom: 18px; }
            .offer-logo img { width: 100%; max-width: 520px; height: auto; }
            .offer-title { text-align: center; font-size: 27px; font-weight: 700; letter-spacing: 1.4px; margin: 6px 0 0; }
            .offer-subtitle { text-align: center; margin: 10px 0 16px; font-size: 14px; color: #475467; }
            .offer-date { text-align: right; margin: 18px 0 22px; font-size: 15px; }
            .offer-copy { font-size: 15px; line-height: 1.72; margin: 0 0 14px; text-align: justify; }
            .offer-table { width: 100%; border-collapse: collapse; margin: 20px 0 24px; }
            .offer-table td, .offer-table th { border: 1px solid #111827; padding: 10px 12px; vertical-align: top; }
            .offer-table th { background: #efefef; text-align: left; }
            .offer-section-title { margin: 24px 0 10px; font-size: 18px; }
            .offer-highlights { margin: 0 0 0 18px; padding: 0; }
            .offer-highlights li { margin-bottom: 8px; line-height: 1.6; }
            .offer-signoff { margin-top: 28px; font-size: 15px; line-height: 1.8; }
            .offer-annexure { margin-top: 28px; padding-top: 18px; border-top: 1px solid #cbd5e1; }
            .offer-annexure strong { display: block; margin-bottom: 6px; }
        </style>
    </head>
    <body>
        <div class=\"offer-shell\">
            <div class=\"offer-logo\">
                <img src=\"https://i.postimg.cc/kgHvKMLz/employed-India-Logo.png\" alt=\"ATG Offer Letter\" />
            </div>
            <div class=\"offer-title\">{{{{ offer_heading }}}}</div>
            <div class=\"offer-subtitle\">Legacy template: {label}</div>
            {{{{ offer_disclaimer }}}}
            <div class=\"offer-date\"><strong>{{{{ joining_date }}}}</strong></div>
            <p class=\"offer-copy\">Dear Mr./Ms. {{{{ candidate_name }}}},</p>
            <p class=\"offer-copy\">We are pleased to offer you the position of <strong>{{{{ position_title }}}}</strong> with <strong>{{{{ company_name }}}}</strong>. This offer package follows the classic intranet letter style and is ready for real onboarding communication.</p>
            <p class=\"offer-copy\">{summary}</p>
            <table class=\"offer-table\">
                <tbody>
                    <tr><th style=\"width:34%\">Designation</th><td>{{{{ position_title }}}}</td></tr>
                    <tr><th>Date of Joining / Issue</th><td>{{{{ joining_date }}}}</td></tr>
                    <tr><th>Department</th><td>{{{{ department_name }}}}</td></tr>
                    <tr><th>Sub Department</th><td>{{{{ sub_department_name }}}}</td></tr>
                    <tr><th>Employment Type</th><td>{{{{ employment_type }}}}</td></tr>
                    <tr><th>Compensation</th><td>{{{{ pay_type }}}}</td></tr>
                    <tr><th>System Username</th><td>{{{{ username }}}}</td></tr>
                    <tr><th>Candidate Email</th><td>{{{{ candidate_email }}}}</td></tr>
                </tbody>
            </table>
            <h3 class=\"offer-section-title\">Role Highlights</h3>
            <ul class=\"offer-highlights\">{highlights}</ul>
            <div class=\"offer-annexure\">
                <strong>Terms and Conditions</strong>
                <p class=\"offer-copy\">This offer remains subject to company policy, confidentiality expectations, performance standards, and successful completion of the onboarding formalities communicated by the HR or hiring team.</p>
                <p class=\"offer-copy\">You are requested to confirm acceptance in writing within the communicated validity window. Once accepted, your onboarding access package and reporting instructions will be shared through the official onboarding email.</p>
            </div>
            <div class=\"offer-signoff\">Regards,<br /><strong>Team {{{{ company_name }}}}</strong></div>
        </div>
    </body>
</html>""".format(label=definition["label"], summary=definition["summary"], highlights=highlights)

    @staticmethod
    def build_legacy_onboarding_email_html(definition):
        return """<!doctype html>
<html>
    <body style=\"margin:0;padding:24px;background:#f5f7fb;font-family:Arial,Helvetica,sans-serif;color:#18202f;\">
        <div style=\"max-width:700px;margin:0 auto;background:#ffffff;border:1px solid #dfe5ee;border-radius:18px;overflow:hidden;box-shadow:0 12px 28px rgba(24,32,47,.08);\">
            <div style=\"padding:28px 32px;background:#111827;color:#ffffff;text-align:center;\">
                <img src=\"https://i.postimg.cc/kgHvKMLz/employed-India-Logo.png\" alt=\"ATG\" style=\"max-width:280px;width:100%;height:auto;\" />
                <div style=\"margin-top:16px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#a7f3d0;\">Legacy onboarding email</div>
                <h1 style=\"margin:10px 0 0;font-size:28px;line-height:1.2;\">Your onboarding pack is ready</h1>
            </div>
            <div style=\"padding:28px 32px;\">
                <p style=\"margin-top:0;font-size:15px;line-height:1.7;\">Hi {{{{ candidate_name }}}},</p>
                <p style=\"font-size:15px;line-height:1.7;\">Congratulations. {{{{ company_name }}}} is ready to move forward with your onboarding for the <strong>{{{{ position_title }}}}</strong> role.</p>
                <p style=\"font-size:15px;line-height:1.7;\">This email contains your formal offer workflow. Use the button below to review the letter, download it for records, and confirm acceptance.</p>
                <div style=\"margin:28px 0;text-align:center;\">
                    <a href=\"{{{{ offer_url }}}}\" target=\"_blank\" style=\"display:inline-block;background:#2454d6;color:#ffffff;text-decoration:none;padding:14px 24px;border-radius:999px;font-weight:700;\">Open offer and onboarding page</a>
                </div>
                <table style=\"width:100%;border-collapse:collapse;margin:20px 0;\">
                    <tr><td style=\"padding:10px 0;border-top:1px solid #e5e7eb;color:#667085;\">Template</td><td style=\"padding:10px 0;border-top:1px solid #e5e7eb;text-align:right;font-weight:700;\">{label}</td></tr>
                    <tr><td style=\"padding:10px 0;border-top:1px solid #e5e7eb;color:#667085;\">Candidate email</td><td style=\"padding:10px 0;border-top:1px solid #e5e7eb;text-align:right;font-weight:700;\">{{{{ candidate_email }}}}</td></tr>
                    <tr><td style=\"padding:10px 0;border-top:1px solid #e5e7eb;color:#667085;\">Joining date</td><td style=\"padding:10px 0;border-top:1px solid #e5e7eb;text-align:right;font-weight:700;\">{{{{ joining_date }}}}</td></tr>
                </table>
                <p style=\"font-size:14px;line-height:1.7;color:#475467;\">If you have questions related to the offer, onboarding, or access credentials, reply to this email and the hiring team will assist you.</p>
                <p style=\"font-size:14px;line-height:1.7;color:#475467;\">If the button does not work, copy this URL into your browser: <span style=\"word-break:break-word;color:#2454d6;\">{{{{ offer_url }}}}</span></p>
                <p style=\"font-size:14px;line-height:1.7;margin-bottom:0;\">Regards,<br /><strong>Team {{{{ company_name }}}}</strong></p>
            </div>
        </div>
    </body>
</html>""".format(label=definition["label"])

    @staticmethod
    def sync_legacy_offer_library(context, offers_dir="", domains=None):
        domains = domains or ["ATG", "Banao", "Bunny"]
        rows = []
        catalog = TemplateRenderService.legacy_offer_catalog(offers_dir=offers_dir)
        if not catalog:
            return ServiceResult.failure({"templatePath": "Legacy offer template directory not found."}, status_code=404)
        # Real onboarding email + NDA + certificate bodies copied from old intranet
        onboarding_email_html = TemplateRenderService._read_legacy_file("onboarding_email.html") or TemplateRenderService.build_legacy_onboarding_email_html(catalog[0])
        nda_html = TemplateRenderService._read_legacy_file("nda.html")
        certificate_html = TemplateRenderService._read_legacy_file("certificates", "certificate.html")
        certificate_email_html = TemplateRenderService._read_legacy_file("certificates", "certificate_email.html")
        cleaned_onboarding_email = TemplateRenderService._clean_legacy_body_for_storage(onboarding_email_html)
        cleaned_nda = TemplateRenderService._clean_legacy_body_for_storage(nda_html)
        cleaned_certificate = TemplateRenderService._clean_legacy_body_for_storage(certificate_html)
        cleaned_certificate_email = TemplateRenderService._clean_legacy_body_for_storage(certificate_email_html)
        for definition in catalog:
            raw_offer_html = definition.get("raw_html") or ""
            cleaned_offer_html = TemplateRenderService._clean_legacy_body_for_storage(raw_offer_html)
            # Skip empty placeholder files (hr.html / tech_lead.html in old intranet are 0 bytes)
            if not cleaned_offer_html.strip():
                cleaned_offer_html = (
                    f"<!doctype html><html><body style='font-family:Georgia,serif;padding:32px;'>"
                    f"<h2 style='text-align:center'>{definition['label']} Offer</h2>"
                    f"<p>Dear {{{{ candidate_name }}}},</p>"
                    f"<p>We are pleased to extend an offer for {{{{ position_title }}}} with {{{{ company_name }}}}.</p>"
                    f"<p>{definition['summary']}</p>"
                    f"<p>Joining date: <strong>{{{{ joining_date }}}}</strong></p>"
                    f"<p>Regards,<br/>Team {{{{ company_name }}}}</p>"
                    f"</body></html>"
                )
            for domain in domains:
                content_template, _created = ContentTemplate.objects.update_or_create(
                    tenant=context.tenant,
                    name=f"{domain} {definition['label']} Offer",
                    template_type="Offer",
                    offer_domain=domain,
                    offer_type=definition["offer_type"],
                    position=definition["position"],
                    defaults={
                        "workspace": context.workspace,
                        "subject": f"Offer for {{{{ position_title }}}} - {domain}",
                        "body_html": cleaned_offer_html,
                        "body_text": f"Offer for {{{{ candidate_name }}}} as {{{{ position_title }}}} with {domain}.",
                        "email_template": cleaned_onboarding_email,
                        "email_subject": f"Congratulations! Offer as {{{{ position_title }}}} from {domain}",
                        "status": "Active",
                        "metadata": {
                            "source": "legacy-offer-library",
                            "template_key": definition["template_key"],
                            "source_file": definition["source_file"],
                            "summary": definition["summary"],
                            "domain_hint": definition["domain_hint"],
                            "raw_template_path": f"mainapp/offers/{definition['template_key']}.html",
                            "raw_email_path": "mainapp/onboarding_email.html",
                            "nda_template_path": "mainapp/nda.html" if nda_html else "",
                        },
                        "updated_by": context.actor,
                    },
                )
                GenericHtmlTemplate.objects.update_or_create(
                    tenant=context.tenant,
                    offer_domain=domain,
                    offer_type=definition["offer_type"],
                    position=definition["position"],
                    defaults={
                        "workspace": context.workspace,
                        "template": content_template,
                        "category": "Offer",
                        "offer_html_template": cleaned_offer_html,
                        "render_settings": {
                            "library": "legacy-offer-library",
                            "template_key": definition["template_key"],
                            "raw_template_path": f"mainapp/offers/{definition['template_key']}.html",
                        },
                        "updated_by": context.actor,
                    },
                )
                OfferTemplate.objects.update_or_create(
                    tenant=context.tenant,
                    template=content_template,
                    position_title=definition["position"],
                    defaults={
                        "workspace": context.workspace,
                        "compensation_payload": {"mode": "Variable", "pay_type": "Performance Based"},
                        "policy_payload": {"summary": definition["summary"]},
                        "updated_by": context.actor,
                    },
                )
                TemplateRenderService.ensure_variables(context, content_template)
                rows.append({"domain": domain, "templateId": content_template.id, "name": content_template.name})
        # Seed shared transactional templates (NDA / Certificate) once per tenant
        if cleaned_nda:
            nda_template, _created = ContentTemplate.objects.update_or_create(
                tenant=context.tenant,
                name="ATG NDA Agreement",
                template_type="NDA",
                offer_domain="ATG",
                offer_type="Intern",
                position="NDA",
                defaults={
                    "workspace": context.workspace,
                    "subject": "ATG Confidentiality Agreement",
                    "body_html": cleaned_nda,
                    "email_template": cleaned_nda,
                    "email_subject": "ATG Confidentiality Agreement",
                    "status": "Active",
                    "metadata": {"source": "legacy-offer-library", "template_key": "nda", "raw_template_path": "mainapp/nda.html"},
                    "updated_by": context.actor,
                },
            )
            TemplateRenderService.ensure_variables(context, nda_template)
            rows.append({"domain": "ATG", "templateId": nda_template.id, "name": nda_template.name})
        if cleaned_certificate:
            cert_template, _created = ContentTemplate.objects.update_or_create(
                tenant=context.tenant,
                name="ATG Internship Completion Certificate",
                template_type="Certificate",
                offer_domain="ATG",
                offer_type="Intern",
                position="Certificate",
                defaults={
                    "workspace": context.workspace,
                    "subject": "Across The Globe (ATG) : Internship Completion Certificate",
                    "body_html": cleaned_certificate,
                    "email_template": cleaned_certificate_email or cleaned_certificate,
                    "email_subject": "Across The Globe (ATG) : Internship Completion Certificate",
                    "status": "Active",
                    "metadata": {"source": "legacy-offer-library", "template_key": "certificate", "raw_template_path": "mainapp/certificates/certificate.html", "raw_email_path": "mainapp/certificates/certificate_email.html"},
                    "updated_by": context.actor,
                },
            )
            TemplateRenderService.ensure_variables(context, cert_template)
            rows.append({"domain": "ATG", "templateId": cert_template.id, "name": cert_template.name})
        OutboxService.publish(context, "ContentTemplate", 0, "LegacyOfferLibrarySynced", {"count": len(rows)})
        return ServiceResult.success({"count": len(rows), "rows": rows}, status_code=201)
