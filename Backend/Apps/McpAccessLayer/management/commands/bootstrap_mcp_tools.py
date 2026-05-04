"""
Management command to bootstrap MCP tools into the database

This command registers all MCP tools from the mcp_server registry into the database,
making them available for permission management and audit logging.

Usage:
    python manage.py bootstrap_mcp_tools --tenant=<tenant_slug>
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from Backend.Apps.McpAccessLayer.models import McpToolDefinition
from Backend.Apps.McpAccessLayer.mcp_server import MCP_TOOLS_REGISTRY
from Backend.EnterpriseCore.models import Tenant


class Command(BaseCommand):
    help = "Bootstrap MCP tools into the database"

    def add_arguments(self, parser):
        parser.add_argument("--tenant", type=str, required=True, help="Tenant slug")
        parser.add_argument("--workspace", type=str, help="Workspace slug (optional)")

    def handle(self, *args, **options):
        tenant_slug = options["tenant"]
        workspace_slug = options.get("workspace")

        try:
            tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant '{tenant_slug}' not found"))
            return

        workspace = None
        if workspace_slug:
            workspace = tenant.workspaces.filter(slug=workspace_slug, is_active=True).first()
            if not workspace:
                self.stdout.write(self.style.ERROR(f"Workspace '{workspace_slug}' not found in tenant '{tenant_slug}'"))
                return

        self.stdout.write(self.style.SUCCESS(f"Bootstrapping MCP tools for tenant: {tenant.name}"))
        if workspace:
            self.stdout.write(self.style.SUCCESS(f"Workspace: {workspace.name}"))

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for tool_name, tool_instance in MCP_TOOLS_REGISTRY.items():
                tool, created = McpToolDefinition.objects.update_or_create(
                    tenant=tenant,
                    slug=tool_name,
                    defaults={
                        "workspace": workspace,
                        "name": tool_instance.name.replace("_", " ").title(),
                        "owning_module": "McpAccessLayer",
                        "description": tool_instance.description,
                        "input_schema": tool_instance.input_schema,
                        "output_schema": {},
                        "is_mutating": tool_instance.is_mutating,
                        "status": "Active",
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Created tool: {tool_name}"))
                else:
                    updated_count += 1
                    self.stdout.write(f"  ↻ Updated tool: {tool_name}")

        self.stdout.write(self.style.SUCCESS(f"\nBootstrap complete!"))
        self.stdout.write(f"  Created: {created_count} tools")
        self.stdout.write(f"  Updated: {updated_count} tools")
        self.stdout.write(f"  Total: {len(MCP_TOOLS_REGISTRY)} tools")
