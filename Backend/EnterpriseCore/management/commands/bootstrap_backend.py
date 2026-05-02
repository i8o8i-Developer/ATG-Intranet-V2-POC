from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from Backend.Apps.Users.models import EmployeeProfile
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
        parser.add_argument("--first-name", default="Backend")
        parser.add_argument("--last-name", default="Admin")
        parser.add_argument("--display-name", default="")
        parser.add_argument("--employee-code", default="EMP-001")

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
            defaults={
                "email": options["email"],
                "first_name": options["first_name"],
                "last_name": options["last_name"],
                "is_staff": True,
                "is_superuser": True,
            },
        )
        display_name = options["display_name"].strip() or " ".join(part for part in [options["first_name"].strip(), options["last_name"].strip()] if part).strip() or options["username"]

        user.email = options["email"]
        user.first_name = options["first_name"]
        user.last_name = options["last_name"]
        user.is_staff = True
        user.is_superuser = True
        user.set_password(options["password"])
        if created_user:
            user.save()
        else:
            user.save(update_fields=["email", "first_name", "last_name", "is_staff", "is_superuser", "password"])

        EmployeeProfile.objects.update_or_create(
            tenant=tenant,
            user=user,
            defaults={
                "workspace": workspace,
                "employee_code": options["employee_code"],
                "display_name": display_name,
                "employment_type": "Leadership",
                "status": EmployeeProfile.STATUS_ACTIVE,
            },
        )

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
        self.stdout.write(f"Employee profile: {display_name}")
        self.stdout.write(f"New capabilities: {capability_count}")
        self.stdout.write(f"New legacy mappings: {legacy_count}")
