"""Fixture: standup meeting"""

METADATA = {
    "meeting_id": "meet-standup-001",
    "project_id": "PROJ-CRM-0014",
    "date": "2025-05-06",
    "meeting_type": "standup",
    "duration_minutes": 18,
    "security_level": "INTERNAL",
    "organiser_id": "p-rohan-pm",
    "attendee_count_internal": 6,
    "attendee_count_external": 0,
    "language_mix": "hinglish",
    "series_id": "standup-crm-daily",
    "client_id": None,
}

ATTENDEES = [
    {"intranet_id": "p-rohan-pm", "name": "Rohan Sharma", "department": "Delivery", "role": "Project Manager", "type": "internal"},
    {"intranet_id": "p-arjun-001", "name": "Arjun Mehta", "department": "PYDJANGO", "role": "Backend Engineer", "type": "internal"},
    {"intranet_id": "p-rohit-002", "name": "Rohit Verma", "department": "PYDJANGO", "role": "Backend Engineer", "type": "internal"},
    {"intranet_id": "p-dev-003", "name": "Dev Patel", "department": "REACT", "role": "Frontend Engineer", "type": "internal"},
    {"intranet_id": "p-uiux-001", "name": "Priya Nair", "department": "UIUX", "role": "UI/UX Designer", "type": "internal"},
    {"intranet_id": "p-ba-001", "name": "Ananya Rao", "department": "BA", "role": "Business Analyst", "type": "internal"},
]

TRANSCRIPT = """[00:00:30] p-rohan-pm: Okay team, let's start the standup. Arjun, you go first.
[00:00:38] p-arjun-001: Haan, yesterday maine api-gateway ka authentication middleware complete kiya. Aaj dekhna hai rate limiting. Ek issue hai — gateway ki complexity jo humne estimate ki thi usse kaafi zyada hai, almost 40% more. Yellow ho raha hoon is task pe.
[00:01:10] p-rohan-pm: Okay, noted. Rohit?
[00:01:14] p-rohit-002: Main abhi bhi CRM credentials ka wait kar raha hoon. BA team ne request bheji thi client ko, but credentials nahi mile abhi tak. Yeh 3 din se same blocker hai. Bina credentials ke staging environment setup nahi kar sakta.
[00:01:45] p-rohan-pm: Haan yeh serious hai. Ananya, BA side se kya update hai?
[00:01:52] p-ba-001: Maine 2 din pehle client ko email kiya tha. Reminder bheja kal bhi. Abhi tak koi response nahi aaya. Main aaj Vikram ko bolunga ki wo escalate kare.
[00:02:10] p-rohan-pm: Theek hai. Dev?
[00:02:14] p-dev-003: [silence]
[00:02:20] p-rohan-pm: Dev? Kya tum sun rahe ho?
[00:02:25] p-dev-003: [no response]
[00:02:30] p-rohan-pm: Okay Dev ne respond nahi kiya, yeh 2nd consecutive day hai. Priya?
[00:02:35] p-uiux-001: Main dashboard mockups v3 pe kaam kar rahi hoon, aaj evening tak complete ho jayega. Sab green hai mere paas.
[00:02:55] p-rohan-pm: Good. Ananya, tumhara update?
[00:03:00] p-ba-001: Requirements document review complete kar liya. Client sign-off pending hai. Green hoon baki sab pe.
[00:03:15] p-rohan-pm: Okay. Ek aur cheez — Arjun ne mention kiya tha kal ki auth module mein ek hotfix ki zaroorat hai. Arjun, can you elaborate?
[00:03:25] p-arjun-001: Haan, production pe ek edge case mila jisme token refresh nahi ho raha correctly. Yeh blocker hai for integration testing. Aaj prioritize karna padega.
[00:03:45] p-rohan-pm: Alright. Rohit ka blocker 3 din se hai, Dev aaj bhi absent hai — main inhe directly ping karunga. Kal milte hain. Bye.
"""
