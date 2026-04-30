from decimal import Decimal

from django.db import models
from django.utils import timezone

from Backend.Apps.Users.models import (
    BenchPeriod,
    Department,
    DepartmentMembership,
    EmployeePaymentSnapshot,
    EmployeeProfile,
    InterviewProgress,
    LeaveBalance,
    LeavePolicy,
    LeaveTransaction,
    PayProfile,
    ResignationRequest,
    Skill,
    UserEffortReport,
    UserSkill,
    UserStatusSnapshot,
)
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class EmployeeLifecycleService:
    @staticmethod
    def activate_employee(context, employee_id):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee not found."}, status_code=404)
        employee.status = EmployeeProfile.STATUS_ACTIVE
        employee.updated_by = context.actor
        employee.save(update_fields=["status", "updated_by", "updated_at"])
        OutboxService.publish(context, "EmployeeProfile", employee.id, "EmployeeActivated", {"employeeId": employee.id})
        return ServiceResult.success(employee)

    @staticmethod
    def change_status(context, employee_id, status, reason="", effective_from=None):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee not found."}, status_code=404)
        effective_from = effective_from or timezone.localdate()
        employee.status = status
        if status == EmployeeProfile.STATUS_EXITED and not employee.exited_on:
            employee.exited_on = effective_from
        employee.updated_by = context.actor
        employee.save(update_fields=["status", "exited_on", "updated_by", "updated_at"])
        snapshot = UserStatusSnapshot.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or employee.workspace,
            employee=employee,
            status=status,
            reason=reason,
            effective_from=effective_from,
            created_by=context.actor,
            updated_by=context.actor,
        )
        if status == EmployeeProfile.STATUS_ON_BENCH:
            bench_period = BenchPeriod.objects.filter(tenant=context.tenant, employee=employee, ended_on__isnull=True).first()
            if not bench_period:
                BenchPeriod.objects.create(
                    tenant=context.tenant,
                    workspace=context.workspace or employee.workspace,
                    employee=employee,
                    reason=reason,
                    created_by=context.actor,
                    updated_by=context.actor,
                )
        else:
            BenchPeriod.objects.filter(tenant=context.tenant, employee=employee, ended_on__isnull=True).update(ended_on=effective_from, updated_by=context.actor)
        OutboxService.publish(context, "EmployeeProfile", employee.id, "EmployeeStatusChanged", {"employeeId": employee.id, "status": status, "snapshotId": snapshot.id})
        return ServiceResult.success(employee)

    @staticmethod
    def transfer_department(context, employee_id, department_id, sub_department_id=None, started_on=None, end_existing=True):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee not found."}, status_code=404)
        department = Department.objects.filter(tenant=context.tenant, id=department_id).first()
        if not department:
            return ServiceResult.failure({"department": "Department not found."}, status_code=404)
        if end_existing:
            DepartmentMembership.objects.filter(tenant=context.tenant, employee=employee, status=DepartmentMembership.STATUS_ACTIVE).update(
                status=DepartmentMembership.STATUS_ENDED,
                ended_on=started_on or timezone.localdate(),
                updated_by=context.actor,
            )
        membership = DepartmentMembership.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or employee.workspace,
            employee=employee,
            department=department,
            sub_department_id=sub_department_id,
            started_on=started_on or timezone.localdate(),
            created_by=context.actor,
            updated_by=context.actor,
        )
        employee.department = department
        employee.updated_by = context.actor
        employee.save(update_fields=["department", "updated_by", "updated_at"])
        EmployeeLifecycleService.assign_department_skills(context, employee)
        OutboxService.publish(context, "EmployeeProfile", employee.id, "EmployeeDepartmentChanged", {"employeeId": employee.id, "departmentId": department.id})
        return ServiceResult.success(membership, status_code=201)

    @staticmethod
    def assign_skill(context, employee, skill, proficiency=1, rating=0, assigned_from_department=False):
        link, _created = UserSkill.objects.update_or_create(
            tenant=context.tenant,
            workspace=context.workspace or employee.workspace,
            employee=employee,
            skill=skill,
            defaults={"proficiency": proficiency, "rating": rating, "assigned_from_department": assigned_from_department, "updated_by": context.actor},
        )
        return ServiceResult.success(link)

    @staticmethod
    def assign_department_skills(context, employee):
        department_ids = list(
            DepartmentMembership.objects.filter(tenant=context.tenant, employee=employee, status=DepartmentMembership.STATUS_ACTIVE).values_list("department_id", flat=True)
        )
        if employee.department_id and employee.department_id not in department_ids:
            department_ids.append(employee.department_id)
        skills = Skill.objects.filter(tenant=context.tenant, is_active=True).filter(models.Q(department_id__in=department_ids) | models.Q(department__isnull=True))
        assigned = []
        for skill in skills:
            result = EmployeeLifecycleService.assign_skill(context, employee, skill, proficiency=1, assigned_from_department=bool(skill.department_id))
            if result.ok:
                assigned.append(result.data.id)
        return ServiceResult.success({"employeeId": employee.id, "assignedSkillIds": assigned, "count": len(assigned)})

    @staticmethod
    def assign_all_department_skills(context):
        employees = EmployeeProfile.objects.filter(tenant=context.tenant, status=EmployeeProfile.STATUS_ACTIVE, is_active=True)
        rows = []
        for employee in employees:
            rows.append(EmployeeLifecycleService.assign_department_skills(context, employee).data)
        return ServiceResult.success({"count": len(rows), "employees": rows})

    @staticmethod
    def complete_onboarding(context, employee_id):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee not found."}, status_code=404)
        employee.onboarding_completed = True
        employee.updated_by = context.actor
        employee.save(update_fields=["onboarding_completed", "updated_by", "updated_at"])
        return ServiceResult.success(employee)

    @staticmethod
    def save_timezone(context, employee_id, timezone_name):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee not found."}, status_code=404)
        employee.timezone_name = timezone_name
        employee.updated_by = context.actor
        employee.save(update_fields=["timezone_name", "updated_by", "updated_at"])
        return ServiceResult.success(employee)


