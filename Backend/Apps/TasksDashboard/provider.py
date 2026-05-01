import os
import time

import requests


class TasksDashboardProviderError(Exception):
    pass


class TasksDashboardProvider:
    clickup_base_url = "https://api.clickup.com/api/v2"
    slack_base_url = "https://slack.com/api"

    def __init__(self, live=False, clickup_token=None, slack_token=None, session=None, timeout=20):
        self.live = live
        self.clickup_token = clickup_token or os.getenv("CLICKUP_API_TOKEN", "")
        self.slack_token = slack_token or os.getenv("SLACK_BOT_TOKEN", "")
        self.session = session or requests.Session()
        self.timeout = timeout

    def _request_json(self, method, url, headers=None, payload=None, max_retries=5):
        for attempt in range(max_retries):
            response = self.session.request(method, url, headers=headers or {}, json=payload, timeout=self.timeout)
            if response.status_code == 429:
                reset_header = response.headers.get("X-RateLimit-Reset") or response.headers.get("Retry-After")
                wait_seconds = int(reset_header or 1)
                if "X-RateLimit-Reset" in response.headers:
                    wait_seconds = max(wait_seconds - int(time.time()) + 1, 1)
                time.sleep(wait_seconds)
                continue
            if response.status_code >= 400:
                raise TasksDashboardProviderError(f"Provider request failed with {response.status_code}: {response.text}")
            return response.json() if response.content else {}
        raise TasksDashboardProviderError("Provider request failed after retry limit.")

    def _clickup_headers(self):
        if not self.clickup_token:
            raise TasksDashboardProviderError("CLICKUP_API_TOKEN is not configured.")
        return {"Authorization": self.clickup_token}

    def _slack_headers(self):
        if not self.slack_token:
            raise TasksDashboardProviderError("SLACK_BOT_TOKEN is not configured.")
        return {"Authorization": f"Bearer {self.slack_token}", "Content-Type": "application/json; charset=utf-8"}

    def fetch_clickup_tasks(self, project_name="", space_ids=None, team_id="", include_closed=False):
        if not self.live:
            return {"dry_run": True, "project_name": project_name, "tasks": []}
        tasks = []
        for space_id in space_ids or []:
            folders = self._request_json("GET", f"{self.clickup_base_url}/space/{space_id}/folder?archived=false", headers=self._clickup_headers()).get("folders", [])
            for folder in folders:
                lists = self._request_json("GET", f"{self.clickup_base_url}/folder/{folder['id']}/list", headers=self._clickup_headers()).get("lists", [])
                for task_list in lists:
                    if project_name and task_list.get("name") != project_name:
                        continue
                    list_tasks = self._request_json("GET", f"{self.clickup_base_url}/list/{task_list['id']}/task?archived=false&include_closed={str(include_closed).lower()}", headers=self._clickup_headers()).get("tasks", [])
                    for task in list_tasks:
                        task["clickup_project"] = task_list.get("name", "")
                        tasks.append(task)
                        if team_id and task.get("id"):
                            subtasks = self._request_json("GET", f"{self.clickup_base_url}/team/{team_id}/task?include_closed=true&page=&parent={task['id']}", headers=self._clickup_headers()).get("tasks", [])
                            for subtask in subtasks:
                                subtask["clickup_project"] = task_list.get("name", "")
                                subtask["parent"] = task.get("id")
                                tasks.append(subtask)
        return {"dry_run": False, "project_name": project_name, "tasks": tasks}

    def send_slack_message(self, channel, text, thread_ts="", blocks=None):
        payload = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        if blocks:
            payload["blocks"] = blocks
        if not self.live:
            return {"dry_run": True, **payload, "ts": "dry-run"}
        data = self._request_json("POST", f"{self.slack_base_url}/chat.postMessage", headers=self._slack_headers(), payload=payload)
        if not data.get("ok"):
            raise TasksDashboardProviderError(f"Slack API error: {data.get('error', 'unknown_error')}")
        return data