# IRIS — Insight & Record Intelligence System
## Agent v1 | OpenCode Build Context

---

## 1. What IRIS Is

IRIS is an **extraction intelligence agent**. Its sole job is to read a completed meeting's raw artifacts and produce a structured YAML insight file. It does not make project-level decisions, it does not track history across meetings, and it does not notify downstream systems directly. It extracts, structures, emits, and stops.

IRIS is Agent 1 in a multi-agent pipeline:
- **IRIS (Agent 1)** → extraction intelligence (this document)
- **ToDo Agent (Agent 2)** → task generation & PM approval loop
- **Project Manager Agent (Agent 3)** → project intelligence, memory, cross-meeting patterns
- **NERVE (Orchestrator)** → routes events between agents (not built yet — simulate for testing)

---

## 2. System Context

**Organisation:** ~190 people, 16 departments, fully remote. All communication happens over Google Meet and Slack.

**Meeting pipeline (already built, IRIS consumes its output):**
1. Chrome extension auto-captures Google Meet recording
2. In-house ASR transcribes audio → Hinglish transcript with speaker labels + timestamps
3. Voice biometrics identify speakers → mapped to intranet employee IDs
4. Organiser fills a POST-MEET form confirming project, agenda, attendees
5. Meeting saved to Cloudflare R2 storage under path:
   `/projects/{project-id}/{YYYY-MM-DD}_{meeting-id}/`
6. Four files land in that folder:
   - `meeting_video.mp4`
   - `transcript.txt` — Hinglish, speaker-labelled, timestamped
   - `metadata.json` — all meeting metadata from the form
   - `attendees.json` — attendee list with intranet IDs, departments, roles

**IRIS triggers after step 6 is complete.**

---

## 3. Trigger Specification

**Trigger:** Event-driven. Fires when a meeting record is fully saved and `transcript_status = completed`.

**Trigger payload (received by IRIS):**
```json
{
  "meeting_id": "abc-defg-hij",
  "project_id": "PROJ-CRM-0014",
  "r2_path": "/projects/PROJ-CRM-0014/2025-05-06_abc-defg-hij/",
  "transcript_status": "completed",
  "triggered_at": "2025-05-06T14:32:00Z"
}
```

**IRIS does NOT trigger on partial saves.** If transcript is still `processing`, the trigger has not fired yet — that is the upstream pipeline's responsibility.

---

## 4. Inputs IRIS Reads

All files are read from R2 at the path in the trigger payload.

### `metadata.json` (key fields IRIS uses)
```json
{
  "meeting_id": "abc-defg-hij",
  "project_id": "PROJ-CRM-0014",
  "date": "2025-05-06",
  "meeting_type": "client-call",
  "duration_minutes": 47,
  "security_level": "INTERNAL",
  "organiser_id": "p-rohan-pm",
  "attendee_count_internal": 3,
  "attendee_count_external": 1,
  "language_mix": "hinglish",
  "series_id": null
}
```
**Note:** `security_level` is read directly from metadata — IRIS never sets or changes it.

### `attendees.json`
```json
[
  {
    "intranet_id": "p-rohan-pm",
    "name": "Rohan Sharma",
    "department": "Delivery",
    "role": "Project Manager",
    "type": "internal"
  },
  {
    "intranet_id": null,
    "name_hash": "a3f9c2",
    "type": "external"
  }
]
```

### `transcript.txt`
- Hinglish (Hindi + English mixed), UTF-8
- Speaker-labelled via voice biometrics (intranet IDs already resolved in transcript)
- Timestamped per utterance
- Example line: `[00:04:32] p-rohan-pm: Toh basically client bol raha hai ki credentials abhi tak nahi mile`

---

## 5. Intranet Employee Table (API Access)

IRIS has read access to an internal employee API for role/department resolution when needed beyond what's in `attendees.json`.

**Endpoint:** `GET /intranet/employees/{intranet_id}`

**Returns:**
```json
{
  "intranet_id": "p-rohan-pm",
  "name": "Rohan Sharma",
  "role": "Project Manager",
  "department": "Delivery",
  "active_projects": ["PROJ-CRM-0014", "PROJ-ECOM-0021"],
  "employment_type": "full-time"
}
```

---

## 6. IRIS Output

IRIS writes one file to R2 in the same meeting folder:

