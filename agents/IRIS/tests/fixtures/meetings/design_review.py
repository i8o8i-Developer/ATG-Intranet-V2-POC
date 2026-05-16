"""Fixture: design-review meeting"""

METADATA = {
    "meeting_id": "meet-design-001",
    "project_id": "PROJ-CRM-0014",
    "date": "2025-05-07",
    "meeting_type": "design-review",
    "duration_minutes": 35,
    "security_level": "INTERNAL",
    "organiser_id": "p-uiux-001",
    "attendee_count_internal": 4,
    "attendee_count_external": 0,
    "language_mix": "hinglish",
    "series_id": None,
    "client_id": None,
}

ATTENDEES = [
    {"intranet_id": "p-uiux-001", "name": "Priya Nair", "department": "UIUX", "role": "UI/UX Designer", "type": "internal"},
    {"intranet_id": "p-dev-003", "name": "Dev Patel", "department": "REACT", "role": "Frontend Engineer", "type": "internal"},
    {"intranet_id": "p-arjun-001", "name": "Arjun Mehta", "department": "PYDJANGO", "role": "Backend Engineer", "type": "internal"},
    {"intranet_id": "p-rohan-pm", "name": "Rohan Sharma", "department": "Delivery", "role": "Project Manager", "type": "internal"},
]

TRANSCRIPT = """[00:01:00] p-uiux-001: Okay team, yeh Dashboard UI mockups ka third review hai. Maine v3 updated kiye hain based on last feedback. Let me share screen.
[00:01:30] p-dev-003: Okay I can see it. Overall looks much better than v2.
[00:02:00] p-rohan-pm: Haan, improvement dikh raha hai. Ek issue — data cards pe colour contrast thoda low hai. Accessibility standards meet nahi kar raha.
[00:02:20] p-uiux-001: Haan mujhe bhi that lag raha tha. Main May 8th tak fix kar sakti hoon.
[00:02:35] p-dev-003: Yeh issue minor hai but fix karna zaroori hai before we implement.
[00:02:50] p-arjun-001: Backend side se mujhe koi issue nahi hai design ke saath. API compatible hai.
[00:03:05] p-rohan-pm: Okay so — conditional approval. Priya fixes the colour contrast issue by May 8th, then we're good to proceed. Is this blocking dev work?
[00:03:20] p-dev-003: Haan, main implementation start nahi kar sakta until final approved mockups hain. So yes it's blocking.
[00:03:35] p-rohan-pm: Understood. Priya, May 8th is the deadline. SOW mein dashboard UI clearly included hai, so we're aligned there.
[00:03:50] p-uiux-001: Confirmed, will be done by May 8th.
[00:04:00] p-rohan-pm: Good. Next review after colour fix. Thanks everyone.
"""
