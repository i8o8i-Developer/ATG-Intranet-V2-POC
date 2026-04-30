from Backend.Apps.TasksDashboard.services import ClickUpSyncService


def request_data_with_rate_limit(url, headers=None):
    return {"url": url, "headers": headers or {}, "dry_run": True}


def get_project_if_exists(project_name):
    return {"project_name": project_name, "exists": False}


def task_check_and_store(context, task, project_mapping_id=None):
    return ClickUpSyncService.sync_tasks(context, [task], project_mapping_id=project_mapping_id)


def get_clickup_data(context, tasks=None, project_mapping_id=None):
    return ClickUpSyncService.sync_tasks(context, tasks or [], project_mapping_id=project_mapping_id)