from django.contrib import admin

from Backend.Apps.Banao.models import AuditArtifact, LeadAccount, LeadActivity, LeadContact, LeadNote, LeadTag, LeadTest, ProposalArtifact, WorkflowStatusHistory, WorkflowTransition


@admin.register(LeadAccount)
class LeadAccountAdmin(admin.ModelAdmin):
    list_display = ("company_name", "stage", "priority", "owner", "estimated_value", "tenant")
    list_filter = ("stage", "priority", "source", "tenant")
    search_fields = ("company_name", "source")


@admin.register(LeadTag)
class LeadTagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "tenant")


@admin.register(LeadContact)
class LeadContactAdmin(admin.ModelAdmin):
    list_display = ("name", "lead", "email", "phone", "is_primary", "tenant")
    search_fields = ("name", "email", "phone")


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ("lead", "activity_type", "title", "scheduled_at", "completed_at", "tenant")
    list_filter = ("activity_type", "tenant")


@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ("lead", "title", "author", "tenant", "created_at")
    search_fields = ("title", "body")


@admin.register(LeadTest)
class LeadTestAdmin(admin.ModelAdmin):
    list_display = ("lead", "title", "status", "score", "due_at", "tenant")
    list_filter = ("status", "tenant")


@admin.register(ProposalArtifact)
class ProposalArtifactAdmin(admin.ModelAdmin):
    list_display = ("lead", "title", "status", "amount", "sent_at", "tenant")
    list_filter = ("status", "tenant")


@admin.register(AuditArtifact)
class AuditArtifactAdmin(admin.ModelAdmin):
    list_display = ("lead", "title", "status", "tenant")
    list_filter = ("status", "tenant")


@admin.register(WorkflowTransition)
class WorkflowTransitionAdmin(admin.ModelAdmin):
    list_display = ("lead", "from_stage", "to_stage", "changed_by", "tenant", "created_at")
    list_filter = ("to_stage", "tenant")


@admin.register(WorkflowStatusHistory)
class WorkflowStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("lead", "status", "result", "checked_at", "tenant")
    list_filter = ("result", "status", "tenant")
