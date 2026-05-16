"""Fixture: sales-bd meeting"""

METADATA = {
    "meeting_id": "meet-sales-001",
    "project_id": "PROJ-SALES-NEW",
    "date": "2025-05-06",
    "meeting_type": "sales-bd",
    "duration_minutes": 42,
    "security_level": "CONFIDENTIAL",
    "organiser_id": "p-ba-001",
    "attendee_count_internal": 2,
    "attendee_count_external": 1,
    "language_mix": "hinglish",
    "series_id": None,
    "client_id": None,
}

ATTENDEES = [
    {"intranet_id": "p-ba-001", "name": "Ananya Rao", "department": "BA", "role": "Business Analyst", "type": "internal"},
    {"intranet_id": "p-vikram-am", "name": "Vikram Singh", "department": "Delivery", "role": "Account Manager", "type": "internal"},
    {"intranet_id": None, "name_hash": "b7d4e1", "type": "external"},
]

TRANSCRIPT = """[00:01:00] p-vikram-am: Thank you for taking the time. We'd love to understand more about what you're looking to build.
[00:01:15] b7d4e1: We need a mobile app — both iOS and Android — for our field sales team. Currently everything is on paper which is very inefficient.
[00:01:35] p-ba-001: What kind of features are you thinking?
[00:01:50] b7d4e1: Order tracking, customer visit logs, GPS check-in, offline mode since our sales guys are often in areas with poor connectivity.
[00:02:15] p-vikram-am: That's a solid scope. How many field agents would use this?
[00:02:25] b7d4e1: Around 80 right now, possibly scaling to 200 in a year.
[00:02:38] p-ba-001: And on the timeline — when are you hoping to go live?
[00:02:50] b7d4e1: Ideally before Diwali. So October-ish.
[00:03:05] p-vikram-am: That's roughly 5 months. Feasible for an MVP. Budget — do you have a range in mind?
[00:03:20] b7d4e1: We have board approval for up to 40 lakhs for this project.
[00:03:35] p-vikram-am: That works. We'd be looking at a React Native app with a Python Django backend. Team of around 5-6 people, timeline of approximately 20-24 weeks for a full build.
[00:04:00] b7d4e1: That sounds reasonable. Who makes the final call on vendor selection at your end?
[00:04:15] p-vikram-am: It would go through our technical director and CEO.
[00:04:25] b7d4e1: On our side, the CTO is the decision maker. He's not on this call today but I will brief him.
[00:04:40] p-vikram-am: Got it. We'll prepare a detailed proposal. Ananya, can we send it by Friday?
[00:04:52] p-ba-001: Haan, Friday May 9th tak bhej sakte hain.
[00:05:05] b7d4e1: That works. Looking forward to it.
"""
