from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from Backend.Apps.Users.models import EmployeeProfile
from Backend.Apps.LegacyBridge.legacy_app_map import LEGACY_APP_TO_BACKEND_APP
from Backend.Apps.LegacyBridge.models import LegacyApplicationMap
from Backend.EnterpriseCore.models import BusinessUnit, Capability, Organization, Role, RoleAssignment, RoleCapability, Tenant, Workspace


CAPABILITY_MODULES = {
    "EnterpriseCore": ["tenant.view", "tenant.manage", "access.manage"],
    "Users": ["employee.view", "employee.manage", "employee.hire", "employee.deactivate", "skill.manage", "goal.manage"],
    "MainApp": ["peopleops.view", "peopleops.manage", "offer.create", "certificate.issue", "notification.send"],
    "Project": ["project.view", "project.manage", "project.create", "milestone.manage", "budget.view"],
    "TasksDashboard": ["work.view", "work.manage", "work.assign"],
    "Banao": ["lead.view", "lead.manage", "lead.assign", "lead.delete"],
    "Lms": ["learning.view", "learning.manage"],
    "Assesment": ["assessment.view", "assessment.manage", "assessment.assign", "assessment.evaluate"],
    "FinanceAndPayroll": ["finance.view", "finance.approve", "finance.pay", "finance.export"],
    "IntegrationHub": ["integration.view", "integration.manage"],
    "McpAccessLayer": ["mcp.view", "mcp.manage"],
    "AtgDocs": ["docs.view", "docs.edit", "docs.manage"],
    "LegacyBridge": ["migration.view", "migration.manage"],
    "GithubExtension": ["github.view", "github.manage"],
    "Git": ["git.view", "git.manage"],
    "HtmlTemplate": ["template.view", "template.manage"],
    "L3": ["college.view", "college.manage", "college.call", "college.data_entry"],
}

# 
LEGACY_GROUPS = {
    "Admin": {
        "capabilities": {"Users": ["employee.manage"]},
        "description": "Interview Operations Admin - Can Send Interview Invites",
    },
    "Business analyst": {
        "capabilities": {"Banao": ["lead.view", "lead.manage"], "Lms": ["learning.view"]},
        "description": "Lead Management / Sales Team",
    },
    "Business analyst - data entry": {
        "capabilities": {"Banao": ["lead.view"]},
        "description": "BA Data Entry Support",
    },
    "Docs view": {
        "capabilities": {"AtgDocs": ["docs.view"]},
        "description": "Read-Only Documentation Access",
    },
    "HR": {
        "capabilities": {"Users": ["employee.manage", "employee.hire", "employee.deactivate"], "MainApp": ["offer.create", "certificate.issue"]},
        "description": "HR Operations",
    },
    "Junior Business analyst": {
        "capabilities": {"Banao": ["lead.view"]},
        "description": "Junior BA - Lead View Only",
    },
    "docs edit": {
        "capabilities": {"AtgDocs": ["docs.view", "docs.edit"]},
        "description": "Documentation Editor",
    },
    "finance manager": {
        "capabilities": {"FinanceAndPayroll": ["finance.view", "finance.approve", "finance.pay", "finance.export"]},
        "description": "Finance Operations Manager",
    },
    "l3 data entry": {
        "capabilities": {"L3": ["college.view", "college.data_entry"]},
        "description": "L3 Data Entry Team",
    },
    "l3_caller": {
        "capabilities": {"L3": ["college.view", "college.call"]},
        "description": "L3 Caller Team",
    },
    "lms-manager": {
        "capabilities": {"Banao": ["lead.view", "lead.manage", "lead.assign"], "Lms": ["learning.view", "learning.manage"]},
        "description": "LMS / Lead System Manager",
    },
    "manager": {
        "capabilities": {"Project": ["project.view", "project.manage"], "Users": ["employee.view"], "TasksDashboard": ["work.view", "work.assign"]},
        "description": "Department / Project Manager",
    },
    "marketing manager": {
        "capabilities": {"L3": ["college.view", "college.manage"]},
        "description": "Marketing / L3 Team Manager",
    },
    "senior project manager": {
        "capabilities": {"Project": ["project.view", "project.manage", "project.create"], "FinanceAndPayroll": ["finance.view"]},
        "description": "Senior Project Manager",
    },
    "banao-admin": {
        "capabilities": {"Banao": ["lead.view", "lead.manage", "lead.assign", "lead.delete"], "Lms": ["learning.view", "learning.manage"]},
        "description": "Banao Admin",
    },
    "banao-manager": {
        "capabilities": {"Banao": ["lead.view", "lead.manage", "lead.assign"]},
        "description": "Banao Manager",
    },
}


class Command(BaseCommand):
    help = "Bootstrap A Runnable Tenant, Workspace, Admin User, Capabilities, And Legacy App Map For The New Backend."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default="Banao")
        parser.add_argument("--workspace", default="Default Workspace")
        parser.add_argument("--username", default="anubhav1608")
        parser.add_argument("--password", default="AnubhavChaurasia")
        parser.add_argument("--email", default="anubhav1608@example.com")
        parser.add_argument("--first-name", default="Anubhav")
        parser.add_argument("--last-name", default="Chaurasia")
        parser.add_argument("--display-name", default="Anubhav Chaurasia")
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

        owner_role, _ = Role.objects.get_or_create(
            tenant=tenant,
            code="OWNER",
            defaults={"name": "Owner", "description": "Default Backend Owner Role", "is_system_role": True},
        )
        RoleAssignment.objects.get_or_create(tenant=tenant, workspace=workspace, user=user, role=owner_role)

        capability_count = 0
        all_capabilities = {}
        for module, codes in CAPABILITY_MODULES.items():
            for code in codes:
                capability, was_created = Capability.objects.get_or_create(
                    code=f"{module}.{code}",
                    defaults={"name": f"{module} {code}", "module": module},
                )
                all_capabilities[f"{module}.{code}"] = capability
                RoleCapability.objects.get_or_create(tenant=tenant, role=owner_role, capability=capability)
                if was_created:
                    capability_count += 1

        # 
        role_count = 0
        for group_name, group_data in LEGACY_GROUPS.items():
            role_code = group_name.upper().replace(" ", "_").replace("-", "_")
            legacy_role, created = Role.objects.get_or_create(
                tenant=tenant,
                code=role_code,
                defaults={"name": group_name, "description": group_data["description"], "is_system_role": False},
            )
            if created:
                role_count += 1
            for module, codes in group_data["capabilities"].items():
                for code in codes:
                    cap_key = f"{module}.{code}"
                    if cap_key in all_capabilities:
                        RoleCapability.objects.get_or_create(tenant=tenant, role=legacy_role, capability=all_capabilities[cap_key])

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

        self.stdout.write(self.style.SUCCESS("Backend Bootstrap Complete."))
        self.stdout.write(f"Tenant ID: {tenant.id}")
        self.stdout.write(f"Workspace ID: {workspace.id}")
        self.stdout.write(f"Admin Username: {user.username}")
        self.stdout.write(f"Employee Profile: {display_name}")
        self.stdout.write(f"New Capabilities: {capability_count}")
        self.stdout.write(f"New Legacy Mappings: {legacy_count}")
        self.stdout.write(f"Legacy Group Roles Created: {role_count}")
