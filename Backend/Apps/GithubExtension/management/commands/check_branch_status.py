from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.GithubExtension.services import GitHubBranchService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Check Branch Tester/Reviewer Status For A Repository."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--repo-name", required=True)
        parser.add_argument("--branch", action="append", default=[])

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant Not Found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = GitHubBranchService.list_branch_status(TenantContext(tenant=tenant, workspace=workspace, source="Command"), options["repo_name"], options.get("branch") or [])
        if not result.ok:
            raise CommandError(result.errors)
        self.stdout.write(self.style.SUCCESS(str(result.data)))