class LeaveWalletService:
    @staticmethod
    def get_or_create_policy(context):
        policy, _created = LeavePolicy.objects.get_or_create(
            tenant=context.tenant,
            workspace=context.workspace,
            name="Default",
            defaults={"leaves_per_month": 2.25, "created_by": context.actor, "updated_by": context.actor},
        )
        return policy

    @staticmethod
    def accrue_for_employee(context, employee, policy=None, amount=None, reason="Monthly leave accrual"):
        policy = policy or LeaveWalletService.get_or_create_policy(context)
        amount = Decimal(str(amount)) if amount is not None else policy.leaves_per_month
        balance, _created = LeaveBalance.objects.get_or_create(
            tenant=context.tenant,
            workspace=context.workspace or employee.workspace,
            employee=employee,
            policy=policy,
            defaults={"created_by": context.actor, "updated_by": context.actor},
        )
        balance.available += amount
        balance.accrued += amount
        balance.save(update_fields=["available", "accrued", "updated_at"])
        employee.leaves_wallet = balance.available
        employee.leaves_per_month = policy.leaves_per_month
        employee.save(update_fields=["leaves_wallet", "leaves_per_month", "updated_at"])
        transaction = LeaveTransaction.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or employee.workspace,
            balance=balance,
            transaction_type="Accrual",
            amount=amount,
            reason=reason,
            created_by=context.actor,
            updated_by=context.actor,
        )
        return ServiceResult.success(transaction, status_code=201)

    @staticmethod
    def update_all_wallets(context, amount=None):
        policy = LeaveWalletService.get_or_create_policy(context)
        transactions = []
        for employee in EmployeeProfile.objects.filter(tenant=context.tenant, status=EmployeeProfile.STATUS_ACTIVE, is_active=True):
            result = LeaveWalletService.accrue_for_employee(context, employee, policy=policy, amount=amount)
            if result.ok:
                transactions.append(result.data.id)
        return ServiceResult.success({"count": len(transactions), "transactionIds": transactions})


