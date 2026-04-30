from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.Project.anti_phishing_service import send_weekly_anti_phishing_assessments
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Launch weekly anti-phishing assessments for a project."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--project-id", type=int, required=True)
        parser.add_argument("--week", type=int, default=1)

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant not found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = send_weekly_anti_phishing_assessments(TenantContext(tenant=tenant, workspace=workspace, source="Command"), options["project_id"], week=options["week"])
        if not result.ok:
            raise CommandError(result.errors)
        self.stdout.write(self.style.SUCCESS(f"Launched campaign {result.data['campaignId']}."))