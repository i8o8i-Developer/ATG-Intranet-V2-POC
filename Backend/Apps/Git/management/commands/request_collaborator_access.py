from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.Git.services import GitRepositoryService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Queue Or Send GitHub Collaborator Access Requests."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--employee-id", type=int)
        parser.add_argument("--github-username", default="")
        parser.add_argument("--repository-id", type=int, action="append", default=[])
        parser.add_argument("--live", action="store_true")

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant not found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = GitRepositoryService.request_collaborator_access(
            TenantContext(tenant=tenant, workspace=workspace, source="Command"),
            employee_id=options.get("employee_id"),
            github_username=options.get("github_username", ""),
            repository_ids=options.get("repository_id") or [],
            live=options["live"],
        )
        if not result.ok:
            raise CommandError(result.errors)
        self.stdout.write(self.style.SUCCESS(f"Created {result.data['count']} collaborator access requests."))