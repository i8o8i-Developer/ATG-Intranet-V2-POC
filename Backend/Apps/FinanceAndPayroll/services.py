from decimal import Decimal

from django.db import models
from django.utils import timezone

from Backend.Apps.FinanceAndPayroll.models import PaymentOrder, PaymentWebhookEvent, PayrollLineItem, PayrollRun, PayoutExecution
from Backend.Apps.FinanceAndPayroll.provider import RazorpayClient
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class PayrollRunService:
    @staticmethod
    def recalculate_totals(context, payroll_run_id):
        payroll_run = PayrollRun.objects.filter(tenant=context.tenant, id=payroll_run_id).first()
        if not payroll_run:
            return ServiceResult.failure({"payrollRun": "Payroll run not found."}, status_code=404)
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
            return ServiceResult.failure({"payrollRun": "Payroll run not found."}, status_code=404)
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
            return ServiceResult.failure({"employee": "Employee not found."}, status_code=404)
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
            return ServiceResult.failure({"payment": "Employee payment snapshot not found."}, status_code=404)
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
        if live:
            bank_account = EmployeeBankAccount.objects.filter(tenant=context.tenant, employee=snapshot.employee).order_by("-created_at").first()
            if not bank_account or not bank_account.fund_account_reference:
                return ServiceResult.failure({"bankAccount": "Fund account reference is required for live payout."}, status_code=400)
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
            return ServiceResult.failure({"payout": "Payout execution not found."}, status_code=404)
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
