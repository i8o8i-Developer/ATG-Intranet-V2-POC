from datetime import datetime, timedelta
from uuid import uuid4

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from Backend.Apps.TasksDashboard.models import ClickUpProjectMapping, DailyStatusEntry, ExternalWorkMapping, ManagerAbbreviation, SlackDeliveryMessage, SlackDeliveryThread, TaskActivity, WorkEntry, WorkItem
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class WorkManagementService:
	@staticmethod
	def create_work_item(context, title, project_id=None, owner_id=None, parent_id=None, description="", priority="Normal", bounty=0, external_id="", provider=""):
		work_item = WorkItem.objects.create(
			tenant=context.tenant,
			workspace=context.workspace,
			project_id=project_id,
			owner_id=owner_id,
			parent_id=parent_id,
			title=title,
			description=description,
			priority=priority,
			bounty=max(0, float(bounty or 0)),
			source_system=provider,
			external_id=external_id,
			created_by=context.actor,
			updated_by=context.actor,
		)
		if provider and external_id:
			ExternalWorkMapping.objects.create(tenant=context.tenant, workspace=context.workspace, work_item=work_item, provider=provider, external_id=external_id, sync_status="Linked", last_synced_at=timezone.now(), created_by=context.actor, updated_by=context.actor)
		return ServiceResult.success(work_item, status_code=201)

	@staticmethod
	def transition_work_item(context, work_item_id, status, message=""):
		work_item = WorkItem.objects.filter(tenant=context.tenant, id=work_item_id).first()
		if not work_item:
			return ServiceResult.failure({"workItem": "Work Item Not Found."}, status_code=404)
		previous_status = work_item.status
		work_item.status = status
		if status in {"Completed", "C", "Done"}:
			work_item.completed_at = timezone.now()
		work_item.updated_by = context.actor
		work_item.save(update_fields=["status", "completed_at", "updated_by", "updated_at"])
		TaskActivity.objects.create(
			tenant=context.tenant,
			workspace=context.workspace,
			work_item=work_item,
			activity_type="StatusChanged",
			message=message,
			payload={"from": previous_status, "to": status},
			created_by=context.actor,
		)
		OutboxService.publish(context, "WorkItem", work_item.id, "WorkItemStatusChanged", {"from": previous_status, "to": status})
		return ServiceResult.success(work_item)

	@staticmethod
	def reorder_work_items(context, ordered_ids):
		updated = []
		for index, work_item_id in enumerate(ordered_ids):
			count = WorkItem.objects.filter(tenant=context.tenant, id=work_item_id).update(order_index=index, updated_by=context.actor)
			if count:
				updated.append(work_item_id)
		return ServiceResult.success({"count": len(updated), "workItemIds": updated})

	@staticmethod
	def initialize_timer(context, work_item_id):
		work_item = WorkItem.objects.filter(tenant=context.tenant, id=work_item_id).first()
		if not work_item:
			return ServiceResult.failure({"workItem": "Work item not found."}, status_code=404)
		work_item.timer_started_at = timezone.now()
		work_item.updated_by = context.actor
		work_item.save(update_fields=["timer_started_at", "updated_by", "updated_at"])
		return ServiceResult.success(work_item)

	@staticmethod
	def log_work_entry(context, work_item_id, employee_id, minutes=0, summary="", entry_date=None, entry_type="WorkLog"):
		work_item = WorkItem.objects.filter(tenant=context.tenant, id=work_item_id).first()
		if not work_item:
			return ServiceResult.failure({"workItem": "Work Item Not Found."}, status_code=404)
		entry = WorkEntry.objects.create(
			tenant=context.tenant,
			workspace=context.workspace or work_item.workspace,
			work_item=work_item,
			employee_id=employee_id,
			entry_date=entry_date or timezone.localdate(),
			minutes=minutes or 0,
			entry_type=entry_type,
			summary=summary,
			created_by=context.actor,
			updated_by=context.actor,
		)
		return ServiceResult.success(entry, status_code=201)


