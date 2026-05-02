from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from Backend.Apps.Users.models import Department, EmployeeProfile, InterviewProgress, Position
from Backend.EnterpriseCore.models import Tenant, Workspace


class Command(BaseCommand):
    help = "Create Lightweight Test Data For InterviewGod Sync."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int, required=True)
        parser.add_argument("--count", type=int, default=2)

    def handle(self, *args, **options):
        tenant = Tenant.objects.get(id=options["tenant_id"])
        workspace = Workspace.objects.get(id=options["workspace_id"], tenant=tenant)
        user_model = get_user_model()
        department, _ = Department.objects.get_or_create(tenant=tenant, workspace=workspace, code="INTERN", defaults={"name": "Interns"})
        position, _ = Position.objects.get_or_create(tenant=tenant, workspace=workspace, code="INTERN", defaults={"title": "Intern"})
        created = []
        for index in range(options["count"]):
            username = f"interviewgod-intern-{tenant.id}-{index + 1}"
            user, _ = user_model.objects.get_or_create(username=username, defaults={"email": f"{username}@example.com"})
            employee, _ = EmployeeProfile.objects.get_or_create(
                tenant=tenant,
                workspace=workspace,
                user=user,
                employee_code=f"IG-{tenant.id}-{index + 1}",
                defaults={"display_name": f"Interview Intern {index + 1}", "department": department, "position": position, "employment_type": "Intern"},
            )
            InterviewProgress.objects.get_or_create(tenant=tenant, workspace=workspace, employee=employee)
            created.append(employee.id)
        self.stdout.write(self.style.SUCCESS(f"Prepared {len(created)} InterviewGod Test Interns."))
