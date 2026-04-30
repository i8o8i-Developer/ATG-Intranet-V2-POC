from django.db.models.signals import post_save
from django.dispatch import receiver

from Backend.Apps.Users.models import DepartmentMembership, EmployeeProfile, Skill
from Backend.Apps.Users.services import EmployeeLifecycleService
from Backend.EnterpriseCore.services import TenantContext


@receiver(post_save, sender=DepartmentMembership, dispatch_uid="backend_users_assign_skills_on_membership")
def assign_skills_on_department_membership(sender, instance, created, **kwargs):
    if not created or instance.status != DepartmentMembership.STATUS_ACTIVE:
        return
    context = TenantContext(tenant=instance.tenant, workspace=instance.workspace, source="Signal")
    EmployeeLifecycleService.assign_department_skills(context, instance.employee)


@receiver(post_save, sender=Skill, dispatch_uid="backend_users_assign_new_department_skill")
def assign_new_skill_to_department_employees(sender, instance, created, **kwargs):
    if not created or not instance.department_id or not instance.is_default_for_department:
        return
    context = TenantContext(tenant=instance.tenant, workspace=instance.workspace, source="Signal")
    employees = EmployeeProfile.objects.filter(tenant=instance.tenant, department=instance.department, status=EmployeeProfile.STATUS_ACTIVE, is_active=True)
    for employee in employees:
        EmployeeLifecycleService.assign_skill(context, employee, instance, assigned_from_department=True)
