from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.TasksDashboard.services import ClickUpSyncService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Mark External Task Mappings As Cleared."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--provider", default="ClickUp")

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant Not Found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = ClickUpSyncService.clear_synced_tasks(TenantContext(tenant=tenant, workspace=workspace, source="Command"), provider=options["provider"])
        self.stdout.write(self.style.SUCCESS(f"Cleared {result.data['count']} Mappings."))