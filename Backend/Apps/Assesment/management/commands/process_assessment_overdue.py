from django.core.management.base import BaseCommand

from Backend.Apps.Assesment.services import AssessmentQueryService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Creates outbox-backed reminders for incomplete assessment assignments."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--grace-days", type=int, default=5)

    def handle(self, *args, **options):
        tenant = Tenant.objects.get(id=options["tenant_id"])
        workspace = None
        if options.get("workspace_id"):
            workspace = Workspace.objects.get(id=options["workspace_id"], tenant=tenant)
        context = TenantContext(tenant=tenant, workspace=workspace, source="Command")
        result = AssessmentQueryService.create_overdue_reminders(context, grace_days=options["grace_days"])
        self.stdout.write(self.style.SUCCESS(f"Created {result.data['count']} assessment reminder events."))
