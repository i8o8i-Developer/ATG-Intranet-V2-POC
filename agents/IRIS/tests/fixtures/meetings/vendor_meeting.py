"""Fixture: vendor meeting"""

METADATA = {
    "meeting_id": "meet-vendor-001",
    "project_id": "INTERNAL-INFRA",
    "date": "2025-05-06",
    "meeting_type": "vendor",
    "duration_minutes": 30,
    "security_level": "INTERNAL",
    "organiser_id": "p-arjun-001",
    "attendee_count_internal": 2,
    "attendee_count_external": 1,
    "language_mix": "hinglish",
    "series_id": None,
    "client_id": None,
}

ATTENDEES = [
    {"intranet_id": "p-arjun-001", "name": "Arjun Mehta", "department": "PYDJANGO", "role": "Backend Engineer", "type": "internal"},
    {"intranet_id": "p-rohan-pm", "name": "Rohan Sharma", "department": "Delivery", "role": "Project Manager", "type": "internal"},
    {"intranet_id": None, "name_hash": "c9f2a7", "type": "external"},
]

TRANSCRIPT = """[00:01:00] p-arjun-001: Hi, thanks for joining. We are evaluating your cloud infrastructure services for our staging and production setup.
[00:01:20] c9f2a7: Of course. We offer managed Kubernetes clusters, auto-scaling, and 99.99% uptime SLA. What's your current setup?
[00:01:40] p-arjun-001: We're currently on a basic VPS. We want to migrate to a managed setup. Main concern is cost and migration complexity.
[00:02:00] c9f2a7: For a team your size, our startup tier would be ideal. It's around 15,000 rupees per month for the setup you'd need.
[00:02:20] p-rohan-pm: Yeh cost implication hai company ke liye. We need to factor this into project budgets.
[00:02:40] p-arjun-001: Kya aap migration support dete ho?
[00:02:50] c9f2a7: Yes we provide full migration support. Our team would handle the transition with zero downtime. We commit to completing migration within 2 weeks of contract signing.
[00:03:10] p-arjun-001: That sounds good. Ek issue hai — our current contract with our VPS provider expires May 31st. We need to have a decision before that.
[00:03:30] c9f2a7: No problem. If you sign before May 20th, we can ensure the migration is complete before May 31st.
[00:03:45] p-rohan-pm: We'll discuss internally and revert by May 15th.
[00:03:58] c9f2a7: Perfect. I'll send over the formal proposal by tomorrow.
[00:04:10] p-arjun-001: One concern — your uptime SLA says 99.99%. What's the resolution time if there's an outage?
[00:04:25] c9f2a7: Critical issues — 15 minute response, 1 hour resolution. That's in the contract.
[00:04:38] p-arjun-001: Okay, that's acceptable. We'll review the proposal and be in touch.
"""
