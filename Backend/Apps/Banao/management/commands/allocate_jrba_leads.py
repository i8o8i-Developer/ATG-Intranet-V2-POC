from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.Banao.services import LeadWorkflowService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Allocate unassigned JRBA leads to employees."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--source", default="JRBA")
        parser.add_argument("--owner-id", type=int, action="append", default=[])

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant not found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = LeadWorkflowService.allocate_jrba_leads(
            TenantContext(tenant=tenant, workspace=workspace, source="Command"),
            owner_ids=options.get("owner_id") or [],
            source=options.get("source", "JRBA"),
        )
        if not result.ok:
            raise CommandError(result.errors)
        self.stdout.write(self.style.SUCCESS(f"Allocated {result.data['count']} leads."))
