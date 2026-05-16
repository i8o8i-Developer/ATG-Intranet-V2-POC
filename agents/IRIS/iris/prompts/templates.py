"""
Per-meeting-type extraction prompt templates.
Each template includes the exact YAML schema fields IRIS must populate.
"""

from iris.core.models import MeetingInputs
import json


def build_user_message(inputs: MeetingInputs, pm_notes: str = "") -> str:
    """
    Assemble the full user message for the LLM:
    metadata + attendees + transcript + (optional) PM correction notes.
    """
    meeting_type = inputs.metadata.meeting_type
    template_fn = TYPE_TEMPLATES.get(meeting_type, _default_template)

    pm_section = ""
    if pm_notes:
        pm_section = f"""
## PM Correction Notes (apply these corrections during re-extraction)

{pm_notes}

"""

    return f"""## Meeting Metadata

{json.dumps(inputs.metadata.model_dump(), indent=2)}

## Attendees

{json.dumps([a.model_dump() for a in inputs.attendees], indent=2)}

## Transcript

{inputs.transcript}
{pm_section}
## Extraction Task

{template_fn(inputs)}
"""


# ── Base schema instruction (included in every template) ──────────

BASE_SCHEMA = """
Extract the BASE section with these fields:

```
meeting_id: <from metadata>
project_id: <from metadata>
date: <from metadata>
meeting_type: <from metadata>
duration_minutes: <from metadata>
security_level: <from metadata — DO NOT change>

organiser_id: <from metadata>
attendee_count_internal: <from metadata>
attendee_count_external: <from metadata>

extraction_confidence: <float 0.0-1.0, mean of field scores>
extraction_review: <true if confidence < 0.6, else false>

language_mix: <from metadata>

follow_up_owner: <intranet_id of person responsible for next action, or null>
follow_up_type: <none | planned | forced>

next_meeting_date: <YYYY-MM-DD if mentioned, else null>
previous_meeting_ref: null

tags: [<tags from controlled taxonomy only>]

consumer_level: <pm | dept-head | director | hr-only — derive using the rules>
```
"""


# ── Type-specific templates ────────────────────────────────────────

def _standup_template(inputs: MeetingInputs) -> str:
    return BASE_SCHEMA + """
Then append the standup section:

```
standup:
  all_green: <true if no blockers, no silent members, no confidence drops>
  submitted_count: <how many people gave updates>
  expected_count: <total team members expected>
  silent_members:
    - person_id: <intranet_id>
      days_silent_in_row: <int>
  blocked_today:
    - person_id: <intranet_id>
      desc: <what they are blocked on, in English>
      carried_from: <YYYY-MM-DD if mentioned, else null>
      days_carried: <int if mentioned, else null>
      cross_team: <true if another department is involved>
      blocking_dept: <department name or null>
  confidence_drops:
    - person_id: <intranet_id>
      from: <green | yellow | red>
      to: <green | yellow | red>
      note: <reason in English>
  unplanned_work_mentioned:
    - desc: <description in English>
      raised_by: <intranet_id>
      in_scope: <true | false | null if unclear>
  pattern_flags:
    - <string: any recurring pattern worth flagging, e.g. "p-rohit-002 blocked 3 days on same item">
```

Output only YAML. No explanation.
"""


def _sprint_planning_template(inputs: MeetingInputs) -> str:
    return BASE_SCHEMA + """
Then append the internal section:

```
internal:
  sprint_ref: <e.g. Sprint-06, or null>
  decisions:
    - id: D-001
      text: <decision text in English>
      owner: <intranet_id or null>
      due: <YYYY-MM-DD or null>
      reverses_previous: <true | false>
  technical_risks:
    - desc: <risk description in English>
      severity: <low | medium | high | critical>
      owner: <intranet_id or null>
      mitigation_agreed: <true | false>
  scope_adjustments:
    - item: <feature/item name>
      direction: <in | out | split>
      agreed_by: <intranet_id or null>
      sow_ref: <section reference or null>
  velocity_concern: <true | false>
  velocity_note: <explanation or null>
  deferred_items:
    - text: <item description in English>
      deferred_to: <when, in English, or null>
      deferred_count: <how many times deferred, or null>
      owner: <intranet_id or null>
  resolved_from_last_sync:
    - text: <item that was resolved>
      resolved: true
  cross_dept_dependencies:
    - blocking_dept: <department>
      blocked_dept: <department>
      item: <what is blocked>
      due: <YYYY-MM-DD or null>
      status: <open | resolved | escalated>
```

Output only YAML. No explanation.
"""


