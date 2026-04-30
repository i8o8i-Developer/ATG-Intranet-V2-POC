def get_bbd_email_template(lead):
    return {
        "subject": f"BBD handoff: {lead.company_name}",
        "body": f"Lead {lead.company_name} is ready for BBD review. Current stage: {lead.stage}.",
        "lead_id": lead.id,
    }


def get_audit_email_template(lead, audit=None):
    return {
        "subject": f"Audit request: {lead.company_name}",
        "body": f"Please review audit requirements for {lead.company_name}.",
        "lead_id": lead.id,
        "audit_id": audit.id if audit else None,
    }


def get_offer_letter_template(lead, proposal=None):
    amount = proposal.amount if proposal else lead.estimated_value
    return {
        "subject": f"Offer proposal: {lead.company_name}",
        "body": f"Offer proposal for {lead.company_name} with estimated value {amount} {lead.currency}.",
        "lead_id": lead.id,
        "proposal_id": proposal.id if proposal else None,
    }
