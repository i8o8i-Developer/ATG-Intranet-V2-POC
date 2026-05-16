"""Fixture: client-call meeting"""

METADATA = {
    "meeting_id": "meet-client-001",
    "project_id": "PROJ-CRM-0014",
    "date": "2025-05-06",
    "meeting_type": "client-call",
    "duration_minutes": 47,
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
    {"intranet_id": "p-vikram-am", "name": "Vikram Singh", "department": "Delivery", "role": "Account Manager", "type": "internal"},
    {"intranet_id": "p-arjun-001", "name": "Arjun Mehta", "department": "PYDJANGO", "role": "Backend Engineer", "type": "internal"},
    {"intranet_id": None, "name_hash": "a3f9c2", "type": "external"},
]

TRANSCRIPT = """[00:01:00] p-rohan-pm: Good afternoon everyone. Let's get started. First I want to address the credentials issue that's been pending.
[00:01:15] a3f9c2: Yes I was going to bring that up too. We are very frustrated. Your team has been asking for these API credentials for 10 days now. This is completely unacceptable.
[00:01:35] p-vikram-am: We completely understand your frustration. This delay has impacted our staging setup significantly.
[00:01:50] a3f9c2: I spoke to our IT team this morning. They will share the credentials by end of day Thursday at the latest. I am committing to this personally.
[00:02:10] p-rohan-pm: Thank you, that's helpful. Just to confirm — Thursday EOD means May 8th, correct?
[00:02:18] a3f9c2: Yes, May 8th.
[00:02:25] p-rohan-pm: Noted. From our side, Vikram had committed to share the staging environment access last call. Vikram, can you confirm?
[00:02:35] p-vikram-am: Yes that's done. Staging access was shared on May 3rd via email.
[00:02:45] a3f9c2: Yes we received that, thank you.
[00:03:00] a3f9c2: One thing I wanted to raise — we had discussed earlier that a reporting dashboard would be very useful for our operations team. Is this in the current scope?
[00:03:20] p-rohan-pm: The reporting dashboard is not in the current SOW. It falls under Phase 2 as per our initial agreement.
[00:03:35] a3f9c2: I understand but honestly for us it is very high priority. We need it before go-live. Can we discuss including it?
[00:03:50] p-rohan-pm: We can look into it but it would require a change request. Let us assess the effort and come back to you.
[00:04:05] a3f9c2: Also I want to be clear — our board has set May 30th as the absolute go-live deadline. There is no flexibility on this date.
[00:04:20] p-rohan-pm: Understood. We are targeting that date as well but the credential delay has put M1 at risk. If we don't receive credentials by Thursday, the May 30th deadline becomes very difficult to meet.
[00:04:40] a3f9c2: I understand. Thursday is confirmed from our side.
[00:04:55] p-rohan-pm: Let's schedule our next check-in for May 9th to confirm credentials received and staging setup complete.
[00:05:05] a3f9c2: Agreed.
[00:05:10] p-rohan-pm: Okay, thank you everyone. Talk on May 9th.
"""
