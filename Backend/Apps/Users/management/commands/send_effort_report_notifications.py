from django.core.management.base import BaseCommand

from Backend.Apps.Users.services import UserWorkflowService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Sends notifications to users to submit their monthly effort reports."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--month", type=int)
        parser.add_argument("--year", type=int)

    def handle(self, *args, **options):
        tenant = Tenant.objects.get(id=options["tenant_id"])
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = UserWorkflowService.create_effort_report_reminders(
            TenantContext(tenant=tenant, workspace=workspace, source="Command"),
            report_month=options.get("month"),
            report_year=options.get("year"),
        )
        self.stdout.write(self.style.SUCCESS(f"Created {result.data['count']} effort report reminders."))
