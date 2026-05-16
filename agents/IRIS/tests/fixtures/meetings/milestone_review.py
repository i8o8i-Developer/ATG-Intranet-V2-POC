"""Fixture: milestone-review meeting"""

METADATA = {
    "meeting_id": "meet-milestone-001",
    "project_id": "PROJ-CRM-0014",
    "date": "2025-05-07",
    "meeting_type": "milestone-review",
    "duration_minutes": 55,
    "security_level": "INTERNAL",
    "organiser_id": "p-rohan-pm",
    "attendee_count_internal": 3,
    "attendee_count_external": 1,
    "language_mix": "hinglish",
    "series_id": None,
    "client_id": "CLIENT-ACME-001",
}

ATTENDEES = [
    {"intranet_id": "p-rohan-pm", "name": "Rohan Sharma", "department": "Delivery", "role": "Project Manager", "type": "internal"},
    {"intranet_id": "p-arjun-001", "name": "Arjun Mehta", "department": "PYDJANGO", "role": "Backend Engineer", "type": "internal"},
    {"intranet_id": "p-vikram-am", "name": "Vikram Singh", "department": "Delivery", "role": "Account Manager", "type": "internal"},
    {"intranet_id": None, "name_hash": "a3f9c2", "type": "external"},
]

TRANSCRIPT = """[00:01:00] p-rohan-pm: Thank you for joining the M1 milestone review. We have two deliverables to review today — the requirements document and the architecture diagram.
[00:01:30] a3f9c2: Sure. Let's start with the requirements document. We reviewed it last week. Our team is happy with it. Accepted.
[00:01:50] p-rohan-pm: Great. And the architecture diagram?
[00:02:05] a3f9c2: The architecture diagram — we have some concerns. The data flow for the reporting module is not clearly shown. We need that to be added before we can sign off.
[00:02:30] p-arjun-001: Okay, main yeh update kar sakta hoon. Ek week mein ho jayega.
[00:02:45] p-rohan-pm: So architecture diagram is rejected pending rework. Arjun will update by May 12th. Does that work?
[00:02:55] a3f9c2: Yes that works.
[00:03:10] p-rohan-pm: Since M1 is partial — requirements accepted, architecture pending — the payment for M1 is not triggered yet. It will trigger once architecture is signed off.
[00:03:30] a3f9c2: Understood.
[00:03:40] p-rohan-pm: M2 start is dependent on M1 completion. So M2 is at risk until the architecture rework is done and signed off.
[00:03:55] a3f9c2: I understand. Please make sure Arjun delivers by the 12th.
[00:04:05] p-arjun-001: Confirmed.
[00:04:15] p-rohan-pm: Overall are you satisfied with the progress so far?
[00:04:25] a3f9c2: It's okay. Not great, not bad. The credential delay was frustrating but I understand things are moving now.
[00:04:40] p-rohan-pm: Thank you. We'll follow up once the architecture diagram is updated.
"""
