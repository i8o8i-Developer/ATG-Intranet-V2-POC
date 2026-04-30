from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.L3.services import TalentPipelineService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Assign L3 college records to a caller."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--employee-id", type=int, required=True)
        parser.add_argument("--college-id", type=int, action="append", default=[])
        parser.add_argument("--limit", type=int)

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant not found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = TalentPipelineService.assign_colleges(TenantContext(tenant=tenant, workspace=workspace, source="Command"), options["employee_id"], college_ids=options.get("college_id") or [], limit=options.get("limit"))
        if not result.ok:
            raise CommandError(result.errors)
        self.stdout.write(self.style.SUCCESS(f"Assigned {result.data['count']} colleges."))