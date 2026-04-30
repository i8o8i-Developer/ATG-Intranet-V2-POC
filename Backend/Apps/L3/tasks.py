from Backend.Apps.L3.services import TalentPipelineService


def assign_colleges(context, employee_id, college_ids=None, limit=None):
    return TalentPipelineService.assign_colleges(context, employee_id, college_ids=college_ids or [], limit=limit)


def send_college_email(context, college_id, template_id=None, assignment_id=None, live=False):
    return TalentPipelineService.send_college_email(context, college_id, template_id=template_id, assignment_id=assignment_id, live=live)


def performance_summary(context, employee_id=None):
    return TalentPipelineService.performance_summary(context, employee_id=employee_id)