class UserWorkflowService:
    @staticmethod
    def submit_effort_report(context, employee_id, report_month, report_year, effort_percent, project_reference="", metadata=None):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee not found."}, status_code=404)
        report = UserEffortReport.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or employee.workspace,
            employee=employee,
            report_month=report_month,
            report_year=report_year,
            effort_percent=effort_percent,
            project_reference=project_reference,
            metadata=metadata or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        OutboxService.publish(context, "UserEffortReport", report.id, "EffortReportSubmitted", {"employeeId": employee.id})
        return ServiceResult.success(report, status_code=201)

    @staticmethod
    def create_effort_report_reminders(context, report_month=None, report_year=None):
        now = timezone.localdate()
        report_month = report_month or now.month
        report_year = report_year or now.year
        employees = EmployeeProfile.objects.filter(tenant=context.tenant, status=EmployeeProfile.STATUS_ACTIVE, is_active=True)
        fixed_pay_employee_ids = PayProfile.objects.filter(tenant=context.tenant, pay_type__iexact="Fixed").values_list("employee_id", flat=True)
        employees = employees.filter(id__in=fixed_pay_employee_ids)
        event_ids = []
        for employee in employees:
            exists = UserEffortReport.objects.filter(tenant=context.tenant, employee=employee, report_month=report_month, report_year=report_year).exists()
            if exists:
                continue
            event = OutboxService.publish(
                context,
                "EmployeeProfile",
                employee.id,
                "EffortReportReminderCreated",
                {"employeeId": employee.id, "month": report_month, "year": report_year},
            )
            event_ids.append(event.id)
        return ServiceResult.success({"count": len(event_ids), "eventIds": event_ids})

    @staticmethod
    def create_daily_activity_reminders(context, reminder_type="EOD"):
        event_ids = []
        for employee in EmployeeProfile.objects.filter(tenant=context.tenant, status=EmployeeProfile.STATUS_ACTIVE, is_active=True):
            event = OutboxService.publish(
                context,
                "EmployeeProfile",
                employee.id,
                "DailyActivityReminderCreated",
                {"employeeId": employee.id, "reminderType": reminder_type},
            )
            event_ids.append(event.id)
        return ServiceResult.success({"count": len(event_ids), "eventIds": event_ids})

    @staticmethod
    def submit_resignation(context, employee_id, reason, last_working_day=None):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee not found."}, status_code=404)
        resignation = ResignationRequest.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or employee.workspace,
            employee=employee,
            reason=reason,
            last_working_day=last_working_day,
            created_by=context.actor,
            updated_by=context.actor,
        )
        OutboxService.publish(context, "ResignationRequest", resignation.id, "ResignationSubmitted", {"employeeId": employee.id})
        return ServiceResult.success(resignation, status_code=201)

    @staticmethod
    def approve_resignation(context, resignation_id, last_working_day=None):
        resignation = ResignationRequest.objects.filter(tenant=context.tenant, id=resignation_id).select_related("employee").first()
        if not resignation:
            return ServiceResult.failure({"resignation": "Resignation request not found."}, status_code=404)
        resignation.status = "Approved"
        resignation.approved_by = context.actor
        resignation.approved_at = timezone.now()
        if last_working_day:
            resignation.last_working_day = last_working_day
        resignation.save(update_fields=["status", "approved_by", "approved_at", "last_working_day", "updated_at"])
        EmployeeLifecycleService.change_status(context, resignation.employee_id, EmployeeProfile.STATUS_EXITED, reason="Resignation approved", effective_from=resignation.last_working_day)
        OutboxService.publish(context, "ResignationRequest", resignation.id, "ResignationApproved", {"employeeId": resignation.employee_id})
        return ServiceResult.success(resignation)


class InterviewSyncService:
    @staticmethod
    def sync_interns(context, employee_id=None, dry_run=True, send_links=False, client=None, mode="sync"):
        from Backend.Apps.Users.interviewgod import InterviewGodService

        return InterviewGodService.run_scheduler(context, employee_id=employee_id, mode=mode, dry_run=dry_run, send_links=send_links, client=client)


class PaymentSyncService:
    @staticmethod
    def request_payment_status_sync(context):
        event_ids = []
        payments = EmployeePaymentSnapshot.objects.filter(tenant=context.tenant).exclude(payout_id="").exclude(payment_status__iexact="processed")
        for payment in payments:
            event = OutboxService.publish(context, "EmployeePaymentSnapshot", payment.id, "PaymentStatusSyncRequested", {"payoutId": payment.payout_id})
            event_ids.append(event.id)
        return ServiceResult.success({"count": len(event_ids), "eventIds": event_ids})


class HRMSDashboardService:
    @staticmethod
    def summarize(context):
        employees = EmployeeProfile.objects.filter(tenant=context.tenant, is_active=True)
        by_status = list(employees.values("status").annotate(count=models.Count("id")).order_by("status"))
        by_department = list(employees.values("department__name").annotate(count=models.Count("id")).order_by("department__name"))
        open_resignations = ResignationRequest.objects.filter(tenant=context.tenant, status="Submitted").count()
        open_bench_periods = BenchPeriod.objects.filter(tenant=context.tenant, ended_on__isnull=True).count()
        return ServiceResult.success(
            {
                "headcount": employees.count(),
                "byStatus": by_status,
                "byDepartment": by_department,
                "openResignations": open_resignations,
                "openBenchPeriods": open_bench_periods,
            }
        )
