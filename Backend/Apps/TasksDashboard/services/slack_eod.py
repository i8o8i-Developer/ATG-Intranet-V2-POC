import os
from datetime import date, datetime

import requests
from django.db import transaction
from django.utils import timezone

from Backend.Apps.TasksDashboard.models import DailyStatusEntry, SlackDeliveryMessage, SlackDeliveryThread, WorkEntry
from Backend.Apps.Users.models import Department, EmployeeProfile
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class SlackAPIError(Exception):
    pass


class SlackRateLimitError(SlackAPIError):
    def __init__(self, message, retry_after=60):
        super().__init__(message)
        self.retry_after = retry_after


class SlackEODService:
    base_url = "https://slack.com/api"

    def __init__(self, context, token=None, timeout=15, session=None, live=False):
        self.context = context
        self.token = token or os.getenv("SLACK_BOT_TOKEN", "")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.live = live

    def _headers(self):
        if not self.token:
            raise SlackAPIError("SLACK_BOT_TOKEN Is Not Configured.")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _request(self, endpoint, payload):
        if not self.live:
            return {"ok": True, "ts": f"dry-{timezone.now().timestamp()}", "dry_run": True, "payload": payload}

        response = self.session.post(
            f"{self.base_url}/{endpoint}",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise SlackRateLimitError("Slack API Rate Limit Exceeded.", retry_after=retry_after)
        if response.status_code >= 500:
            raise SlackAPIError(f"Slack API Server Error ({response.status_code}).")

        data = response.json()
        if not data.get("ok"):
            error_code = data.get("error", "unknown_error")
            if error_code == "ratelimited":
                retry_after = int(response.headers.get("Retry-After", "60"))
                raise SlackRateLimitError("Slack API Rate Limit Exceeded.", retry_after=retry_after)
            raise SlackAPIError(f"Slack API Error: {error_code}")
        return data

    def post_message(self, channel_id, text, blocks=None, thread_ts=None):
        payload = {"channel": channel_id, "text": text}
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts
        return self._request("chat.postMessage", payload)

    def update_message(self, channel_id, ts, text, blocks=None):
        payload = {"channel": channel_id, "ts": ts, "text": text}
        if blocks:
            payload["blocks"] = blocks
        return self._request("chat.update", payload)

    def _parse_date(self, value):
        if not value:
            return timezone.localdate()
        if isinstance(value, date):
            return value
        return datetime.strptime(str(value), "%Y-%m-%d").date()

    def _employee_from_subject(self, subject):
        if isinstance(subject, EmployeeProfile):
            return subject
        queryset = EmployeeProfile.objects.filter(tenant=self.context.tenant).select_related("user", "department")
        if isinstance(subject, int) or str(subject).isdigit():
            return queryset.filter(id=subject).first() or queryset.filter(user_id=subject).first()
        if hasattr(subject, "new_employee_profiles"):
            return queryset.filter(user=subject).first()
        return None

    def get_department_for_employee(self, employee):
        if employee and employee.department_id:
            return employee.department
        raise SlackAPIError(f"No Department Mapping Found For Employee {getattr(employee, 'id', '')}.")

    def get_department_for_user(self, user):
        employee = self._employee_from_subject(user)
        return self.get_department_for_employee(employee)

    def get_channel_mapping(self, department, fallback_channel_name="daily-eod"):
        metadata = department.metadata or {}
        channel_id = (
            metadata.get("slack_channel_id")
            or metadata.get("slackChannelId")
            or metadata.get("slack_channel")
            or metadata.get("slackChannel")
            or fallback_channel_name
        )
        return {"channel_id": channel_id, "channel_name": metadata.get("slack_channel_name") or fallback_channel_name}

    def build_parent_text(self, department, report_date):
        return f"EOD Reports - {report_date.isoformat()} - {department.name}"

    def build_parent_blocks(self, department, report_date):
        return [
            {"type": "header", "text": {"type": "plain_text", "text": f"EOD Reports - {report_date.isoformat()}"}},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Department:* {department.name}\nEmployee Reports For The Day Will Appear In This Thread.",
                },
            },
        ]

    def _work_entries_for_employee(self, employee, report_date):
        return list(
            WorkEntry.objects.filter(tenant=self.context.tenant, employee=employee, entry_date=report_date)
            .select_related("work_item", "work_item__project")
            .order_by("work_item__project__name", "work_item__title")
        )

    def build_employee_text(self, employee, department, report_date, daily_status, work_entries=None):
        lines = [
            f"EOD Report - {employee.display_name}",
            f"Department: {department.name}",
            f"Date: {report_date.isoformat()}",
            "",
            "Summary:",
            daily_status.summary or "No Summary Provided.",
        ]
        if daily_status.blockers:
            lines.extend(["", "Blockers:", daily_status.blockers])
        if daily_status.next_plan:
            lines.extend(["", "Next Plan:", daily_status.next_plan])
        for index, entry in enumerate(work_entries or [], start=1):
            project_name = entry.work_item.project.name if entry.work_item and entry.work_item.project_id else "No Project"
            lines.extend(["", f"{index}. [{project_name}] {entry.work_item.title}", entry.summary or f"{entry.minutes} Minutes Logged."])
        return "\n".join(lines).strip()

    def build_employee_blocks(self, employee, department, report_date, daily_status, work_entries=None):
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Employee:* {employee.display_name}\n"
                        f"*Username:* `{employee.user.username}`\n"
                        f"*Department:* {department.name}\n"
                        f"*Date:* {report_date.isoformat()}"
                    ),
                },
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Summary:*\n{daily_status.summary or 'No Summary Provided.'}"}},
        ]
        if daily_status.blockers:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Blockers:*\n{daily_status.blockers}"}})
        if daily_status.next_plan:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Next Plan:*\n{daily_status.next_plan}"}})
        if work_entries:
            blocks.append({"type": "divider"})
        for entry in work_entries or []:
            project_name = entry.work_item.project.name if entry.work_item and entry.work_item.project_id else "No Project"
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Task:* {entry.work_item.title}\n*Project:* {project_name}\n*Update:*\n{entry.summary or f'{entry.minutes} Minutes Logged.'}",
                    },
                }
            )
        return blocks

    @transaction.atomic
    def ensure_daily_thread(self, department, report_date, channel_id, channel_name="daily-eod"):
        thread_key = f"{department.code or department.id}:{channel_name}:{report_date.isoformat()}"
        daily_thread, _created = SlackDeliveryThread.objects.select_for_update().get_or_create(
            tenant=self.context.tenant,
            thread_key=thread_key,
            defaults={
                "workspace": self.context.workspace,
                "channel_name": channel_name,
                "channel_id": channel_id,
                "thread_date": report_date,
                "status": "Open",
                "created_by": self.context.actor,
                "updated_by": self.context.actor,
            },
        )
        if daily_thread.external_id:
            return daily_thread

        response = self.post_message(
            channel_id=channel_id,
            text=self.build_parent_text(department, report_date),
            blocks=self.build_parent_blocks(department, report_date),
        )
        daily_thread.channel_id = channel_id
        daily_thread.channel_name = channel_name
        daily_thread.external_id = response["ts"]
        daily_thread.status = "Sent" if self.live else "DryRun"
        daily_thread.updated_by = self.context.actor
        daily_thread.save(update_fields=["channel_id", "channel_name", "external_id", "status", "updated_by", "updated_at"])
        return daily_thread

    def sync_user_report(self, subject, report_date=None):
        report_date = self._parse_date(report_date)
        employee = self._employee_from_subject(subject)
        if not employee:
            raise SlackAPIError("Employee Profile Not Found For EOD Slack Sync.")
        department = self.get_department_for_employee(employee)
        channel_mapping = self.get_channel_mapping(department)
        daily_status = DailyStatusEntry.objects.filter(tenant=self.context.tenant, employee=employee, status_date=report_date).first()
        if not daily_status:
            raise SlackAPIError(f"No EOD Entry Found For Employee {employee.id} On {report_date}.")

        daily_thread = self.ensure_daily_thread(department, report_date, channel_mapping["channel_id"], channel_mapping["channel_name"])
        slack_message, _created = SlackDeliveryMessage.objects.get_or_create(
            tenant=self.context.tenant,
            thread=daily_thread,
            daily_status=daily_status,
            defaults={"workspace": self.context.workspace or daily_status.workspace, "employee": employee},
        )
        work_entries = self._work_entries_for_employee(employee, report_date)
        text = self.build_employee_text(employee, department, report_date, daily_status, work_entries)
        blocks = self.build_employee_blocks(employee, department, report_date, daily_status, work_entries)

        try:
            if slack_message.slack_message_ts:
                response = self.update_message(daily_thread.channel_id, slack_message.slack_message_ts, text=text, blocks=blocks)
            else:
                response = self.post_message(daily_thread.channel_id, text=text, blocks=blocks, thread_ts=daily_thread.external_id)
            slack_message.slack_message_ts = response["ts"]
            slack_message.status = "Sent" if self.live else "DryRun"
            slack_message.failure_reason = ""
            slack_message.payload = {"text": text, "blocks": blocks, "dry_run": not self.live}
            daily_status.submitted_to_slack = True
            daily_status.slack_thread = daily_thread
            daily_status.slack_message_ts = slack_message.slack_message_ts
            daily_status.save(update_fields=["submitted_to_slack", "slack_thread", "slack_message_ts", "updated_at"])
        except SlackAPIError as exc:
            slack_message.status = "Failed"
            slack_message.failure_reason = str(exc)
            slack_message.payload = {"text": text, "blocks": blocks, "dry_run": not self.live}
            slack_message.save(update_fields=["status", "failure_reason", "payload", "updated_at"])
            raise

        slack_message.save(update_fields=["slack_message_ts", "status", "failure_reason", "payload", "updated_at"])
        OutboxService.publish(self.context, "SlackDeliveryMessage", slack_message.id, "EODSlackUserReportSynced", {"employeeId": employee.id, "dryRun": not self.live})
        return slack_message

    def build_department_summary(self, department, report_date):
        employees = EmployeeProfile.objects.filter(tenant=self.context.tenant, department=department, is_active=True)
        submitted_count = DailyStatusEntry.objects.filter(tenant=self.context.tenant, employee__in=employees, status_date=report_date).values("employee_id").distinct().count()
        total_users = employees.count()
        missing_count = max(total_users - submitted_count, 0)
        text = f"EOD Summary For {department.name} On {report_date.isoformat()}: {submitted_count}/{total_users} Employees Submitted. Missing: {missing_count}."
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Daily EOD Summary*\n*Department:* {department.name}\n*Date:* {report_date.isoformat()}\n*Submitted:* {submitted_count}/{total_users}\n*Missing:* {missing_count}",
                },
            }
        ]
        return text, blocks

    def build_missing_eod_reminder(self, department, report_date):
        employees = EmployeeProfile.objects.filter(tenant=self.context.tenant, department=department, is_active=True).select_related("user")
        submitted_employee_ids = set(DailyStatusEntry.objects.filter(tenant=self.context.tenant, employee__in=employees, status_date=report_date).values_list("employee_id", flat=True))
        missing_names = [employee.display_name for employee in employees if employee.id not in submitted_employee_ids]
        if not missing_names:
            return None, None
        user_lines = "\n".join(f"- {name}" for name in missing_names[:50])
        text = f"EOD Reminder For {department.name}: {len(missing_names)} Employees Have Not Submitted Their EOD For {report_date.isoformat()}."
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*EOD Reminder*\n*Department:* {department.name}\n*Date:* {report_date.isoformat()}\n*Pending Submissions:* {len(missing_names)}\n{user_lines}",
                },
            }
        ]
        return text, blocks

    def send_department_daily_summary(self, status_date=None, channel_name="daily-eod", department_id=None):
        report_date = self._parse_date(status_date)
        departments = Department.objects.filter(tenant=self.context.tenant, employees__daily_status_entries__status_date=report_date).distinct()
        if department_id:
            departments = departments.filter(id=department_id)
        thread_ids = []
        message_ids = []
        for department in departments:
            channel_mapping = self.get_channel_mapping(department, fallback_channel_name=channel_name)
            thread = self.ensure_daily_thread(department, report_date, channel_mapping["channel_id"], channel_mapping["channel_name"])
            summary_text, summary_blocks = self.build_department_summary(department, report_date)
            summary_message, _created = SlackDeliveryMessage.objects.update_or_create(
                tenant=self.context.tenant,
                thread=thread,
                daily_status=None,
                employee=None,
                defaults={
                    "workspace": self.context.workspace or thread.workspace,
                    "status": "Sent" if self.live else "DryRun",
                    "payload": {"text": summary_text, "blocks": summary_blocks, "dry_run": not self.live},
                },
            )
            response = self.post_message(thread.channel_id, text=summary_text, blocks=summary_blocks, thread_ts=thread.external_id)
            summary_message.slack_message_ts = response["ts"]
            summary_message.save(update_fields=["slack_message_ts", "status", "payload", "updated_at"])
            thread_ids.append(thread.id)
            message_ids.append(summary_message.id)
            for entry in DailyStatusEntry.objects.filter(tenant=self.context.tenant, status_date=report_date, employee__department=department):
                synced = self.sync_user_report(entry.employee, report_date)
                message_ids.append(synced.id)
        OutboxService.publish(self.context, "SlackDeliveryThread", ",".join(str(item) for item in thread_ids), "EODSlackDepartmentSummarySynced", {"count": len(message_ids), "dryRun": not self.live})
        return ServiceResult.success({"threadIds": thread_ids, "messageIds": message_ids, "count": len(message_ids)})

    def send_missing_eod_reminders(self, status_date=None, channel_name="daily-eod", department_id=None):
        report_date = self._parse_date(status_date)
        departments = Department.objects.filter(tenant=self.context.tenant, employees__is_active=True).distinct()
        if department_id:
            departments = departments.filter(id=department_id)
        message_ids = []
        for department in departments:
            reminder_text, reminder_blocks = self.build_missing_eod_reminder(department, report_date)
            if not reminder_text:
                continue
            channel_mapping = self.get_channel_mapping(department, fallback_channel_name=channel_name)
            thread = self.ensure_daily_thread(department, report_date, channel_mapping["channel_id"], channel_mapping["channel_name"])
            response = self.post_message(thread.channel_id, text=reminder_text, blocks=reminder_blocks, thread_ts=thread.external_id)
            reminder_message = SlackDeliveryMessage.objects.create(
                tenant=self.context.tenant,
                workspace=self.context.workspace or thread.workspace,
                thread=thread,
                status="Sent" if self.live else "DryRun",
                slack_message_ts=response["ts"],
                payload={"text": reminder_text, "blocks": reminder_blocks, "dry_run": not self.live},
                created_by=self.context.actor,
                updated_by=self.context.actor,
            )
            message_ids.append(reminder_message.id)
        OutboxService.publish(self.context, "SlackDeliveryMessage", ",".join(str(item) for item in message_ids), "EODSlackMissingRemindersSynced", {"count": len(message_ids), "dryRun": not self.live})
        return ServiceResult.success({"messageIds": message_ids, "count": len(message_ids)})