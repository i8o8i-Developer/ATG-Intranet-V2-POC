"""Fixture: cross-dept meeting"""

METADATA = {
    "meeting_id": "meet-crossdept-001",
    "project_id": "PROJ-CRM-0014",
    "date": "2025-05-06",
    "meeting_type": "cross-dept",
    "duration_minutes": 25,
    "security_level": "INTERNAL",
    "organiser_id": "p-arjun-001",
    "attendee_count_internal": 3,
    "attendee_count_external": 0,
    "language_mix": "hinglish",
    "series_id": None,
    "client_id": None,
}

ATTENDEES = [
    {"intranet_id": "p-arjun-001", "name": "Arjun Mehta", "department": "PYDJANGO", "role": "Backend Engineer", "type": "internal"},
    {"intranet_id": "p-dev-003", "name": "Dev Patel", "department": "REACT", "role": "Frontend Engineer", "type": "internal"},
    {"intranet_id": "p-rohan-pm", "name": "Rohan Sharma", "department": "Delivery", "role": "Project Manager", "type": "internal"},
]

TRANSCRIPT = """[00:00:30] p-arjun-001: Okay, yeh meeting specifically API contract ke baare mein hai dashboard feed ke liye. Dev, tumhare kya requirements hain?
[00:00:50] p-dev-003: Mujhe ek REST endpoint chahiye jo dashboard ke liye data return kare — project metrics, task counts, and team velocity. Pagination bhi chahiye.
[00:01:10] p-arjun-001: Theek hai. Main propose karta hoon v2 endpoint — /api/v2/dashboard-feed. JSON response with the fields you mentioned. Pagination we'll do cursor-based.
[00:01:30] p-dev-003: Cursor-based sounds good. What about rate limiting?
[00:01:45] p-arjun-001: Rate limiting pe abhi decision nahi hua hai. Mujhe backend team se discuss karna padega. May 8th tak confirm kar sakta hoon.
[00:02:00] p-dev-003: That works. But yeh block kar raha hai mera frontend work until schema is final.
[00:02:15] p-arjun-001: API schema I can confirm today — v2 endpoint, cursor pagination, JSON. Rate limiting is the only open item. Yeh toh main May 8th tak de dunga.
[00:02:30] p-dev-003: Okay, so API schema is resolved, rate limiting is still open?
[00:02:38] p-arjun-001: Correct.
[00:02:45] p-rohan-pm: Good. Let's document this. API schema finalized, rate limiting open with May 8th deadline. Arjun owns that. Anything else?
[00:03:00] p-dev-003: Nahi, that covers it.
[00:03:08] p-rohan-pm: Okay, thanks both.
"""
