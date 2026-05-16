"""Fixture: company-allhands meeting"""

METADATA = {
    "meeting_id": "meet-allhands-001",
    "project_id": "INTERNAL-COMPANY",
    "date": "2025-05-02",
    "meeting_type": "company-allhands",
    "duration_minutes": 60,
    "security_level": "INTERNAL",
    "organiser_id": "ceo",
    "attendee_count_internal": 165,
    "attendee_count_external": 0,
    "language_mix": "hinglish",
    "series_id": "monthly-allhands",
    "client_id": None,
}

ATTENDEES = [
    {"intranet_id": "ceo", "name": "Aditya Kumar", "department": "Leadership", "role": "CEO", "type": "internal"},
    {"intranet_id": "hr-head", "name": "Sunita Kapoor", "department": "HR", "role": "HR Head", "type": "internal"},
]

TRANSCRIPT = """[00:01:00] ceo: Good morning everyone. Welcome to our May all-hands. Bahut khushi ki baat hai — Q2 mein humne apna revenue target achieve kar liya. 18 crore ka target tha, humne 19.2 crore kiya. Yeh poori team ki mehnat ka result hai.
[00:02:00] ceo: Aage ke plans — Q3 mein hum React Native department ko 4 aur logon se expand karne ka plan kar rahe hain. Demand bohot zyada hai aur hum ready rehna chahte hain.
[00:03:00] hr-head: Ek announcement meri taraf se — we are launching a new L&D program next month. Every employee will get a learning budget of 5000 rupees per quarter for courses and certifications.
[00:04:00] ceo: Thank you Sunita. Kuch employees ne ek question raise kiya hai regarding remote work policy. Specifically — kya hum permanent remote remain karenge ya koi hybrid model aayega.
[00:04:30] ceo: I want to be transparent — we are evaluating this. No decision has been made yet. Hum next quarter tak ek clear policy announce karenge. I understand this creates uncertainty and I appreciate your patience.
[00:05:00] ceo: Koi aur questions?
[00:05:10] employee_voice_1: Sir, kya office reopening ka koi plan hai?
[00:05:20] ceo: Jaise maine kaha — next quarter mein decide karenge. Koi forced return is year nahi hoga.
[00:05:35] ceo: Alright, that's all for today. Thank you everyone. Milte hain next month.
"""
