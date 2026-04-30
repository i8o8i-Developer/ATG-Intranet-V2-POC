from Backend.Apps.Project.anti_phishing_data import ANTI_PHISHING_WEEKS
from Backend.Apps.Project.services import ProjectDeliveryService


def get_week_content(week=1):
    return next((item for item in ANTI_PHISHING_WEEKS if item["week"] == week), ANTI_PHISHING_WEEKS[0])


def send_weekly_anti_phishing_assessments(context, project_id, week=1):
    content = get_week_content(week)
    return ProjectDeliveryService.launch_compliance_campaign(context, project_id, name=content["title"])