from django.contrib import admin

from Backend.Apps.Project.models import ComplianceAssignment, ComplianceCampaign, DefaultCheckpoint, DeliveryAlert, DeliveryDocument, DeliveryMilestone, MilestoneComponent, ProjectContact, ProjectDelay, ProjectWorkspace, RepositoryLink, TeamAssignment


admin.site.register(ProjectWorkspace)
admin.site.register(ProjectContact)
admin.site.register(DefaultCheckpoint)
admin.site.register(MilestoneComponent)
admin.site.register(DeliveryMilestone)
admin.site.register(TeamAssignment)
admin.site.register(RepositoryLink)
admin.site.register(DeliveryDocument)
admin.site.register(DeliveryAlert)
admin.site.register(ComplianceCampaign)
admin.site.register(ComplianceAssignment)
admin.site.register(ProjectDelay)