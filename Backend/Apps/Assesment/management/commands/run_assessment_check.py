from django.core.management.base import BaseCommand

from Backend.Apps.Assesment.services import AssessmentAutomationService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Runs assessment provider status checks, next-assessment assignment, and overdue reminder processing."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--grace-days", type=int, default=5)
        parser.add_argument("--sync-provider", action="store_true")
        parser.add_argument("--skip-auto-assign", action="store_true")
        parser.add_argument("--skip-reminders", action="store_true")

    def handle(self, *args, **options):
        tenant = Tenant.objects.get(id=options["tenant_id"])
        workspace = None
        if options.get("workspace_id"):
            workspace = Workspace.objects.get(id=options["workspace_id"], tenant=tenant)
        context = TenantContext(tenant=tenant, workspace=workspace, source="Command")
        result = AssessmentAutomationService.run_assessment_check(
            context,
            sync_provider=options["sync_provider"],
            auto_assign_next=not options["skip_auto_assign"],
            create_reminders=not options["skip_reminders"],
            grace_days=options["grace_days"],
        )
        if not result.ok:
            self.stdout.write(self.style.ERROR(str(result.errors)))
            return
        self.stdout.write(self.style.SUCCESS("Assessment check completed successfully."))
        self.stdout.write(f"Provider synced: {result.data['providerSynced']}")
        self.stdout.write(f"Auto-assigned next assessments: {len(result.data['autoAssigned'])}")
        self.stdout.write(f"Reminder events: {result.data['reminders']['count']}")
