"""Fixture: sprint-planning meeting"""

METADATA = {
    "meeting_id": "meet-sprint-001",
    "project_id": "PROJ-CRM-0014",
    "date": "2025-05-05",
    "meeting_type": "sprint-planning",
    "duration_minutes": 65,
    "security_level": "INTERNAL",
    "organiser_id": "p-rohan-pm",
    "attendee_count_internal": 5,
    "attendee_count_external": 0,
    "language_mix": "hinglish",
    "series_id": None,
    "client_id": None,
}

ATTENDEES = [
    {"intranet_id": "p-rohan-pm", "name": "Rohan Sharma", "department": "Delivery", "role": "Project Manager", "type": "internal"},
    {"intranet_id": "p-arjun-001", "name": "Arjun Mehta", "department": "PYDJANGO", "role": "Backend Engineer", "type": "internal"},
    {"intranet_id": "p-rohit-002", "name": "Rohit Verma", "department": "PYDJANGO", "role": "Backend Engineer", "type": "internal"},
    {"intranet_id": "p-dev-003", "name": "Dev Patel", "department": "REACT", "role": "Frontend Engineer", "type": "internal"},
    {"intranet_id": "p-uiux-001", "name": "Priya Nair", "department": "UIUX", "role": "UI/UX Designer", "type": "internal"},
]

TRANSCRIPT = """[00:01:00] p-rohan-pm: Okay team, Sprint 6 planning start karte hain. Pehle last sprint ka retrospective — W19 mein humne jo plan kiya tha uska sirf 60% complete hua. Yeh concerning hai.
[00:01:30] p-arjun-001: Haan, api-gateway ne bohot time le liya. Complexity underestimate thi.
[00:02:00] p-rohan-pm: Theek hai. Is sprint mein hum reporting dashboard ko scope se bahar rakhenge — yeh Phase 2 mein jayega. Yeh decision final hai.
[00:02:20] p-arjun-001: Agreed. Dashboard ke bina bhi bohot kaam hai.
[00:02:35] p-rohan-pm: API versioning approach — last sync mein yeh open tha. Arjun, kya resolve hua?
[00:02:45] p-arjun-001: Haan, humne v2 endpoint approach decide kiya. Yeh resolve ho gaya.
[00:03:00] p-rohan-pm: Good. Database migration strategy abhi bhi open hai. Yeh 2nd time defer ho raha hai.
[00:03:15] p-arjun-001: Main is sprint mein handle nahi kar sakta without credentials. Next sync tak defer karte hain.
[00:03:30] p-rohan-pm: Theek hai. Arjun, api-gateway complexity — is pe koi risk mitigation plan hai?
[00:03:45] p-arjun-001: Abhi koi formal plan nahi hai. Main spike lena chahta hoon — 2 days — to properly understand the scope.
[00:04:00] p-rohan-pm: Okay, spike approve hai. Risk medium consider karte hain for now.
[00:04:20] p-dev-003: Ek dependency hai meri — UIUX team se final mockups chahiye dashboard feed ke liye. Priya, kab milenge?
[00:04:35] p-uiux-001: Main May 8th tak de sakti hoon.
[00:04:45] p-dev-003: That works.
[00:05:00] p-rohan-pm: Alright, let's lock this. Sprint 6 scope is finalized without reporting dashboard. Api-gateway risk is flagged, Arjun will take spike. Database migration deferred again. Any objections?
[00:05:20] p-arjun-001: No objections.
[00:05:25] p-rohan-pm: Okay, let's go. Next sync on Friday.
"""
