from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.LegacyBridge.services import LegacyMappingService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Seed default legacy-to-backend app mappings."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant not found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = LegacyMappingService.seed_default_app_map(TenantContext(tenant=tenant, workspace=workspace, source="Command"))
        self.stdout.write(self.style.SUCCESS(f"Created {result.data['count']} mappings."))