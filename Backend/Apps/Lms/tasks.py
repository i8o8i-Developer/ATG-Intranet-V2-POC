from Backend.Apps.Lms.services import LeadManagementService, LearningAssignmentService


def mark_learning_complete(context, assignment_id):
    return LearningAssignmentService.mark_complete(context, assignment_id)


def send_ba_followup_reminder(context):
    return LeadManagementService.check_leads_without_today_note(context)


def snapshot_ba_queue(context, employee_id=None):
    return LeadManagementService.create_queue_snapshot(context, employee_id=employee_id)


def weekly_workload(context):
    return LeadManagementService.weekly_workload(context)