**Path:** `/projects/{project-id}/{YYYY-MM-DD}_{meeting-id}/insights.yaml`

After writing, IRIS emits one event:

```json
{
  "event": "iris.extraction.complete",
  "meeting_id": "abc-defg-hij",
  "project_id": "PROJ-CRM-0014",
  "confidence_score": 0.91,
  "flagged": false,
  "insights_path": "/projects/PROJ-CRM-0014/2025-05-06_abc-defg-hij/insights.yaml",
  "timestamp": "2025-05-06T14:35:12Z"
}
```

`flagged: true` when `extraction_confidence < 0.6`. NERVE routes flagged extractions to the PM's todo queue.

---

## 7. Output YAML Schema

Every meeting gets the **BASE section**. Then exactly one **type-specific section** is appended based on `meeting_type`.

### BASE (all meetings)
```yaml
meeting_id: abc-defg-hij
project_id: PROJ-CRM-0014
date: "2025-05-06"
meeting_type: client-call
  # standup | sprint-planning | client-call |
  # milestone-review | cross-dept | design-review |
  # hr | sales-bd | company-allhands | vendor
duration_minutes: 47
security_level: INTERNAL
  # Read from metadata.json — never set by IRIS

organiser_id: "p-rohan-pm"
attendee_count_internal: 3
attendee_count_external: 1

extraction_confidence: 0.91
  # 0.0 - 1.0. IRIS sets flagged=true in event if < 0.6
extraction_review: false
  # true if confidence < 0.6

language_mix: hinglish
  # english | hindi | hinglish

follow_up_owner: "p-rohan-pm"
follow_up_type: forced
  # none | planned | forced
  # forced = meeting ended with unresolved items, no clear owner
  # planned = next checkpoint was scheduled

next_meeting_date: "2025-05-09"   # null if not mentioned
previous_meeting_ref: null
  # NOT set by IRIS — Agent 3 (PM) owns this field

tags: [client, scope-change, blocker, sentiment-negative]
  # Controlled vocabulary only — see Section 8

consumer_level: pm
  # pm | dept-head | director | hr-only
  # Derived by IRIS from meeting_type and security_level
```

### TYPE-SPECIFIC SECTIONS

#### `meeting_type: standup`
```yaml
standup:
  all_green: false
  submitted_count: 6
  expected_count: 7
  silent_members:
    - person_id: "p-dev-003"
      days_silent_in_row: 2
  blocked_today:
    - person_id: "p-rohit-002"
      desc: "waiting on CRM credentials from AM"
      carried_from: "2025-05-05"
      days_carried: 2
      cross_team: true
      blocking_dept: "BA"
  confidence_drops:
    - person_id: "p-arjun-001"
      from: green
      to: yellow
      note: "api-gateway more complex than estimated"
  unplanned_work_mentioned:
    - desc: "hotfix needed on auth module"
      raised_by: "p-arjun-001"
      in_scope: true
  pattern_flags:
    - "p-rohit-002 blocked 3 days running on same item"
    - "p-dev-003 silent 2 days running"
```

#### `meeting_type: sprint-planning`
```yaml
internal:
  sprint_ref: "Sprint-06"
  decisions:
    - id: D-001
      text: "Defer reporting dashboard to Phase 2"
      owner: "p-rohan-pm"
      due: null
      reverses_previous: false
  technical_risks:
    - desc: "api-gateway complexity underestimated by ~40%"
      severity: medium   # low | medium | high | critical
      owner: "p-arjun-001"
      mitigation_agreed: false
  scope_adjustments:
    - item: "reporting-dashboard"
      direction: out     # in | out | split
      agreed_by: "p-rohan-pm"
      sow_ref: "Section 4.2"
  velocity_concern: true
  velocity_note: "W19 completion was 60% of planned"
  deferred_items:
    - text: "database migration strategy"
      deferred_to: "next sync"
      deferred_count: 2
      owner: "p-arjun-001"
  resolved_from_last_sync:
    - text: "API versioning approach"
      resolved: true
  cross_dept_dependencies:
    - blocking_dept: "UIUX"
      blocked_dept: "REACT"
      item: "final mockups for dashboard"
      due: "2025-05-08"
      status: open       # open | resolved | escalated
```

