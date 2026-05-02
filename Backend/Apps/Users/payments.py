import uuid

from Backend.Apps.Users.models import EmployeePaymentSnapshot, EmployeeProfile
from Backend.EnterpriseCore.services import TenantContext


def sanitize_narration(narration):
    return " ".join(str(narration or "").replace("\n", " ").split())[:30]


def generate_idempotency_key():
    return str(uuid.uuid4())


def start_payment(context, employee_id, month, year, amount=None, bonus=0, bounty=0, deduction=0, pay_for="ATG", notes="", live=False, provider=None):
    from Backend.Apps.FinanceAndPayroll.services import PayoutService

    employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
    if not employee:
        return {"ok": False, "errors": {"employee": "Employee Not Found."}}
    snapshot, _created = EmployeePaymentSnapshot.objects.update_or_create(
        tenant=context.tenant,
        workspace=context.workspace or employee.workspace,
        employee=employee,
        month=month,
        year=year,
        defaults={
            "normal_pay": amount or 0,
            "bonus": bonus,
            "bounty": bounty,
            "deduction": deduction,
            "notes": notes,
            "metadata": {"pay_for": pay_for},
        },
    )
    result = PayoutService.request_employee_payout(context, snapshot.id, live=live, provider=provider)
    return {"ok": result.ok, "data": result.data, "errors": result.errors}


def new_start_payment(context, employee_id, month, year, **kwargs):
    return start_payment(context, employee_id, month, year, **kwargs)


def startpayment(user_id, entered_bonus, mode, month_no, year_no, normal_pay=0, bounty=0, task_count=0, bug_ids="", payNote="", payFor="ATG", customPay=0):
    employee = EmployeeProfile.objects.filter(user_id=user_id).select_related("tenant", "workspace").first()
    if not employee:
        return {"msg": "Employee not found", "payment_status": "Failed"}
    context = TenantContext(tenant=employee.tenant, workspace=employee.workspace, source="LegacyPaymentWrapper")
    result = start_payment(context, employee.id, month_no, year_no, amount=customPay or normal_pay, bonus=entered_bonus, bounty=bounty, pay_for=payFor, notes=payNote)
    return {"msg": "Payment queued", "payment_status": "Queued", "result": result}


def newstartpayment(user_id, entered_bonus, month_no, year_no, normal_pay=0, bounty=0, task_count=0, bug_ids="", payNote="", customPay=0):
    return startpayment(user_id, entered_bonus, "NEFT", month_no, year_no, normal_pay=normal_pay, bounty=bounty, task_count=task_count, bug_ids=bug_ids, payNote=payNote, customPay=customPay)
