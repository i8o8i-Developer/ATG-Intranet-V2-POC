"""Fixture: hr meeting"""

METADATA = {
    "meeting_id": "meet-hr-001",
    "project_id": "INTERNAL-HR",
    "date": "2025-05-06",
    "meeting_type": "hr",
    "duration_minutes": 30,
    "security_level": "CONFIDENTIAL",
    "organiser_id": "hr-head",
    "attendee_count_internal": 2,
    "attendee_count_external": 0,
    "language_mix": "hinglish",
    "series_id": None,
    "client_id": None,
}

ATTENDEES = [
    {"intranet_id": "hr-head", "name": "Sunita Kapoor", "department": "HR", "role": "HR Head", "type": "internal"},
    {"intranet_id": "hr-assoc-001", "name": "Meera Joshi", "department": "HR", "role": "HR Associate", "type": "internal"},
]

TRANSCRIPT = """[00:01:00] hr-head: Meera, aaj ki meeting hiring ke baare mein hai. REACT team ne 2 React Native engineers ki request ki hai PROJ-CRM ke liye.
[00:01:25] hr-assoc-001: Haan, mujhe Delivery team se request mili hai. Kya hum approve kar sakte hain?
[00:01:40] hr-head: Haan, main approve karti hoon. 2 React Native engineers hire karne hain. May 15th tak JDs post ho jaane chahiye.
[00:02:00] hr-assoc-001: Main kal hi JD draft karungi. Kisi specific seniority level ki zaroorat hai?
[00:02:15] hr-head: Mid to senior level. 3+ years React Native experience.
[00:02:30] hr-assoc-001: Okay. Kya attrition ki koi concern hai team mein?
[00:02:45] hr-head: Abhi nahi. Sab stable lag raha hai. Hiring velocity on-track hai overall.
[00:03:00] hr-assoc-001: Theek hai. Main May 9th tak JDs finalize karke post kar dungi.
[00:03:15] hr-head: Perfect. Aur overall team morale — amber hai. Kuch logon ne workload ke baare mein concerns raise kiye hain last week. Keep an eye on that.
[00:03:35] hr-assoc-001: Noted, I'll check in with team leads this week.
[00:03:45] hr-head: Good. That's all for today.
"""