#### `meeting_type: client-call`
```yaml
client:
  sentiment: negative    # positive | neutral | negative | mixed
  sentiment_note: "Client frustrated about credential delay"
  relationship_trajectory: declining
    # improving | stable | declining
  client_id: "CLIENT-ACME-001"
  commitments:
    - id: C-001
      text: "API credentials shared by EOD Friday"
      owner: "p-vikram-am"
      due: "2025-05-09"
      made_by: client-side   # our-side | client-side
      status: open           # open | fulfilled | breached
      critical_path: true
  open_commitments_from_last_call:
    - id: C-prev-001
      text: "Share staging environment access"
      status: fulfilled
  scope_requests:
    - item: "reporting-dashboard"
      in_sow: false
      client_priority: high
      our_response: deferred # accepted | rejected | deferred | tbd
      revenue_implication: true
  deadline_pressure: true
  deadline_note: "Client mentioned May 30 as hard cutoff"
  budget_pressure: false
  escalation_signal: false
  satisfaction_signal: low   # high | medium | low | not-detectable
  risks:
    - desc: "M1 at risk if credentials delayed past Friday"
      severity: high
      trigger: "any further delay"
```

#### `meeting_type: milestone-review`
```yaml
milestone_review:
  milestone_id: "M1"
  milestone_name: "Discovery & Architecture"
  acceptance_status: partial  # accepted | partial | rejected
  sign_offs:
    - deliverable: "Requirements document"
      status: accepted
      reviewer: client-side
    - deliverable: "Architecture diagram"
      status: rejected
      rework_requested: "Add data flow for reporting module"
      rework_owner: "p-arjun-001"
      rework_due: "2025-05-12"
  rework_count_this_milestone: 1
  next_milestone_id: "M2"
  next_milestone_at_risk: true
  next_milestone_risk_note: "M2 start blocked on M1 rework completion"
  payment_trigger: false
  client_satisfaction_signal: medium
```

#### `meeting_type: cross-dept`
```yaml
cross_dept:
  departments_present:
    - "PYDJANGO"
    - "REACT"
  dependency_item: "API contract for dashboard feed"
  dependency_status: resolved  # open | resolved | escalated | deferred
  blocking_dept: "PYDJANGO"
  blocked_dept: "REACT"
  resolution:
    text: "API schema finalised — v2 endpoint agreed"
    owner: "p-arjun-001"
    due: "2025-05-07"
  unresolved_items:
    - text: "Rate limiting approach not agreed"
      owner: "p-arjun-001"
      due: "2025-05-08"
  escalation_needed: false
  projects_affected:
    - "PROJ-CRM-0014"
```

#### `meeting_type: design-review`
```yaml
design_review:
  deliverable: "Dashboard UI mockups v3"
  review_round: 3
  reviewer_type: internal   # internal | client | both
  approval_status: conditional  # approved | conditional | rejected
  feedback_items:
    - item: "Colour contrast on data cards"
      severity: minor       # minor | major | blocking
      owner: "p-uiux-001"
      due: "2025-05-08"
  blocking_development: true
  sow_alignment: true
```

#### `meeting_type: sales-bd`
```yaml
sales_bd:
  lead_id: "LEAD-0042"
  client_name_hash: "a3f9c2"
  meeting_subtype: discovery  # discovery | proposal | negotiation | closed-won | closed-lost
  lead_stage_before: qualified
  lead_stage_after: proposal-sent
  proposal_value_band: medium   # low | medium | high | enterprise
  tech_stack_requested:
    - "Python Django"
    - "React Native"
  estimated_team_size: 6
  estimated_duration_weeks: 24
  next_action: "Send proposal by Friday"
  next_action_owner: "p-ba-001"
  next_action_due: "2025-05-09"
  qualification_signals:
    budget_confirmed: true
    timeline_realistic: true
    decision_maker_present: false
  lost_reason: null
```

#### `meeting_type: hr`
```yaml
hr:
  subtype: hiring
    # hiring | performance-review | disciplinary |
    # offboarding | general | salary-review
  headcount_discussed: true
  decisions:
    - text: "Approve 2 new React Native hires"
      owner: "hr-head"
      due: "2025-05-15"
  aggregate_signal: amber   # green | amber | red
  attrition_risk_mentioned: false
  hiring_velocity: on-track # ahead | on-track | behind | blocked
  action_items:
    - text: "Post 2 React Native JDs"
      owner: "hr-assoc-001"
      due: "2025-05-09"
```

