from django import forms

from Backend.Apps.TasksDashboard.models import ClickUpProjectMapping, DailyStatusEntry, WorkEntry, WorkItem


class WorkItemForm(forms.ModelForm):
    class Meta:
        model = WorkItem
        fields = ["project", "parent", "owner", "title", "description", "status", "priority", "order_index", "bounty", "due_at", "metadata"]


class WorkEntryForm(forms.ModelForm):
    class Meta:
        model = WorkEntry
        fields = ["work_item", "employee", "entry_date", "minutes", "entry_type", "summary", "metadata"]


class DailyStatusEntryForm(forms.ModelForm):
    class Meta:
        model = DailyStatusEntry
        fields = ["employee", "status_date", "summary", "blockers", "next_plan", "submitted_to_slack", "metadata"]


class ClickUpProjectMappingForm(forms.ModelForm):
    class Meta:
        model = ClickUpProjectMapping
        fields = ["project", "project_name", "space_id", "list_id", "sync_status", "metadata"]