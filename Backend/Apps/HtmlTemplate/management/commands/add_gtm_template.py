from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.HtmlTemplate.services import TemplateRenderService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Sync the GTM Enterprise Growth offer template."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--template-path", default="")
        parser.add_argument("--offer-type", default="Intern")
        parser.add_argument("--position", default="Business Analyst")
        parser.add_argument("--domain", action="append", default=[])

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant not found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = TemplateRenderService.sync_gtm_offer_template(
            TenantContext(tenant=tenant, workspace=workspace, source="Command"),
            template_path=options.get("template_path", ""),
            offer_type=options.get("offer_type", "Intern"),
            position=options.get("position", "Business Analyst"),
            domains=options.get("domain") or ["ATG", "EI"],
        )
        if not result.ok:
            raise CommandError(result.errors)
        self.stdout.write(self.style.SUCCESS(f"GTM offer templates synced: {result.data['count']}"))