def _client_call_template(inputs: MeetingInputs) -> str:
    return BASE_SCHEMA + """
Then append the client section:

```
client:
  sentiment: <positive | neutral | negative | mixed>
  sentiment_note: <one-line explanation in English>
  relationship_trajectory: <improving | stable | declining>
  client_id: <from metadata.client_id or null>
  commitments:
    - id: C-001
      text: <commitment text in English>
      owner: <intranet_id>
      due: <YYYY-MM-DD or null>
      made_by: <our-side | client-side>
      status: <open | fulfilled | breached>
      critical_path: <true | false>
  open_commitments_from_last_call:
    - id: C-prev-001
      text: <commitment text>
      status: <fulfilled | breached | still-open>
  scope_requests:
    - item: <feature/scope requested>
      in_sow: <true | false>
      client_priority: <high | medium | low>
      our_response: <accepted | rejected | deferred | tbd>
      revenue_implication: <true | false>
  deadline_pressure: <true | false>
  deadline_note: <explanation or null>
  budget_pressure: <true | false>
  escalation_signal: <true | false>
  satisfaction_signal: <high | medium | low | not-detectable>
  risks:
    - desc: <risk description in English>
      severity: <low | medium | high | critical>
      trigger: <what would cause this risk to materialise>
```

Output only YAML. No explanation.
"""


def _milestone_review_template(inputs: MeetingInputs) -> str:
    return BASE_SCHEMA + """
Then append the milestone_review section:

```
milestone_review:
  milestone_id: <e.g. M1>
  milestone_name: <name in English>
  acceptance_status: <accepted | partial | rejected>
  sign_offs:
    - deliverable: <deliverable name>
      status: <accepted | rejected>
      reviewer: <our-side | client-side>
      rework_requested: <description or null>
      rework_owner: <intranet_id or null>
      rework_due: <YYYY-MM-DD or null>
  rework_count_this_milestone: <int>
  next_milestone_id: <e.g. M2 or null>
  next_milestone_at_risk: <true | false>
  next_milestone_risk_note: <explanation or null>
  payment_trigger: <true | false>
  client_satisfaction_signal: <high | medium | low | not-detectable>
```

Output only YAML. No explanation.
"""


def _cross_dept_template(inputs: MeetingInputs) -> str:
    return BASE_SCHEMA + """
Then append the cross_dept section:

```
cross_dept:
  departments_present:
    - <department name>
  dependency_item: <what the dependency is about, in English>
  dependency_status: <open | resolved | escalated | deferred>
  blocking_dept: <department name>
  blocked_dept: <department name>
  resolution:
    text: <resolution description in English or null>
    owner: <intranet_id or null>
    due: <YYYY-MM-DD or null>
  unresolved_items:
    - text: <item description in English>
      owner: <intranet_id or null>
      due: <YYYY-MM-DD or null>
  escalation_needed: <true | false>
  projects_affected:
    - <project_id>
```

Output only YAML. No explanation.
"""


def _design_review_template(inputs: MeetingInputs) -> str:
    return BASE_SCHEMA + """
Then append the design_review section:

```
design_review:
  deliverable: <name of design deliverable in English>
  review_round: <int>
  reviewer_type: <internal | client | both>
  approval_status: <approved | conditional | rejected>
  feedback_items:
    - item: <feedback description in English>
      severity: <minor | major | blocking>
      owner: <intranet_id or null>
      due: <YYYY-MM-DD or null>
  blocking_development: <true | false>
  sow_alignment: <true | false>
```

Output only YAML. No explanation.
"""


