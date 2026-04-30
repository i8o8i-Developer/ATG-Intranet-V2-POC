from Backend.Apps.Project.services import ProjectDeliveryService


def send_project_notifications(context):
    return ProjectDeliveryService.daily_notifications(context)


def populate_default_checkpoints(context, project_id):
    return ProjectDeliveryService.create_default_checkpoints(context, project_id)


def send_weekly_anti_phishing_assessments(context, project_id):
    return ProjectDeliveryService.launch_compliance_campaign(context, project_id)


def update_project_health(context, project_id):
    return ProjectDeliveryService.calculate_health(context, project_id)