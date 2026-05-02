from django.core.management.base import BaseCommand

from Backend.Apps.Users.provider import InterviewGodClient
from Backend.Apps.Users.services import InterviewSyncService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Sync Interns With InterviewGod. Defaults To Dry-Run Mode."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--employee-id", type=int)
        parser.add_argument("--live", action="store_true")
        parser.add_argument("--send-links", action="store_true")

    def handle(self, *args, **options):
        tenant = Tenant.objects.get(id=options["tenant_id"])
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = InterviewSyncService.sync_interns(
            TenantContext(tenant=tenant, workspace=workspace, source="Command"),
            employee_id=options.get("employee_id"),
            dry_run=not options["live"],
            send_links=options["send_links"],
            client=InterviewGodClient() if options["live"] else None,
        )
        self.stdout.write(self.style.SUCCESS(f"Processed {result.data['count']} Interns."))