def _sales_bd_template(inputs: MeetingInputs) -> str:
    return BASE_SCHEMA + """
Then append the sales_bd section:

```
sales_bd:
  lead_id: <lead identifier or null>
  client_name_hash: <hash or null — never use real client name>
  meeting_subtype: <discovery | proposal | negotiation | closed-won | closed-lost>
  lead_stage_before: <stage before this meeting>
  lead_stage_after: <stage after this meeting>
  proposal_value_band: <low | medium | high | enterprise>
  tech_stack_requested:
    - <technology name>
  estimated_team_size: <int or null>
  estimated_duration_weeks: <int or null>
  next_action: <description in English or null>
  next_action_owner: <intranet_id or null>
  next_action_due: <YYYY-MM-DD or null>
  qualification_signals:
    budget_confirmed: <true | false>
    timeline_realistic: <true | false>
    decision_maker_present: <true | false>
  lost_reason: <reason in English or null>
```

Output only YAML. No explanation.
"""


def _hr_template(inputs: MeetingInputs) -> str:
    return BASE_SCHEMA + """
Then append the hr section:

```
hr:
  subtype: <hiring | performance-review | disciplinary | offboarding | general | salary-review>
  headcount_discussed: <true | false>
  decisions:
    - text: <decision in English>
      owner: <intranet_id or null>
      due: <YYYY-MM-DD or null>
  aggregate_signal: <green | amber | red>
  attrition_risk_mentioned: <true | false>
  hiring_velocity: <ahead | on-track | behind | blocked | null>
  action_items:
    - text: <action in English>
      owner: <intranet_id or null>
      due: <YYYY-MM-DD or null>
```

Output only YAML. No explanation.
"""


def _allhands_template(inputs: MeetingInputs) -> str:
    return BASE_SCHEMA + """
Then append the allhands section:

```
allhands:
  attendance_pct: <int percentage or null>
  announcements:
    - text: <announcement in English>
      category: <financial | org | product | culture | other>
  strategic_decisions:
    - text: <decision in English>
      owner: <intranet_id or null>
      due: <YYYY-MM-DD or null>
  sentiment_overall: <positive | neutral | negative | mixed>
  concerns_raised: <true | false>
  concerns_note: <description in English or null>
  followup_comms_needed: <true | false>
```

Output only YAML. No explanation.
"""


def _vendor_template(inputs: MeetingInputs) -> str:
    return BASE_SCHEMA + """
Then append the vendor section:

```
vendor:
  vendor_name_hash: <anonymised hash or null>
  vendor_type: <software | hardware | services | infrastructure | other>
  meeting_subtype: <evaluation | negotiation | onboarding | review | issue-resolution | renewal>
  contract_discussed: <true | false>
  contract_ref: <contract identifier or null>
  commitments:
    - id: V-001
      text: <commitment in English>
      owner: <intranet_id for our side, or "vendor-side">
      due: <YYYY-MM-DD or null>
      status: <open | fulfilled | breached>
  issues_raised:
    - desc: <issue description in English>
      severity: <low | medium | high | critical>
      owner: <intranet_id or null>
      resolution: <resolution or null>
  cost_implication: <true | false>
  cost_note: <description or null>
  renewal_due: <YYYY-MM-DD or null>
  escalation_needed: <true | false>
  relationship_health: <good | neutral | strained>
```

Output only YAML. No explanation.
"""


def _default_template(inputs: MeetingInputs) -> str:
    """Fallback for unknown/future meeting types — BASE only."""
    return BASE_SCHEMA + "\nOutput only YAML. No explanation."


# ── Dispatch map ──────────────────────────────────────────────────

TYPE_TEMPLATES = {
    "standup": _standup_template,
    "sprint-planning": _sprint_planning_template,
    "client-call": _client_call_template,
    "milestone-review": _milestone_review_template,
    "cross-dept": _cross_dept_template,
    "design-review": _design_review_template,
    "sales-bd": _sales_bd_template,
    "hr": _hr_template,
    "company-allhands": _allhands_template,
    "vendor": _vendor_template,
}
