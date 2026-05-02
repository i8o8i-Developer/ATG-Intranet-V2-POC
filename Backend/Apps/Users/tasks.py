from celery import shared_task

from Backend.Apps.Users.services import InterviewSyncService, LeaveWalletService, PaymentSyncService, PayrollExportService, UserWorkflowService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


def _context(tenant_id, workspace_id=None):
    tenant = Tenant.objects.get(id=tenant_id)
    workspace = Workspace.objects.filter(id=workspace_id, tenant=tenant).first() if workspace_id else None
    return TenantContext(tenant=tenant, workspace=workspace, source="Celery")


@shared_task
def update_leave_wallets(tenant_id, workspace_id=None):
    return LeaveWalletService.update_all_wallets(_context(tenant_id, workspace_id)).data


@shared_task
def send_monthly_effort_report_notifications(tenant_id, workspace_id=None, report_month=None, report_year=None):
    return UserWorkflowService.create_effort_report_reminders(_context(tenant_id, workspace_id), report_month=report_month, report_year=report_year).data


@shared_task
def send_daily_activity_notifications(tenant_id, workspace_id=None, reminder_type="EOD"):
    return UserWorkflowService.create_daily_activity_reminders(_context(tenant_id, workspace_id), reminder_type=reminder_type).data


@shared_task
def sync_intern_interviews(tenant_id, workspace_id=None, dry_run=True, send_links=False):
    return InterviewSyncService.sync_interns(_context(tenant_id, workspace_id), dry_run=dry_run, send_links=send_links).data


@shared_task
def sync_payments(tenant_id, workspace_id=None):
    return PaymentSyncService.request_payment_status_sync(_context(tenant_id, workspace_id)).data


@shared_task(bind=True)
def generate_payroll_excel_task(self, tenant_id, workspace_id=None, report_month=None, report_year=None, pay_type=""):
    context = _context(tenant_id, workspace_id)
    self.update_state(state="PROGRESS", meta={"status": "Building Payroll Export..."})
    result = PayrollExportService.generate_excel(context, report_month=report_month, report_year=report_year, pay_type=pay_type)
    if not result.ok:
        raise RuntimeError(str(result.errors))
    return result.data