#### `meeting_type: company-allhands`
```yaml
allhands:
  attendance_pct: 87
  announcements:
    - text: "Q2 revenue target achieved"
      category: financial  # financial | org | product | culture | other
  strategic_decisions:
    - text: "Expand React Native dept by 4 people in Q3"
      owner: "ceo"
      due: null
  sentiment_overall: positive
  concerns_raised: true
  concerns_note: "Multiple staff asked about remote work policy"
  followup_comms_needed: true
```

---

## 8. Controlled Tag Taxonomy

IRIS picks tags **only from this list**. No freeform tags.

```
# State
blocker | decision | scope-change | risk | commitment |
deadline-pressure | budget-pressure | escalation

# Sentiment
sentiment-positive | sentiment-negative | sentiment-mixed | sentiment-neutral

# Meeting health
unresolved-items | decision-reversed | velocity-concern |
rework-requested | deferred-item | silent-member

# People / process
cross-dept | external-client | commitment-breached | commitment-fulfilled

# Meeting type context
hiring | performance | sprint | milestone | sales | design
```

Multiple tags allowed. IRIS auto-generates tags from extraction signals.

---

## 9. consumer_level Derivation Logic

IRIS sets `consumer_level` based on these rules (first match wins):

| Condition | consumer_level |
|-----------|---------------|
| `security_level = CONFIDENTIAL` or `meeting_type = hr` | `hr-only` |
| `meeting_type = company-allhands` | `director` |
| `meeting_type = sales-bd` or `meeting_type = milestone-review` | `dept-head` |
| All others | `pm` |

---

## 10. Second Entrypoint — PM Feedback Re-run

When a PM reviews a flagged YAML and provides correction notes, IRIS exposes a second entrypoint:

**`POST /iris/rerun`**
```json
{
  "meeting_id": "abc-defg-hij",
  "pm_notes": "The blocker was actually resolved in this meeting. Client confirmed credentials will arrive Thursday not Friday. Sentiment should be mixed not negative."
}
```

IRIS re-reads the same R2 artifacts, injects `pm_notes` as additional context into the extraction prompt, and overwrites `insights.yaml`. Emits the same `iris.extraction.complete` event with updated confidence score.

---

## 11. LLM Extraction Strategy

**Language:** Hinglish input → English output always. IRIS must use a model capable of understanding mixed Hindi-English speech.

**Recommended approach for opencode to evaluate:**
- Single LLM call per meeting with full transcript + structured prompt
- System prompt instructs: extract in English, map to schema, assign confidence per field
- Meeting type detected first (from `metadata.json`) → type-specific extraction prompt loaded
- Overall `extraction_confidence` = mean of per-field confidence scores

**No prompt has been pre-designed. No LLM has been selected. Opencode should select and justify.**

**Cost constraint:** This runs on every meeting automatically. Optimise for cost. Consider:
- Chunking long transcripts
- Using a smaller/cheaper model for standup extractions vs client calls
- Caching intranet employee lookups

---

## 12. What IRIS Does NOT Do

- Does not set `security_level` — reads from `metadata.json`
- Does not fill `previous_meeting_ref` — Agent 3 owns this
- Does not notify ToDo Agent or PM directly — NERVE routes the event
- Does not access `meeting_video.mp4`
- Does not make project-level decisions or track patterns across meetings
- Does not write to ERP or intranet

---

## 13. Repository Scope for OpenCode

Build the IRIS agent as a standalone service. The following must be simulated/mocked for testing:

- R2 read/write (mock with local filesystem or MinIO)
- Intranet employee API (mock JSON server)
- Trigger webhook (simulate with a test script that fires the payload)
- NERVE event receiver (mock endpoint that logs received events)

**Deliverables:**
1. IRIS service (trigger handler, extraction pipeline, R2 write, event emit)
2. `rerun` entrypoint
3. Full test suite with at least one test meeting per `meeting_type`
4. Sample `insights.yaml` for each meeting type
5. README with setup, env vars, how to trigger a test run

---

## 14. Open Questions for Opencode to Decide

- LLM selection and justification (cost vs quality tradeoff for Hinglish)
- Whether to use one prompt or chained prompts (type detection → extraction)
- Confidence scoring methodology
- R2 client library choice
- Event emission mechanism (webhook? queue? pub/sub?)
- Error handling: what happens if R2 write fails after extraction succeeds?
