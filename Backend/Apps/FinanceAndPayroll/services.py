from calendar import monthrange
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from Backend.Apps.FinanceAndPayroll.models import BankAccount, PaymentOrder, PaymentWebhookEvent, PayrollLineItem, PayrollRun, PayoutExecution
from Backend.Apps.FinanceAndPayroll.provider import RazorpayClient
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class PayrollRunService:
    @staticmethod
    def recalculate_totals(context, payroll_run_id):
        payroll_run = PayrollRun.objects.filter(tenant=context.tenant, id=payroll_run_id).first()
        if not payroll_run:
            return ServiceResult.failure({"payrollRun": "Payroll Run Not Found."}, status_code=404)
        line_items = PayrollLineItem.objects.filter(tenant=context.tenant, payroll_run=payroll_run)
        payroll_run.gross_amount = sum(item.gross_amount for item in line_items)
        payroll_run.deduction_amount = sum(item.deduction_amount for item in line_items)
        payroll_run.net_amount = sum(item.net_amount for item in line_items)
        payroll_run.updated_by = context.actor
        payroll_run.save(update_fields=["gross_amount", "deduction_amount", "net_amount", "updated_by", "updated_at"])
        return ServiceResult.success(payroll_run)

    @staticmethod
    def submit_for_approval(context, payroll_run_id):
        payroll_run = PayrollRun.objects.filter(tenant=context.tenant, id=payroll_run_id).first()
        if not payroll_run:
            return ServiceResult.failure({"payrollRun": "Payroll Run Not Found."}, status_code=404)
        payroll_run.status = "PendingApproval"
        payroll_run.updated_by = context.actor
        payroll_run.save(update_fields=["status", "updated_by", "updated_at"])
        OutboxService.publish(context, "PayrollRun", payroll_run.id, "PayrollRunSubmitted", {"payrollRunId": payroll_run.id})
        return ServiceResult.success(payroll_run)


class PayrollCalculationService:
    @staticmethod
    def _decimal(value):
        return Decimal(str(value or 0))

    @staticmethod
    def calculate_for_employee(context, employee_id, month=None, year=None):
        from Backend.Apps.Users.models import EmployeeBankAccount, EmployeePaymentSnapshot, EmployeeProfile, PayProfile, UserEffortReport

        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).select_related("department", "position", "user").first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee Not Found."}, status_code=404)
        now = timezone.localdate()
        month = int(month or now.month)
        year = int(year or now.year)
        pay_profile = PayProfile.objects.filter(tenant=context.tenant, employee=employee).order_by("-effective_at").first()
        snapshot = EmployeePaymentSnapshot.objects.filter(tenant=context.tenant, employee=employee, month=month, year=year).first()
        effort = UserEffortReport.objects.filter(tenant=context.tenant, employee=employee, report_month=month, report_year=year).aggregate(total=models.Sum("effort_percent"))["total"] or Decimal("0")
        base_pay = PayrollCalculationService._decimal(pay_profile.base_pay if pay_profile else 0)
        pay_per_task = PayrollCalculationService._decimal(pay_profile.pay_per_task if pay_profile else 0)
        task_count = snapshot.task_count if snapshot else 0
        normal_pay = snapshot.normal_pay if snapshot else base_pay + (pay_per_task * task_count)
        bonus = snapshot.bonus if snapshot else Decimal("0")
        bounty = snapshot.bounty if snapshot else Decimal("0")
        deduction = snapshot.deduction if snapshot else Decimal("0")
        gross = normal_pay + bonus + bounty
        net = gross - deduction
        bank_account = EmployeeBankAccount.objects.filter(tenant=context.tenant, employee=employee).order_by("-created_at").first()
        return ServiceResult.success(
            {
                "employee": employee.id,
                "employeeName": employee.display_name,
                "month": month,
                "year": year,
                "payType": pay_profile.pay_type if pay_profile else "",
                "normalPay": normal_pay,
                "bonus": bonus,
                "bounty": bounty,
                "deduction": deduction,
                "grossPay": gross,
                "netPay": net,
                "taskCount": task_count,
                "effortPercent": effort,
                "bankDetailsExists": bool(bank_account),
                "paymentData": {
                    "manager_status": snapshot.manager_status if snapshot else "Pending",
                    "finance_manager_status": snapshot.finance_status if snapshot else "Pending",
                    "payment_status": snapshot.payment_status if snapshot else "",
                    "payout_id": snapshot.payout_id if snapshot else "",
                    "utr_number": snapshot.utr_number if snapshot else "",
                },
            }
        )

    @staticmethod
    def previous_payment_data(context, employee_id, month=None, year=None, limit=12):
        from Backend.Apps.Users.models import EmployeePaymentSnapshot

        queryset = EmployeePaymentSnapshot.objects.filter(tenant=context.tenant, employee_id=employee_id).order_by("-year", "-month")
        if month and year:
            queryset = queryset.exclude(month=month, year=year)
        rows = queryset.values("month", "year", "normal_pay", "bonus", "deduction", "bounty", "payment_status", "payout_id", "utr_number")[: int(limit)]
        return ServiceResult.success(list(rows))


