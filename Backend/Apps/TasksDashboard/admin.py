from django.contrib import admin

from Backend.Apps.TasksDashboard.models import ClickUpProjectMapping, DailyStatusEntry, ExternalWorkMapping, ManagerAbbreviation, SlackDeliveryMessage, SlackDeliveryThread, TaskActivity, WorkEntry, WorkItem


admin.site.register(WorkItem)
admin.site.register(WorkEntry)
admin.site.register(TaskActivity)
admin.site.register(DailyStatusEntry)
admin.site.register(SlackDeliveryThread)
admin.site.register(SlackDeliveryMessage)
admin.site.register(ExternalWorkMapping)
admin.site.register(ManagerAbbreviation)
admin.site.register(ClickUpProjectMapping)