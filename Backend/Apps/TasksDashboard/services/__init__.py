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
			bounty=bounty or 0,
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
			return ServiceResult.failure({"workItem": "Work item not found."}, status_code=404)
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
			return ServiceResult.failure({"workItem": "Work item not found."}, status_code=404)
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