class FinanceLegacyService:
    MONTH_NAMES = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    @staticmethod
    def _decimal(value):
        return Decimal(str(value or 0))

    @staticmethod
    def _int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _actor_profile(context):
        from Backend.Apps.Users.models import EmployeeProfile

        actor = getattr(context, "actor", None)
        if not actor or not context.tenant:
            return None
        return EmployeeProfile.objects.filter(tenant=context.tenant, user=actor).select_related("department", "workspace", "user").order_by("id").first()

    @staticmethod
    def _resolve_employee(context, employee_id=None, user_id=None):
        from Backend.Apps.Users.models import EmployeeProfile

        queryset = EmployeeProfile.objects.filter(tenant=context.tenant).select_related("user", "department", "workspace")
        if employee_id:
            return queryset.filter(id=employee_id).first()
        if user_id:
            return queryset.filter(user_id=user_id).first()
        return FinanceLegacyService._actor_profile(context)

    @staticmethod
    def _mask_account_number(account_number):
        digits = str(account_number or "").strip()
        if len(digits) <= 4:
            return digits
        return f"{'*' * max(len(digits) - 4, 0)}{digits[-4:]}"

    @classmethod
    def resolve_period(cls, month=None, year=None, month_name=""):
        today = timezone.localdate()
        if month:
            return cls._int(month, today.month), cls._int(year, today.year)
        normalized_month = str(month_name or "").strip()
        if normalized_month in cls.MONTH_NAMES:
            month_number = cls.MONTH_NAMES.index(normalized_month) + 1
            resolved_year = cls._int(year, today.year)
            if not year and today.month in {1, 2} and month_number in {11, 12}:
                resolved_year -= 1
            return month_number, resolved_year
        return today.month, cls._int(year, today.year)

    @staticmethod
    def _api_keys_available():
        return bool(getattr(settings, "RAZORPAY_KEY", "") and getattr(settings, "RAZORPAY_SECRET_KEY", ""))

    @staticmethod
    def _department_scope(context, manager_scope=False, domain_name=""):
        from Backend.Apps.Users.models import Department

        departments = Department.objects.filter(tenant=context.tenant, is_archived=False).select_related("domain").order_by("name")
        if domain_name:
            departments = departments.filter(domain__name__iexact=domain_name)
        if manager_scope:
            actor_profile = FinanceLegacyService._actor_profile(context)
            if not actor_profile:
                return Department.objects.none()
            department_ids = set(
                actor_profile.direct_reports.exclude(department__isnull=True).values_list("department_id", flat=True)
            )
            if actor_profile.department_id:
                department_ids.add(actor_profile.department_id)
            departments = departments.filter(id__in=list(department_ids)) if department_ids else Department.objects.none()
        return departments

    @staticmethod
    def _filter_employees(context, departments=None, search="", month=None, year=None, include_approved=False):
        from Backend.Apps.Users.models import EmployeePaymentSnapshot, EmployeeProfile

        month, year = FinanceLegacyService.resolve_period(month=month, year=year)
        last_date = timezone.datetime(year, month, monthrange(year, month)[1]).date()
        employees = EmployeeProfile.objects.filter(tenant=context.tenant, user__is_active=True, status=EmployeeProfile.STATUS_ACTIVE).select_related("user", "department")
        employees = employees.filter(Q(joined_on__isnull=True) | Q(joined_on__lte=last_date))
        if departments is not None:
            employees = employees.filter(department__in=departments)
        if search:
            employees = employees.filter(
                Q(display_name__icontains=search)
                | Q(user__username__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )
        snapshots = EmployeePaymentSnapshot.objects.filter(tenant=context.tenant, month=month, year=year)
        if not include_approved:
            employees = employees.exclude(id__in=snapshots.values_list("employee_id", flat=True))
        return employees.order_by("display_name"), {item.employee_id: item for item in snapshots}

    @staticmethod
    def legacy_dashboard(context, month=None, year=None, month_name="", search="", selected_departments=None, show_approved=False, manager_scope=False, domain_name="", flag_name=""):
        from Backend.Apps.Users.models import PayProfile

        month, year = FinanceLegacyService.resolve_period(month=month, year=year, month_name=month_name)
        departments = FinanceLegacyService._department_scope(context, manager_scope=manager_scope, domain_name=domain_name)
        selected_departments = selected_departments or []
        scoped_departments = departments
        if selected_departments:
            numeric_ids = [int(item) for item in selected_departments if str(item).isdigit()]
            named_ids = [str(item).strip() for item in selected_departments if not str(item).isdigit()]
            if numeric_ids:
                scoped_departments = scoped_departments.filter(id__in=numeric_ids)
            if named_ids:
                scoped_departments = scoped_departments.filter(name__in=named_ids)
        employees, snapshots = FinanceLegacyService._filter_employees(
            context,
            departments=scoped_departments,
            search=search,
            month=month,
            year=year,
            include_approved=show_approved,
        )
        rows = []
        for employee in employees:
            pay_profile = PayProfile.objects.filter(tenant=context.tenant, employee=employee).order_by("-effective_at").first()
            snapshot = snapshots.get(employee.id)
            rows.append(
                {
                    "id": employee.id,
                    "user_id": employee.user_id,
                    "username": employee.user.username,
                    "display_name": employee.display_name,
                    "department": employee.department.name if employee.department else "",
                    "employment_type": employee.employment_type,
                    "base_pay": pay_profile.base_pay if pay_profile else Decimal("0"),
                    "pay_type": pay_profile.pay_type if pay_profile else "",
                    "pay_per_task": pay_profile.pay_per_task if pay_profile else Decimal("0"),
                    "has_payment_snapshot": bool(snapshot),
                    "payment_status": snapshot.payment_status if snapshot else "",
                    "manager_status": snapshot.manager_status if snapshot else "Pending",
                    "finance_status": snapshot.finance_status if snapshot else "Pending",
                }
            )
        rows = sorted(rows, key=lambda item: (0 if item.get("employment_type") == "Full-Time" else 1, -(FinanceLegacyService._decimal(item.get("base_pay"))), item.get("username", "")))
        result = {
            "departments": [{"id": department.id, "name": department.name} for department in departments],
            "selected_departments": [str(item) for item in selected_departments],
            "search_query": search,
            "show_approved": show_approved,
            "pay_month": "current",
            "month": month,
            "month_name": FinanceLegacyService.MONTH_NAMES[month - 1],
            "year": year,
            "user_list": rows,
            "api_keys": FinanceLegacyService._api_keys_available(),
        }
        if flag_name:
            result[flag_name] = True
        return ServiceResult.success(result)

    @staticmethod
    def legacy_payment_records(context, month=None, year=None):
        from Backend.Apps.Users.models import EmployeeBankAccount, EmployeePaymentSnapshot

        month, year = FinanceLegacyService.resolve_period(month=month, year=year)
        snapshots = EmployeePaymentSnapshot.objects.filter(tenant=context.tenant, month=month, year=year).select_related("employee", "employee__user")
        bank_accounts = EmployeeBankAccount.objects.filter(tenant=context.tenant).select_related("employee", "employee__user")
        return ServiceResult.success(
            {
                "month": month,
                "year": year,
                "filled_data": [
                    {
                        "id": snapshot.id,
                        "employee": snapshot.employee_id,
                        "username": snapshot.employee.user.username,
                        "manager_status": snapshot.manager_status,
                        "finance_status": snapshot.finance_status,
                        "payment_status": snapshot.payment_status,
                        "normal_pay": snapshot.normal_pay,
                        "bonus": snapshot.bonus,
                        "bounty": snapshot.bounty,
                        "deduction": snapshot.deduction,
                        "task_count": snapshot.task_count,
                        "payout_id": snapshot.payout_id,
                        "utr_number": snapshot.utr_number,
                    }
                    for snapshot in snapshots
                ],
                "bank_data": [
                    {
                        "id": account.id,
                        "employee": account.employee_id,
                        "username": account.employee.user.username,
                        "ifsc_code": account.ifsc_code,
                        "upi_id": account.upi_id,
                        "verification_status": account.verification_status,
                    }
                    for account in bank_accounts
                ],
            }
        )

    @staticmethod
    def upsert_bank_details(context, employee_id=None, user_id=None, account_number="", ifsc_code="", upi_id=""):
        from Backend.Apps.Users.models import EmployeeBankAccount

        employee = FinanceLegacyService._resolve_employee(context, employee_id=employee_id, user_id=user_id)
        if not employee:
            return ServiceResult.failure({"employee": "Employee not found."}, status_code=404)
        masked_number = FinanceLegacyService._mask_account_number(account_number)

        user_account = EmployeeBankAccount.objects.filter(tenant=context.tenant, employee=employee).order_by("-id").first()
        if user_account:
            user_account.masked_account_number = masked_number
            user_account.ifsc_code = ifsc_code
            user_account.upi_id = upi_id
            user_account.verification_status = "Verified"
            user_account.metadata = {**user_account.metadata, "legacy_account_number": account_number}
            user_account.updated_by = context.actor
            user_account.save(update_fields=["masked_account_number", "ifsc_code", "upi_id", "verification_status", "metadata", "updated_by", "updated_at"])
        else:
            user_account = EmployeeBankAccount.objects.create(
                tenant=context.tenant,
                workspace=context.workspace or employee.workspace,
                employee=employee,
                account_holder_name=employee.display_name,
                masked_account_number=masked_number,
                ifsc_code=ifsc_code,
                upi_id=upi_id,
                verification_status="Verified",
                metadata={"legacy_account_number": account_number},
                created_by=context.actor,
                updated_by=context.actor,
            )

        finance_account = BankAccount.objects.filter(tenant=context.tenant, employee=employee).order_by("-id").first()
        if finance_account:
            finance_account.account_holder_name = employee.display_name
            finance_account.masked_account_number = masked_number
            finance_account.ifsc_code = ifsc_code
            finance_account.verification_status = "Verified"
            finance_account.metadata = {**finance_account.metadata, "upi_id": upi_id, "legacy_account_number": account_number}
            finance_account.updated_by = context.actor
            finance_account.save(update_fields=["account_holder_name", "masked_account_number", "ifsc_code", "verification_status", "metadata", "updated_by", "updated_at"])
        else:
            finance_account = BankAccount.objects.create(
                tenant=context.tenant,
                workspace=context.workspace or employee.workspace,
                employee=employee,
                account_holder_name=employee.display_name,
                masked_account_number=masked_number,
                ifsc_code=ifsc_code,
                verification_status="Verified",
                metadata={"upi_id": upi_id, "legacy_account_number": account_number},
                created_by=context.actor,
                updated_by=context.actor,
            )

        return ServiceResult.success(
            {
                "message": "Bank Details Saved Successfully.",
                "employee": employee.id,
                "bank_details": {
                    "masked_account_number": user_account.masked_account_number,
                    "ifsc_code": user_account.ifsc_code,
                    "upi_id": user_account.upi_id,
                    "verification_status": user_account.verification_status,
                },
                "api": FinanceLegacyService._api_keys_available(),
            },
            status_code=201,
        )

    @staticmethod
    def bank_details_summary(context, employee_id=None, user_id=None):
        from Backend.Apps.Users.models import EmployeeBankAccount

        employee = FinanceLegacyService._resolve_employee(context, employee_id=employee_id, user_id=user_id)
        if not employee:
            return ServiceResult.failure({"employee": "Employee Not Found."}, status_code=404)
        accounts = EmployeeBankAccount.objects.filter(tenant=context.tenant, employee=employee)
        return ServiceResult.success(
            {
                "Bankdetails": True,
                "api": FinanceLegacyService._api_keys_available(),
                "bank_details": [
                    {
                        "id": account.id,
                        "masked_account_number": account.masked_account_number,
                        "ifsc_code": account.ifsc_code,
                        "upi_id": account.upi_id,
                        "verification_status": account.verification_status,
                    }
                    for account in accounts
                ],
            }
        )

    @staticmethod
    def _get_ptrc_deduction(normal_pay, bonus):
        total = (normal_pay or 0) + (bonus or 0)
        return Decimal("200") if total >= Decimal("25000") else Decimal("0")

    @staticmethod
    def _generate_payslip(context, employee, month, year, normal_pay, bonus, bounty, deduction):
        from Backend.Apps.FinanceAndPayroll.models import PayPeriod, PayrollLineItem, PayrollRun, PayslipDocument
        period_name = f"{month}_{year}"
        pay_period, _ = PayPeriod.objects.get_or_create(
            tenant=context.tenant,
            name=period_name,
            defaults={
                "workspace": context.workspace or employee.workspace,
                "starts_on": timezone.now().replace(month=month, day=1).date(),
                "ends_on": timezone.now().replace(month=month, day=28).date(),
                "status": "Closed",
                "created_by": context.actor,
            },
        )
        run, _ = PayrollRun.objects.get_or_create(
            tenant=context.tenant,
            pay_period=pay_period,
            defaults={
                "workspace": context.workspace or employee.workspace,
                "status": "Approved",
                "gross_amount": Decimal("0"),
                "deduction_amount": Decimal("0"),
                "net_amount": Decimal("0"),
                "created_by": context.actor,
            },
        )
        gross = (normal_pay or 0) + (bonus or 0) + (bounty or 0)
        net = gross - (deduction or 0)
        line, _ = PayrollLineItem.objects.get_or_create(
            tenant=context.tenant,
            payroll_run=run,
            employee=employee,
            defaults={
                "workspace": context.workspace or employee.workspace,
                "gross_amount": gross,
                "deduction_amount": deduction or 0,
                "net_amount": net,
                "status": "Paid",
            },
        )
        if not _:
            line.gross_amount = gross
            line.deduction_amount = deduction or 0
            line.net_amount = net
            line.status = "Paid"
            line.save(update_fields=["gross_amount", "deduction_amount", "net_amount", "status", "updated_at"])
        payslip, _ = PayslipDocument.objects.get_or_create(
            tenant=context.tenant,
            payroll_line_item=line,
            defaults={
                "workspace": context.workspace or employee.workspace,
                "storage_reference": f"payslip/{employee.employee_code}/{month}_{year}",
                "status": "Generated",
            },
        )
        return payslip

    @staticmethod
    def approve_payment(
        context,
        role="Finance",
        employee_id=None,
        user_id=None,
        month=None,
        year=None,
        bonus=0,
        normal_pay=0,
        bounty=0,
        task_count=0,
        bug_ids="",
        pay_note="",
        pay_for="ATG",
        custom_pay=False,
        live=False,
    ):
        from Backend.Apps.Users.models import EmployeePaymentSnapshot

        employee = FinanceLegacyService._resolve_employee(context, employee_id=employee_id, user_id=user_id)
        if not employee:
            return ServiceResult.failure({"employee": "Employee Not Found."}, status_code=404)
        month, year = FinanceLegacyService.resolve_period(month=month, year=year)
        total_bonus = FinanceLegacyService._decimal(bonus)
        total_normal_pay = FinanceLegacyService._decimal(normal_pay)
        total_bounty = FinanceLegacyService._decimal(bounty)
        ptrc = FinanceLegacyService._get_ptrc_deduction(total_normal_pay, total_bonus)
        task_count = FinanceLegacyService._int(task_count)
        snapshot = EmployeePaymentSnapshot.objects.filter(tenant=context.tenant, employee=employee, month=month, year=year).first()
        role_name = str(role or "Finance").strip().lower()

        if role_name == "manager" and snapshot and snapshot.manager_status == "Approved":
            return ServiceResult.success(
                {
                    "msg": "Already Approved For User ",
                    "user": employee.user.username,
                    "status": "Error",
                }
            )

        snapshot, _created = EmployeePaymentSnapshot.objects.update_or_create(
            tenant=context.tenant,
            employee=employee,
            month=month,
            year=year,
            defaults={
                "workspace": context.workspace or employee.workspace,
                "normal_pay": total_normal_pay,
                "bonus": total_bonus,
                "bounty": total_bounty,
                "deduction": ptrc,
                "task_count": task_count,
                "notes": pay_note or snapshot.notes if snapshot else pay_note,
                "metadata": {
                    **(snapshot.metadata if snapshot else {}),
                    "bug_ids": str(bug_ids or "")[:990],
                    "pay_for": pay_for or "ATG",
                    "custom_pay": bool(custom_pay),
                },
                "manager_status": "Approved" if role_name == "manager" else (snapshot.manager_status if snapshot else "Pending"),
                "finance_status": "Approved" if role_name != "manager" else (snapshot.finance_status if snapshot else "Pending"),
                "updated_by": context.actor,
            },
        )

        if role_name == "manager":
            return ServiceResult.success(
                {
                    "msg": "Payment Approved For ",
                    "user": employee.user.username,
                    "status": "Success",
                    "totalpay": total_normal_pay + total_bonus,
                }
            )

        payout_result = PayoutService.request_employee_payout(context, snapshot.id, live=live)
        if not payout_result.ok:
            return ServiceResult.success(
                {
                    "msg": payout_result.errors.get("bankAccount") or payout_result.errors.get("payment") or "Payment Error Occured",
                    "user": employee.user.username,
                    "status": "Error",
                    "totalpay": total_normal_pay + total_bonus - snapshot.deduction,
                },
                status_code=payout_result.status_code,
            )
        snapshot.refresh_from_db()
        return ServiceResult.success(
            {
                "msg": f"Payment Amount Is {snapshot.payment_status or 'Queued'} To ",
                "user": employee.user.username,
                "status": "Success",
                "payment_status": snapshot.payment_status,
                "payment_id": snapshot.payout_id,
                "totalpay": snapshot.normal_pay + snapshot.bonus + snapshot.bounty - snapshot.deduction,
            }
        )

    @staticmethod
    def project_finances(context, project_id):
        from Backend.Apps.Project.models import DeliveryMilestone, ProjectWorkspace, TeamAssignment
        from Backend.Apps.Users.models import PayProfile, UserEffortReport

        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"error": "Project Not Found"}, status_code=404)
        assignments = TeamAssignment.objects.filter(tenant=context.tenant, project=project, status="Active").select_related("employee", "employee__user")
        milestones = DeliveryMilestone.objects.filter(tenant=context.tenant, project=project)
        total_bounties = sum((FinanceLegacyService._decimal(item.bounty) for item in milestones), Decimal("0"))
        completed_bounties = sum((FinanceLegacyService._decimal(item.bounty) for item in milestones.filter(status__iexact="Completed")), Decimal("0"))
        total_budget_utilized = Decimal("0")
        details = []
        for assignment in assignments:
            employee = assignment.employee
            pay_profile = PayProfile.objects.filter(tenant=context.tenant, employee=employee).order_by("-effective_at").first()
            pay_type = pay_profile.pay_type if pay_profile else ""
            pay_per_task = FinanceLegacyService._decimal(pay_profile.pay_per_task if pay_profile else 0)
            base_pay = FinanceLegacyService._decimal(pay_profile.base_pay if pay_profile else 0)
            allocation = Decimal(str(assignment.allocation_percent or 0)) / Decimal("100")
            assigned_bounties = total_bounties * allocation
            completed = completed_bounties * allocation
            effort = UserEffortReport.objects.filter(
                tenant=context.tenant,
                employee=employee,
            ).filter(
                Q(project_reference=str(project.id)) | Q(project_reference=project.code) | Q(project_reference=project.name)
            ).order_by("-report_year", "-report_month", "-submitted_at").first()
            effort_percent = FinanceLegacyService._decimal(effort.effort_percent if effort else assignment.allocation_percent)
            if str(pay_type).lower() == "fixed":
                budget_assigned = (pay_per_task * assigned_bounties) + base_pay
                budget_utilized = budget_assigned * (effort_percent / Decimal("100"))
            else:
                budget_assigned = pay_per_task * assigned_bounties
                budget_utilized = pay_per_task * completed
            budget_left = budget_assigned - budget_utilized
            total_budget_utilized += budget_utilized
            details.append(
                {
                    "role": assignment.role,
                    "personnel": employee.user.username,
                    "pay_type": pay_type,
                    "pay_per_task": pay_per_task,
                    "bounties_assigned": assigned_bounties,
                    "completed": completed,
                    "budget_assigned": budget_assigned,
                    "budget_utilized": budget_utilized,
                    "budget_left": budget_left,
                }
            )
        total_budget = FinanceLegacyService._decimal(project.metadata.get("budget") or project.metadata.get("total_budget") or total_budget_utilized)
        return ServiceResult.success(
            {
                "id": project.id,
                "project_name": project.name,
                "total_budget": total_budget,
                "remaining_budget": total_budget - total_budget_utilized,
                "details": details,
            }
        )


