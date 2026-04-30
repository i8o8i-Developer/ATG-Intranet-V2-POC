from Backend.Apps.Banao.services import LeadWorkflowService


def send_audit(context, lead_id, notes=None):
    return LeadWorkflowService.send_audit(context, lead_id, notes=notes or {})


def send_to_bbd(context, lead_id, notes=None):
    return LeadWorkflowService.send_to_bbd(context, lead_id, notes=notes or {})


def check_workflow_status(context):
    return LeadWorkflowService.check_workflow_status(context)


def allocate_jrba_leads(context, owner_ids=None, source="JRBA"):
    return LeadWorkflowService.allocate_jrba_leads(context, owner_ids=owner_ids or [], source=source)
