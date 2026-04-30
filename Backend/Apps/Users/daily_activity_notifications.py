from Backend.Apps.Users.services import UserWorkflowService


class DailyActivityNotificationService:
    @staticmethod
    def send_eod_reminders(context):
        return UserWorkflowService.create_daily_activity_reminders(context, reminder_type="EOD")

    @staticmethod
    def send_bounty_reminders(context):
        return UserWorkflowService.create_daily_activity_reminders(context, reminder_type="Bounty")

    @staticmethod
    def send_leave_reminders(context):
        return UserWorkflowService.create_daily_activity_reminders(context, reminder_type="Leave")

    @staticmethod
    def send_all(context):
        results = {
            "eod": DailyActivityNotificationService.send_eod_reminders(context).data,
            "bounty": DailyActivityNotificationService.send_bounty_reminders(context).data,
            "leave": DailyActivityNotificationService.send_leave_reminders(context).data,
        }
        return results