class EODService:
	@staticmethod
	def submit_status(context, employee_id, summary="", blockers="", next_plan="", status_date=None):
		status_date = status_date or timezone.localdate()
		entry, _created = DailyStatusEntry.objects.update_or_create(
			tenant=context.tenant,
			employee_id=employee_id,
			status_date=status_date,
			defaults={"workspace": context.workspace, "summary": summary, "blockers": blockers, "next_plan": next_plan, "submitted_at": timezone.now(), "updated_by": context.actor},
		)
		return ServiceResult.success(entry, status_code=201)

	@staticmethod
	def deliver_daily_summary(context, status_date=None, channel_name="daily-eod", live=False):
		status_date = status_date or timezone.localdate()
		thread, _created = SlackDeliveryThread.objects.get_or_create(
			tenant=context.tenant,
			thread_key=f"{channel_name}:{status_date.isoformat()}",
			defaults={"workspace": context.workspace, "channel_name": channel_name, "thread_date": status_date, "status": "Sent" if live else "DryRun", "external_id": f"dry-{status_date.isoformat()}", "created_by": context.actor, "updated_by": context.actor},
		)
		entries = DailyStatusEntry.objects.filter(tenant=context.tenant, status_date=status_date)
		messages = []
		for entry in entries:
			message, _created = SlackDeliveryMessage.objects.update_or_create(
				tenant=context.tenant,
				thread=thread,
				daily_status=entry,
				defaults={"workspace": context.workspace or entry.workspace, "employee": entry.employee, "status": "Sent" if live else "DryRun", "payload": {"summary": entry.summary, "blockers": entry.blockers, "next_plan": entry.next_plan}, "updated_by": context.actor},
			)
			entry.submitted_to_slack = True
			entry.slack_thread = thread
			entry.slack_message_ts = message.slack_message_ts or f"dry-{message.id}"
			entry.updated_by = context.actor
			entry.save(update_fields=["submitted_to_slack", "slack_thread", "slack_message_ts", "updated_by", "updated_at"])
			messages.append(message.id)
		OutboxService.publish(context, "SlackDeliveryThread", thread.id, "EODSlackSummaryQueued", {"count": len(messages), "dryRun": not live})
		return ServiceResult.success({"threadId": thread.id, "messageIds": messages, "count": len(messages)})

	@staticmethod
	def missing_eod_report(context, status_date=None):
		from Backend.Apps.Users.models import EmployeeProfile

		status_date = status_date or timezone.localdate()
		submitted = DailyStatusEntry.objects.filter(tenant=context.tenant, status_date=status_date).values_list("employee_id", flat=True)
		missing = EmployeeProfile.objects.filter(tenant=context.tenant, is_active=True).exclude(id__in=submitted)
		return ServiceResult.success({"status_date": status_date.isoformat(), "missing_employee_ids": list(missing.values_list("id", flat=True)), "count": missing.count()})


class ClickUpSyncService:
	@staticmethod
	def sync_tasks(context, tasks, project_mapping_id=None):
		mapping = ClickUpProjectMapping.objects.filter(tenant=context.tenant, id=project_mapping_id).first() if project_mapping_id else None
		synced = []
		for task in tasks:
			title = task.get("title") or task.get("name") or "Untitled task"
			external_id = str(task.get("id") or task.get("external_id") or "")
			work_item, _created = WorkItem.objects.update_or_create(
				tenant=context.tenant,
				source_system="ClickUp",
				external_id=external_id,
				defaults={
					"workspace": context.workspace,
					"project": mapping.project if mapping else None,
					"title": title,
					"description": task.get("description", ""),
					"status": task.get("status", "Open"),
					"priority": task.get("priority", "Normal"),
					"metadata": task,
					"updated_by": context.actor,
				},
			)
			ExternalWorkMapping.objects.update_or_create(
				tenant=context.tenant,
				provider="ClickUp",
				external_id=external_id,
				defaults={"workspace": context.workspace, "work_item": work_item, "remote_status": task.get("status", ""), "sync_status": "Synced", "last_synced_at": timezone.now(), "metadata": task, "updated_by": context.actor},
			)
			synced.append(work_item.id)
		return ServiceResult.success({"count": len(synced), "workItemIds": synced})

	@staticmethod
	def clear_synced_tasks(context, provider="ClickUp"):
		mappings = ExternalWorkMapping.objects.filter(tenant=context.tenant, provider=provider)
		count = mappings.update(sync_status="Cleared", updated_by=context.actor)
		return ServiceResult.success({"count": count})


class ManagerAbbreviationService:
	@staticmethod
	def generate(context, employee):
		parts = [part[0].upper() for part in employee.display_name.split() if part]
		abbreviation = "".join(parts[:3]) or employee.employee_code[:3].upper()
		item, _created = ManagerAbbreviation.objects.update_or_create(
			tenant=context.tenant,
			employee=employee,
			defaults={"workspace": context.workspace or employee.workspace, "abbreviation": abbreviation, "updated_by": context.actor},
		)
		return ServiceResult.success(item, status_code=201)


