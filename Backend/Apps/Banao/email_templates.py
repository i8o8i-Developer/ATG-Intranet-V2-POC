def get_bbd_email_template(lead):
    return {
        "subject": f"BBD HandOff: {lead.company_name}",
        "body": f"Lead {lead.company_name} Is Ready for BBD Review. Current Stage: {lead.stage}.",
        "lead_id": lead.id,
    }


def get_audit_email_template(lead, audit=None):
    return {
        "subject": f"Audit Request: {lead.company_name}",
        "body": f"Please Review Audit Requirements for {lead.company_name}.",
        "lead_id": lead.id,
        "audit_id": audit.id if audit else None,
    }


def get_offer_letter_template(lead, proposal=None):
    amount = proposal.amount if proposal else lead.estimated_value
    return {
        "subject": f"Offer Proposal: {lead.company_name}",
        "body": f"Offer Proposal for {lead.company_name} with Estimated Value {amount} {lead.currency}.",
        "lead_id": lead.id,
        "proposal_id": proposal.id if proposal else None,
    }