class PaymentOrderService:
    @staticmethod
    def create_order(context, amount, currency="INR", receipt="", notes=None, employee_id=None, live=False, provider=None):
        amount = Decimal(str(amount or 0))
        order = PaymentOrder.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            employee_id=employee_id,
            amount=amount,
            currency=currency,
            receipt=receipt,
            notes=notes or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        if live:
            provider = provider or RazorpayClient()
            payload = provider.create_order(amount * 100, currency=currency, receipt=receipt or f"order-{order.id}", notes=notes or {})
            order.provider_order_id = payload.get("id", "")
            order.status = payload.get("status", "Created")
            order.response_payload = payload
            order.save(update_fields=["provider_order_id", "status", "response_payload", "updated_at"])
        OutboxService.publish(context, "PaymentOrder", order.id, "PaymentOrderCreated", {"amount": str(amount), "live": live})
        return ServiceResult.success(order, status_code=201)


class PayoutService:
    @staticmethod
    def request_employee_payout(context, payment_snapshot_id, live=False, provider=None):
        from Backend.Apps.Users.models import EmployeeBankAccount, EmployeePaymentSnapshot
        from Backend.Apps.Users.payments import generate_idempotency_key, sanitize_narration

        snapshot = EmployeePaymentSnapshot.objects.filter(tenant=context.tenant, id=payment_snapshot_id).select_related("employee").first()
        if not snapshot:
            return ServiceResult.failure({"payment": "Employee Payment Snapshot Not Found."}, status_code=404)
        amount = snapshot.normal_pay + snapshot.bonus + snapshot.bounty - snapshot.deduction
        execution = PayoutExecution.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or snapshot.workspace,
            provider="Razorpay",
            status="Queued",
            amount=amount,
            currency="INR",
            response_payload={"paymentSnapshotId": snapshot.id},
            created_by=context.actor,
            updated_by=context.actor,
            payroll_run_id=None,
        )
        snapshot.payment_status = execution.status
        snapshot.finance_status = "Approved"
        snapshot.payout_id = execution.external_id or f"queued-{execution.id}"
        snapshot.save(update_fields=["payment_status", "finance_status", "payout_id", "updated_at"])
        if live:
            bank_account = EmployeeBankAccount.objects.filter(tenant=context.tenant, employee=snapshot.employee).order_by("-created_at").first()
            if not bank_account or not bank_account.fund_account_reference:
                return ServiceResult.failure({"bankAccount": "Fund Account Reference Is Required For Live Payout."}, status_code=400)
            provider = provider or RazorpayClient()
            payload = provider.create_payout(
                bank_account.fund_account_reference,
                amount * 100,
                narration=sanitize_narration(snapshot.notes or "ATG Payment"),
                reference_id=f"payout-ref-{snapshot.employee.employee_code}-{snapshot.month}-{snapshot.year}",
                notes={"employee": snapshot.employee.employee_code, "month": snapshot.month, "year": snapshot.year},
                idempotency_key=generate_idempotency_key(),
            )
            execution.status = payload.get("status", "Queued")
            execution.external_id = payload.get("id", "")
            execution.response_payload = payload
            snapshot.payout_id = execution.external_id
            snapshot.payment_status = execution.status
            snapshot.utr_number = payload.get("utr", "") or snapshot.utr_number
            snapshot.save(update_fields=["payout_id", "payment_status", "utr_number", "updated_at"])
            execution.save(update_fields=["status", "external_id", "response_payload", "updated_at"])
        OutboxService.publish(context, "EmployeePaymentSnapshot", snapshot.id, "EmployeePayoutRequested", {"amount": str(amount), "live": live})
        return ServiceResult.success({"executionId": execution.id, "paymentSnapshotId": snapshot.id, "status": execution.status}, status_code=201)

    @staticmethod
    def sync_payout_status(context, payout_execution_id, provider_payload=None, provider=None):
        execution = PayoutExecution.objects.filter(tenant=context.tenant, id=payout_execution_id).first()
        if not execution:
            return ServiceResult.failure({"payout": "Payout Execution Not Found."}, status_code=404)
        payload = provider_payload or {}
        if not payload and execution.external_id:
            payload = (provider or RazorpayClient()).fetch_payout(execution.external_id)
        if payload:
            execution.status = payload.get("status", execution.status)
            execution.response_payload = {**execution.response_payload, "sync": payload}
            execution.save(update_fields=["status", "response_payload", "updated_at"])
            OutboxService.publish(context, "PayoutExecution", execution.id, "PayoutStatusSynced", {"status": execution.status})
        return ServiceResult.success(execution)


class PaymentWebhookService:
    @staticmethod
    def record_event(context, payload, signature="", raw_body=b"", provider=None):
        provider = provider or RazorpayClient()
        verified = provider.verify_signature(raw_body or payload, signature) if signature else False
        event = PaymentWebhookEvent.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            event_type=payload.get("event", "unknown") if isinstance(payload, dict) else "unknown",
            external_event_id=payload.get("id", "") if isinstance(payload, dict) else "",
            signature=signature,
            verified=verified,
            payload=payload if isinstance(payload, dict) else {"raw": str(payload)},
            processed_at=timezone.now(),
            created_by=context.actor,
            updated_by=context.actor,
        )
        OutboxService.publish(context, "PaymentWebhookEvent", event.id, "PaymentWebhookReceived", {"eventType": event.event_type, "verified": verified})
        return ServiceResult.success(event, status_code=201)
