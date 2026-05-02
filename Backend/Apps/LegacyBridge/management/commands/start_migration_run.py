from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.LegacyBridge.services import LegacyMigrationService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Start A Tracked Legacy Migration Run."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--source-app", required=True)
        parser.add_argument("--target-app", default="")
        parser.add_argument("--live", action="store_true")

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant Not Found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = LegacyMigrationService.start_run(TenantContext(tenant=tenant, workspace=workspace, source="Command"), options["source_app"], target_app_label=options.get("target_app", ""), dry_run=not options["live"])
        self.stdout.write(self.style.SUCCESS(f"Started Migration Run {result.data.batch_id}."))