def get_duration_in_days_or_weeks(days):
    duration = ''
    if days <= 7:
        duration = str(days) + ' days' 
    else:
        duration = str(round(days/7)) + ' weeks'
    return duration


def cost_formatter(cost):
    from math import ceil
    cost_array = str(cost).split('.')
    formatted_cost = ''
    length = len(cost_array[0])

    if length > 3:
        comma_count = ceil((length - 3) / 2)
        i = length - 3 
        j = 0
        while j < comma_count:
            formatted_cost = cost_array[0][0: i] + ',' + formatted_cost[i:] 
            i -= 2
            j += 1
        formatted_cost += f'{cost_array[0][(length-3):]}.' + (cost_array[1] if len(cost_array) == 2 else '0')
    else:
        formatted_cost = '.'.join(cost_array) + ('' if len(cost_array) == 2 else '.0')

    return f'₹{formatted_cost}'


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


def get_offer_letter_template(context):
    """
    Generate full HTML offer letter template for Banao projects.
    
    Expected context structure:
    {
        'member_details': {
            'name': str,
            'duration_in_days': int,
            'milestones': [
                {'name': str, 'assignment_cost': float},
                ...
            ]
        },
        'project_details': {
            'offer_letter_message': str,
            'link': str
        }
    }
    """
    html = '''<html>
    <head></head>
    <body style="font-size: 1rem;font-weight: 400; font-family: 'Lato', sans-serif;">
    <div style="border: 1px solid black;margin: auto;width: 712px;">
    <div style="text-align:center;">
      <div style="width:100%;">
        <img src="https://banao.tech/static/images/logo%202%201.png" height="90" />
      </div>
    </div>
    <div style="text-align:center;">
      <div style="width:100%;">
        <strong><u>COMPENSATION LETTER</u></strong><br>
      </div>
    </div>
    <div style="padding: 3rem 4rem;">
      <div style="width:100%;">
        <p>Dear <span class="member-name">{}</span>,</p>
        
        <p>{}</p>
        <p>The project scope, timeline and pay are as below:</p>
        
        <p>Project Scope: <a href="{}" class="project-scope" target="_blank">Link</a></p>
        <p>Estimated Work effort: 20 hours/week</p>
        <p>Timeline: <span class="project-span">{}</span></p>
        
        <table style="border: 1px solid black; border-collapse:collapse; width:100%;">
            <tr>
                <td colspan="2" style="border: 1px solid; padding: .75rem;">Pay Type: <strong>Milestone Based</strong></td>
            </tr>
            '''.format(context['member_details']['name'], context['project_details']['offer_letter_message'], context['project_details']['link'], get_duration_in_days_or_weeks(context['member_details']['duration_in_days']))

    total_cost = 0
    for milestone in context['member_details']['milestones']:
        milestone_cost = milestone['assignment_cost']
        total_cost += milestone_cost

        html += '''<tr>
              <td class="milestone-name" style="border: 1px solid; padding: .75rem;">{}</td>
              <td class="milestone-cost" style="border: 1px solid; padding: .75rem;">{}</td>
            </tr>'''.format(milestone['name'], cost_formatter(milestone_cost))

    html += '''<tr>
              <td style="border: 1px solid; padding: .75rem;">Total</td>
              <td class="milestone-cost" style="border: 1px solid; padding: .75rem;">{}</td>
            </tr>
          </table>
            <p>For more details you can refer to the full project proposal.</p>
          </div></div>
          <div style="padding: 3rem 4rem;">
            <div style="width:100%;">
              <img src="https://intranet.atg.party/static/banao/images/signature.png" height="70">
              <p>Sincerely,</p>
              <p>Saurabh Bassi</p>
              <p>(Co-Founder / CEO, BANAO)</p>
            </div>
          </div>  
          <div style="padding: 3rem 4rem;">
            <div style="width:100%;">
            <b><u>TERMS</u></b>
            <b><ol style="padding:0;">
              <li>Client will have 2 (feedback) + 1 (confirmation) design iterations. Subsequent design iterations will be paid hourly.</li>
              <li>Work effort and project timelines are estimated and need to be chased as strict deadlines.</li>
              <li>If you accept the offer, please respond to your hiring manager with a confrimation reply to this mail ( YES, I &lt;YOUR NAME&gt; ACCEPT THE OFFER).</li>
              <li>Offer is valid for 2 days from the day you receive it.</li>
              <li>Project milestones are dependent on the project progress and delivery (as a team effort). In case the project goes on hold, the payments go on hold too.</li>
            </ol></b>
            </div>
          </div></div></body></html>'''.format(cost_formatter(total_cost))

    return html
