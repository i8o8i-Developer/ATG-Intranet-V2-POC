from Backend.Apps.TasksDashboard.services import EODService


class SlackAPIError(Exception):
    pass


class SlackRateLimitError(SlackAPIError):
    pass


class SlackEODService:
    def __init__(self, context, live=False):
        self.context = context
        self.live = live

    def send_department_daily_summary(self, status_date=None, channel_name="daily-eod"):
        return EODService.deliver_daily_summary(self.context, status_date=status_date, channel_name=channel_name, live=self.live)