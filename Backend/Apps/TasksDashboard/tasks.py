from Backend.Apps.TasksDashboard.services import ClickUpSyncService, EODService


def fetch_clickup_data(context, tasks=None, project_mapping_id=None):
    return ClickUpSyncService.sync_tasks(context, tasks or [], project_mapping_id=project_mapping_id)


def sync_eod_report_to_slack(context, status_date=None):
    return EODService.deliver_daily_summary(context, status_date=status_date)


def send_department_daily_eod_summary(context, status_date=None):
    return EODService.deliver_daily_summary(context, status_date=status_date)


def send_missing_eod_reminders(context, status_date=None):
    return EODService.missing_eod_report(context, status_date=status_date)