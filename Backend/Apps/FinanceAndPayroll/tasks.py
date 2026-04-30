from Backend.Apps.FinanceAndPayroll.services import PaymentOrderService, PayrollCalculationService, PayrollRunService, PayoutService


def recalculate_payroll_run(context, payroll_run_id):
    return PayrollRunService.recalculate_totals(context, payroll_run_id)


def calculate_employee_payroll(context, employee_id, month=None, year=None):
    return PayrollCalculationService.calculate_for_employee(context, employee_id, month=month, year=year)


def create_payment_order(context, amount, **kwargs):
    return PaymentOrderService.create_order(context, amount, **kwargs)


def request_employee_payout(context, payment_snapshot_id, live=False):
    return PayoutService.request_employee_payout(context, payment_snapshot_id, live=live)
