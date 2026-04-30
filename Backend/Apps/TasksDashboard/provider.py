class TasksDashboardProvider:
    def __init__(self, live=False):
        self.live = live

    def fetch_clickup_tasks(self, project_name=""):
        return {"dry_run": not self.live, "project_name": project_name, "tasks": []}

    def send_slack_message(self, channel, text, thread_ts=""):
        return {"dry_run": not self.live, "channel": channel, "text": text, "thread_ts": thread_ts}