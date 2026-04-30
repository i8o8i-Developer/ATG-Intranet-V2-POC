from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from Backend.Apps.LegacyBridge.legacy_app_map import LEGACY_APP_TO_BACKEND_APP
from Backend.Apps.LegacyBridge.models import LegacyApplicationMap
from Backend.EnterpriseCore.models import BusinessUnit, Capability, Organization, Role, RoleAssignment, RoleCapability, Tenant, Workspace


CAPABILITY_MODULES = {
    "EnterpriseCore": ["tenant.view", "tenant.manage", "access.manage"],
    "Users": ["employee.view", "employee.manage"],
    "MainApp": ["peopleops.view", "peopleops.manage"],
    "Project": ["project.view", "project.manage"],
    "TasksDashboard": ["work.view", "work.manage"],
    "Banao": ["lead.view", "lead.manage"],
    "Lms": ["learning.view", "learning.manage"],
    "Assesment": ["assessment.view", "assessment.manage", "assessment.assign", "assessment.evaluate"],
    "FinanceAndPayroll": ["finance.view", "finance.approve"],
    "IntegrationHub": ["integration.view", "integration.manage"],
    "McpAccessLayer": ["mcp.view", "mcp.manage"],
}


class Command(BaseCommand):
    help = "Bootstrap a runnable tenant, workspace, admin user, capabilities, and legacy app map for the new Backend."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default="Banao")
        parser.add_argument("--workspace", default="Default Workspace")
        parser.add_argument("--username", default="backend-admin")
        parser.add_argument("--password", default="backend-admin")
        parser.add_argument("--email", default="backend-admin@example.com")

    def handle(self, *args, **options):
        user_model = get_user_model()
        tenant, _ = Tenant.objects.get_or_create(
            slug=options["tenant"].lower().replace(" ", "-"),
            defaults={"name": options["tenant"], "legal_name": options["tenant"]},
        )
        organization, _ = Organization.objects.get_or_create(
            tenant=tenant,
            slug="default-org",
            defaults={"name": "Default Organization"},
        )
        business_unit, _ = BusinessUnit.objects.get_or_create(
            tenant=tenant,
            organization=organization,
            code="DEFAULT",
            defaults={"name": "Default Business Unit"},
        )
        workspace, _ = Workspace.objects.get_or_create(
            tenant=tenant,
            business_unit=business_unit,
            code="DEFAULT",
            defaults={"name": options["workspace"]},
        )
        user, created_user = user_model.objects.get_or_create(
            username=options["username"],
            defaults={"email": options["email"], "is_staff": True, "is_superuser": True},
        )
        if created_user or not user.has_usable_password():
            user.set_password(options["password"])
            user.save(update_fields=["password", "is_staff", "is_superuser", "email"])

        role, _ = Role.objects.get_or_create(
            tenant=tenant,
            code="OWNER",
            defaults={"name": "Owner", "description": "Default backend owner role", "is_system_role": True},
        )
        RoleAssignment.objects.get_or_create(tenant=tenant, workspace=workspace, user=user, role=role)

        capability_count = 0
        for module, codes in CAPABILITY_MODULES.items():
            for code in codes:
                capability, was_created = Capability.objects.get_or_create(
                    code=f"{module}.{code}",
                    defaults={"name": f"{module} {code}", "module": module},
                )
                RoleCapability.objects.get_or_create(tenant=tenant, role=role, capability=capability)
                if was_created:
                    capability_count += 1

        legacy_count = 0
        for legacy_app, backend_app in LEGACY_APP_TO_BACKEND_APP.items():
            _item, was_created = LegacyApplicationMap.objects.get_or_create(
                tenant=tenant,
                workspace=workspace,
                legacy_app_label=legacy_app,
                backend_app_label=backend_app,
            )
            if was_created:
                legacy_count += 1

        self.stdout.write(self.style.SUCCESS("Backend bootstrap complete."))
        self.stdout.write(f"Tenant ID: {tenant.id}")
        self.stdout.write(f"Workspace ID: {workspace.id}")
        self.stdout.write(f"Admin username: {user.username}")
        self.stdout.write(f"New capabilities: {capability_count}")
        self.stdout.write(f"New legacy mappings: {legacy_count}")
