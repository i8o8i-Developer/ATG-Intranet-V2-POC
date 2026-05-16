from django.contrib import admin

from Backend.Apps.Project.models import ComplianceAssignment, ComplianceCampaign, DefaultCheckpoint, DeliveryAlert, DeliveryDocument, DeliveryMilestone, MilestoneComponent, ProjectBudget, ProjectContact, ProjectDelay, ProjectWorkspace, RepositoryLink, TeamAssignment, TeamAssignmentHistory


class ProjectWorkspaceAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "project_type", "associate_project_manager", "project_manager", "status", "health", "priority", "starts_on", "ends_on"]
    list_filter = ["project_type", "status", "health", "priority"]
    search_fields = ["name", "code", "client_name"]
    raw_id_fields = ["associate_project_manager", "project_manager"]


class TeamAssignmentAdmin(admin.ModelAdmin):
    list_display = ["project", "employee", "role", "status", "allocation_percent"]
    list_filter = ["status", "role"]


class DeliveryMilestoneAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "status", "due_on", "bounty"]
    list_filter = ["status", "project__project_type"]


admin.site.register(ProjectWorkspace, ProjectWorkspaceAdmin)
admin.site.register(ProjectContact)
admin.site.register(DefaultCheckpoint)
admin.site.register(MilestoneComponent)
admin.site.register(DeliveryMilestone, DeliveryMilestoneAdmin)
admin.site.register(TeamAssignment, TeamAssignmentAdmin)
admin.site.register(RepositoryLink)
admin.site.register(DeliveryDocument)
admin.site.register(DeliveryAlert)
admin.site.register(ComplianceCampaign)
admin.site.register(ComplianceAssignment)
admin.site.register(ProjectDelay)
admin.site.register(ProjectBudget)
admin.site.register(TeamAssignmentHistory)