class TasksDashboardLegacyService:
	SYNC_CACHE_PREFIX = "tasksdashboard:clickup-sync:"

	@staticmethod
	def _project_manager_assignment(project):
		from Backend.Apps.Project.models import TeamAssignment

		assignments = TeamAssignment.objects.filter(project=project, status="Active").select_related("employee", "employee__user")
		preferred = assignments.filter(
			Q(role__icontains="manager")
			| Q(role__iexact="pm")
			| Q(role__iexact="spm")
			| Q(role__icontains="lead")
		).order_by("id").first()
		return preferred or assignments.order_by("id").first()

	@staticmethod
	def _manager_payload(context, project):
		assignment = TasksDashboardLegacyService._project_manager_assignment(project) if project else None
		if not assignment:
			return None
		abbreviation = ManagerAbbreviation.objects.filter(tenant=context.tenant, employee=assignment.employee).first()
		if not abbreviation:
			generated = ManagerAbbreviationService.generate(context, assignment.employee)
			abbreviation = generated.data if generated.ok else None
		return {
			"employee_id": assignment.employee_id,
			"display_name": assignment.employee.display_name,
			"abbreviation": abbreviation.abbreviation if abbreviation else "--",
		}

	@staticmethod
	def _task_payload(context, work_item):
		manager = TasksDashboardLegacyService._manager_payload(context, work_item.project) if work_item.project_id else None
		return {
			"id": work_item.id,
			"name": work_item.title,
			"status": work_item.status,
			"due_date": work_item.due_at.isoformat() if work_item.due_at else None,
			"manager": f"({manager['abbreviation']})" if manager else "--",
			"project_name": work_item.project.name if work_item.project_id else "",
			"milestone": work_item.metadata.get("milestone", ""),
			"subtask_count": work_item.subtasks.count(),
		}

	@staticmethod
	def _parse_month_filter(filter_type):
		if not filter_type or filter_type in {"last_7_days", "last_15_days"}:
			return None
		try:
			return datetime.strptime(str(filter_type).title(), "%B").month
		except ValueError:
			return None

	@staticmethod
	def build_dashboard(context, work_type="", manager_ids=None, project_names=None):
		from Backend.Apps.Project.models import ProjectWorkspace

		manager_ids = [int(manager_id) for manager_id in manager_ids or [] if str(manager_id).isdigit()]
		project_names = [project_name for project_name in (project_names or []) if project_name]
		projects = ProjectWorkspace.objects.filter(tenant=context.tenant)
		if work_type:
			projects = projects.filter(project_type__iexact=work_type)
		if manager_ids:
			projects = projects.filter(team_assignments__employee_id__in=manager_ids).distinct()
		if project_names:
			projects = projects.filter(name__in=project_names)

		work_items = WorkItem.objects.filter(tenant=context.tenant).exclude(status__in=["Completed", "C", "Done"]).select_related("project", "owner")
		if work_type:
			work_items = work_items.filter(project__project_type__iexact=work_type)
		if manager_ids:
			work_items = work_items.filter(project__team_assignments__employee_id__in=manager_ids).distinct()
		if project_names:
			work_items = work_items.filter(project__name__in=project_names)

		today = timezone.localdate()
		three_days_ago = today - timedelta(days=3)
		seven_days_ago = today - timedelta(days=7)

		def serialize_projects(queryset):
			rows = []
			for project in queryset.order_by("name"):
				manager = TasksDashboardLegacyService._manager_payload(context, project)
				rows.append({"project_name": project.name, "manager": f"({manager['abbreviation']})" if manager else "--"})
			return rows

		projects_3_days = serialize_projects(projects.filter(updated_at__date__gte=three_days_ago))
		projects_7_days = serialize_projects(projects.filter(updated_at__date__lt=three_days_ago, updated_at__date__gte=seven_days_ago))
		projects_7plus_days = serialize_projects(projects.filter(Q(updated_at__date__lt=seven_days_ago) | Q(updated_at__isnull=True)))

		tasks_rows = [TasksDashboardLegacyService._task_payload(context, work_item) for work_item in work_items.order_by("-due_at", "id")]
		tasks_overdue = [row for row in tasks_rows if row["due_date"] and row["due_date"][:10] < today.isoformat()]
		tasks_due_today = [row for row in tasks_rows if row["due_date"] and row["due_date"][:10] == today.isoformat()]
		tasks_due_tomorrow = [row for row in tasks_rows if row["due_date"] and row["due_date"][:10] == (today + timedelta(days=1)).isoformat()]
		tasks_without_due_date = [row for row in tasks_rows if not row["due_date"]]

		managers = []
		seen_manager_ids = set()
		for project in projects:
			manager = TasksDashboardLegacyService._manager_payload(context, project)
			if manager and manager["employee_id"] not in seen_manager_ids:
				seen_manager_ids.add(manager["employee_id"])
				managers.append(manager)

		return ServiceResult.success(
			{
				"tasks": tasks_rows,
				"projects_3_days": projects_3_days,
				"projects_7_days": projects_7_days,
				"projects_7plus_days": projects_7plus_days,
				"managers": managers,
				"Dashboard_clickup": True,
				"tasks_overdue": tasks_overdue,
				"tasks_due_today": tasks_due_today,
				"tasks_due_tomorrow": tasks_due_tomorrow,
				"tasks_without_due_date": tasks_without_due_date,
			}
		)

	@staticmethod
	def _latest_sync_timestamp(context):
		mapping = ExternalWorkMapping.objects.filter(tenant=context.tenant, provider="ClickUp", last_synced_at__isnull=False).order_by("-last_synced_at").first()
		if mapping:
			return mapping.last_synced_at
		project_mapping = ClickUpProjectMapping.objects.filter(tenant=context.tenant).order_by("-updated_at").first()
		return project_mapping.updated_at if project_mapping else None

	@staticmethod
	def check_log_update(context):
		latest_sync = TasksDashboardLegacyService._latest_sync_timestamp(context)
		if latest_sync and (timezone.now() - latest_sync).total_seconds() <= 40:
			return ServiceResult.success({"status": "UPDATED"})
		return ServiceResult.success({"status": "NOT_UPDATED"})

	@staticmethod
	def initialize_sync_timer(context):
		latest_sync = TasksDashboardLegacyService._latest_sync_timestamp(context)
		if not latest_sync:
			return ServiceResult.success({"minutes": "0"})
		minutes = int((timezone.now() - latest_sync).total_seconds() // 60)
		return ServiceResult.success({"minutes": str(minutes)})

	@staticmethod
	def update_clickup(context, tasks=None, project_mapping_id=None):
		task_id = uuid4().hex
		result = ClickUpSyncService.sync_tasks(context, tasks or [], project_mapping_id=project_mapping_id)
		payload = {"status": "completed" if result.ok else "failed", "result": result.data if result.ok else result.errors}
		cache.set(f"{TasksDashboardLegacyService.SYNC_CACHE_PREFIX}{task_id}", payload, timeout=3600)
		return ServiceResult.success({"task_id": task_id})

	@staticmethod
	def check_task_status(task_id):
		payload = cache.get(f"{TasksDashboardLegacyService.SYNC_CACHE_PREFIX}{task_id}") or {"status": "PENDING"}
		return ServiceResult.success(payload)

	@staticmethod
	def reorder_all_tasks(context):
		ordered_ids = list(WorkItem.objects.filter(tenant=context.tenant).order_by("id").values_list("id", flat=True))
		return WorkManagementService.reorder_work_items(context, ordered_ids)

	@staticmethod
	def create_missing_activities(context):
		created = 0
		for work_item in WorkItem.objects.filter(tenant=context.tenant, activities__isnull=True).order_by("id"):
			TaskActivity.objects.create(
				tenant=context.tenant,
				workspace=context.workspace or work_item.workspace,
				work_item=work_item,
				actor=work_item.owner,
				activity_type="Created",
				message=f"Created at {timezone.localtime(work_item.created_at).strftime('%d %b %y')}",
				created_by=context.actor,
				updated_by=context.actor,
			)
			created += 1
		return ServiceResult.success({"status": "success", "count": created})

	@staticmethod
	def eod_report(context, employee_id=None, filter_type=""):
		today = timezone.localdate()
		queryset = DailyStatusEntry.objects.filter(tenant=context.tenant).select_related("employee", "employee__user")
		if employee_id:
			queryset = queryset.filter(employee_id=employee_id)
		if filter_type == "last_7_days":
			queryset = queryset.filter(status_date__gte=today - timedelta(days=7))
		elif filter_type == "last_15_days":
			queryset = queryset.filter(status_date__gte=today - timedelta(days=15))
		else:
			month_number = TasksDashboardLegacyService._parse_month_filter(filter_type)
			if month_number:
				queryset = queryset.filter(status_date__month=month_number)
		rows = [
			{
				"id": entry.id,
				"user_id": entry.employee_id,
				"user_name": entry.employee.display_name,
				"date": entry.status_date.isoformat(),
				"summary": entry.summary,
				"blockers": entry.blockers,
				"next_plan": entry.next_plan,
			}
			for entry in queryset.order_by("-status_date", "-id")
		]
		return ServiceResult.success({"count": len(rows), "results": rows})