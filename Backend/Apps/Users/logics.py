from Backend.Apps.Users.models import EmployeePaymentSnapshot, EmployeeProfile
from Backend.Apps.Users.utils import summarize_effort, summarize_headcount, summarize_payments
from Backend.EnterpriseCore.services import TenantContext


def flatten_leave(leaves):
    if not leaves:
        return []
    flattened = []
    for leave in leaves:
        if isinstance(leave, (list, tuple, set)):
            flattened.extend(flatten_leave(leave))
        else:
            flattened.append(leave)
    return flattened


def get_user_issues(employee, status=""):
    payload = employee.profile_payload or {}
    issues = payload.get("issues", [])
    if status:
        issues = [issue for issue in issues if str(issue.get("status", "")).lower() == status.lower()]
    return issues


def calculate_payroll(employee, month=None, year=None):
    from Backend.Apps.FinanceAndPayroll.services import PayrollCalculationService

    context = TenantContext(tenant=employee.tenant, workspace=employee.workspace, source="UsersLogic")
    return PayrollCalculationService.calculate_for_employee(context, employee.id, month=month, year=year).data


def new_calculate_payroll(employee, month=None, year=None):
    return calculate_payroll(employee, month=month, year=year)


def get_previous_payment_data(employee, month, year):
    return list(
        EmployeePaymentSnapshot.objects.filter(tenant=employee.tenant, employee=employee, year__lte=year)
        .exclude(month=month, year=year)
        .order_by("-year", "-month")
        .values("month", "year", "normal_pay", "bonus", "deduction", "bounty", "payment_status", "payout_id", "utr_number")[:12]
    )


def payroll_context_for_employee(employee_id, tenant):
    employee = EmployeeProfile.objects.filter(tenant=tenant, id=employee_id).first()
    if not employee:
        return {"employee": "Employee not found."}
    return {
        "headcount": summarize_headcount(tenant),
        "effort": summarize_effort(tenant),
        "payments": summarize_payments(tenant),
        "payroll": calculate_payroll(employee),
    }
