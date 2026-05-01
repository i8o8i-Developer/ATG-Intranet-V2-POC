from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.TasksDashboard.services import ClickUpSyncService
from Backend.Apps.TasksDashboard.provider import TasksDashboardProvider
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Dry-run sync ClickUp task payloads into the rebuilt task dashboard."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--space-id", action="append", dest="space_ids", default=[])
        parser.add_argument("--team-id", default="")
        parser.add_argument("--project-name", default="")
        parser.add_argument("--live", action="store_true")

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant not found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        provider = TasksDashboardProvider(live=options["live"])
        payload = provider.fetch_clickup_tasks(project_name=options["project_name"], space_ids=options["space_ids"], team_id=options["team_id"])
        result = ClickUpSyncService.sync_tasks(TenantContext(tenant=tenant, workspace=workspace, source="Command"), payload["tasks"])
        self.stdout.write(self.style.SUCCESS(f"Synced {result.data['count']} tasks."))